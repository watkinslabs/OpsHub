---
id: T151
type: task
status: planned
parent_epic: E001
parent_feature: F038
parent_story: S076
depends_on: [T150]
owned_paths: [crates/domain/src/auth/**, crates/auth/src/auth/**, services/api/src/auth/**, apps/web/src/features/auth/**, testing/features/F038/api/**, testing/features/F038/frontend/**]
feature_flag: F038_FEATURE
branch: t151-api-tokens-and-rate-limits
started_at: null
finished_at: null
---

# T151 — API tokens and rate limits

## Identity

- Parent story: `S076` MFA and API tokens
- Owner: platform
- Branch: `t151-api-tokens-and-rate-limits`

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 3, 4
- Canonical contract: `docs/capability-contracts.md` row F038

## Objective

Implement scoped API tokens with bearer authentication, the PostgreSQL token-bucket rate limiter, the MFA enforcement layer, the tenant security policy route, and their admin and settings UI.

## Specification

- Owned paths: `crates/domain/src/auth/{api_token.rs, policy.rs, rate_limit.rs, service_token.rs, service_policy.rs, mfa_gate.rs}`, `crates/auth/src/auth/{bearer.rs, rate_limiter.rs}`, `services/api/src/auth/{handlers_token.rs, handlers_policy.rs, mfa_layer.rs}`, `apps/web/src/features/auth/{ApiTokensTable.tsx, CreateApiTokenDialog.tsx, TokenRevealPanel.tsx, SecurityPolicyForm.tsx, SecurityPolicyPage.tsx}`
- Contract/input: `CreateApiTokenRequest { name 1–80, scopes ≤ 32, expires_at? }`, `UpdateSecurityPolicyRequest { mfa_required?, session_max_age_seconds?, idle_timeout_seconds?, refresh_ttl_seconds?, allowed_email_domains?, api_token_max_ttl_seconds? }` with `If-Match`; `RateLimiter::check(key, capacity, window) -> Result<Remaining, RetryAfter>` implemented as one `INSERT ... ON CONFLICT DO UPDATE` on `rate_limit_buckets`.
- Output/behavior: routes `GET /api/v1/api-tokens`, `POST /api/v1/api-tokens`, `DELETE /api/v1/api-tokens/{id}`, `PATCH /api/v1/tenants/{id}/security-policy`; token format `oh_` + 8 visible + 32 random chars, SHA-256 hash stored, scope subset check, TTL cap; `bearer.rs` extends the T149 extractor so `Authorization: Bearer` yields `ActorContext { auth_kind: ApiToken }` and throttles `last_used_at`; `mfa_layer.rs` returns `403 denied` reason `mfa_required` on non-exempt `/api/v1` routes; buckets per FR-F038-13 with `429` and `Retry-After`; events `api-token.created.v1`, `api-token.revoked.v1`; metrics `auth_rate_limited_total{bucket}`; UI per ticket section 3 with the one-time token reveal panel.
- Dependencies: T150 routes and pages; F002 `TenantGate` ordering (tenant gate, then extractor, then MFA layer).
- Feature flag: `F038_FEATURE`

## TDD

- Failing test first: `testing/features/F038/api/token_tests.rs::api_token_create_returns_plaintext_once`, `::api_token_scope_escalation_denied`, `::api_token_ttl_capped_by_policy`, `::bearer_authenticates_with_token_scopes`, `::bearer_revoked_token_invalid`, `::bearer_last_used_throttled`; `testing/features/F038/api/policy_tests.rs::policy_patch_member_denied`, `::policy_range_invalid`, `::mfa_required_blocks_api_until_verified`; `testing/features/F038/api/rate_limit_tests.rs::login_rate_limit_returns_retry_after`, `::bucket_refills_after_window`; `testing/features/F038/frontend/CreateApiTokenDialog.test.tsx::reveals_token_once_with_copy`, `SecurityPolicyForm.test.tsx::validates_ranges_and_stale_version`
- Targeted command: `cargo xtask test-feature F038`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/auth.rs` tokens and required-MFA tenant; fixed clock advanced per test

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Layers ordered in `services/api/src/router.rs`; OpenAPI regenerated; pages registered
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S076
- [ ] `finished_at` recorded
