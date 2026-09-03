---
id: T104
type: task
status: planned
parent_epic: E006
parent_feature: F026
parent_story: S052
depends_on: [T103]
owned_paths: [testing/features/F026/**]
feature_flag: F026_FEATURE
branch: t104-identity-tests
started_at: null
finished_at: null
---

# T104 — Identity tests

## Identity

- Parent story: `S052` Lifecycle sync
- Owner: platform
- Branch: `t104-identity-tests`
- Decision references: `docs/architecture-decisions.md` sections 4, 9; `docs/capability-contracts.md` row F026

## Objective

Complete the F026 harness with provider-shaped assertion fixtures, permission-negative and tenant-isolation suites, the end-to-end browser flow through the stub identity provider, accessibility checks, and the performance lane.

## Specification

- Owned paths: `testing/features/F026/api/negative_tests.rs`, `testing/features/F026/database/constraint_tests.rs`, `testing/features/F026/e2e/sso.spec.ts`, `testing/features/F026/accessibility/sso.a11y.spec.ts`, `testing/features/F026/performance/{acs_bench.rs, scim_bench.rs}`, `testing/features/F026/{README.md, requirements/cases.md}`
- Contract/input: assertion fixtures shaped like Microsoft Entra ID (`http://schemas.xmlsoap.org/ws/2005/05/identity/claims/*` attributes, RSA-SHA256) and Google Workspace (`email`, `firstName`, `lastName` attributes) signed by the stub key; tenant A and B with one connection and one SCIM token each; Playwright stub IdP page at `/testing/idp` served by the harness.
- Output/behavior: negatives prove `not_found` for foreign-tenant connection and SCIM access, `denied` for member connection writes and for logins on disabled connections, rejection of signature-wrapped responses with two assertions, XML with a DTD, and assertions signed with a retired certificate; the E2E flow configures a connection, signs in as Ana through the stub IdP, suspends Ben through SCIM, and shows Ana as owner of Ben's sheet; accessibility runs axe on `/admin/sso`, the form, the token dialog, and the mapping editor; performance measures ACS p95 under 800 ms over 200 logins and group PATCH with 500 members under 2 s.
- Dependencies: T101, T102, T103 implementations; `testing/harness/` Playwright and criterion runners.
- Feature flag: `F026_FEATURE`

## TDD

- Failing test first: `testing/features/F026/api/negative_tests.rs::foreign_tenant_connection_not_found`, `::disabled_connection_login_denied`, `::signature_wrapping_two_assertions_rejected`, `::dtd_in_response_rejected`, `::retired_certificate_rejected`; `testing/features/F026/e2e/sso.spec.ts::configure_connection_and_login_via_idp`, `::scim_suspend_transfers_sheet_owner`; `testing/features/F026/accessibility/sso.a11y.spec.ts::admin_sso_pages_have_no_serious_violations`; `testing/features/F026/performance/acs_bench.rs::acs_login_p95`, `testing/features/F026/performance/scim_bench.rs::scim_group_patch_500_members_p95`
- Targeted command: `cargo xtask test-feature F026`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/sso.rs` provider-shaped assertions; stub IdP page; 500-member group generator with fixed seed

## Exit criteria

- [ ] Tests written before implementation and observed failing where the behavior is not yet present
- [ ] All seven lanes green in targeted and full modes with evidence under `testing/evidence/F026/`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S052
- [ ] `finished_at` recorded
