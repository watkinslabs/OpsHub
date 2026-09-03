# F014 api cases

File: `testing/features/F014/api/{form_tests.rs,condition_tests.rs,public_tests.rs,abuse_tests.rs,upload_tests.rs}`. Flag `F014_FEATURE`.

- `form_create_returns_draft_version_one` — FR-F014-01: POST `/api/v1/forms` as form admin returns 201, `status: draft`, `version: 1`, empty fields.
- `form_field_foreign_column_invalid` — FR-F014-02: field referencing a column of another sheet → 400 with `field_errors.fields[0].column_id`.
- `condition_hidden_field_not_required` — FR-F014-03: required "Budget" with `show_if Type eq Purchase`; submitting `Type = Question` without Budget is accepted.
- `condition_depth_over_four_invalid` — FR-F014-03: five nested `and` nodes → 400 `field_errors.fields[0].show_if`.
- `validation_regex_only_on_text_columns` — FR-F014-02: `regex` on a number column → 400 `invalid`.
- `form_publish_freezes_version_and_emits_event` — FR-F014-04: publish → `published_at` set, token returned once, `form.published.v1` in outbox.
- `form_patch_after_publish_creates_draft` — FR-F014-04: PATCH label on published version 1 → version 2 draft; version 1 fields unchanged.
- `form_token_rotate_invalidates_old_token` — FR-F014-05: rotate → old token 404 on `GET /public/forms/{token}`, new token 200.
- `revoked_token_not_found` — FR-F014-05: revoke → both public routes 404 with generic body.
- `public_schema_omits_internal_ids` — FR-F014-06: response JSON contains no `sheet_id`, `column_id`, `tenant_id`, `created_by`.
- `submission_rate_limit_returns_429_with_retry_after` — FR-F014-07: 61 posts from one IP within an hour → 61st is 429 with `Retry-After`, rejection event reason `rate_limited`.
- `daily_token_limit_enforced` — FR-F014-07: 1,001 posts across IPs in one day → 429.
- `honeypot_filled_rejected_without_hint` — FR-F014-08: honeypot value → 400 `invalid`; body identical to CAPTCHA failure; event reason `honeypot`.
- `captcha_failure_rejected` — FR-F014-08: stub verifier fails → 400; event reason `captcha_failed`.
- `captcha_unavailable_fails_closed` — FR-F014-08: verifier returns outage → 503 `unavailable`, metric incremented, no intake event.
- `authenticated_mode_without_session_denied` — FR-F014-09: `authenticated` identity mode, no session → 403 `denied`.
- `email_mode_requires_valid_address` — FR-F014-09: `email: "nope"` → 400 `field_errors.email`.
- `submission_intake_event_precedes_row` — FR-F014-10: accepted submission → `form_submissions.id` < `rows.id` (UUIDv7 order), `status: accepted`, `form.submitted.v1` carries both ids.
- `submission_replay_returns_original_ids` — FR-F014-11: same key twice → same `submission_id` and `row_id`, one row; different body → 409.
- `submission_validation_error_records_rejection` — FR-F014-12: regex failure → 400 `field_errors.<key>` with configured message; rejected event reason `validation`; `form.submission-rejected.v1`.
- `upload_over_limit_rejected` — FR-F014-13: 11 files or one 26 MB file → reason `upload_rejected`.
- `upload_mime_outside_allowlist_rejected` — FR-F014-13: `application/x-msdownload` → 400.
- `upload_pending_when_files_flag_off` — FR-F014-13: `F017_FEATURE` off → accepted with `pending_attachments`.
- `draft_saved_without_row` — FR-F014-14: `draft: true` → `status: draft`, `draft_token`, `expires_at` +7 days, no row.
- `submission_closed_window_rejected` — FR-F014-15: clock after `closes_at` → 400, reason `form_closed`.
- `public_response_sets_frame_ancestors` — FR-F014-16: `/public/forms/{token}` has `Content-Security-Policy: frame-ancestors` and no `X-Frame-Options`.
- `submissions_list_pages_and_filters` — FR-F014-17: 450 events, `limit=200`, three pages; `status=rejected` filter; `row_id` present on accepted.
- `form_cross_tenant_not_found` — FR-F014-18: tenant B on every admin route → 404.
- `form_submitter_admin_routes_denied` — FR-F014-18: submitter POST/PATCH/publish/DELETE → 403.
- `payload_over_one_megabyte_rejected` — NFR-F014-02: 1.1 MB body → 413 `invalid` before any write.
- `submission_log_has_no_payload` — NFR-F014-02: captured log lines contain no field values; `ip_hash` differs from raw IP.
- `row_failure_keeps_received_with_error_code` — NFR-F014-04: forced row-create failure → `received`, `error_code`, span carries `submission_id`.

Evidence: JUnit output and request logs under `testing/evidence/F014/api/`.
