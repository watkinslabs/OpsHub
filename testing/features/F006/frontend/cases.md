# F006 frontend cases

File: `testing/features/F006/frontend/{GridView.test.tsx,BoardView.test.tsx,NewSheetDialog.test.tsx}`. Vitest with MSW. Flag `F006_FEATURE`.

- `renders_groups_and_rows` — FR-F006-13: seeded sheet renders 3 sections and 50 rows in position order.
- `shows_loading_skeleton_then_content` — FR-F006-13: pending query shows skeleton; resolves to rows.
- `shows_empty_state_with_add_row` — FR-F006-13: sheet with no rows shows call to action.
- `shows_error_banner_with_correlation_id` — NFR-F006-04: 500 response shows banner containing `correlation_id` and retry.
- `shows_denied_state_for_viewer` — FR-F006-14: viewer role hides add/move affordances and shows read-only label.
- `shows_not_found_for_non_member` — FR-F006-14: 404 renders not-found page.
- `keyboard_move_calls_api` — FR-F006-13: Space, ArrowRight, Enter on a card calls `moveRow` with the target group.
- `rolls_back_on_conflict` — FR-F006-04: `moveRow` 409 restores the card and shows the stale banner.
- `offline_disables_edits` — FR-F006-13: `navigator.onLine=false` shows offline badge and disables mutations.
- `new_sheet_dialog_validates_name` — FR-F006-01: empty name blocks submit; duplicate shows `field_errors.name`.
- `mode_switch_emits_telemetry` — FR-F006-13: grid→board emits `sheet_mode_changed`.

Evidence: Vitest JUnit under `testing/evidence/F006/frontend/`.
