---
id: T224
type: task
status: planned
parent_epic: E008
parent_feature: F056
parent_story: S112
depends_on: [T223]
owned_paths: [testing/features/F056/e2e/**, testing/features/F056/accessibility/**, testing/features/F056/performance/**, testing/features/F056/api/**]
feature_flag: F056_FEATURE
branch: t224-calculation-tests
started_at: null
finished_at: null
---

# T224 — Calculation tests

## Identity

- Parent story: `S112` Saved outputs
- Owner: platform
- Branch: `t224-calculation-tests`
- Decision references: `docs/architecture-decisions.md` section 9; `docs/capability-contracts.md` row F056

## Objective

Prove aggregation correctness, permission filtering, stale detection, accessibility, and the compute and read performance budgets with golden fixtures and end-to-end flows.

## Specification

- Owned paths: `testing/features/F056/api/golden_tests.rs`, `testing/features/F056/e2e/pivot.spec.ts`, `testing/features/F056/accessibility/pivot.a11y.spec.ts`, `testing/features/F056/performance/pivot_bench.rs`, `testing/features/F056/api/fixtures/golden_pivots.json`
- Contract/input: golden file lists 12 pivot definitions with expected cells computed independently in SQL over the seeded 2,000-row sheet, including DST week and month buckets, `count_distinct` over person columns, and `avg` with decimal rounding to 4 places.
- Output/behavior: every golden case matches cell for cell; hidden rows change no visible sum; E2E covers build → compute → grid → materialize → open sheet, stale banner after a source edit, and the unentitled upsell; axe reports zero serious violations on builder and grid; performance lane records p95 for outputs read of 5,000 cells (< 500 ms) and 100,000-row compute (< 30 s).
- Dependencies: T223 complete; Playwright and axe harness from `testing/harness/`.
- Feature flag: `F056_FEATURE`

## TDD

- Failing test first: `testing/features/F056/api/golden_tests.rs::golden_pivots_match_sql_reference`, `::hidden_rows_never_change_visible_sums`; `testing/features/F056/e2e/pivot.spec.ts::build_compute_materialize_open_sheet`, `::stale_banner_after_source_edit`, `::unentitled_tenant_sees_upsell`; `testing/features/F056/accessibility/pivot.a11y.spec.ts::builder_and_grid_have_no_serious_axe_violations`; `testing/features/F056/performance/pivot_bench.rs::outputs_read_5k_cells_p95`, `::compute_100k_rows_under_30s`
- Targeted command: `cargo xtask test-feature F056`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: golden JSON with fixed seed; 100,000-row generator; Playwright against the real API on a seeded entitled tenant and an unentitled tenant

## Exit criteria

- [ ] Golden, E2E, accessibility, and performance lanes pass in targeted and full modes
- [ ] p95 targets from NFR-F056-01 recorded under `testing/evidence/F056/performance/`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S112
- [ ] `finished_at` recorded
