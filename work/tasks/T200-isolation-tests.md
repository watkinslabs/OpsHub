---
id: T200
type: task
status: planned
parent_epic: E008
parent_feature: F050
parent_story: S100
depends_on: [T199]
owned_paths: [testing/features/F050/**]
feature_flag: F050_FEATURE
branch: t200-isolation-tests
started_at: null
finished_at: null
---

# T200 — Isolation tests

## Identity

- Parent story: `S100` Controlled editing
- Owner: platform
- Branch: `t200-isolation-tests`
- Decision references: `docs/architecture-decisions.md` sections 4, 9, 10; `docs/capability-contracts.md` row F050

## Objective

Complete the F050 harness with the isolation, E2E, accessibility, and performance suites proving that hidden data never leaves the service and that every audience boundary holds.

## Specification

- Owned paths: `testing/features/F050/api/isolation_tests.rs`, `testing/features/F050/e2e/dynamic_view.spec.ts`, `testing/features/F050/accessibility/dynamic_view.a11y.spec.ts`, `testing/features/F050/performance/{rows_bench.rs, edit_bench.rs}`, `testing/features/F050/requirements/cases.md` (final traceability), `testing/features/F050/README.md`
- Contract/input: seeded tenant A (owner, vendor 1, vendor 2, unshared sheet viewer), tenant B, a 100,000-row sheet generator for the performance lane, a live token and a revoked token; raw HTTP capture for body inspection.
- Output/behavior: isolation suite asserts hidden column IDs and values are absent from raw response bodies, outbox payloads, audit diffs, and captured logs; vendor 1 never sees vendor 2 rows through rows, edits, or `preview_as`; tenant B receives `404` on every route and the token of tenant A resolves only under tenant A's module guard; E2E covers owner policy → vendor edit → owner sees edit → revoke blocks link; accessibility covers axe on grid, editor, dialog, and editable-cell announcements; performance covers 100k-row filtered list p95 < 500 ms, edit p95 < 800 ms, token resolve < 20 ms; the requirements table maps every FR-F050-01..14 and NFR-F050-01..04 to case IDs and lanes.
- Dependencies: T199 UI and edit route; F004 compose baseline for Playwright.
- Feature flag: `F050_FEATURE` on for the suite; one E2E case runs with the flag off and asserts `/dv/{token}` is not-found.

## TDD

- Failing test first: `testing/features/F050/api/isolation_tests.rs::hidden_values_absent_from_bodies_events_logs`, `::vendor_cannot_see_other_vendor_rows`, `::cross_tenant_every_route_not_found`, `::preview_as_ignored_for_non_owner`; `testing/features/F050/e2e/dynamic_view.spec.ts::owner_policy_to_vendor_edit_round_trip`, `::revoked_link_shows_inactive_page`; `testing/features/F050/accessibility/dynamic_view.a11y.spec.ts::grid_editor_dialog_no_serious_axe_violations`; `testing/features/F050/performance/rows_bench.rs::filtered_rows_100k_p95`
- Targeted command: `cargo xtask test-feature F050`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: Playwright against the real API with seeded roles; k6 script for rows and edits; log capture sink from `testing/harness/logs.rs`

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Isolation, E2E, accessibility, and performance lanes pass; evidence stored under `testing/evidence/F050/`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S100
- [ ] `finished_at` recorded
