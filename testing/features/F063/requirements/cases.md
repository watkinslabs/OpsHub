# F063 requirements cases

Feature: Microsoft Entra integration. Flag `F063_FEATURE`. Every case maps to a ticket requirement ID. Entra is optional and additive; no case contacts a real Microsoft endpoint.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F063-REQ-001` | FR-F063-01 | api, e2e | Entra enabled → password, TOTP, WebAuthn, generic OIDC and SAML all still sign in; disconnect → all still work; tenant with no connection shows no Entra affordance |
| `F063-REQ-002` | FR-F063-02 | api, database | `PUT /connection` seals the secret into `credential_ciphertext` and returns `status`, `capabilities`, `version`, redirect URI; unknown `cloud` or malformed GUID → `400 invalid` with `field_errors` |
| `F063-REQ-003` | FR-F063-03 | api | `POST /connection/test` → token plus `GET /v1.0/organization` under 10 s; missing consent → `ok: false` naming `GroupMember.Read.All`; `error_class`, never a raw provider string |
| `F063-REQ-004` | FR-F063-04 | api, e2e | `/auth/entra/login` carries S256 PKCE, tenant-bound 10-minute `state` and `nonce`; callback validates `state`, `nonce`, `iss`, `aud`, JWKS signature and issues an F038 session; reused, expired or foreign `state` → `400 invalid` plus audit |
| `F063-REQ-005` | FR-F063-05 | api | `email` matched case-insensitively, `preferred_username` as fallback; unlisted domain → `denied` `no_matching_user`; deactivated user → `user_inactive`; `oid` stored as `users.external_id` |
| `F063-REQ-006` | FR-F063-06 | api, e2e | `POST /sync-groups` and the nightly job read `groups` delta, map to an F002 group or F003 role binding, add and remove members, never touch `source: manual`, publish `entra.group-synced.v1`; cross-tenant target → `404 not_found` |
| `F063-REQ-007` | FR-F063-07 | api, performance | bounds of 500 groups and 50,000 members hold; a diff removing 30% of a 100-member group → `needs_review` with nothing changed; each add and removal audited with the directory group as reason |
| `F063-REQ-008` | FR-F063-08 | api | `mail` capability registers the F037 `graph` transport sending `users/{sender}/sendMail` with F037 templates and delivery records; SMTP stays default and fallback; `entra.mail-sent.v1` carries `message_id` and `recipient_domain` only |
| `F063-REQ-009` | FR-F063-09 | api, performance | one typed Graph client: 10 s timeout, backoff retries, `Retry-After` on `429`/`503`, per-tenant concurrency 4, breaker open 5 minutes after 5 failures; each call logged with operation, status and duration, recipient by domain only |
| `F063-REQ-010` | FR-F063-10 | api, frontend | `GET /connection` returns `status`, `last_test_at`, `last_error_class`, per-capability state and last sync counts with no secret; `DELETE` reverts to SMTP, stops sync and sign-in, publishes `entra.revoked.v1`, deletes no user or group |
| `F063-REQ-011` | FR-F063-11 | api | mutations require `Idempotency-Key` and `If-Match`, write a redacted audit row and publish `entra.connected.v1` or `entra.revoked.v1`; non-`identity-admin` → `403 denied`; cross-tenant id → `404 not_found` |
| `F063-REQ-012` | FR-F063-12 | frontend, e2e | `/admin/entra` shows form, copyable redirect URI, `Test connection` result, capability switches, mapping table with `Add mapping`, last sync counts and a `Disconnect` confirmation; `Sign in with Microsoft` appears on `/login` only when `sign_in` is active, beside the existing methods |
| `F063-REQ-013` | FR-F063-13 | api, frontend | tenant without a connection → `200` `status: disconnected`, no button rendered, no Graph call attempted |
| `F063-NFR-001` | NFR-F063-01 | performance | connection read p95 < 300 ms; `test` < 10 s; 500-group 50,000-member delta sync < 10 min under throttling; Graph mail ack p95 < 3 s |
| `F063-NFR-002` | NFR-F063-02 | api, database | secrets sealed and absent from responses, logs, audit diffs and exports; PKCE, `state`, `nonce`, `iss`, `aud` mandatory; unknown JWKS key rejected; suspended tenant and F003 deny rules not bypassable; recipients logged by domain |
| `F063-NFR-003` | NFR-F063-03 | accessibility | axe serious = 0 on `/admin/entra` and `/login`; the sign-in button has a text label and keyboard path; status is text plus icon; test result announced once |
| `F063-NFR-004` | NFR-F063-04 | api, performance | sync idempotent per delta token, resumable after restart, dead-lettered after 3 retries with connection `error`; `entra_graph_calls_total`, `entra_signins_total`, `entra_group_sync_members_total`, `entra_mail_total` emitted; spans carry `tenant_id` and `correlation_id` |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F063/`.
