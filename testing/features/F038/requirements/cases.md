# F038 requirements cases

Feature: Authentication and MFA. Flag `F038_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F038-REQ-001` | FR-F038-01 | api | start with slug `acme` → 302 to provider with `code_challenge_method=S256`; signed 10-minute cookie set; unknown slug → 404 |
| `F038-REQ-002` | FR-F038-02 | api | callback with valid token → user resolved; wrong nonce → 403; inactive user → 403 `user_not_provisioned` |
| `F038-REQ-003` | FR-F038-03 | api, database | callback → `sessions` and `refresh_tokens` rows, `__Host-oh_session` cookie, `last_login_at`, `session.created.v1` |
| `F038-REQ-004` | FR-F038-04 | api | rotated token reused → 401, whole family revoked with reason `refresh_reuse` |
| `F038-REQ-005` | FR-F038-05 | api | logout twice → 204 both times; cookie cleared; one `session.revoked.v1` |
| `F038-REQ-006` | FR-F038-06 | api, frontend | self lists 2 sessions with `current`; admin lists by `user_id`; other user's session → 404 |
| `F038-REQ-007` | FR-F038-07 | api | enroll returns secret once; code at +1 step verifies; +2 steps → 400 `field_errors.code` |
| `F038-REQ-008` | FR-F038-08 | api | register then assert → `mfa_verified_at`; replayed counter → 400 |
| `F038-REQ-009` | FR-F038-09 | api | sixth factor → 400; remove last factor under required policy → 400 `mfa_required` |
| `F038-REQ-010` | FR-F038-10 | api, e2e | required policy, unverified session → `GET /api/v1/groups` 403 `mfa_required`; web routes to enrolment |
| `F038-REQ-011` | FR-F038-11 | api | create returns `oh_` plaintext once; superset scopes → 400; TTL over cap → 400; revoke emits event |
| `F038-REQ-012` | FR-F038-12 | api | bearer → `ActorContext` ApiToken; revoked/expired/unknown → 401 `invalid_token` |
| `F038-REQ-013` | FR-F038-13 | api, performance | 11th login start per IP in a minute → 429 with `Retry-After`; bucket refills |
| `F038-REQ-014` | FR-F038-14 | api, frontend | admin PATCH with `If-Match` → 200; `session_max_age_seconds: 100` → 400; member → 403 |
| `F038-REQ-015` | FR-F038-15 | api | no credential on `/api/v1/sessions` → 401 `unauthenticated`; handlers receive `ActorContext` |
| `F038-REQ-016` | FR-F038-16 | api | every auth flow → audit row with ip, user agent, correlation; no secret in rows or logs |
| `F038-NFR-001` | NFR-F038-01 | performance | callback p95 < 800 ms; session and bearer lookup p95 < 20 ms; limiter < 2 ms |
| `F038-NFR-002` | NFR-F038-02 | api, database | secrets encrypted, hashes unique, `__Host-` cookies, PKCE mandatory, Microsoft and Google fixtures pass |
| `F038-NFR-003` | NFR-F038-03 | accessibility | axe serious = 0 on auth pages; QR has text alternative; live regions announce |
| `F038-NFR-004` | NFR-F038-04 | api | JWKS outage → refresh still works from cache; metrics emitted; spans carry `auth_kind` |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F038/`.
