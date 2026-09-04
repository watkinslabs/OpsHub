---
id: T198
type: task
status: planned
parent_epic: E008
parent_feature: F050
parent_story: S099
depends_on: [T197]
owned_paths: [crates/domain/src/dynamic-views/**, crates/persistence/src/dynamic-views/**, services/api/src/dynamic-views/**, testing/features/F050/api/**, testing/features/F050/requirements/**, testing/features/F050/performance/**]
feature_flag: F050_FEATURE
branch: t198-external-access
started_at: null
finished_at: null
---

# T198 — External access

## Identity

- Parent story: `S099` Restricted views
- Owner: platform
- Branch: `t198-external-access`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 10; `docs/capability-contracts.md` row F050

## Objective

Implement public token issuance, hashing, expiry, revocation, and the unauthenticated public route so an external audience can read a dynamic view without any tenant discovery.

## Specification

- Owned paths: `crates/domain/src/dynamic-views/{token.rs, service_token.rs}`, `services/api/src/dynamic-views/{handlers_public.rs, public_routes.rs}`, `services/api/src/dynamic-views/handlers_view.rs` (token branch of PATCH)
- Contract/input: `UpdateDynamicViewRequest.public_token: { enable: bool, expires_at?, allow_edit? }` with `If-Match`; raw token is 32 random bytes, base64url in the link, stored as SHA-256 in `dynamic_views.token_hash`; `GET /public/dynamic-views/{token}` with optional `cursor`, `limit`, `fields`.
- Output/behavior: enabling returns the raw token exactly once in `DynamicViewResponse.public_link`; `expires_at` must be in the future and at most 30 days ahead or `400 invalid` with `field_errors.public_token.expires_at`; revocation sets `token_revoked_at` and the next public request returns `403 denied` with `field_errors.token = "inactive"`; the public response is `PublicViewResponse { name, columns (visible only), rows page, allow_edit, expires_at }` with no tenant, workspace, or sheet identifiers; token resolution runs `RequireModule` for the view's tenant and reads are rate-limited to 600 per token per minute; audit `dynamic-view.token.enable` / `token.revoke` and `dynamic-view.updated.v1` with `changed_fields: [public_token]`; logs include only the first 6 hex chars of the hash.
- Dependencies: T197 view and rows service; F038 `rate_limit_buckets`; F048 evaluator for `max_external_editors` (tokens with `allow_edit: true` count against it).
- Feature flag: `F050_FEATURE` gates both routers; with the flag off the public route returns `404 not_found`.

## TDD

- Failing test first: `testing/features/F050/api/token_tests.rs::token_enable_returns_raw_once_and_stores_hash`, `::token_expiry_over_30_days_invalid`, `::public_view_response_has_no_tenant_ids`, `::revoked_token_denied_on_next_request`, `::expired_token_denied`, `::token_reads_rate_limited_at_601`, `::edit_tokens_count_against_external_editor_limit`; `testing/features/F050/performance/token_bench.rs::token_resolve_under_20ms`
- Targeted command: `cargo xtask test-feature F050`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: fixed token bytes from the fixture; injectable clock for expiry; log capture for hash-prefix assertion

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Public router mounted in `services/api/src/router.rs` at `/public/dynamic-views`; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S099
- [ ] `finished_at` recorded
