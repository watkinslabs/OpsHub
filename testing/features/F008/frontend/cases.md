# F008 frontend cases

File: `testing/features/F008/frontend/{VirtualGrid.test.tsx,CellEditor.test.tsx,ClipboardController.test.tsx,UndoRedoController.test.tsx,BulkEditDialog.test.tsx,CellHistoryPopover.test.tsx}`. Vitest with MSW. Flag `F008_FEATURE`.

- `virtual_grid_renders_viewport_only` — FR-F008-13: 100,000-row, 500-column source renders ≤ 60 rows and ≤ 40 columns; scrolling swaps rows.
- `shift_arrow_extends_selection` — FR-F008-13: Shift+ArrowDown ×3 selects a 4-cell range; Ctrl+Click adds a non-contiguous cell.
- `enter_commits_and_escape_cancels` — FR-F008-01: typing then Enter calls `patchCells` with `expected_row_version`; Escape restores the old value with no request.
- `invalid_result_keeps_raw_with_code_badge` — FR-F008-01: per-cell `invalid: type_mismatch` keeps the typed text and shows the code badge.
- `conflict_result_shows_outline_and_reload` — FR-F008-15: per-cell `conflict` restores the server value, shows `ConflictOutline` with "Changed by Ada Lovelace", and `Reload` fetches the change feed.
- `paste_tsv_maps_to_visible_columns` — FR-F008-11: 3×40 TSV pasted at B2 with column C hidden → 120 edits mapped to B, D, E in one request.
- `paste_chunks_200_cells` — FR-F008-11: 5×100 paste → three `patchCells` requests of 200, 200, 100.
- `fill_handle_calls_bulk_fill` — FR-F008-12: dragging the handle 10 rows calls `bulkEditCells` with `mode: fill` and `source_cell`.
- `ctrl_z_calls_undo_and_announces` — FR-F008-06: Ctrl+Z calls `undo`, live region reads "Undid 117 cells"; Ctrl+Y calls `redo`.
- `layout_change_debounced_and_persisted` — FR-F008-14: resize then freeze within 1 s → one `patchCells` with `layout` only and empty `edits`.
- `hide_primary_column_disabled` — FR-F008-10: header menu `Hide` is disabled on the primary column.
- `previews_row_count_and_toasts_result` — FR-F008-03: dialog shows "Will update 812 rows"; result toast "412 cells updated, 3 invalid".
- `history_popover_pages_entries` — FR-F008-09: popover lists 5 entries newest first and loads the next cursor.
- `viewer_sees_read_only_cells` — FR-F008-15: viewer role renders cells without editors and shows the lock badge on hover.
- `offline_disables_editing` — FR-F008-15: `navigator.onLine=false` shows the offline badge and blocks typing.

Evidence: Vitest JUnit under `testing/evidence/F008/frontend/`.
