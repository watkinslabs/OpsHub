---
id: T123
type: task
status: planned
parent_epic: E007
parent_feature: F031
parent_story: S062
depends_on: [T122]
owned_paths: [apps/web/src/features/portfolios/**, testing/features/F031/frontend/**, testing/features/F031/e2e/**, testing/features/F031/accessibility/**]
feature_flag: F031_FEATURE
branch: t123-portfolio-ui
started_at: null
finished_at: null
---

# T123 — Portfolio UI

## Identity

- Parent story: `S062` Project rollup
- Owner: platform
- Branch: `t123-portfolio-ui`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 6; `docs/capability-contracts.md` row F031

## Objective

Build the portfolio list and rollup pages with the project picker, measure mapping editor, refresh control, stale badge, and permission-aware drill links wired to the real portfolio API.

## Specification

- Owned paths: `apps/web/src/features/portfolios/{PortfolioListPage.tsx, PortfolioPage.tsx, PortfolioHeader.tsx, RollupTable.tsx, RollupTotals.tsx, MeasureCell.tsx, ProjectPicker.tsx, NewPortfolioDialog.tsx, MeasureMappingEditor.tsx, api.ts, hooks.ts, routes.ts}`
- Contract/input: generated `PortfoliosApi` client; route params `workspaceId`, `portfolioId`; query keys `['portfolios', workspaceId, cursor]`, `['portfolio', id]`, `['portfolio-rollup', id]`.
- Output/behavior: list page with `New portfolio` for administrators; rollup page renders `RollupTotals` and `RollupTable` (one row per project; columns status, schedule variance, budget planned/actual/variance, risk, value, health) with `Last refreshed`, stale badge after `stale_after_seconds`, `Refresh` that calls `requestRefresh` and polls `['portfolio', id]` every 2 seconds while `rollup_state === 'refreshing'`, `Missing` cells with reason tooltip, `Restricted project` rows for `denied`, drill link only for `ok` rows; `ProjectPicker` replaces membership optimistically and shows `field_errors.projects[i]` inline on `invalid`; states: loading skeleton, empty call to action, error banner with correlation ID, refreshing, failed with `last_refresh_error`, denied affordances for viewers, not-found page; under 768 px rows become stacked cards; Lucide icons and tokens per ticket section 3; telemetry `portfolio_created`, `portfolio_opened`, `portfolio_projects_replaced`, `portfolio_refresh_requested`, `portfolio_drill_opened`.
- Data access: this task is browser-only and touches no database; it consumes `PortfoliosApi`, and the `measure_mappings` object and `rows`/`totals` arrays it renders keep their JSON shapes even though the server stores them as `portfolio_measure_mappings`, `portfolio_rollup_rows`, and `portfolio_rollup_totals` rows (decision sections 2 and 2.1).
- Dependencies: T122 routes; F005 workspace shell for the `Portfolios` sidebar entry; F006 sheet page as the drill target.
- Feature flag: `F031_FEATURE` read through the flag hook; routes are not registered when off.

## TDD

- Failing test first: `testing/features/F031/frontend/RollupTable.test.tsx::renders_rows_with_measure_states`, `::shows_stale_badge_after_threshold`, `::hides_drill_link_for_denied_row`, `PortfolioPage.test.tsx::refresh_polls_until_fresh`, `::shows_denied_affordances_for_viewer`, `ProjectPicker.test.tsx::shows_per_project_errors_on_invalid`; `testing/features/F031/e2e/portfolio.spec.ts::create_portfolio_add_projects_refresh`, `::viewer_sees_restricted_row_without_values`; `testing/features/F031/accessibility/portfolio.a11y.spec.ts::rollup_page_has_no_serious_axe_violations`
- Targeted command: `cargo xtask test-feature F031`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: MSW handlers from the three-project fixture including a denied row and a missing budget measure; Playwright uses the real API against a seeded tenant

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Component, E2E, and accessibility lanes pass
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S062
- [ ] `finished_at` recorded
