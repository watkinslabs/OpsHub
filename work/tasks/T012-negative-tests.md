---
id: T012
type: task
status: planned
parent_epic: E001
parent_feature: F003
parent_story: S006
depends_on: [T011]
owned_paths: [testing/features/F003/**]
feature_flag: F003_FEATURE
branch: t012-negative-tests
started_at: null
finished_at: null
---

# T012 — Negative tests

## Identity

- Parent story: `S006` Activity history
- Owner: platform
- Branch: `t012-negative-tests`

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 4, 9
- Canonical contract: `docs/capability-contracts.md` row F003

## Objective

Publish the reusable authorization negative matrix (cross-tenant, role, guest, link, field-level), the E2E flow from role creation to audit inspection, the accessibility lane, and the audit performance lane so later features import the matrix rather than rewriting it.

## Specification

- Owned paths: `testing/features/F003/{api/negative_matrix.rs, api/isolation_tests.rs, e2e/authz.spec.ts, accessibility/authz.a11y.spec.ts, performance/audit_bench.rs, requirements/cases.md}`
- Contract/input: `NegativeMatrix::for_routes(routes: &[RouteSpec]) -> Vec<Case>` where each `RouteSpec` names method, path template, required permission, and resource kind; generated cases run the route as tenant B admin (`404`), as each system role lacking the permission (`403` or `404` per read rule), as a guest with and without a direct entry, with a placeholder link token (denied until F036 defines links), and with a field-level assertion that redacted fields are absent from responses.
- Output/behavior: `isolation_tests.rs` applies the matrix to all seven F003 routes and re-applies it to the F002 and F038 route lists to prove the extractor swap; `authz.spec.ts` drives create role, set ACL with a deny, verify the denied user sees not-found, inspect the audit trail and copy the correlation id; `authz.a11y.spec.ts` runs axe on `/admin/roles`, the `AclEditor`, and `/admin/audit` with keyboard matrix navigation; `audit_bench.rs` seeds 10,000,000 audit rows across 12 partitions and measures list p95 and `record_audit` overhead.
- Dependencies: T011 complete; `testing/fixtures/{tenants.rs, auth.rs, authz.rs}`; Playwright from F001.
- Feature flag: `F003_FEATURE`

## TDD

- Failing test first: `testing/features/F003/api/negative_matrix.rs::matrix_generates_cases_for_every_role`; `testing/features/F003/api/isolation_tests.rs::all_authz_routes_cross_tenant_not_found`, `::all_authz_routes_role_negative`, `::f002_and_f038_routes_pass_matrix`, `::audit_cross_tenant_empty_page`; `testing/features/F003/e2e/authz.spec.ts::create_role_set_deny_inspect_audit`; `testing/features/F003/accessibility/authz.a11y.spec.ts::matrix_keyboard_navigation_and_axe`; `testing/features/F003/performance/audit_bench.rs::audit_list_10m_rows_p95`, `::record_audit_overhead_p95`
- Targeted command: `cargo xtask test-feature F003`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: fixture principals for every system role and a guest; 10,000,000-row generator with fixed seed

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Matrix, isolation, E2E, accessibility, and performance lanes green; matrix imported by the F005 harness without modification
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S006
- [ ] `finished_at` recorded
