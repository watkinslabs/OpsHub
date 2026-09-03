---
id: T088
type: task
status: planned
parent_epic: E005
parent_feature: F022
parent_story: S044
depends_on: [T087]
owned_paths: [testing/features/F022/**, crates/domain/src/metrics/**, apps/web/src/features/metrics/**]
feature_flag: F022_FEATURE
branch: t088-calculation-fixtures
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 4, 9
- Capability contract: `docs/capability-contracts.md` row F022

# T088 — Calculation fixtures

## Identity

- Parent story: `S044` Rollups/trends
- Owner: platform
- Branch: `t088-calculation-fixtures`
- Decision references: `docs/architecture-decisions.md` sections 4, 9; `docs/capability-contracts.md` row F022

## Objective

Build deterministic calculation fixtures with known expected values for every aggregation, grain, comparison, and locale, and complete the permission, E2E, accessibility, and performance lanes, fixing defects they expose.

## Specification

- Owned paths: `testing/features/F022/api/calculation_tests.rs`, `testing/features/F022/api/permission_tests.rs`, `testing/features/F022/fixtures/expected_values.json`, `testing/features/F022/e2e/metric.spec.ts`, `testing/features/F022/accessibility/kpi.a11y.spec.ts`, `testing/features/F022/performance/{metric_values_bench.rs, recompute_bench.rs}`, `testing/features/F022/requirements/cases.md`, fixes limited to `crates/domain/src/metrics/**` and `apps/web/src/features/metrics/**`
- Contract/input: `expected_values.json` lists 40 cases `{ metric, scope, grain, from, to, expected_current, expected_series, expected_comparison, expected_formatted }` derived by hand from the three-sheet fixture at clock `2026-09-03T00:00:00Z`, including DST weeks of 2026-03-08 and 2026-11-01, an empty denominator for `percent_of`, and locale `de-DE` currency.
- Output/behavior: calculation tests load each case, recompute, read values, and assert equality to the decimal; permission tests cover cross-tenant `404`, viewer mutation `403`, restricted-source scope, hidden-column null, and scope_key isolation between two viewers; E2E defines a metric from the report UI, waits for the value, edits a source row, sees the stale badge, and recomputes; accessibility runs axe on the card grid and editor and checks text alternatives; performance measures `values` p95 < 300 ms and recompute < 30 s over 100,000 rows with evidence under `testing/evidence/F022/`.
- Dependencies: T087 UI and rollups; F021 fixture; Playwright and criterion runners in `testing/harness/`.
- Feature flag: `F022_FEATURE`

## TDD

- Failing test first: `testing/features/F022/api/calculation_tests.rs::expected_values_match_for_all_cases`, `::dst_week_buckets_have_seven_days`, `::percent_of_matches_hand_computed_ratio`; `testing/features/F022/api/permission_tests.rs::two_viewers_never_share_scope_values`, `::restricted_viewer_gets_scoped_count`; `testing/features/F022/e2e/metric.spec.ts::define_metric_and_see_value`, `::stale_badge_after_source_edit`; `testing/features/F022/performance/metric_values_bench.rs::metric_values_p95`
- Targeted command: `cargo xtask test-feature F022`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `expected_values.json`; seeded tenant for Playwright; 100,000-row source generator with seed `0x0F22`

## Exit criteria

- [ ] Tests written before fixes and observed failing where defects exist
- [ ] All seven lanes green; evidence stored under `testing/evidence/F022/`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S044
- [ ] `finished_at` recorded
