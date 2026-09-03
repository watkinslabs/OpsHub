# F029 api cases

File: `testing/features/F029/api/{vault_tests.rs,connection_tests.rs,adapter_tests.rs,notify_tests.rs,calendar_tests.rs,conflict_tests.rs,chat_tests.rs,provider_contract_tests.rs,negative_tests.rs}`. Flag `F029_FEATURE`.

- `vault_seal_open_round_trip` — FR-F029-04: sealed refresh token opens to the original under the tenant key; `nonce` unique per seal.
- `vault_rewrap_changes_key_id_only` — NFR-F029-02: rotating the wrapping key updates `key_id` and still opens the token.
- `providers_list_reflects_deployment_credentials` — FR-F029-01: Slack credentials removed → `enabled: false`; start on it → 400 `invalid`.
- `start_connection_returns_pkce_authorize_url` — FR-F029-02: URL carries `code_challenge_method=S256` and a state stored with a 10-minute expiry.
- `callback_rejects_reused_state` — FR-F029-03: second callback with the same state → 400 `invalid` and audit `integration.callback-rejected`.
- `callback_stores_sealed_tokens_and_publishes_connected` — FR-F029-03: mock exchange → `oauth_tokens` row with ciphertext, `status: active`, `integration.connected.v1`.
- `callback_narrowed_scopes_sets_limited` — FR-F029-03: granted scopes missing `Calendars.ReadWrite` → `limited` with `missing_scopes`.
- `refresh_three_failures_sets_needs_reauth` — FR-F029-05: mock `invalid_grant` three times → three `integration.refresh-failed.v1`, `needs_reauth`, owner notification, bindings paused.
- `forced_refresh_renews_before_expiry` — FR-F029-05: `POST /refresh` → new `expires_at`, `last_success_at` updated.
- `revoke_deletes_tokens_and_publishes_revoked` — FR-F029-06: DELETE → mock revoke endpoint hit, token row deleted, `revoked`, `integration.revoked.v1`.
- `connection_list_filters_by_provider_and_status` — FR-F029-07: `provider=slack&status=active` → one row; cursor paging over 60 connections.
- `connection_response_never_contains_tokens` — FR-F029-04: every response body free of `access_token`, `refresh_token`, and ciphertext.
- `microsoft_exchange_parses_token_set_and_account` — FR-F029-13: recorded response → `TokenSet` and `ExternalAccount` with label.
- `http_client_honors_retry_after_on_429` — FR-F029-13: mock 429 with `Retry-After: 2` → one wait then success; `integration_events` shows both calls.
- `http_client_retries_5xx_three_times` — FR-F029-13: three 503s then 200 → success; fourth 503 → error class `Unavailable`.
- `notify_test_delivers_and_publishes_notified` — FR-F029-09: Slack `chat.postMessage` mock → `delivered: true`, `provider_message_id`, `integration.notified.v1`.
- `notify_test_rate_limited_after_ten` — FR-F029-09: 11th test within an hour → 429 `rate_limited`.
- `templates_render_five_kinds_with_deep_links` — FR-F029-08: `mention`, `assignment`, `approval`, `due_soon`, `workflow_failed` render for all three providers with the record link.
- `calendar_sync_pushes_row_dates_to_provider` — FR-F029-10: 50 rows → 50 events created on the mock; `calendar_event_links` populated.
- `calendar_sync_pulls_provider_changes_with_cursor` — FR-F029-10: mock delta page moves an event → row date updated; cursor stored.
- `calendar_sync_ignores_own_echo` — FR-F029-10: provider change matching our last write is skipped.
- `conflict_newest_wins_takes_provider_value` — FR-F029-11: OpsHub 10:00 vs provider 10:05 → provider value; conflict event with both values.
- `conflict_manual_marks_needs_review` — FR-F029-11: `manual` → row untouched, link `needs_review`, visible in conflicts.
- `chat_sync_imports_thread_reply_as_comment` — FR-F029-12: `conversations.replies` fixture → F016 comment with `source: provider`, author by email.
- `owner_can_test_but_not_revoke` — FR-F029-14: owner `notify-test` → 200; owner DELETE → 403 `denied`.
- `member_cannot_start_or_revoke_connection` — FR-F029-14: member POST/DELETE → 403.
- `foreign_state_cannot_complete_on_other_tenant` — NFR-F029-02: state minted for tenant A used with tenant B callback context → 400 and audit.
- `foreign_connection_not_found` — FR-F029-14: tenant B connection id → 404 on GET, DELETE, refresh, notify-test.
- `sync_job_idempotent_after_restart` — NFR-F029-04: job cancelled mid-page and re-run → no duplicate events; metrics emitted.

Evidence: JUnit output and mock provider logs under `testing/evidence/F029/api/`.
