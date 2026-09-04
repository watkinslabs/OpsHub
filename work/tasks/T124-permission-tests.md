---
id: T124
type: task
status: planned
parent_epic: E007
parent_feature: F031
parent_story: S062
depends_on: [T123]
owned_paths: [testing/features/F031/api/**, testing/features/F031/e2e/**, testing/features/F031/performance/**, testing/features/F031/requirements/**]
feature_flag: F031_FEATURE
branch: t124-permission-tests
started_at: null
finished_at: null
---

# T124 — Permission tests

## Identity

- Parent story: `S062` Project rollup
- Owner: platform
- Branch: `t124-permission-tests`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 4, 9; `docs/capability-contracts.md` row F031

## Objective

Prove that portfolio reads, rollup snapshots, and drill links never expose values from projects the actor cannot read, and that the rollup meets its performance targets under a 500-project fixture.

## Specification

- Owned paths: `testing/features/F031/api/permission_tests.rs`, `testing/features/F031/e2e/portfolio_permissions.spec.ts`, `testing/features/F031/performance/rollup_bench.rs`, `testing/features/F031/requirements/cases.md`
- Contract/input: fixture tenant A with portfolio-admin, portfolio-viewer, a guest link holder, and three projects where the viewer is explicitly denied on project "Merger"; fixture tenant B admin; a generated 500-project portfolio with fixed seed.
- Output/behavior: tests assert that tenant B receives `404 not_found` on all seven routes; the viewer receives `403 denied` on POST, PATCH, PUT, and refresh; the viewer's rollup contains a `denied` row for "Merger" with null name and measures and `excluded_project_count: 1`, while the admin's rollup for the same snapshot contains its values; the stored `portfolio_rollup_rows` row for a project the tenant system actor cannot read carries `row_state: denied` and null measure values; a guest link holder receives `404` on the rollup; the drill link for a denied row is absent in the DOM; `GET /rollup` with 500 projects p95 < 500 ms over 200 requests; refresh of 100 projects completes under 30 s; enqueue acks under 2 s.
- Data access: fixtures and assertions read and write through `PortfolioRepository` and `PortfolioRollupRepository`, never with SQL of their own; the one exception is the constraint suite in `testing/features/F031/database/`, which issues raw statements on purpose to prove the database rejects them (decision section 2.1).
- Dependencies: T122 routes and job; T123 page; F003 fixture bindings including an explicit deny; F036 guest link fixture.
- Feature flag: `F031_FEATURE`

## TDD

- Failing test first: `testing/features/F031/api/permission_tests.rs::cross_tenant_all_routes_not_found`, `::viewer_all_mutations_denied`, `::viewer_rollup_excludes_denied_project_from_totals`, `::snapshot_row_stores_no_values_for_unreadable_project`, `::rollup_totals_exclude_denied_project`, `::guest_link_cannot_read_rollup`; `testing/features/F031/e2e/portfolio_permissions.spec.ts::denied_row_has_no_drill_link`; `testing/features/F031/performance/rollup_bench.rs::rollup_read_500_projects_p95`, `::refresh_100_projects_under_30s`
- Targeted command: `cargo xtask test-feature F031`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/portfolios.rs` with explicit deny binding; 500-project generator with fixed seed; real authz engine

## Exit criteria

- [ ] Tests written before any permission fix and observed failing where behavior is missing
- [ ] Permission-negative, tenant-isolation, and performance lanes green in targeted and full modes
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S062
- [ ] `finished_at` recorded
