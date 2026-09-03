---
id: T095
type: task
status: planned
parent_epic: E005
parent_feature: F024
parent_story: S048
depends_on: [S048]
owned_paths: [apps/web/src/features/charts/**, crates/domain/src/charts/**, services/api/src/charts/**, testing/features/F024/api/**]
feature_flag: F024_FEATURE
branch: t095-chart-components
started_at: null
finished_at: null
---

# T095 — Burndown, timeline, workload and chart components

## Identity

- Parent story: `S048` Burndown, timeline, workload and chart rendering
- Owner: platform
- Branch: `t095-chart-components`
- Decision references: `docs/architecture-decisions.md` sections 2, 4, 6, 9; `docs/capability-contracts.md` row F024

## Objective

Implement burndown reconstruction from F008 `cell_history`, the timeline and workload resolvers, the `GET /api/v1/sheets/{sheet_id}/burndown` route, and the eight web chart renderers plus `ChartFrame`, `ChartDataTable`, and `ChartSpecEditor` registered in the F023 renderer registry.

## Specification

- Owned paths: `crates/domain/src/charts/{burndown.rs, timeline.rs, workload.rs}`; `crates/domain/src/charts/adapters/sheet.rs` history replay; `services/api/src/charts/handlers_burndown.rs` and its `BurndownResponse` DTO; `apps/web/src/features/charts/{BarChart.tsx, LineChart.tsx, PieChart.tsx, BurndownChart.tsx, TimelineChart.tsx, WorkloadHeatmap.tsx, KpiWidget.tsx, MetricComparisonWidget.tsx, ChartFrame.tsx, ChartDataTable.tsx, ChartSpecEditor.tsx, DimensionPicker.tsx, MeasurePicker.tsx, FormattingForm.tsx, StateMessagesForm.tsx, registerChartRenderers.ts, api.ts, hooks.ts}`.
- Contract/input: `GET /api/v1/sheets/{sheet_id}/burndown?start&end&done_field&done_values&scope&timezone` where `scope` is `count` or `field:<column>` and `timezone` is IANA; `timeline` needs `start_field`, `end_field`, optional `group_field`; `workload` needs `person_field`, `bucket` (`week|month`), a `count` or `sum` measure, and optional `capacity_per_bucket`.
- Output/behavior: burndown returns daily `{ date, ideal, remaining, completed, added }`; each row's `done` state is reconstructed at each local midnight with one window-function pass per day boundary over `cell_history(row_id, column_id, changed_at)`; `ideal` is linear from the `start` total to zero; rows created after `start` increment `added`; a span over 366 days is `400 invalid`; the result is cached 60 s per `(sheet_id, params, scope_key)` and hits increment `burndown_cache_hits_total`; audit `burndown.compute` is written. `timeline` returns `{ row_id, label, start, end, group, milestone }` sorted by `start`, capped at 500 bars with `truncated: true`; a null `end_field` sets `milestone: true`. `workload` returns `{ person, bucket_start, value, capacity, over_capacity }` for at most 200 people and 53 buckets, `capacity_per_bucket` defaulting to 40 hours for `sum` and none for `count`.
- Scope and errors: only viewer-visible rows contribute; a hidden numeric field makes its `sum` measure `y: null`; a sheet in another tenant or without a read grant returns `404 not_found` before any history query runs.
- React rendering: SVG via `d3-scale` and `d3-shape` (no canvas); series colors `--chart-1`..`--chart-8` and pattern fills from `apps/web/src/design/tokens.css`; `ChartFrame` renders skeleton, `empty_state.message`, `error_state.message` with `correlation_id` and retry, the F023 denied tile and stale badge, and "Showing first 1,000 points" when `meta.truncated`; legends move below the plot under 480 px; the workload heatmap scrolls horizontally with a frozen person column; `registerChartRenderers.ts` calls F023 `registerWidgetRenderer` for all eight kinds.
- Accessibility: each renderer sets an `aria-label` naming kind, series count, min, max, and latest; `Tab` enters, arrows move between points and announce them through a polite live region, `T` toggles `ChartDataTable`, `Escape` leaves; tooltips are `role="tooltip"`; `prefers-reduced-motion` disables bar growth and line draw.
- Editor: `ChartSpecEditor` blocks save while a required declaration is missing, maps server `field_errors` (`spec.formatting`, `spec.error_state`) to the matching control, and previews through the same `POST /api/v1/charts/query` the widget will issue.
- State and telemetry: TanStack Query keys `['chart-query', specHash, from, to]` (60 s stale), `['chart', id]`, `['burndown', sheetId, params]`, `['time-series', metricId, grain, method, horizon]`; events `chart_rendered`, `chart_table_toggled`, `chart_spec_saved`, `projection_viewed`, `burndown_viewed`.
- Dependencies: T093 spec model and query route; T094 time-series route; F008 `cell_history`; F022 `KpiCard` wrapped by `KpiWidget`; F023 renderer registry and widget config panel; F049 formatter.
- Feature flag: `F024_FEATURE` gates the burndown route and renderer registration; with the flag off the widgets fall back to the F023 unavailable state.

## TDD

- Failing test first: `testing/features/F024/api/burndown_tests.rs::burndown_replays_cell_history_per_local_midnight`, `::burndown_ideal_is_linear_from_start_total`, `::burndown_counts_rows_added_after_start`, `::burndown_scope_field_sums_numeric_column`, `::burndown_span_over_366_days_rejected`, `::burndown_second_call_served_from_cache`, `::burndown_dst_day_has_one_bucket`, `::restricted_sheet_burndown_not_found`; `testing/features/F024/api/timeline_workload_tests.rs::timeline_marks_null_end_as_milestone`, `::timeline_truncates_at_500_bars`, `::workload_over_capacity_flagged_at_forty_hours`, `::workload_caps_at_200_people`, `::hidden_numeric_field_yields_null_workload_value`
- Targeted command: `cargo xtask test-feature F024`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/charts.rs` sheet "Sprint 12" (200 rows, `Status` history across 14 days, `Points` numeric, `Assignee` person, `Start`/`End` dates) plus a 10,000-row variant, dashboard "Weekly review" with one widget per kind, MSW handlers for the five chart routes, timezone `America/New_York` including a DST boundary, fixed clock `2026-09-03T00:00:00Z`, seed `0x0F24`

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Burndown route mounted in `services/api/src/router.rs`; `registerChartRenderers.ts` imported by the F023 dashboard bootstrap behind `F024_FEATURE`
- [ ] OpenAPI regenerated without drift; generated `ChartsApi` client used by `api.ts`
- [ ] Owned-path check passes; no file exceeds 500 lines; lint and security gates pass
- [ ] Handoff evidence recorded in S048 with artifacts under `testing/evidence/F024/`
- [ ] `finished_at` recorded
