# F023 frontend cases

File: `testing/features/F023/frontend/{GridCanvas.test.tsx,WidgetPalette.test.tsx,WidgetConfigPanel.test.tsx,DashboardViewer.test.tsx,ShareDashboardDialog.test.tsx}`. Vitest with MSW. Flag `F023_FEATURE`.

- `grid_renders_widgets_at_positions` — FR-F023-12: five widgets render at their grid cells on a 12-column canvas.
- `grid_keyboard_move_announces_position` — FR-F023-12, NFR-F023-03: `Enter`, `ArrowRight` moves one cell; live region reads "Table moved to column 1 row 0".
- `grid_shift_arrow_resizes` — FR-F023-12: `Shift+ArrowDown` increases `h` by 1 up to 12.
- `overlap_blocked_client_side` — FR-F023-13: moving onto another widget is refused with an inline message.
- `palette_lists_twelve_kinds` — FR-F023-03: palette shows all twelve kinds with labels.
- `config_panel_validates_text_length` — FR-F023-13: 8,001-char markdown shows the limit error and disables `Save`.
- `unsaved_changes_prompt_on_navigation` — FR-F023-13: dirty layout triggers the confirm dialog.
- `save_sends_single_replace_widgets_call` — FR-F023-13: `Save` issues one `replaceWidgets` with the full set.
- `viewer_renders_unavailable_for_unregistered_kind` — FR-F023-04: `unavailable` status renders "Widget type not enabled".
- `viewer_shows_denied_tile` — FR-F023-09: `denied` renders the access message and emits `widget_denied_shown`.
- `viewer_polls_while_computing` — FR-F023-05: `computing` refetches every 3 s until `fresh`.
- `stale_badge_refreshes_widget` — FR-F023-05: `stale` badge `Refresh` calls `refreshDashboard`.
- `viewer_folds_to_six_columns_at_800px` — FR-F023-12: widths halve and round up at 800 px.
- `share_dialog_creates_expiring_link` — FR-F023-09: creates link with 30-day expiry and shows `link_active`.
- `error_tile_isolated_with_correlation_id` — NFR-F023-04: one widget 500 shows its tile error while others render.

Evidence: Vitest JUnit under `testing/evidence/F023/frontend/`.
