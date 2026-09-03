---
id: T244
type: task
status: planned
parent_epic: E008
parent_feature: F061
parent_story: S122
depends_on: [S122]
owned_paths: [testing/features/F061/**]
feature_flag: F061_FEATURE
branch: t244-request-tests
started_at: null
finished_at: null
---

# T244 — Request tests

## Identity

- Parent story: `S122` Recipient experience
- Owner: platform
- Branch: `t244-request-tests`
- Decision references: `docs/architecture-decisions.md` sections 6, 8; `docs/capability-contracts.md` row F061

## Objective

Build the F061 fixture factory and the end-to-end, accessibility, performance, and negative-path suites that prove the whole update-request loop — send, remind, respond, revoke — including the tenant-isolation and token-abuse cases that no single implementation task owns.

## Specification

- Owned paths: `testing/features/F061/{requirements,api,database,frontend,e2e,accessibility,performance}/**`, `testing/fixtures/update_requests.rs`, `testing/features/F061/{README.md, feature.toml}`
- Contract/input: the fixture factory seeds tenant A and tenant B, sheet `Site works` with 12 typed columns (text, date, single-select, contact, formula) and 250 rows, a requester, a sheet-admin, a plain member, two internal recipients, the external recipient `paul@contractor.example`, an open request scoped to 12 rows × 3 columns, a completed request, a cancelled request, an expired request, a 100,000-row `reminder_schedules` generator, a recorded `NotificationService`, a recorded outbox, a fixed token seed, and the clock `2026-09-03T00:00:00Z`
- Output/behavior: `e2e/update_requests.spec.ts` drives send → open the link with no session → save a draft → return → submit → verify the sheet cells, the change log, and the audit trail, then a second flow that fires a reminder and a third that cancels and proves the link dies; `accessibility/update_requests.a11y.spec.ts` runs axe over the dialog, list, detail drawer, and the public form at 320 px and asserts keyboard-only completion and live-region announcements; `performance/{public_scope_bench.rs, submit_bench.rs, list_bench.rs}` cover the 200×20 scope read, the 50-cell submission, and the 10,000-request list against NFR-F061-01; the negative suite covers cross-tenant tokens and ids, brute-forced tokens, payloads over 1 MB, and submissions after cancel or expiry; every lane's `cases.md` stays the traceability index from FR and NFR ids to the test names actually implemented.
- Dependencies: T241 schema and routes, T242 jobs, T243 public routes and React surfaces; F008 sheet fixtures; F037 recorded notification service; Mailpit for the delivered-email assertion.
- Feature flag: `F061_FEATURE` gates every suite; `cargo xtask test-feature F061` runs them in isolation with one schema per worker.

## TDD

- Failing test first: `testing/features/F061/e2e/update_requests.spec.ts::external_recipient_completes_in_two_visits`, `::reminder_fires_and_appears_in_mailpit`, `::cancel_kills_every_link`; `testing/features/F061/accessibility/update_requests.a11y.spec.ts::public_form_has_no_serious_violations_at_320px`, `::public_form_completable_by_keyboard`; `testing/features/F061/api/negative_tests.rs::foreign_tenant_token_returns_not_found`, `::brute_forced_token_rate_limited_and_counted`, `::payload_over_one_megabyte_rejected`, `::submission_after_cancel_returns_conflict`; `testing/features/F061/performance/public_scope_bench.rs::scope_read_200x20_under_300ms`
- Targeted command: `cargo xtask test-feature F061`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/update_requests.rs` as above; MSW for the frontend lane; Playwright with a session-free browser context for public pages; Mailpit for delivery assertions; positive control per gate — break one assertion, observe RED, restore, observe GREEN

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] All seven lanes green in targeted and full modes with evidence under `testing/evidence/F061/`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S122
- [ ] `finished_at` recorded
