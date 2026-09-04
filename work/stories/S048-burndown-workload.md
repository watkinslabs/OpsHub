---
id: S048
type: story
status: planned
parent_epic: E005
parent_feature: F024
depends_on: [F024]
owned_paths: [crates/domain/src/charts/**, services/api/src/charts/**, apps/web/src/features/charts/**, testing/features/F024/**]
feature_flag: F024_FEATURE
branch: s048-burndown-workload
started_at: null
finished_at: null
---

# S048 — Burndown, timeline, workload and chart rendering

## Identity

- Parent feature: `F024` Charts and insights
- Owner: platform
- Branch: `s048-burndown-workload`
- Child tasks: `T095` chart components, `T096` render tests
- Decision references: `docs/architecture-decisions.md` sections 2, 4, 6, 7, 9; `docs/capability-contracts.md` row F024; `docs/product-capability-spec.md` section 5.6 REPORT-04

## Vertical slice

As a delivery lead, I want a sprint burndown reconstructed from cell history, a milestone timeline, and a per-person workload heatmap on the weekly review dashboard, each rendered with a legend, an empty and error state, and a keyboard-reachable table alternative, so that the review reads progress and load without exporting to a spreadsheet.

The slice runs end to end: `GET /api/v1/sheets/{sheet_id}/burndown` → `crates/domain/src/charts/adapters/sheet.rs` replaying F008 `cell_history` at each local midnight → daily points; the `timeline` and `workload` resolvers → `ChartData` bars and cells; `apps/web/src/features/charts/` renderers registered in the F023 renderer registry → SVG built with `d3-scale`/`d3-shape`, `ChartFrame` states, and `ChartDataTable`.

## Requirements

- **SR-S048-01:** `GET /api/v1/sheets/{sheet_id}/burndown?start&end&done_field&done_values&scope&timezone` returns daily `{ date, ideal, remaining, completed, added }` over viewer-visible rows, reconstructing each row's `done` state at each local midnight from F008 `cell_history` through the F008 repository's day-boundary window query, so no SQL lives in `crates/domain/src/charts` or `services/api/src/charts`; `scope: count` counts rows and `scope: field` sums a numeric field; rows created after `start` increment `added`; `ideal` is linear from the `start` total to zero; a span over 366 days is `400 invalid`; results are cached 60 s per `(sheet_id, params, scope_key)` and `burndown_cache_hits_total` is incremented on a hit (covers FR-F024-08, NFR-F024-01, NFR-F024-04).
- **SR-S048-02:** The `timeline` resolver returns bars `{ row_id, label, start, end, group, milestone }` for rows with a non-null `start_field`, marking `milestone: true` when `end_field` is null, sorted by `start` and limited to 500 bars with `truncated: true` beyond that; the `workload` resolver returns cells `{ person, bucket_start, value, capacity, over_capacity }` for at most 200 people and 53 buckets, using `capacity_per_bucket` when given, defaulting to 40 hours for `sum` and no capacity for `count` (covers FR-F024-09).
- **SR-S048-03:** Burndown, timeline, and workload obey the viewer scope exactly like their sheet: rows the viewer cannot read are absent from every point, a hidden numeric field makes its `sum` measure `y: null`, and a sheet in another tenant or with no read grant returns `404 not_found` before any history query is executed (covers FR-F024-12, NFR-F024-02).
- **SR-S048-04:** `apps/web/src/features/charts/` ships `BarChart`, `LineChart`, `PieChart`, `BurndownChart`, `TimelineChart`, `WorkloadHeatmap`, `KpiWidget`, and `MetricComparisonWidget`, all registered through F023 `registerWidgetRenderer` in `registerChartRenderers.ts`, drawing SVG with `d3-scale` and `d3-shape`, series colors `--chart-1`..`--chart-8` plus pattern fills from `apps/web/src/design/tokens.css` (covers FR-F024-11).
- **SR-S048-05:** `ChartFrame` renders every state: skeleton while loading, `empty_state.message` centered when every series is empty, `error_state.message` with `correlation_id` and retry on failure, the F023 denied tile and stale badge, and the note "Showing first 1,000 points" when `meta.truncated` is true; legends move below the plot under 480 px and the workload heatmap scrolls horizontally with a frozen person column (covers FR-F024-10, FR-F024-11).
- **SR-S048-06:** Every renderer carries an `aria-label` summarizing kind, series count, min, max, and latest value; `Tab` enters the chart, arrow keys move between points and announce them ("Dana, 7 risks") through a polite live region, `T` toggles `ChartDataTable` with the same numbers, `Escape` leaves; tooltips are `role="tooltip"` reachable by keyboard; `prefers-reduced-motion` disables bar growth and line draw; axe reports zero serious or critical violations (covers NFR-F024-03).
- **SR-S048-07:** `ChartSpecEditor` (with `DimensionPicker`, `MeasurePicker`, `FormattingForm`, `StateMessagesForm`) is used by the F023 widget config panel and the report viewer `Chart this report` drawer; it blocks save while a required declaration is missing, surfaces server `field_errors` against the matching control, and previews the spec through the same `chart-query` request the widget will issue (covers FR-F024-01, FR-F024-11).
- **SR-S048-08:** Telemetry `chart_rendered` (`kind`, `point_count`, `truncated`), `chart_table_toggled`, `chart_spec_saved`, `projection_viewed`, and `burndown_viewed` is emitted; TanStack Query keys are `['chart-query', specHash, from, to]` with 60 s stale time and `['burndown', sheetId, params]`; a 1,000-point line renders under 100 ms on the reference laptop (covers NFR-F024-01, NFR-F024-04).

## Surfaces

- Rust domain: `crates/domain/src/charts/{burndown.rs, timeline.rs, workload.rs}` and `crates/domain/src/charts/adapters/sheet.rs` (visible-row reads plus `cell_history` day-boundary replay, both issued through the F008 and F021 repository traits)
- Persistence: none added by this story — the chart-definition and time-series repositories in `crates/persistence/src/charts/` are owned by S047 and the burndown, timeline and workload reads go through F008 and F021 repositories
- Rust API: `services/api/src/charts/handlers_burndown.rs` and its `BurndownResponse` DTO on `GET /api/v1/sheets/{sheet_id}/burndown`
- React/UI: `apps/web/src/features/charts/{BarChart.tsx, LineChart.tsx, PieChart.tsx, BurndownChart.tsx, TimelineChart.tsx, WorkloadHeatmap.tsx, KpiWidget.tsx, MetricComparisonWidget.tsx, ChartFrame.tsx, ChartDataTable.tsx, ChartSpecEditor.tsx, DimensionPicker.tsx, MeasurePicker.tsx, FormattingForm.tsx, StateMessagesForm.tsx, registerChartRenderers.ts, api.ts, hooks.ts}`
- Design tokens: series colors `--chart-1`..`--chart-8` and pattern fills from `apps/web/src/design/tokens.css`; Lucide `BarChart3`, `LineChart`, `PieChart`, `TrendingDown`, `GanttChart`, `Users`, `Table`
- Mocks/fixtures: `testing/fixtures/charts.rs` sheet "Sprint 12" (200 rows, `Status` history across 14 days, `Points` numeric, `Assignee` person, `Start`/`End` dates), dashboard "Weekly review" with one widget per kind, MSW handlers for the five chart routes, timezone `America/New_York` with a DST boundary case

## TDD harness

- Test path: `testing/features/F024/{requirements,api,frontend,e2e,accessibility,performance}/`
- Feature flag: `F024_FEATURE`
- Targeted command: `cargo xtask test-feature F024`
- Full command: `cargo xtask test-all`
- First failing tests: `burndown_replays_cell_history_per_local_midnight`, `burndown_span_over_366_days_rejected`, `burndown_second_call_served_from_cache`, `timeline_marks_null_end_as_milestone`, `workload_over_capacity_flagged_at_forty_hours`, `restricted_sheet_burndown_not_found`, `chart_frame_renders_empty_state_message`, `chart_table_toggle_matches_series_values`, `line_chart_arrow_keys_announce_point`

## Exit criteria

- [ ] Requirement tests SR-S048-01 through SR-S048-08 written first and observed failing
- [ ] Tasks T095 and T096 complete and wired
- [ ] API, frontend, e2e, accessibility, and performance lanes pass in targeted and full modes
- [ ] Production call path named: `services/api/src/charts/handlers_burndown.rs` reachable through `services/api/src/router.rs`; `apps/web/src/features/charts/registerChartRenderers.ts` imported by the F023 dashboard bootstrap
- [ ] axe reports zero serious violations across the eight renderers; 1,000-point render measured under 100 ms
- [ ] Handoff evidence recorded in the F024 ticket with artifacts under `testing/evidence/F024/`
