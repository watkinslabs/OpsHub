---
id: T084
type: task
status: planned
parent_epic: E005
parent_feature: F021
parent_story: S042
depends_on: [T083]
owned_paths: [testing/features/F021/**, apps/web/src/features/reports/**]
feature_flag: F021_FEATURE
branch: t084-query-tests
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 4, 9
- Capability contract: `docs/capability-contracts.md` row F021

# T084 — Query tests

## Identity

- Parent story: `S042` Filters/joins
- Owner: platform
- Branch: `t084-query-tests`
- Decision references: `docs/architecture-decisions.md` sections 4, 9; `docs/capability-contracts.md` row F021

## Objective

Complete the F021 harness with property tests over join and filter semantics, the permission-negative suite, browser E2E, accessibility, and the 100,000-row performance lane, fixing defects they expose in the report UI.

## Specification

- Owned paths: `testing/features/F021/api/property_tests.rs`, `testing/features/F021/api/permission_tests.rs`, `testing/features/F021/e2e/report.spec.ts`, `testing/features/F021/accessibility/report.a11y.spec.ts`, `testing/features/F021/performance/report_rows_bench.rs`, `testing/features/F021/performance/refresh_bench.rs`, `testing/features/F021/requirements/cases.md`, fixes limited to `apps/web/src/features/reports/**`
- Contract/input: routes and DTOs from T083; the `proptest` strategies generate definitions with 1..5 sources, random join trees, filter trees to depth 4, and typed values; the 100,000-row generator seeds three sheets with 500 columns using seed `0x0F21`.
- Output/behavior: property tests assert that a definition survives `replace_definition` then `load_definition` unchanged across the eight definition tables, that every joined row references existing source rows through its `report_snapshot_row_sources` entries, that `inner` joins never emit nulls on the right, that filters are equivalent to an in-memory reference evaluator, and that group aggregates equal a reference fold over visible rows; permission suite covers cross-tenant, viewer mutation, restricted sheet, hidden column, field-level ACL, and guest share link; E2E builds the three-sheet report through the UI, refreshes, checks group headers, stale banner after editing a source row, and restricted-source bar as the restricted viewer; accessibility runs axe on editor and viewer and checks live-region announcements; performance measures rows page p95 < 500 ms and three-sheet refresh < 60 s and records results under `testing/evidence/F021/`.
- Dependencies: T083 routes and UI; `testing/harness/` Playwright and criterion runners.
- Feature flag: `F021_FEATURE`

## TDD

- Failing test first: `testing/features/F021/api/property_tests.rs::joined_rows_reference_existing_sources`, `::filter_tree_matches_reference_evaluator`, `::group_aggregates_match_reference_fold`; `testing/features/F021/api/permission_tests.rs::guest_link_cannot_refresh`, `::field_level_acl_hides_column`; `testing/features/F021/e2e/report.spec.ts::build_three_sheet_report_and_refresh`, `::restricted_viewer_sees_notice`; `testing/features/F021/performance/report_rows_bench.rs::report_rows_100k_p95`
- Targeted command: `cargo xtask test-feature F021`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: seeded tenant for Playwright; 100,000-row generator; real API and worker in compose; every Rust lane reads and writes through `ReportRepository` and `ReportSnapshotRepository` and contains no SQL string, `sqlx::query*` call, or connection

## Exit criteria

- [ ] Tests written before fixes and observed failing where defects exist
- [ ] All seven lanes green; evidence stored under `testing/evidence/F021/`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S042
- [ ] `finished_at` recorded
