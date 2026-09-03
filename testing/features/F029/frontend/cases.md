# F029 frontend cases

File: `testing/features/F029/frontend/{ProviderCard.test.tsx,OauthPopup.test.tsx,ConnectionTable.test.tsx,NotifyTestDialog.test.tsx,CalendarBindingDialog.test.tsx,ConflictList.test.tsx,CallLogTable.test.tsx}`. Vitest with MSW. Flag `F029_FEATURE`.

- `disabled_provider_shows_missing_credentials` — FR-F029-01: `enabled: false` card disables `Connect` and explains missing deployment credentials.
- `callback_result_refetches_and_announces` — FR-F029-15: popup message `connected` refetches connections and announces "Slack connected".
- `limited_row_lists_missing_scopes` — FR-F029-03: `limited` connection row shows `Calendars.ReadWrite` missing with `Reconnect`.
- `needs_reauth_row_shows_reconnect` — FR-F029-05: `needs_reauth` row renders a warning with the last error class and `Reconnect`.
- `notify_test_dialog_shows_delivery_result` — FR-F029-09: submitting `#ops` shows `Delivered` with the message id; 429 shows the hourly limit message.
- `previews_first_five_rows` — FR-F029-10: `CalendarBindingDialog` renders five preview events from the selected columns.
- `binding_rejects_non_date_column` — FR-F029-10: choosing a text column for start shows the `field_errors.start_column_id` message.
- `policy_radio_group_explains_each_option` — FR-F029-11: four policies with one-line descriptions; `newest_wins` default.
- `shows_both_values_and_winner` — FR-F029-11: `ConflictList` row shows OpsHub value, provider value, timestamps, and the applied side or `needs_review`.
- `call_log_filters_by_kind` — FR-F029-13: `CallLogTable` filters `call`, `notify`, `sync`, `conflict` and shows status code and duration.
- `shows_denied_page_for_member` — FR-F029-14: member loading `/admin/integrations` sees the denied page.
- `shows_error_banner_with_correlation_id` — NFR-F029-04: 500 renders banner with `correlation_id` and retry.

Evidence: Vitest JUnit under `testing/evidence/F029/frontend/`.
