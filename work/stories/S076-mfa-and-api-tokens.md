---
id: S076
type: story
status: planned
parent_epic: E001
parent_feature: F038
depends_on: [S075]
owned_paths: [crates/domain/src/auth/**, crates/auth/src/auth/**, services/api/src/auth/**, apps/web/src/features/auth/**, testing/features/F038/**]
feature_flag: F038_FEATURE
branch: s076-mfa-and-api-tokens
started_at: null
finished_at: null
---

# S076 — MFA and API tokens

## Identity

- Parent feature: `F038` Authentication and MFA
- Owner: platform
- Branch: `s076-mfa-and-api-tokens`

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 3, 4, 9
- Canonical contract: `docs/capability-contracts.md` row F038

## Vertical slice

As a tenant administrator, I want to require MFA and bound session and token lifetimes for the whole tenant, and as a member I want to mint scoped API tokens for integrations, so that policy is enforced at the gateway, automation has least-privilege credentials, and abuse is rate limited.

## Requirements

- **SR-S076-01:** With `mfa_required = true` and no `mfa_verified_at`, every `/api/v1` route except `/api/v1/mfa/*`, `GET /api/v1/sessions`, and `POST /auth/logout` returns `403 denied` reason `mfa_required`; the web app routes to `/settings/security?enroll=1` (covers FR-F038-10).
- **SR-S076-02:** `POST /api/v1/api-tokens` returns the plaintext `oh_` token once, stores the SHA-256 hash, enforces scope subset and the policy TTL cap, emits `api-token.created.v1`; list and delete work per self, delete emits `api-token.revoked.v1` (FR-F038-11).
- **SR-S076-03:** `Authorization: Bearer oh_...` authenticates by hash into `ActorContext { auth_kind: ApiToken, scopes }`, throttles `last_used_at` writes to once per minute, and rejects revoked, expired, or unknown tokens with `401 denied` reason `invalid_token` (FR-F038-12).
- **SR-S076-04:** `rate_limit_buckets` enforce login 10/min per IP and 5/min per user, MFA verify 5 per 10 minutes, bearer auth 600/min per token, returning `429 rate_limited` with `Retry-After` (FR-F038-13).
- **SR-S076-05:** `PATCH /api/v1/tenants/{id}/security-policy` validates ranges, requires tenant-admin and `If-Match`, and takes effect on the next request without revoking sessions (FR-F038-14).
- **SR-S076-06:** Every auth event writes an audit row through `AuthAuditSink` without secrets, and logs redact codes, tokens, and OIDC parameters (FR-F038-16, NFR-F038-02).
- **SR-S076-07:** The negative suite proves member policy patch denied, cross-user and cross-tenant session and token access `404`, scope escalation denied, and unauthenticated `401` across every F038 route; callback, session, and bearer lookups meet NFR-F038-01.

## Surfaces

- Infrastructure/container: none
- Rust service/API: `crates/domain/src/auth/{api_token.rs, policy.rs, rate_limit.rs, service_token.rs, service_policy.rs, mfa_gate.rs}`; `crates/auth/src/auth/{bearer.rs, rate_limiter.rs}`; `services/api/src/auth/{handlers_token.rs, handlers_policy.rs, mfa_layer.rs}`
- Data/migration: none new; uses `api_tokens`, `security_policies`, `rate_limit_buckets` from S075's migration
- React/UI: `apps/web/src/features/auth/{ApiTokensTable.tsx, CreateApiTokenDialog.tsx, TokenRevealPanel.tsx, SecurityPolicyForm.tsx, SecurityPolicyPage.tsx}`
- Mocks/fixtures: `testing/fixtures/auth.rs` extended with one token per tenant and a required-MFA tenant variant; fixed clock advanced per test for bucket refill

## TDD harness

- Test path: `testing/features/F038/{api,frontend,e2e,accessibility,performance}/`
- Feature flag: `F038_FEATURE`
- Targeted command: `cargo xtask test-feature F038`
- Full command: `cargo xtask test-all`
- First failing tests: `mfa_required_blocks_api_until_verified`, `api_token_create_returns_plaintext_once`, `api_token_scope_escalation_denied`, `bearer_revoked_token_invalid`, `login_rate_limit_returns_retry_after`, `policy_patch_member_denied`, `policy_range_invalid`, `all_routes_cross_tenant_not_found`

## Exit criteria

- [ ] Requirement tests SR-S076-01 through SR-S076-07 written first and failing
- [ ] Tasks T151 and T152 complete; MFA layer and bearer extractor wired into the `/api/v1` stack
- [ ] Unit, API, React, E2E, accessibility, permission, and performance tests pass
- [ ] Production call path named: `services/api/src/auth/mfa_layer.rs` applied in `services/api/src/router.rs` after the `ActorContext` extractor; `apps/web/src/features/auth/SecurityPolicyPage.tsx` mounted at `/admin/security-policy`
- [ ] Handoff evidence recorded in the F038 ticket
