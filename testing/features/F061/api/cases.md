# F061 api cases

File: `testing/features/F061/api/{request_tests.rs,reminder_tests.rs,public_tests.rs,response_tests.rs,audit_tests.rs,negative_tests.rs}`. Flag `F061_FEATURE`.

- `create_rejects_unwritable_column` — FR-F061-01: a formula column or a column the actor lacks `cell.write` on → 400 `invalid` with `field_errors.column_ids`.
- `create_rejects_row_outside_sheet` — FR-F061-01: a row id from another sheet → 400 `invalid` with `field_errors.row_ids`.
- `create_caps_scope_at_200_rows_and_20_columns` — FR-F061-01: 201 rows or 21 columns → 400 `invalid`.
- `create_mints_one_hashed_token_per_recipient` — FR-F061-02: three recipients → three distinct `token_hash` values, plaintext returned once, absent from the stored row.
- `expiry_beyond_ninety_days_rejected` — FR-F061-02: `expires_at` 91 days out → 400; omitted `expires_at` → `due_at + 7 days`.
- `scope_keys_hide_row_and_column_ids` — FR-F061-03: `scope_keys` maps 12 `row_key` and 3 `field_key` values; a row deleted after send raises `removed_count` to 1.
- `public_scope_omits_internal_identifiers` — FR-F061-04: response body contains no `sheet_id`, `row_id`, `column_id`, `tenant_id`, or user id, and carries the `no-referrer`, `noindex`, and `no-store` headers.
- `revoked_and_expired_tokens_return_same_not_found` — FR-F061-04: revoked, expired, and never-issued tokens produce byte-identical 404 bodies.
- `first_load_marks_recipient_opened` — FR-F061-04: first GET sets `opened_at` and `status: opened`; a second GET does not move `opened_at`.
- `field_key_outside_scope_returns_not_found` — FR-F061-05: a `field_key` from another request → 404 `not_found`, no cell written.
- `invalid_value_returns_field_errors` — FR-F061-05: a bad date and an out-of-list select → `field_errors.<row_key>.<field_key>` for both.
- `submit_rate_limited_after_thirty` — FR-F061-05: 31st submission within an hour → 429 `rate_limited` with `Retry-After`.
- `response_row_written_before_cell_apply` — FR-F061-06: an injected apply failure leaves a `received` row with `error_code` and no cell change.
- `applied_response_publishes_cell_and_response_events` — FR-F061-06: 36 cells → 36 `cell.updated.v1` and one `update-request.responded.v1` with `cells_updated: 36`.
- `draft_writes_no_cells_and_resumes` — FR-F061-07: `submit: false` → `draft` row, zero cell changes, reload returns the draft values.
- `partial_submit_marks_recipient_partial` — FR-F061-07: 9 of 36 fields → recipient `partial`, request still `open`.
- `incomplete_submit_rejected_when_partial_disabled` — FR-F061-07: `allow_partial: false` with a gap → 400 `invalid` reason `incomplete`, nothing written.
- `stale_row_version_returns_conflict_with_current_values` — FR-F061-08: row bumped to version 5 after load → 409 with `current_version` and `current_values`, response `rejected` reason `stale_row`.
- `submission_replay_returns_original_result` — FR-F061-06: same `Idempotency-Key` twice → identical `response_id`, no second row, no second cell write.
- `request_completes_when_every_scoped_pair_filled` — FR-F061-09: two recipients covering the scope between them → request `completed`.
- `submission_after_completion_returns_conflict` — FR-F061-09: post to a completed recipient → 409 `conflict` reason `closed`.
- `first_sequence_scheduled_before_due_date` — FR-F061-10: cadence `every_3_days` → `sequence 1` at `due_at - 3 days`, never before `now`.
- `remind_job_claims_due_rows_without_duplicates` — FR-F061-10: job run twice over the same due row → one notification, one `update-request.reminded.v1`.
- `concurrent_workers_send_one_notification_per_sequence` — NFR-F061-04: two workers on one row → one `sent` state, one F037 `dedupe_key` hit.
- `remind_stops_after_first_response` — FR-F061-10: `stop_on_response` → remaining schedules `cancelled` on the first submitted response.
- `remind_stops_at_max_reminders` — FR-F061-10: `max_reminders: 2` → no `sequence 3` inserted.
- `cadence_stable_across_dst_transition` — FR-F061-10: `Australia/Sydney` daily cadence across the DST change keeps the local send time.
- `manual_remind_skips_completed_recipients` — FR-F061-11: `skipped` lists completed and revoked recipients with reasons; the token is unchanged.
- `manual_remind_rate_limited_after_three` — FR-F061-11: 4th manual reminder in 24 h → 429 `rate_limited`.
- `cancel_revokes_tokens_and_pending_reminders` — FR-F061-12: cancel → `token_hash` null, pending schedules `cancelled`, public routes 404, repeat cancel 200.
- `cancel_on_completed_returns_conflict` — FR-F061-12: cancelling a completed request → 409 `conflict`.
- `detail_masks_email_for_non_owner` — FR-F061-13: a `sheet.admin` reader sees `a***@example.com`; the requester sees the full address.
- `list_filters_and_pages` — FR-F061-13: `status=open&due_before=` filters correctly; cursor paging over 120 requests.
- `audit_rows_share_correlation_id_with_cell_history` — FR-F061-14: `update-request.respond` and its `cell_history` rows share one `correlation_id`.
- `recipient_response_recorded_as_system_actor` — FR-F061-14: audit row has `actor_kind: 'system'`, null `actor_id`, and `after.recipient` naming the external email.
- `requester_permission_revoked_rejects_apply` — NFR-F061-02: requester loses `cell.write` after send → submission rejected with reason `requester_denied`.
- `member_cannot_create_or_cancel_request` — FR-F061-13: member without `requester` → 403 `denied` on create, remind, and cancel.
- `foreign_tenant_token_returns_not_found` — NFR-F061-02: tenant B token against tenant A context → 404; tenant B request id → 404 on all four authenticated routes.
- `brute_forced_token_rate_limited_and_counted` — NFR-F061-02: 200 random tokens from one IP → 429 after the limit and `update_request_token_rejections_total` increments.
- `payload_over_one_megabyte_rejected` — FR-F061-05: 1.5 MB body → 400 `invalid`, no row written.

Evidence: JUnit output and recorded notification logs under `testing/evidence/F061/api/`.
