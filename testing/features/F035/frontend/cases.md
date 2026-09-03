# F035 frontend cases

File: `testing/features/F035/frontend/{FormulaEditor.test.tsx,FormulaCellBadge.test.tsx,FormulaGraphPanel.test.tsx}`. Vitest with MSW. Flag `F035_FEATURE`.

- `shows_position_error_from_parse` — FR-F035-15: typing `=SUM(` renders the parse message with a caret at position 6 and `aria-describedby` on the textbox.
- `autocomplete_inserts_function` — FR-F035-15: `Ctrl+Space` after `=SU` lists `SUM`, `SUMIF`, `SUBSTITUTE`; `Enter` inserts `SUM(`.
- `reference_chips_reflect_parse_response` — FR-F035-15: references from parse render as chips with current labels.
- `preview_row_debounces_evaluate` — FR-F035-07: three keystrokes in 200 ms produce one `evaluateFormula` call; value `12` shown.
- `save_uses_if_match_and_invalidates` — FR-F035-06: `Ctrl+Enter` calls `setColumnFormula` with the column version; `['grid-rows', sheetId]` invalidated.
- `shows_stale_banner_on_conflict` — FR-F035-06: 409 response shows the reload banner and keeps the draft text.
- `viewer_sees_read_only_editor` — FR-F035-16: viewer role renders textbox `readOnly` with explanation; no save button.
- `renders_badge_per_error_code` — FR-F035-08: `invalid`, `missing_reference`, `type_mismatch`, `cycle`, `timeout` render `#INVALID`, `#REF`, `#TYPE`, `#CYCLE`, `#TIMEOUT` with tooltips.
- `pending_cells_show_shimmer` — FR-F035-15: `status = pending` renders shimmer with `aria-busy`.
- `graph_panel_highlights_cycle` — FR-F035-13: `has_cycle = true` marks the cycle edges and shows the list layout under 640 px.
- `recalculate_button_shows_rate_limited` — FR-F035-14: 429 response shows "A recalculation is already running".
- `editor_open_emits_telemetry` — FR-F035-15: opening the editor emits `formula_editor_opened` with `sheet_id` and `column_id`.

Evidence: Vitest JUnit under `testing/evidence/F035/frontend/`.
