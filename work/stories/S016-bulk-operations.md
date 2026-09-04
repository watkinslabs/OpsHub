---
id: S016
type: story
status: planned
parent_epic: E002
parent_feature: F008
depends_on: [S015]
owned_paths: [crates/domain/src/grid/**, services/api/src/grid/**, apps/web/src/features/grid/**, testing/features/F008/**]
feature_flag: F008_FEATURE
branch: s016-bulk-operations
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 6, 9
- Capability contract: `docs/capability-contracts.md` row F008

# S016 — Bulk operations

## Identity

- Parent feature: `F008` Grid editing
- Owner: platform
- Branch: `s016-bulk-operations`
- Decision references: `docs/architecture-decisions.md` sections 2–4, 6, 9; `docs/capability-contracts.md` row F008

## Vertical slice

As a sheet editor, I want to paste blocks, fill ranges, multi-select, bulk edit rows and cells, resize, reorder, hide, and freeze columns, and undo any of it from a virtualized grid, so that a 100,000-row sheet is maintained as fast as a spreadsheet while every change is typed, versioned, and auditable.

## Requirements

- **SR-S016-01:** `POST /api/v1/sheets/{sheet_id}/cells/bulk` with `mode set|fill|clear`, a selection of row IDs or filter, and column IDs applies up to 5,000 cells in one transaction, returns counts and row versions, and emits one `cells.bulk-updated.v1`; 5,001 cells returns `400 invalid` with `field_errors.selection` (FR-F008-03).
- **SR-S016-02:** `POST /api/v1/sheets/{sheet_id}/rows/bulk` applies the same cell map to up to 1,000 rows, returns per-row versions, and emits one `rows.bulk-updated.v1` (FR-F008-04).
- **SR-S016-03:** Bulk requests create an `edit_batches` row so `undo` reverts the whole batch or reports `conflict` on changed cells (FR-F008-05, FR-F008-06).
- **SR-S016-04:** `ClipboardController` maps a pasted TSV block to visible columns in order, chunks into 200-cell patches, and badges invalid cells with their code without aborting the paste (FR-F008-11).
- **SR-S016-05:** `FillHandle` continues numeric and date sequences and repeats text through `mode: fill`; Ctrl+D fills down the selection (FR-F008-12).
- **SR-S016-06:** `VirtualGrid` renders at most 60 rows and 40 columns for a 100,000-row, 500-column sheet, supports Shift+Arrow, Shift+Click, and Ctrl+Click selection, and keeps 60 fps scrolling (FR-F008-13, NFR-F008-01).
- **SR-S016-07:** Column resize, reorder, hide, and freeze apply immediately and persist through the `layout` field within 1 s; the layout is restored on the next visit and never shown to other users (FR-F008-14).
- **SR-S016-08:** `BulkEditDialog` previews the affected row count, applies through the bulk routes, and toasts applied, invalid, and conflict counts; `CellHistoryPopover` pages history; viewers see read-only cells and the denied state (FR-F008-09, FR-F008-15, NFR-F008-03).

## Surfaces

- Infrastructure/container: none
- Rust service/API: `crates/domain/src/grid/{bulk.rs, selection.rs, fill.rs}`; `services/api/src/grid/handlers_bulk.rs`; the bulk paths use the same `crates/persistence/src/grid/` repositories plus the F006 `CellRepository` and `RowRepository` and contain no SQL (decision 2.1)
- Data/migration: none new; uses `cell_history`, `edit_batches`, `sheet_user_layouts`, and `sheet_user_column_layouts` from S015 through those repositories
- React/UI: `apps/web/src/features/grid/{VirtualGrid.tsx, GridHeaderRow.tsx, GridRow.tsx, GridCell.tsx, CellEditor.tsx, SelectionModel.ts, ClipboardController.ts, FillHandle.tsx, UndoRedoController.ts, ColumnResizeHandle.tsx, ColumnHeaderMenu.tsx, FrozenColumnsPane.tsx, BulkEditDialog.tsx, CellHistoryPopover.tsx, ConflictOutline.tsx, api.ts, hooks.ts}`
- Mocks/fixtures: seeded 12-column/500-row sheet; 100,000-row generator for performance lane; MSW handlers for component tests; two-browser Playwright context for conflicts

## TDD harness

- Test path: `testing/features/F008/{api,frontend,e2e,accessibility,performance}/`
- Feature flag: `F008_FEATURE`
- Targeted command: `cargo xtask test-feature F008`
- Full command: `cargo xtask test-all`
- First failing tests: `bulk_cells_applies_and_emits_one_event`, `bulk_cells_rejects_over_5000`, `bulk_rows_returns_row_versions`, `paste_tsv_maps_to_visible_columns`, `fill_handle_continues_number_sequence`, `virtual_grid_renders_viewport_only`, `layout_persists_per_user`, `bulk_5000_cells_under_5s`

## Exit criteria

- [ ] Requirement tests SR-S016-01 through SR-S016-08 written first and failing
- [ ] Tasks T031 and T032 complete; UI wired to real API through generated client
- [ ] Unit, API, React, E2E, accessibility, permission, and performance tests pass
- [ ] Production call path named: `apps/web/src/features/grid/VirtualGrid.tsx` mounted by `apps/web/src/features/sheets/SheetPage.tsx` at `/w/:workspaceId/sheets/:sheetId?mode=grid`
- [ ] Handoff evidence recorded in the F008 ticket
