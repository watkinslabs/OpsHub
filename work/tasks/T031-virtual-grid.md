---
id: T031
type: task
status: planned
parent_epic: E002
parent_feature: F008
parent_story: S016
depends_on: [T030]
owned_paths: [apps/web/src/features/grid/**, testing/features/F008/frontend/**, testing/features/F008/accessibility/**]
feature_flag: F008_FEATURE
branch: t031-virtual-grid
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 3, 6, 9
- Capability contract: `docs/capability-contracts.md` row F008

# T031 — Virtual grid

## Identity

- Parent story: `S016` Bulk operations
- Owner: platform
- Branch: `t031-virtual-grid`
- Decision references: `docs/architecture-decisions.md` sections 3, 6, 9; `docs/capability-contracts.md` row F008

## Objective

Build the virtualized, keyboard-accessible editing grid with inline editors, paste, fill, multi-select, undo/redo, column layout controls, the bulk edit dialog, and the cell history popover wired to the real grid API.

## Specification

- Owned paths: `apps/web/src/features/grid/{VirtualGrid.tsx, GridHeaderRow.tsx, GridRow.tsx, GridCell.tsx, CellEditor.tsx, SelectionModel.ts, ClipboardController.ts, FillHandle.tsx, UndoRedoController.ts, ColumnResizeHandle.tsx, ColumnHeaderMenu.tsx, FrozenColumnsPane.tsx, BulkEditDialog.tsx, CellHistoryPopover.tsx, ConflictOutline.tsx, api.ts, hooks.ts, index.ts}`
- Contract/input: generated `GridApi` client (`patchCells`, `bulkEditCells`, `bulkEditRows`, `undo`, `redo`, `listChanges`, `listCellHistory`); F006 `SheetPage` passes `sheetId`, columns from F007 `['columns', sheetId]`, and rows from `['grid-rows', sheetId, cursor]`.
- Output/behavior: `VirtualGrid` renders at most 60 rows and 40 columns with `role="grid"`, `aria-rowindex`, `aria-colindex`; `CellEditor` picks the editor by column type and submits through `patchCells` with optimistic update, reconciling per-cell `applied`, `invalid` (code badge), or `conflict` (`ConflictOutline` with actor name and `Reload`); `SelectionModel` supports Shift+Arrow, Shift+Click, Ctrl+Click, Ctrl+A; `ClipboardController` parses TSV, maps to visible columns, chunks 200 cells per request; `FillHandle` and Ctrl+D call `bulkEditCells` with `mode: fill`; `UndoRedoController` binds Ctrl+Z/Ctrl+Y and announces results in a live region; `ColumnResizeHandle`, `ColumnHeaderMenu` (reorder, hide, freeze up to here), and `FrozenColumnsPane` update `['grid-layout', sheetId]` and debounce a `layout`-only `patchCells` by 1 s; `BulkEditDialog` previews the row count and toasts results; `CellHistoryPopover` pages `listCellHistory`; the change feed polls every 15 s while visible; states: loading skeleton, empty, error banner with correlation ID, denied read-only cells, offline badge with editing disabled; Lucide icons and tokens per ticket section 3; telemetry `cell_edited`, `cells_pasted`, `fill_applied`, `edit_undone`, `edit_redone`, `bulk_edit_applied`, `layout_changed`.
- Dependencies: T030 routes; F006 `SheetPage` mount point; F007 column metadata and editor value formats.
- Feature flag: `F008_FEATURE` read through the flag hook; `SheetPage` falls back to the F006 read-only `GridView` when off.

## TDD

- Failing test first: `testing/features/F008/frontend/VirtualGrid.test.tsx::virtual_grid_renders_viewport_only`, `::shift_arrow_extends_selection`, `::conflict_result_shows_outline_and_reload`; `CellEditor.test.tsx::enter_commits_and_escape_cancels`, `::invalid_result_keeps_raw_with_code_badge`; `ClipboardController.test.tsx::paste_tsv_maps_to_visible_columns`; `UndoRedoController.test.tsx::ctrl_z_calls_undo_and_announces`; `BulkEditDialog.test.tsx::previews_row_count_and_toasts_result`; `testing/features/F008/accessibility/grid.a11y.spec.ts::grid_has_no_serious_axe_violations`, `::keyboard_only_edit_paste_undo`
- Targeted command: `cargo xtask test-feature F008`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: MSW handlers from the seeded 12-column/500-row fixture plus a 100,000-row synthetic page source; axe-core via Playwright

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Component and accessibility lanes pass
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S016
- [ ] `finished_at` recorded
