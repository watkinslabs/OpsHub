---
id: T029
type: task
status: planned
parent_epic: E002
parent_feature: F008
parent_story: S015
depends_on: [S015]
owned_paths: [services/api/migrations/*_grid_*.sql, crates/domain/src/grid/**, services/api/src/grid/**, testing/features/F008/database/**, testing/features/F008/api/**]
feature_flag: F008_FEATURE
branch: t029-optimistic-concurrency-and-undo
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4
- Capability contract: `docs/capability-contracts.md` row F008

# T029 — Optimistic concurrency and undo

## Identity

- Parent story: `S015` Inline edit
- Owner: platform
- Branch: `t029-optimistic-concurrency-and-undo`
- Decision references: `docs/architecture-decisions.md` sections 2–4; `docs/capability-contracts.md` row F008

## Objective

Create the grid schema and implement version-checked cell patching, edit batches whose inverse is their `cell_history` rows, and the undo and redo routes so every single-cell edit is safe under concurrent editors and reversible.

## Specification

- Owned paths: `services/api/migrations/<ts>_grid_create_tables.sql`, `services/api/migrations/<ts>_grid_create_tables.down.sql`, `crates/domain/src/grid/{mod.rs, edit.rs, batch.rs, inverse.rs, history.rs, errors.rs, service.rs, schema.rs}`, `services/api/src/grid/{mod.rs, routes.rs, handlers_cells.rs, handlers_undo.rs, dto.rs}`
- Contract/input: DDL per F008 ticket section 4 (`cell_history`, `edit_batches` with no `inverse` column, `sheet_user_layouts` carrying only `frozen_column_count` and `version`, `sheet_user_column_layouts(tenant_id, sheet_id, user_id, column_id references columns(id) on delete cascade, width, position, hidden)`, `sheets.change_version`, `cells.change_version`, indexes including `cell_history(batch_id)`, check constraints); `PatchCellsRequest { edits: [{ row_id, column_id, value, expected_row_version }] (0–200), layout? }`; `POST /undo` and `POST /redo` with empty bodies; headers `Idempotency-Key`, `If-Match` not required because versions travel per edit.
- Output/behavior: `PATCH /api/v1/sheets/{sheet_id}/cells` locks target rows through `RowRepository::lock_rows_for_edit` (the only `FOR UPDATE` statement, inside `crates/persistence`), normalizes through `columns::normalize`, writes cells, one `cell_history` row per changed cell carrying `previous_raw`, `new_raw`, and the row version, one `edit_batches` row, audit rows, and `cell.updated.v1` per applied cell in one `UnitOfWork`, then returns `PatchCellsResponse { results, summary, batch_id }`; stack trimmed to 50 per `(sheet_id, actor_id)`; `POST /api/v1/sheets/{sheet_id}/undo` and `/redo` read the batch's inverse through `CellHistoryRepository::inverse_for_batch`, verify the recorded row versions, apply the inverse, set `undone_at`/`redone_at`, publish `edit.undone.v1`, and return `UndoRedoResponse`; new edits after undo delete pending redo batches; error mapping per ticket section 4.
- Dependencies: F006 `RowRepository` and `CellRepository` with the row lock helper; F007 `ColumnType` normalizer and validation codes; F003 `authz::require(actor, Permission::SheetEdit, sheet)`; F004 outbox writer.
- Feature flag: `F008_FEATURE` gates router mounting; migration runs regardless.
- Large-table note: `cell_history` grows with every edit, so the migration adds the `(row_id, column_id, occurred_at desc)` index up front and future changes must be additive.

## TDD

- Failing test first: `testing/features/F008/database/migration_tests.rs::grid_tables_exist_with_constraints`, `::cell_history_version_unique`, `::cell_history_batch_index_supports_inverse_lookup`, `::layout_frozen_count_check`, `::layout_column_row_cascades_with_column`, `::rollback_drops_tables`; `testing/features/F008/api/cell_tests.rs::patch_cells_reports_per_cell_outcomes`, `::patch_cells_writes_history_and_event`, `::patch_cells_rejects_201_edits`, `::patch_cells_idempotent_replay`; `testing/features/F008/api/undo_tests.rs::undo_reverts_last_batch`, `::undo_conflicts_when_other_user_changed_cell`, `::redo_stack_discarded_by_new_edit`, `::stack_trimmed_to_50`
- Targeted command: `cargo xtask test-feature F008`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: schema-per-worker database from `testing/harness/db.rs`; `testing/fixtures/grid.rs` editor A and editor B; in-memory outbox recorder

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; router mounted in `services/api/src/router.rs` behind the flag
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S015
- [ ] `finished_at` recorded
