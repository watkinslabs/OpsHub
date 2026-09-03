# F008 e2e cases

File: `testing/features/F008/e2e/grid.spec.ts`. Playwright against seeded tenant, two browser contexts for conflicts. Flag `F008_FEATURE`.

- `type_into_cell_and_reload` — FR-F008-01, FR-F008-02: editor types 1250 into "Budget", presses Enter, reload shows 1,250.00 and history popover lists the edit.
- `paste_block_with_invalid_cells` — FR-F008-11: paste 3×40 block containing "abc" in a number column → 119 cells applied, one badged `type_mismatch`, toast counts match.
- `fill_down_dates` — FR-F008-12: fill handle from 2026-01-01 down 10 rows → consecutive dates after reload.
- `undo_paste_then_redo` — FR-F008-06, FR-F008-07: Ctrl+Z reverts the paste with the announcement; Ctrl+Y restores it.
- `two_sessions_conflict_outline_and_reload` — FR-F008-15, NFR-F008-02: session B edits a cell session A is viewing; A's edit shows the conflict outline with B's name; `Reload` shows B's value.
- `layout_persists_after_reload` — FR-F008-14: resize "Budget" to 240 px, hide "Notes", freeze 2; reload as A restores it; B sees defaults.
- `bulk_edit_dialog_updates_rows` — FR-F008-03, FR-F008-04: select 812 rows, set "Status" to Done, confirm → toast and cells updated.
- `viewer_cannot_edit` — FR-F008-15: viewer login sees read-only cells, no fill handle, no bulk edit entry.

Evidence: Playwright traces and videos under `testing/evidence/F008/e2e/`.
