---
id: T092
type: task
status: planned
parent_epic: E005
parent_feature: F023
parent_story: S046
depends_on: [T091]
owned_paths: [testing/features/F023/**, apps/web/src/features/dashboards/**]
feature_flag: F023_FEATURE
branch: t092-visual-access-tests
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 4, 6, 9
- Capability contract: `docs/capability-contracts.md` row F023

# T092 — Visual/access tests

## Identity

- Parent story: `S046` Sharing
- Owner: platform
- Branch: `t092-visual-access-tests`
- Decision references: `docs/architecture-decisions.md` sections 4, 6, 9; `docs/capability-contracts.md` row F023

## Objective

Complete the F023 harness with visual regression snapshots of the grid at three breakpoints, the access suite for editors, viewers, guests, and foreign tenants, E2E, accessibility, and performance lanes, fixing defects they expose in the dashboard UI.

## Specification

- Owned paths: `testing/features/F023/api/permission_tests.rs`, `testing/features/F023/e2e/dashboard.spec.ts`, `testing/features/F023/e2e/visual.spec.ts`, `testing/features/F023/e2e/__snapshots__/`, `testing/features/F023/accessibility/dashboard.a11y.spec.ts`, `testing/features/F023/performance/{dashboard_get_bench.rs, widget_data_bench.rs, refresh_bench.rs}`, `testing/features/F023/requirements/cases.md`, fixes limited to `apps/web/src/features/dashboards/**`
- Contract/input: routes and UI from T091; Playwright visual comparisons at 1280, 800, and 390 px widths with a 0.1% pixel threshold; the 40-widget generator with seed `0x0F23`.
- Output/behavior: the permission suite drives the dashboard repository traits rather than issuing SQL and covers cross-tenant `404` on every route including widget data, viewer mutation `403`, share-link mutation and refresh `403`, a `denied` widget for a restricted `dashboard_widget_sources` row, expired link `404`, and cache isolation between scopes; the visual suite likewise seeds fixtures through the repository traits; visual suite snapshots the builder and viewer at three widths and the six widget statuses; E2E builds "Weekly review", saves, shares with a group, opens as viewer and as link guest, refreshes, and observes the stale badge after a report refresh; accessibility runs axe on builder and viewer and checks keyboard move, resize, and announcements; performance measures 40-widget `GET` p95 < 500 ms, cache hit p95 < 300 ms, full refresh < 60 s, and drag frame time with evidence under `testing/evidence/F023/`.
- Dependencies: T091 UI; T090 repository traits used by the fixtures; Playwright, axe, and criterion runners in `testing/harness/`; F021 report fixture whose snapshot version drives the `widget_cache_sources` stale scenario.
- Feature flag: `F023_FEATURE`

## TDD

- Failing test first: `testing/features/F023/api/permission_tests.rs::expired_share_link_not_found`, `::cache_isolated_between_scopes`, `::foreign_tenant_widget_data_not_found`; `testing/features/F023/e2e/dashboard.spec.ts::build_save_share_and_view_as_guest`, `::stale_badge_after_report_refresh`; `testing/features/F023/e2e/visual.spec.ts::grid_matches_snapshots_at_three_widths`; `testing/features/F023/accessibility/dashboard.a11y.spec.ts::keyboard_move_and_resize_announced`; `testing/features/F023/performance/dashboard_get_bench.rs::dashboard_get_40_widgets_p95`
- Targeted command: `cargo xtask test-feature F023`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: seeded tenant for Playwright; 40-widget generator; share-link guest session; real API and worker in compose

## Exit criteria

- [ ] Tests written before fixes and observed failing where defects exist
- [ ] All seven lanes green; snapshots and evidence stored under `testing/evidence/F023/`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S046
- [ ] `finished_at` recorded
