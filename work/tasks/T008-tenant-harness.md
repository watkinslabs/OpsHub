---
id: T008
type: task
status: planned
parent_epic: E001
parent_feature: F002
parent_story: S004
depends_on: [T007]
owned_paths: [testing/features/F002/**]
feature_flag: F002_FEATURE
branch: t008-tenant-harness
started_at: null
finished_at: null
---

# T008 — Tenant harness

## Identity

- Parent story: `S004` Users and groups
- Owner: platform
- Branch: `t008-tenant-harness`

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 4, 9
- Canonical contract: `docs/capability-contracts.md` row F002

## Objective

Publish the two-tenant fixture, the cross-tenant and role-negative suite, and the E2E, accessibility, and performance lanes so every later feature can prove isolation with the same seeded principals.

## Specification

- Owned paths: `testing/features/F002/{api/isolation_tests.rs, e2e/admin.spec.ts, accessibility/admin.a11y.spec.ts, performance/user_list_bench.rs, requirements/cases.md}` and the fixture module documented in `testing/features/F002/README.md` (the fixture source `testing/fixtures/tenants.rs` is written under the F002 lane and referenced by path from later features)
- Contract/input: fixture builder `TenantFixture::seed(db) -> TenantFixture { tenant_a, tenant_b, admin_a, admin_b, member_a, member_b, invited_a, deactivated_a, groups_a: [3], groups_b: [3] }` with fixed UUIDv7 seeds and clock `2026-09-03T00:00:00Z`, seeded through `TenantRepository`, `UserRepository`, and `GroupRepository` so the fixture writes `tenants`, `tenant_settings` (the trigger-created row, patched for the required-locale case), `users`, `groups`, and `group_members` with no SQL in the harness (decision 2.1); a `Negative` helper that replays a request under `tenant_b` context and asserts `404 not_found`, and under `member` context and asserts `403 denied`.
- Output/behavior: `isolation_tests.rs` iterates all twelve F002 routes through the helper; `admin.spec.ts` covers invite, group creation, member editing, deactivation, and the suspended-tenant notice showing the seeded `tenant_settings.operator_contact`; `admin.a11y.spec.ts` runs axe on the three admin pages and verifies keyboard member toggling and live-region announcements; `user_list_bench.rs` seeds 100,000 users and 5,000-member groups through the repositories and records p95 values against NFR-F002-01.
- Dependencies: T007 routes and pages; Playwright and axe from F001; `testing/harness/db.rs`.
- Feature flag: `F002_FEATURE`

## TDD

- Failing test first: `testing/features/F002/api/isolation_tests.rs::all_routes_cross_tenant_not_found`, `::all_mutations_member_denied`, `::suspended_tenant_writes_denied`; `testing/features/F002/e2e/admin.spec.ts::invite_user_create_group_edit_members`, `::deactivate_user_revokes_access`; `testing/features/F002/accessibility/admin.a11y.spec.ts::admin_pages_have_no_serious_axe_violations`; `testing/features/F002/performance/user_list_bench.rs::user_list_100k_p95`
- Targeted command: `cargo xtask test-feature F002`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: the fixture itself; Playwright runs against the real API with Mailpit capturing invite mail once F037 exists (until then invite mail is not asserted)

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Fixture consumed by at least the F038 harness without modification
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S004
- [ ] `finished_at` recorded
