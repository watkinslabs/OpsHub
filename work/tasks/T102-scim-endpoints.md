---
id: T102
type: task
status: planned
parent_epic: E006
parent_feature: F026
parent_story: S051
depends_on: [T101]
owned_paths: [crates/domain/src/sso/**, crates/persistence/src/sso/**, services/api/src/sso/**, apps/web/src/features/sso/**, testing/features/F026/api/**, testing/features/F026/frontend/**]
feature_flag: F026_FEATURE
branch: t102-scim-endpoints
started_at: null
finished_at: null
---

# T102 — SCIM endpoints

## Identity

- Parent story: `S051` SAML login
- Owner: platform
- Branch: `t102-scim-endpoints`
- Decision references: `docs/architecture-decisions.md` sections 3, 4; `docs/capability-contracts.md` row F026

## Objective

Implement SCIM bearer-token authentication with rotation, the RFC 7644 `Users` and `Groups` endpoints over F002 users and groups, SCIM error bodies, per-token rate limiting, and the one-time token dialog.

## Specification

- Owned paths: `crates/domain/src/sso/scim/{mod.rs, token.rs, filter.rs, users.rs, groups.rs, errors.rs}`, `crates/persistence/src/sso/{scim_token_repository.rs, sync_log_repository.rs}`, `services/api/src/sso/{handlers_scim.rs, scim_auth.rs, scim_dto.rs}`, `apps/web/src/features/sso/{ScimTokenDialog.tsx, ProvisioningTab.tsx}`
- Contract/input: `Authorization: Bearer <token>`; `ScimUser { schemas, id, externalId, userName, name { givenName, familyName }, emails [ { value, primary } ], active, groups, meta }`, `ScimGroup { schemas, id, externalId, displayName, members [ { value, display } ], meta }`, `ScimPatch { schemas, Operations [ { op: add|remove|replace, path?, value } ] }`; list query `filter` (`userName eq`, `externalId eq`, `displayName eq`), `startIndex` (1-based), `count` (1–200).
- Output/behavior: routes `GET /scim/v2/Users`, `POST /scim/v2/Users`, `PATCH /scim/v2/Users/{id}`, `DELETE /scim/v2/Users/{id}`, `GET /scim/v2/Groups`, `POST /scim/v2/Groups`, `PATCH /scim/v2/Groups/{id}` with `Content-Type: application/scim+json`; `ListResponse { totalResults, startIndex, itemsPerPage, Resources }`; errors `{ schemas, status, scimType, detail }` with `uniqueness` on duplicate `userName`, 404 on unknown ID or foreign tenant, 401 on unknown, revoked, or expired token; `PATCH { rotate_scim_token: true }` on the connection returns the plaintext token once, stores SHA-256, and revokes the previous token after 15 minutes; `token.rs` uses constant-time comparison; 60 requests per minute per token via F038 `rate_limit_buckets` keyed `scim:<token_id>`; each write appends `scim_sync_log` and publishes `scim.user-synced.v1` or `scim.group-synced.v1`; `active: false` delegates to `lifecycle::suspend` (T103 completes the ownership transfer; this task revokes sessions).
- Dependencies: T101 connection tables and router; F002 `users` and `groups` services; F038 session revocation and rate-limit buckets.
- Feature flag: `F026_FEATURE` gates `/scim/v2` mounting.

## TDD

- Failing test first: `testing/features/F026/api/scim_tests.rs::scim_create_user_returns_scim_json`, `::scim_list_users_filters_by_username`, `::scim_duplicate_username_uniqueness_error`, `::scim_patch_group_adds_and_removes_members`, `::scim_delete_user_deactivates_then_404`, `::scim_unknown_token_401`, `::scim_rotated_token_grace_period`, `::scim_rate_limit_429_with_retry_after`, `::scim_foreign_tenant_token_not_found`; `testing/features/F026/frontend/ScimTokenDialog.test.tsx::shows_token_once_and_copies`
- Targeted command: `cargo xtask test-feature F026`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/sso.rs` SCIM token for tenant A and B; fixed clock advanced across the grace window

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] `/scim/v2` mounted outside session middleware behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S051
- [ ] `finished_at` recorded
