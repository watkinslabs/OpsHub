---
id: T096
type: task
status: planned
parent_epic: E005
parent_feature: F024
parent_story: S048
depends_on: [S048]
owned_paths: [testing/features/F024/frontend/**, testing/features/F024/e2e/**, testing/features/F024/accessibility/**, testing/features/F024/performance/**, testing/features/F024/requirements/**]
feature_flag: F024_FEATURE
branch: t096-render-tests
started_at: null
finished_at: null
---

# T096 — Chart render, E2E, accessibility and performance tests

## Identity

- Parent story: `S048` Burndown, timeline, workload and chart rendering
- Owner: platform
- Branch: `t096-render-tests`
- Decision references: `docs/architecture-decisions.md` sections 6, 9; `docs/capability-contracts.md` row F024

## Objective

Build the frontend, E2E, accessibility, and performance lanes of `testing/features/F024/` that prove the eight renderers, `ChartFrame` states, the table alternative, and the spec editor behave for data, empty, error, denied, stale, and truncated payloads, and that the render and query budgets in NFR-F024-01 hold.

## Specification

- Owned paths: `testing/features/F024/frontend/{BarChart.test.tsx, LineChart.test.tsx, PieChart.test.tsx, BurndownChart.test.tsx, TimelineChart.test.tsx, WorkloadHeatmap.test.tsx, KpiWidget.test.tsx, MetricComparisonWidget.test.tsx, ChartFrame.test.tsx, ChartDataTable.test.tsx, ChartSpecEditor.test.tsx}`; `testing/features/F024/e2e/charts.spec.ts`; `testing/features/F024/accessibility/charts.a11y.spec.ts`; `testing/features/F024/performance/{chart_query_bench.rs, burndown_bench.rs, render_bench.ts}`; `testing/features/F024/requirements/cases.md` traceability table.
- Runners: Vitest with MSW for `frontend`, Playwright against the seeded tenant for `e2e` and `accessibility` (axe-core), criterion for the Rust benches and a Playwright performance trace for the render bench. All lanes run under `F024_FEATURE`.
- Fixture contract consumed (owned by T093 and T095): `testing/fixtures/charts.rs` with report "Portfolio status" (100,000 rows, `Budget.margin` hidden from viewer Lee), sheet "Sprint 12" (200 rows with 14 days of `Status` history, plus a 10,000-row 90-day variant), metric "Open high risks" (52 weekly values), dashboard "Weekly review" with one widget per kind, fixed clock `2026-09-03T00:00:00Z`, timezone `America/New_York`, seed `0x0F24`.
- Frontend lane asserts: each renderer with populated, empty, error, denied, stale, and truncated payloads; `ChartFrame` shows `empty_state.message`, `error_state.message` with `correlation_id` and retry, and "Showing first 1,000 points"; `ChartDataTable` values match the series exactly; `ChartSpecEditor` blocks save on a missing declaration and maps `field_errors` to controls; `WorkloadHeatmap` marks over-capacity cells; legends reflow under 480 px.
- E2E lane asserts: an editor adds Bar, Line with a 30-day linear projection, Burndown for "Sprint 12", and Workload widgets to "Weekly review", each renders, keyboard navigation announces points, `T` reveals the table, and viewer Lee sees `denied` on the widget over the restricted sheet.
- Accessibility lane asserts: zero serious or critical axe violations on the dashboard and the spec editor drawer, `aria-label` summaries naming kind, series count, min, max, and latest, keyboard-reachable tooltips, pattern fills so series are not colour-only at 3:1 contrast, and `prefers-reduced-motion` disabling transitions.
- Performance lane asserts: `POST /charts/query` p95 under 800 ms over the 100,000-row snapshot with 2 dimensions, burndown p95 under 2 s over 10,000 rows and 90 days with the 60 s cache measured on the second call, and a 1,000-point line render under 100 ms.
- Evidence: Vitest and Playwright JUnit, axe JSON, criterion summaries, and traces written under `testing/evidence/F024/{frontend,e2e,accessibility,performance}/`.
- Feature flag: `F024_FEATURE` on for every lane; a flag-off smoke case asserts the F023 unavailable tile.

## TDD

- Failing test first: `testing/features/F024/frontend/ChartFrame.test.tsx::renders_empty_state_message_when_all_series_empty`, `::renders_error_state_with_correlation_id_and_retry`, `::renders_truncated_note_at_one_thousand_points`; `testing/features/F024/frontend/ChartDataTable.test.tsx::table_toggle_matches_series_values`; `testing/features/F024/frontend/ChartSpecEditor.test.tsx::blocks_save_when_formatting_missing`, `::maps_field_errors_to_controls`; `testing/features/F024/frontend/WorkloadHeatmap.test.tsx::marks_cells_over_capacity`; `testing/features/F024/e2e/charts.spec.ts::add_bar_line_burndown_and_workload_widgets`, `::line_chart_arrow_keys_announce_point`, `::viewer_sees_denied_tile_for_restricted_sheet`; `testing/features/F024/accessibility/charts.a11y.spec.ts::dashboard_charts_have_no_serious_violations`, `::chart_summary_label_names_min_max_latest`, `::series_distinguishable_without_colour`; `testing/features/F024/performance/chart_query_bench.rs::chart_query_p95_under_800ms_on_100k_rows`; `testing/features/F024/performance/burndown_bench.rs::burndown_10k_rows_90_days_under_2s`; `testing/features/F024/performance/render_bench.ts::line_1000_points_renders_under_100ms`
- Targeted command: `cargo xtask test-feature F024`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: MSW handlers for `POST /api/v1/charts/query`, `GET /api/v1/charts/{id}`, `PATCH /api/v1/charts/{id}`, `GET /api/v1/sheets/{sheet_id}/burndown`, `GET /api/v1/time-series/{metric_id}` returning recorded success, empty, denied, stale, truncated, and 500 payloads

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Every FR-F024 and NFR-F024 id appears in `testing/features/F024/requirements/cases.md` with a lane and a named case
- [ ] Frontend, e2e, accessibility, and performance lanes pass in targeted and full modes
- [ ] Evidence artifacts published under `testing/evidence/F024/`
- [ ] Owned-path check passes; no file exceeds 500 lines; lint gates pass
- [ ] Handoff evidence recorded in S048; `finished_at` recorded
