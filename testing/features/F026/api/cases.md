# F026 api cases

File: `testing/features/F026/api/{connection_tests.rs,saml_tests.rs,scim_tests.rs,lifecycle_tests.rs,mapping_tests.rs,negative_tests.rs}`. Flag `F026_FEATURE`.

- `connection_create_returns_sp_metadata_fields` — FR-F026-01: POST `/api/v1/identity/connections` as tenant-admin → 201, `version: 1`, `status: draft`, `sp_entity_id`, ACS URL.
- `connection_duplicate_domain_conflicts` — FR-F026-02: second active connection with `example.com` → 409 `conflict`, `field_errors.domains`.
- `connection_activate_requires_recent_test` — FR-F026-07: PATCH `status: active` without a passing test in 24 h → 400 `invalid`; after test → 200.
- `member_cannot_create_connection` — NFR-F026-02: member POST → 403 `denied`, no row.
- `acs_accepts_signed_assertion_within_skew` — FR-F026-04, FR-F026-05: assertion issued 60 s in the future with skew 120 → session cookie and redirect to RelayState.
- `acs_rejects_expired_outside_skew` — FR-F026-04: `NotOnOrAfter` 200 s in the past with skew 120 → 401 reason `expired`.
- `acs_rejects_unsigned_assertion` — NFR-F026-02: signed `Response` with unsigned `Assertion` → 401 `bad_signature`.
- `acs_rejects_replayed_assertion_id` — FR-F026-04: same `SAMLResponse` twice → second is 401 `replayed`.
- `acs_rejects_audience_mismatch` — FR-F026-04: audience of another SP → 401 `audience_mismatch`.
- `rotation_accepts_either_current_certificate` — FR-F026-06: assertions signed by old and new certificate both succeed during overlap.
- `jit_provisioning_creates_user` — FR-F026-05: unknown email with JIT on → user with `source: saml`; JIT off → 401 `unknown_user`.
- `saml_login_writes_audit_and_event` — FR-F026-08: success and failure each write one audit row and one `saml.login.v1` outbox row.
- `scim_create_user_returns_scim_json` — FR-F026-10: POST Users → 201, `application/scim+json`, `meta.resourceType: User`.
- `scim_list_users_filters_by_username` — FR-F026-10: `filter=userName eq "ana@example.com"` → one resource; `count=201` → 400 `invalidValue`.
- `scim_duplicate_username_uniqueness_error` — FR-F026-10: duplicate `userName` → 409 `scimType: uniqueness`.
- `scim_patch_group_adds_and_removes_members` — FR-F026-13: add and remove operations → F002 membership updated, `scim.group-synced.v1` published.
- `scim_delete_user_deactivates_then_404` — FR-F026-12: DELETE → 204 and user inactive; DELETE again → 404.
- `scim_unknown_token_401` — FR-F026-15: random bearer → 401 SCIM error body.
- `scim_rotated_token_grace_period` — FR-F026-09: old token works at +14 min, fails at +16 min.
- `scim_rate_limit_429_with_retry_after` — FR-F026-15: 61 requests in one minute → 429 `rate_limited` with `Retry-After`.
- `scim_foreign_tenant_token_not_found` — NFR-F026-02: tenant B token reading tenant A user ID → 404.
- `scim_suspend_revokes_sessions_and_transfers_ownership` — FR-F026-11: `active: false` → 0 live sessions, 6 objects owned by Ana, 6 `ownership.transferred` audit rows.
- `scim_reinstate_keeps_transferred_ownership` — FR-F026-11: `active: true` → user active, ownership unchanged.
- `group_mapping_assigns_and_removes_roles` — FR-F026-14: join mapped group → binding with `source scim:`; leave → binding removed.
- `group_mapping_preserves_manual_bindings` — FR-F026-14: manual `tenant-admin` binding survives leaving the mapped group.
- `signature_wrapping_two_assertions_rejected` — NFR-F026-02: response with two assertions → 401 `bad_signature`.
- `dtd_in_response_rejected` — NFR-F026-02: XML with DOCTYPE → 401 `bad_signature`, parser never expands entities.
- `sso_request_span_carries_ids` — NFR-F026-04: ACS and SCIM spans include `tenant_id`, `connection_id`, `correlation_id`; counters incremented.

Evidence: JUnit output and request logs under `testing/evidence/F026/api/`.
