# F065 api cases

File: `testing/features/F065/api/{public_routes_tests.rs,anti_abuse_tests.rs,enumeration_tests.rs,provisioning_tests.rs,lifecycle_tests.rs,race_tests.rs,negative_tests.rs}`. Flag `F065_FEATURE`.

- `signup_returns_generic_accepted_body` — FR-F065-01: a valid submission returns `202 { status: "pending_verification", expires_in_seconds: 86400 }` and nothing else.
- `four_cases_share_status_body_and_latency_band` — FR-F065-02: new address, existing active user's address, taken slug, and rate-suppressed request produce identical status, headers, and body bytes within the 250–600 ms band.
- `existing_email_mail_carries_no_token` — FR-F065-02: the "you already have an account" message contains a sign-in link and no `signup_tokens` row is created.
- `sixth_signup_from_one_ip_is_absorbed` — FR-F065-03: the 6th signup in an hour writes no row, sends no mail, and still returns the standard `202`.
- `network_bucket_caps_twenty_per_hour` — FR-F065-03: 30 signups from one `/24` produce 20 rows; the IPv6 case uses a `/48`.
- `third_signup_per_email_hash_is_absorbed` — FR-F065-03: a 4th signup for the same normalized address within 24 hours is suppressed.
- `availability_rate_limit_returns_retry_after` — FR-F065-03: the 61st availability call in a minute returns `429 rate_limited` with `Retry-After`.
- `honeypot_filled_sends_no_mail` — FR-F065-04: a non-empty `company_website` records `risk_flags` and suppresses the mail.
- `elapsed_under_two_seconds_rejected` — FR-F065-04: `elapsed_ms: 800` is absorbed; `elapsed_ms: 2500` proceeds.
- `turnstile_outage_degrades_not_rejects` — FR-F065-04: a siteverify timeout flags `botcheck_unavailable` and still applies the honeypot, timing, and rate checks.
- `disposable_domain_absorbed_with_flag` — FR-F065-05: a domain from `disposable_domains.txt` yields `risk_flags = ["disposable_domain"]` and no mail.
- `domain_without_mx_absorbed_with_flag` — FR-F065-05: `StaticMxResolver` returning no record yields `no_mx`.
- `email_hash_ignores_dots_and_plus_tags` — FR-F065-05: `d.ana+trial@gmail.com` and `dana@gmail.com` share one `email_hash`; `dana@acme.io` and `d.ana@acme.io` do not.
- `availability_hides_reason_for_unavailable_slug` — FR-F065-06: taken, reserved, and soft-reserved slugs return the same `{ slug, available: false }`.
- `second_claimant_stores_null_slug_with_flag` — FR-F065-07: the second pending request for `orbit` stores `requested_slug = null` and `slug_taken`.
- `token_is_stored_only_as_hash` — FR-F065-08: the row holds a 32-byte digest; the raw value appears in no column, response, or log line.
- `token_compare_is_constant_time` — FR-F065-08, NFR-F065-02: 10,000 comparisons of near-miss digests show no timing separation beyond noise.
- `first_token_read_verifies_and_publishes_once` — FR-F065-08: the first successful read sets `verified_at` and publishes `signup.verified.v1`; a second read before completion publishes nothing.
- `token_read_after_expiry_returns_gone` — FR-F065-08: a token 24 hours and 1 second old returns `410 gone` with `reason: expired`.
- `unknown_token_matches_expired_response` — FR-F065-08: a token that never existed returns the same body as an expired one.
- `sixth_token_attempt_is_rejected` — FR-F065-08: the 6th read of one token returns `429 rate_limited` and leaves `attempts` at 5.
- `resend_reuses_token_and_respects_cooldown` — FR-F065-09: a resend after 60 s reuses the token row; one within 60 s and a 4th resend are rejected.
- `mail_goes_through_notification_service_only` — FR-F065-09: every message is one F037 `create` with category `system` and `dedupe_key` `signup:{request_id}:{kind}`.
- `complete_provisions_through_f002_use_case` — FR-F065-10: the provisioner spy records one `create_tenant` call with `plan: "free"` and `region: "us-east"`.
- `signup_module_never_writes_tenants_directly` — FR-F065-10, NFR-F065-02: the spy fails the test if any statement touches `tenants`, `users`, or `role_bindings` from signup code.
- `first_user_gets_tenant_admin_from_seed_hook` — FR-F065-10: the F003 seed hook produced the `tenant-admin` binding; signup wrote none.
- `completion_sets_session_cookie_with_signup_auth_kind` — FR-F065-10: the response carries `__Host-oh_session` and the session records `auth_kind = signup`.
- `failed_subscription_start_rolls_back_tenant` — FR-F065-10, NFR-F065-04: a forced F064 error leaves no tenant, no entitlement, and an unconsumed token.
- `trial_grants_four_modules_for_fourteen_days` — FR-F065-11: `dynamic-views`, `workapps`, `calendar-app`, and `pivots` are `trial` with `trial_ends_at` 14 days out; the other six are `none`.
- `grace_marks_trial_modules_expired_but_sheets_writable` — FR-F065-12: after `trial_ends_at` F048 evaluates `trial_expired` for the four modules while a row write on a sheet still succeeds.
- `grace_end_suspends_tenant_without_data_loss` — FR-F065-12: the suspend route is called on grace day 7; writes return `403 denied` with `reason = tenant_suspended` and every row survives.
- `conversion_activates_entitlements_and_lifts_suspension` — FR-F065-13: `subscription.updated.v1` with `status: active` moves the four entitlements to `active`, clears `trial_ends_at`, and lifts the suspension.
- `sweep_scrubs_pii_at_seven_days` — FR-F065-14: `email`, `email_normalized`, `company_name`, `ip`, and `user_agent` are null; `email_hash`, `status`, `risk_flags`, and `tenant_id` remain.
- `sweep_deletes_request_and_tokens_at_thirty_days` — FR-F065-14: the request row and its `signup_tokens` children are gone and `signup.abandoned.v1` was published once.
- `invitation_requires_platform_operator` — FR-F065-15: anonymous and `tenant-admin` callers get `403 denied`; the operator gets `201`.
- `invitation_pins_reserved_slug` — FR-F065-15: a `reserved_slugs` row with `reason: "pinned"` and the token's `expires_at` blocks self-serve use of that name.
- `replayed_completion_returns_gone_consumed` — NFR-F065-04: the second completion returns `410 gone` with `reason: consumed` and exactly one tenant exists.
- `concurrent_completions_provision_exactly_one_tenant` — FR-F065-07: two parallel completions on `orbit` yield one tenant, one `tenant.provisioned.v1`, and one `409 conflict`.
- `race_loser_token_survives_and_succeeds_on_new_slug` — FR-F065-07: the losing token is unconsumed and completes on `orbit-hq`.
- `logs_never_contain_email_or_raw_token` — NFR-F065-02: the captured log and span fields carry `request_id` and `email_hash` only.
- `anonymous_rejections_write_no_audit_rows` — NFR-F065-05: 100 suppressed signups add zero `audit_events` rows and increment `signup_rejected_total{reason}`.
- `new_admin_cannot_read_other_tenant` — NFR-F065-02: the freshly provisioned admin gets `404 not_found` on tenant `acme` resources.

Evidence: JUnit output, captured mail, and spy logs under `testing/evidence/F065/api/`.
