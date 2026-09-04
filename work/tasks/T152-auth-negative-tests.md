---
id: T152
type: task
status: planned
parent_epic: E001
parent_feature: F038
parent_story: S076
depends_on: [T151]
owned_paths: [testing/features/F038/**]
feature_flag: F038_FEATURE
branch: t152-auth-negative-tests
started_at: null
finished_at: null
---

# T152 — Auth negative tests

## Identity

- Parent story: `S076` MFA and API tokens
- Owner: platform
- Branch: `t152-auth-negative-tests`

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 4, 9
- Canonical contract: `docs/capability-contracts.md` row F038

## Objective

Deliver the auth negative matrix, secret-redaction checks, E2E login and policy flows, accessibility lane, and performance lane so the feature's security claims are proven rather than asserted.

## Specification

- Owned paths: `testing/features/F038/{api/negative_tests.rs, api/redaction_tests.rs, e2e/auth.spec.ts, accessibility/auth.a11y.spec.ts, performance/auth_bench.rs, requirements/cases.md}`
- Contract/input: `TenantFixture` from F002 plus `AuthFixture` (mock provider, factors, tokens with their `api_token_scopes` rows, a required-MFA tenant, and a policy with two `security_policy_email_domains` rows), seeded through `SessionRepository`, `MfaFactorRepository`, `ApiTokenRepository`, `SecurityPolicyRepository`, and `RateLimitBucketRepository` so no harness file contains SQL (decision 2.1); the F002 `Negative` helper extended with `unauthenticated()`, `as_token(scopes)`, and `as_other_user()` replays.
- Output/behavior: `negative_tests.rs` replays all fifteen F038 routes under tenant B (`404`), other user (`404` for sessions, factors, tokens), member on policy (`403`), token whose `api_token_scopes` rows do not cover the route (`403`), no credential (`401`), plus attack cases: forged `state`, wrong `nonce`, expired ID token, unknown `kid`, refresh reuse, WebAuthn counter replay, open-redirect `return_to`; `redaction_tests.rs` captures logs and audit rows during every flow and asserts no `code`, `state`, secret, or `oh_` plaintext appears; `auth.spec.ts` drives the browser through the mock provider, TOTP enrolment under a required policy, session revocation from a second browser context, token creation and use, and policy save; `auth.a11y.spec.ts` runs axe on all auth pages; `auth_bench.rs` measures callback, session lookup, bearer lookup, and rate-limit overhead against NFR-F038-01.
- Dependencies: T151 complete; Playwright with `https://localhost` dev certificate for WebAuthn; software authenticator via CDP `WebAuthn.addVirtualAuthenticator`.
- Feature flag: `F038_FEATURE`

## TDD

- Failing test first: `testing/features/F038/api/negative_tests.rs::all_routes_cross_tenant_not_found`, `::all_routes_unauthenticated_401`, `::other_user_sessions_factors_tokens_not_found`, `::token_scope_escalation_denied`, `::forged_state_and_nonce_denied`; `testing/features/F038/api/redaction_tests.rs::no_secret_in_logs_or_audit`; `testing/features/F038/e2e/auth.spec.ts::login_enroll_totp_under_required_policy`, `::revoke_session_from_second_context`; `testing/features/F038/performance/auth_bench.rs::callback_p95`, `::session_lookup_p95`
- Targeted command: `cargo xtask test-feature F038`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/{tenants.rs, auth.rs}`; log capture layer from `testing/harness/`

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Negative matrix, redaction, E2E, accessibility, and performance lanes green
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S076
- [ ] `finished_at` recorded
