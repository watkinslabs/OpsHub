# F063 api cases

File: `testing/features/F063/api/{connection_tests.rs,test_connection_tests.rs,graph_client_tests.rs,sign_in_tests.rs,matching_tests.rs,group_sync_tests.rs,mail_tests.rs,negative_tests.rs}`. Flag `F063_FEATURE`. Mock Entra authority and mock Graph only.

- `put_connection_seals_secret_and_returns_redirect_uri` — FR-F063-02: secret stored as `credential_key_id`/`credential_nonce`/`credential_ciphertext`; response carries `status`, `capabilities`, `version` and the redirect URI.
- `put_connection_rejects_unknown_cloud` — FR-F063-02: `cloud: "germany"` → `400 invalid` with `field_errors.cloud`.
- `put_connection_rejects_malformed_guid_with_field_errors` — FR-F063-02: non-GUID `directory_tenant_id` → `400 invalid` naming the field.
- `mail_capability_requires_sender_mailbox` — FR-F063-08: `mail` without `sender_mailbox` → `400 invalid`.
- `connection_response_never_contains_credential` — NFR-F063-02: no response, log line, audit diff or export contains the secret, thumbprint or ciphertext.
- `connection_get_without_connection_is_disconnected` — FR-F063-13: no row → `200` `status: disconnected`; the mock Graph records zero calls.
- `test_connection_reports_missing_group_scope` — FR-F063-03: app registration without `GroupMember.Read.All` → `ok: false`, `missing_scopes: ["GroupMember.Read.All"]`, `status: needs_consent`.
- `test_connection_returns_error_class_not_provider_string` — FR-F063-03: mock `AADSTS7000215` → `error_class: invalid_client` with no provider text echoed.
- `test_connection_completes_under_ten_seconds` — NFR-F063-01: token plus `organization` round trips within the 10 s budget.
- `login_redirect_carries_s256_pkce_and_nonce` — FR-F063-04: authorize URL has `code_challenge_method=S256`, `nonce`, `scope=openid profile email`, and a `state` row expiring in 10 minutes.
- `callback_rejects_reused_state` — FR-F063-04: second callback with the same `state` → `400 invalid` and `entra.signin-rejected`.
- `callback_rejects_foreign_tenant_state` — NFR-F063-02: `state` minted for tenant A presented in tenant B → `400 invalid` plus audit.
- `callback_rejects_bad_nonce` — FR-F063-04: id token `nonce` mismatch → `400 invalid`.
- `callback_rejects_unknown_jwks_key` — NFR-F063-02: token signed by a key absent from the JWKS set → `400 invalid`; rotation fixture accepts the new key.
- `callback_rejects_wrong_aud_and_iss` — FR-F063-04: `aud` other than `client_id`, or `iss` from another cloud → `400 invalid`.
- `callback_issues_f038_session_for_matched_user` — FR-F063-04: matched user gets a session from F038's session service; no second session store row exists.
- `email_match_is_case_insensitive` — FR-F063-05: `Ada.Lovelace@contoso.com` matches `ada.lovelace@contoso.com` within the tenant only.
- `preferred_username_used_when_email_absent` — FR-F063-05: id token without `email` matches on `preferred_username`.
- `unmatched_domain_is_denied_no_matching_user` — FR-F063-05: domain outside `allowed_email_domains` → `403 denied` `reason: no_matching_user`, no user created.
- `jit_provision_stores_oid_as_external_id` — FR-F063-05: allowed domain with provisioning on → user created with `users.external_id` = `oid`.
- `deactivated_user_is_denied_user_inactive` — FR-F063-05: deactivated match → `403 denied` `reason: user_inactive`.
- `suspended_tenant_cannot_sign_in_through_entra` — NFR-F063-02: suspended F002 tenant → denied before any session is issued.
- `graph_client_honors_retry_after_on_429` — FR-F063-09: `429` with `Retry-After: 2` → one wait then success; both calls in `entra_mail_log`.
- `breaker_opens_after_five_consecutive_failures` — FR-F063-09: five failures → breaker open 5 minutes; the sixth call is skipped without a request.
- `graph_call_logs_domain_only` — NFR-F063-02: log lines and `entra_mail_log` carry `contoso.com`, never the address, subject, body or token.
- `sync_adds_and_removes_mapped_members` — FR-F063-06: delta page adds 24 and removes 2 from the mapped F002 group; `entra.group-synced.v1` carries both counts.
- `sync_skips_manual_source_members` — FR-F063-06: a member with `source: manual` survives a delta that omits them.
- `sync_halts_needs_review_over_twenty_percent_removal` — FR-F063-07: 100-member group with 70 returned → `status: needs_review`, zero membership writes.
- `confirm_destructive_applies_held_removals` — FR-F063-07: rerun with `confirm_destructive: true` applies the 30 removals with per-member audit.
- `expired_delta_token_falls_back_to_full_read` — NFR-F063-04: expired token → full read with no duplicated members and a new token stored.
- `sync_idempotent_after_restart` — NFR-F063-04: job cancelled mid-page and re-run → no duplicate members or events; metrics emitted.
- `role_target_binds_through_f003` — FR-F063-06: `target_kind: role` grants and revokes an F003 role binding, not a new group model.
- `sync_without_group_sync_capability_conflicts` — FR-F063-13: capability absent → `409 conflict` on `field_errors.capabilities`.
- `graph_transport_registers_into_f037_registry` — FR-F063-08: startup with `mail` puts `graph` in F037's channel registry using F037 templates and delivery records.
- `graph_failure_falls_back_to_smtp_and_records_both` — FR-F063-08: three `503`s → SMTP delivery with both attempts and status codes on the one delivery record.
- `no_smtp_configured_dead_letters_after_three_retries` — NFR-F063-04: tenant B without SMTP → dead letter and connection `error`.
- `mail_sent_event_carries_message_id_and_domain_only` — FR-F063-08: `entra.mail-sent.v1` payload has exactly `message_id` and `recipient_domain`.
- `member_denied_on_every_entra_route` — FR-F063-11: a member gets `403 denied` on GET, PUT, test, DELETE and sync-groups.
- `foreign_tenant_connection_not_found` — FR-F063-11: tenant B connection or group-map id → `404 not_found` on every route.
- `mutations_require_idempotency_key_and_if_match` — FR-F063-11: missing header → `400 invalid`; stale `If-Match` → `409 conflict`.
- `entra_enabled_leaves_password_totp_webauthn_oidc_saml_working` — FR-F063-01: every F038 and F026 method still authenticates with Entra active.
- `revoke_reverts_transport_and_publishes_revoked` — FR-F063-10: DELETE → tokens gone, SMTP selected, sync stopped, Entra sign-in refused, `entra.revoked.v1`.
- `disconnect_leaves_users_and_groups_intact` — FR-F063-10: user, group and role rows unchanged after revocation.

Evidence: JUnit output and mock provider logs under `testing/evidence/F063/api/`.
