# F038 api cases

File: `testing/features/F038/api/{oidc_tests.rs,session_tests.rs,mfa_tests.rs,token_tests.rs,policy_tests.rs,rate_limit_tests.rs,negative_tests.rs,redaction_tests.rs}`. Flag `F038_FEATURE`.

- `oidc_start_sets_pkce_state_cookie` — FR-F038-01: redirect URL carries `code_challenge`, `state`, `nonce`; `__Host-oh_oidc` cookie is signed, HttpOnly, 10-minute.
- `oidc_start_unknown_tenant_not_found` — FR-F038-01: slug `nope` → 404; tenant without provider config → 503 `unavailable`.
- `oidc_callback_creates_session_and_cookie` — FR-F038-03: valid code → session row, refresh row, cookie, `last_login_at`, `session.created.v1`.
- `oidc_callback_bad_state_denied` — FR-F038-02: mismatched `state` or `nonce` → 403, no session.
- `oidc_callback_unknown_kid_refreshes_jwks_once` — FR-F038-02, NFR-F038-04: rotated provider key → one JWKS refetch then success; second miss → 403.
- `oidc_callback_unprovisioned_user_denied` — FR-F038-02: email not in tenant or status `invited` → 403 `user_not_provisioned`.
- `oidc_callback_open_redirect_blocked` — FR-F038-03: `return_to=//evil.test` → redirect to `/`.
- `oidc_microsoft_and_google_fixtures_login` — NFR-F038-02: both claim shapes resolve the same user.
- `refresh_rotates_and_reuse_revokes_family` — FR-F038-04: rotation returns a new token; old token again → 401 and family revoked with `refresh_reuse`.
- `refresh_after_ttl_denied` — FR-F038-04: clock past `refresh_ttl_seconds` → 401.
- `idle_timeout_expires_session` — FR-F038-04: no activity past `idle_timeout_seconds` → next request 401.
- `logout_is_idempotent` — FR-F038-05: two logouts → 204, one `session.revoked.v1` reason `logout`.
- `session_list_self_and_admin` — FR-F038-06: self sees own sessions with `current`; admin with `user_id` sees another user's.
- `session_delete_other_user_not_found` — FR-F038-06: member deleting another member's session → 404.
- `totp_enroll_returns_secret_once` — FR-F038-07: response has `otpauth_uri` and `secret`; factor row unverified with encrypted secret.
- `totp_verify_within_one_step` — FR-F038-07: code from 30 s earlier verifies; sets `mfa_verified_at`; `mfa.enrolled.v1`.
- `totp_verify_two_steps_off_invalid` — FR-F038-07: code from 60 s earlier → 400 `field_errors.code`.
- `webauthn_register_and_assert_sets_mfa_verified` — FR-F038-08: two-call registration then assertion → `mfa_verified_at`.
- `webauthn_counter_replay_rejected` — FR-F038-08: assertion with equal `sign_count` → 400.
- `sixth_factor_rejected` — FR-F038-09: sixth enrol → 400.
- `last_factor_removal_under_required_policy_invalid` — FR-F038-09: DELETE last factor with `mfa_required` → 400 `mfa_required`; with policy off → 204 and `mfa.removed.v1`.
- `mfa_required_blocks_api_until_verified` — FR-F038-10: `GET /api/v1/groups` → 403 `mfa_required`; `/api/v1/mfa/totp/verify` allowed; after verify → 200.
- `api_token_create_returns_plaintext_once` — FR-F038-11: `oh_` prefix, 8 visible chars, hash stored; list never returns plaintext.
- `api_token_scope_escalation_denied` — FR-F038-11: scopes not in creator's set → 400 `field_errors.scopes`.
- `api_token_ttl_capped_by_policy` — FR-F038-11: `expires_at` beyond cap → 400.
- `bearer_authenticates_with_token_scopes` — FR-F038-12: `ActorContext.auth_kind = ApiToken`, scopes match.
- `bearer_revoked_token_invalid` — FR-F038-12: revoked, expired, unknown → 401 `invalid_token`.
- `bearer_last_used_throttled` — FR-F038-12: 10 calls in a minute → one `last_used_at` write.
- `login_rate_limit_returns_retry_after` — FR-F038-13: 11th start per IP → 429 with `Retry-After`; `auth_rate_limited_total{bucket="login_ip"}` +1.
- `bucket_refills_after_window` — FR-F038-13: advance clock 60 s → request allowed.
- `policy_patch_member_denied` — FR-F038-14: member → 403; version unchanged.
- `policy_range_invalid` — FR-F038-14: `session_max_age_seconds: 100` → 400 `field_errors.session_max_age_seconds`.
- `policy_stale_version_conflicts` — FR-F038-14: stale `If-Match` → 409.
- `unauthenticated_request_401` — FR-F038-15: no cookie or bearer → 401 `unauthenticated`.
- `all_routes_cross_tenant_not_found` — NFR-F038-02: tenant B ids on sessions, factors, tokens, policy → 404.
- `no_secret_in_logs_or_audit` — FR-F038-16: log and audit capture contain no `code=`, `state=`, secret, or `oh_` plaintext.
- `jwks_outage_uses_cached_keys` — NFR-F038-04: provider JWKS down → refresh and session validation still succeed.

Evidence: JUnit output and request logs under `testing/evidence/F038/api/`.
