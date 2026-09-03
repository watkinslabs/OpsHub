---
id: T204
type: task
status: planned
parent_epic: E008
parent_feature: F051
parent_story: S102
depends_on: [T203]
owned_paths: [testing/features/F051/**]
feature_flag: F051_FEATURE
branch: t204-app-security-tests
started_at: null
finished_at: null
---

# T204 — App security tests

## Identity

- Parent story: `S102` Role experiences
- Owner: platform
- Branch: `t204-app-security-tests`
- Decision references: `docs/architecture-decisions.md` sections 4, 9, 10; `docs/capability-contracts.md` row F051

## Objective

Complete the F051 harness with the security, E2E, accessibility, and performance suites proving that an app never widens access and that role boundaries and versions behave as specified.

## Specification

- Owned paths: `testing/features/F051/api/security_tests.rs`, `testing/features/F051/e2e/workapp.spec.ts`, `testing/features/F051/accessibility/workapp.a11y.spec.ts`, `testing/features/F051/performance/{manifest_bench.rs, shell_bench.spec.ts}`, `testing/features/F051/requirements/cases.md` (final traceability), `testing/features/F051/README.md`
- Contract/input: seeded tenant A (app admin, procurement user, vendor user via group `Vendors`, no-role member), tenant B, published app with four pages and two roles, a 50-page/20-role generated app for performance; network capture in Playwright.
- Output/behavior: security suite asserts the vendor manifest lists two pages and no other role's members, every embed request in the browser goes to the source endpoint with the viewer's session, a page whose sheet the vendor cannot read yields a 404 from the sheets API and a denied frame, the no-role member and tenant B get `404` on the slug, a non-admin cannot read the draft, and a not-entitled tenant gets `403`; E2E covers build → publish → vendor sees two pages → admin edits draft without change to served app → restore version 1; accessibility covers axe on shell and builder, keyboard reorder, nav current state, role preview announcement; performance covers manifest p95 < 300 ms and shell navigation render < 500 ms; the requirements table maps every FR-F051-01..13 and NFR-F051-01..04 to case IDs and lanes.
- Dependencies: T203 UI and viewer route; F004 compose baseline for Playwright.
- Feature flag: `F051_FEATURE` on for the suite; one E2E case runs with the flag off and asserts `/apps/{slug}` is not-found.

## TDD

- Failing test first: `testing/features/F051/api/security_tests.rs::vendor_manifest_has_two_pages_and_no_foreign_members`, `::no_role_member_and_cross_tenant_not_found`, `::non_admin_cannot_read_draft`, `::not_entitled_tenant_denied`; `testing/features/F051/e2e/workapp.spec.ts::build_publish_vendor_sees_two_pages`, `::embed_requests_hit_source_endpoints_with_viewer_session`, `::draft_edit_does_not_change_served_app`, `::restore_version_one`; `testing/features/F051/accessibility/workapp.a11y.spec.ts::shell_and_builder_no_serious_axe_violations`; `testing/features/F051/performance/manifest_bench.rs::manifest_50_pages_20_roles_p95`
- Targeted command: `cargo xtask test-feature F051`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: Playwright against the real API with seeded roles and network capture; k6 script for the manifest route; generated large app from `testing/fixtures/workapps.rs::large_app`

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Security, E2E, accessibility, and performance lanes pass; evidence stored under `testing/evidence/F051/`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S102
- [ ] `finished_at` recorded
