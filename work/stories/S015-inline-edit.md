---
id: S015
type: story
status: planned
parent_epic: E002
parent_feature: F008
depends_on: [F007]
owned_paths: [crates/domain/src/grid/**, services/api/src/grid/**, services/api/migrations/*_grid_*.sql, testing/features/F008/**]
feature_flag: F008_FEATURE
branch: s015-inline-edit
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4
- Capability contract: `docs/capability-contracts.md` row F008

# S015 — Inline edit

## Identity

- Parent feature: `F008` Grid editing
- Owner: platform
- Branch: `s015-inline-edit`
- Decision references: `docs/architecture-decisions.md` sections 2–4; `docs/capability-contracts.md` row F008

## Vertical slice

As a sheet editor, I want to change individual cells with per-cell validation and version checks, undo and redo my own edits, read a cell's history, refresh from a change feed, and keep my column layout, so that everyday grid editing is safe under concurrent use before any bulk tooling exists.

## Requirements

- **SR-S015-01:** `PATCH /api/v1/sheets/{sheet_id}/cells` with 1–200 edits normalizes each value through F007, checks `expected_row_version` under `FOR UPDATE`, and returns per-cell `applied | invalid | conflict` with a summary (covers FR-F008-01).
- **SR-S015-02:** Every applied cell writes `cell_history`, an audit event, increments `sheets.change_version`, and publishes `cell.updated.v1` with `changed_fields` and `correlation_id` in the same transaction (FR-F008-02).
- **SR-S015-03:** Each patch creates an `edit_batches` row with inverse cells; the actor's stack per sheet is trimmed to 50 (FR-F008-05).
- **SR-S015-04:** `POST /undo` and `POST /redo` apply the inverse only when recorded row versions still match, otherwise return `409 conflict` listing changed cells; a new edit after undo discards the redo stack; success publishes `edit.undone.v1` (FR-F008-06, FR-F008-07).
- **SR-S015-05:** `GET /api/v1/sheets/{sheet_id}/changes?since=` returns ordered changes with `next_since` and the actor's `layout`, `limit` ≤ 1,000 (FR-F008-08).
- **SR-S015-06:** `GET /api/v1/cells/{row_id}/{column_id}/history` pages newest first and requires read access to the row (FR-F008-09).
- **SR-S015-07:** The optional `layout` field on `PATCH cells` upserts `sheet_user_layouts` for the actor, rejects hiding the primary column, and bounds `frozen_column_count` to 0–5 (FR-F008-10).
- **SR-S015-08:** Viewers and commenters receive `403 denied` on mutations; foreign-tenant actors receive `404 not_found` on every route; `Idempotency-Key` replay returns the stored response (FR-F008-15, FR-F008-16).

## Surfaces

- Infrastructure/container: none beyond F004 baseline
- Rust service/API: `crates/domain/src/grid/{mod.rs, edit.rs, batch.rs, inverse.rs, history.rs, layout.rs, feed.rs, errors.rs, service.rs}`; `services/api/src/grid/{mod.rs, routes.rs, handlers_cells.rs, handlers_undo.rs, handlers_feed.rs, handlers_history.rs, dto.rs}`; tables are reached through `CellHistoryRepository`, `EditBatchRepository`, and `SheetUserLayoutRepository` in `crates/persistence/src/grid/`, and cells, rows, and `sheets.change_version` through the F006 `CellRepository`, `RowRepository`, and `SheetRepository`; `inverse.rs` builds the inverse from the batch's `cell_history` rows and the row lock is `RowRepository::lock_rows_for_edit`, so no handler, service, or test holds SQL (decision 2.1)
- Data/migration: `services/api/migrations/<ts>_grid_create_tables.sql` creating `cell_history`, `edit_batches`, `sheet_user_layouts`, `sheet_user_column_layouts`, and adding `change_version` to `sheets` and `cells` with the indexes from ticket section 4, including `cell_history(batch_id)` for the undo read
- React/UI: none in this story (S016 and T031 cover the grid)
- Mocks/fixtures: `testing/fixtures/grid.rs` tenant, 12-column sheet, 500 rows, editor A, editor B, commenter, viewer, foreign tenant; in-memory outbox recorder

## TDD harness

- Test path: `testing/features/F008/api/` and `testing/features/F008/database/`
- Feature flag: `F008_FEATURE`
- Targeted command: `cargo xtask test-feature F008`
- Full command: `cargo xtask test-all`
- First failing tests: `patch_cells_reports_per_cell_outcomes`, `patch_cells_writes_history_and_event`, `undo_conflicts_when_other_user_changed_cell`, `redo_stack_discarded_by_new_edit`, `changes_feed_orders_by_change_version`, `layout_upsert_rejects_hidden_primary`, `viewer_patch_denied`

## Exit criteria

- [ ] Requirement tests SR-S015-01 through SR-S015-08 written first and failing
- [ ] Tasks T029 and T030 complete and wired through `services/api` router
- [ ] Unit, API, database, permission tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/grid/routes.rs` mounted in `services/api/src/router.rs`
- [ ] Handoff evidence recorded in the F008 ticket
