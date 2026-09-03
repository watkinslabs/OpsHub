# F061 frontend cases

File: `testing/features/F061/frontend/{RequestUpdateDialog.test.tsx,ScopePicker.test.tsx,PublicRequestPage.test.tsx,PublicRowCard.test.tsx,DraftBar.test.tsx,ConflictPanel.test.tsx,TerminalNotice.test.tsx,RecipientStatusTable.test.tsx,ChangeLogTable.test.tsx}`. Vitest with MSW. Flag `F061_FEATURE`.

- `blocks_send_without_recipient_or_column` — FR-F061-01: `RequestUpdateDialog` disables `Send` until at least one column and one recipient are chosen and shows the reason.
- `scope_picker_hides_unwritable_columns` — FR-F061-01: `ScopePicker` omits formula and system columns and explains why the list is shorter than the sheet.
- `renders_only_scoped_fields_with_current_values` — FR-F061-04: `PublicRequestPage` renders 12 cards with 3 fields each and no other sheet data.
- `save_draft_persists_and_restores` — FR-F061-07: `DraftBar` writes `update-request-draft:{token}` and a remount restores the entered values.
- `partial_progress_shown_in_sticky_bar` — FR-F061-07: 9 of 36 filled renders `9 of 36 filled` and keeps `Submit` enabled when `allow_partial` is true.
- `submit_disabled_when_partial_not_allowed` — FR-F061-07: with `allow_partial: false` and a gap, `Submit` is disabled with an explanatory message.
- `conflict_panel_offers_use_current` — FR-F061-08: a 409 renders the changed rows with old and current values and a `Use current` control that refills the field.
- `terminal_notice_for_cancelled_link` — FR-F061-12: a 404 for a cancelled token renders the cancelled screen naming the requester with no cell data.
- `terminal_notice_for_expired_link` — FR-F061-09: an expired token renders the expired screen with the expiry date and no retry action.
- `offline_badge_and_local_draft` — FR-F061-15: going offline shows the badge, keeps typing local, and re-enables `Submit` on reconnect.
- `recipient_table_shows_status_and_last_reminded` — FR-F061-13: `RecipientStatusTable` shows per-recipient status, `reminder_count`, and `last_reminded_at` with text plus icon.
- `change_log_shows_old_new_and_author` — FR-F061-13: `ChangeLogTable` shows old value, new value, contributing recipient, and applied time per cell.
- `remind_button_disabled_after_limit` — FR-F061-11: a 429 from `remind` disables the button and shows the 24-hour limit message.
- `shows_error_banner_with_correlation_id` — NFR-F061-04: a 500 on the detail route renders a banner with `correlation_id` and retry.

Evidence: Vitest JUnit under `testing/evidence/F061/frontend/`.
