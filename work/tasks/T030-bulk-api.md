---
id: T030
type: task
status: planned
parent_epic: E002
parent_feature: F008
parent_story: S015
depends_on: [T029]
owned_paths: [crates/domain/src/grid/**, services/api/src/grid/**, testing/features/F008/api/**, testing/features/F008/requirements/**]
feature_flag: F008_FEATURE
branch: t030-bulk-api
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4
- Capability contract: `docs/capability-contracts.md` row F008

# T030 — Bulk API

## Identity

- Parent story: `S015` Inline edit
- Owner: platform
- Branch: `t030-bulk-api`
- Decision references: `docs/architecture-decisions.md` sections 2–4; `docs/capability-contracts.md` row F008

## Objective

Implement the bulk cell and bulk row routes, the change feed, the cell history route, and per-user layout persistence so the grid has every server capability it needs for paste, fill, bulk edit, refresh, and layout.

## Specification

- Owned paths: `crates/domain/src/grid/{bulk.rs, selection.rs, fill.rs, feed.rs, layout.rs}`, `services/api/src/grid/{handlers_bulk.rs, handlers_feed.rs, handlers_history.rs}`
- Contract/input: `BulkCellsRequest { mode: set|fill|clear, selection: { row_ids?: [uuid], filter?: FilterExpr }, column_ids: [uuid], value?, source_cell?: { row_id, column_id } }` ≤ 5,000 target cells; `BulkRowsRequest { mode: set|clear, selection, cells: { column_id: value } }` ≤ 1,000 rows; `GET /changes?since=&limit=` with `limit` 1–1,000; `GET /api/v1/cells/{row_id}/{column_id}/history?cursor=&limit=` with `limit` ≤ 100; `layout` object on `PATCH cells` per FR-F008-10.
- Output/behavior: `POST /api/v1/sheets/{sheet_id}/cells/bulk` and `POST /api/v1/sheets/{sheet_id}/rows/bulk` resolve the selection (`resolve_selection` caps at 1,000 rows / 5,000 cells, over-cap returns `400 invalid` with `field_errors.selection = "too_large"`), lock rows through `RowRepository::lock_rows_for_edit`, normalize per F007, write cells and `cell_history`, one `edit_batches` row whose inverse is those history rows, aggregate audit row, and one `cells.bulk-updated.v1` or `rows.bulk-updated.v1` event in one transaction, returning `BulkResponse { batch_id, applied, invalid, conflict, row_versions }`; `fill.rs` continues integer, decimal, and date sequences from `source_cell` and repeats text; `GET /api/v1/sheets/{sheet_id}/changes` calls `CellRepository::changes_since` (`change_version > since`, ascending) and returns `ChangesResponse { changes, next_since, layout }`; `GET /api/v1/cells/{row_id}/{column_id}/history` pages `CellHistoryRepository` newest first; `save_user_layout` upserts the actor's `sheet_user_layouts` row and replaces its `sheet_user_column_layouts` rows through `SheetUserLayoutRepository` in one transaction, assembling the same `layout` object on read, rejects a hidden primary column with `field_errors.layout.hidden_columns`, and bounds `frozen_column_count` 0–5. Every statement lives in `crates/persistence/src/grid/`; the handlers and domain modules hold none (decision 2.1).
- Dependencies: T029 schema, batch, and inverse code; F007 normalizer; the F006 `RowRepository` lock helper and `CellRepository`; F003 authz; F004 `OutboxRepository`.
- Feature flag: `F008_FEATURE`

## TDD

- Failing test first: `testing/features/F008/api/bulk_tests.rs::bulk_cells_applies_and_emits_one_event`, `::bulk_cells_rejects_over_5000`, `::bulk_cells_fill_continues_date_sequence`, `::bulk_rows_returns_row_versions`, `::bulk_batch_undo_reverts_all_cells`; `testing/features/F008/api/feed_tests.rs::changes_feed_orders_by_change_version`, `::changes_feed_returns_actor_layout`; `testing/features/F008/api/history_tests.rs::history_pages_newest_first`, `::history_cross_tenant_not_found`; `testing/features/F008/api/layout_tests.rs::layout_upsert_rejects_hidden_primary`, `::layout_is_private_per_user`, `::layout_replaces_column_rows_atomically`
- Targeted command: `cargo xtask test-feature F008`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: seeded 12-column/500-row sheet; in-memory outbox recorder; fixed clock for date sequences

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] All seven F008 routes mounted; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S015
- [ ] `finished_at` recorded
