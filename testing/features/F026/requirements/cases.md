# F026 requirements cases

Feature: SSO/SCIM. Flag `F026_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F026-REQ-001` | FR-F026-01 | api | admin creates SAML connection → 201, version 1, `status: draft`, `sp_entity_id`, ACS URL |
| `F026-REQ-002` | FR-F026-02 | api, database | second active connection with `example.com` → 409 `conflict`, `field_errors.domains` |
| `F026-REQ-003` | FR-F026-03 | api | metadata renders SP certificate; login issues signed `AuthnRequest`, ID stored 10 minutes |
| `F026-REQ-004` | FR-F026-04 | api | unsigned, expired, wrong audience, replayed assertion → 401 `denied` with reason code |
| `F026-REQ-005` | FR-F026-05 | api, e2e | verified assertion → session; unknown user with JIT off → `unknown_user`; suspended → `user_suspended` |
| `F026-REQ-006` | FR-F026-06 | api | two current certificates → assertions signed by either accepted; retired one rejected |
| `F026-REQ-007` | FR-F026-07 | api | test returns three checks; activate without test in 24 h → 400 `invalid` |
| `F026-REQ-008` | FR-F026-08 | api, database | each attempt → audit `saml.login.succeeded|failed` and `saml.login.v1` |
| `F026-REQ-009` | FR-F026-09 | api, database | rotate token → plaintext once, hash stored, old token valid 15 minutes |
| `F026-REQ-010` | FR-F026-10 | api | Users list filter `userName eq`, `startIndex`, `count` ≤ 200, `application/scim+json` |
| `F026-REQ-011` | FR-F026-11 | api, e2e | `active: false` → sessions revoked, ownership moved, one audit event per object |
| `F026-REQ-012` | FR-F026-12 | api | DELETE user → 204 and deactivated; repeat → 404 |
| `F026-REQ-013` | FR-F026-13 | api, database | Groups create/patch → F002 group updated, `scim_sync_log` row, `scim.group-synced.v1` |
| `F026-REQ-014` | FR-F026-14 | api | mapping to `tenant-admin` → binding added on join, removed on leave, manual binding kept |
| `F026-REQ-015` | FR-F026-15 | api | unknown token → 401; 61st request in a minute → 429 with `Retry-After` |
| `F026-REQ-016` | FR-F026-16 | frontend, e2e | admin page lists status, domains, expiry warning at 30 days, last login and sync |
| `F026-NFR-001` | NFR-F026-01 | performance | ACS p95 < 800 ms; SCIM user op p95 < 500 ms; 500-member group PATCH < 2 s |
| `F026-NFR-002` | NFR-F026-02 | api, database | signature wrapping, DTD, foreign tenant, hashed token suite green |
| `F026-NFR-003` | NFR-F026-03 | accessibility | axe serious = 0 on `/admin/sso`; expiry warning announced; keyboard token copy |
| `F026-NFR-004` | NFR-F026-04 | api | spans carry tenant, connection, correlation; `saml_login_total` and `scim_request_total` emitted |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F026/`.
