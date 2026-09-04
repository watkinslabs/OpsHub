---
id: F024
type: feature
status: planned
priority: P1
owner: platform
estimate: 8
target_milestone: M4
parent_epic: E005
depends_on: [F022, F023]
blocks: []
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/charts/**, crates/persistence/src/charts/**, services/api/src/charts/**, services/worker/src/charts/**, apps/web/src/features/charts/**, services/api/migrations/*_charts_*.sql, testing/features/F024/**]
feature_flag: F024_FEATURE
flag_default: off
branch: f024-charts-and-insights
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 6, 7, 9
- Capability contract: `docs/capability-contracts.md` row F024
- Product spec: `docs/product-capability-spec.md` section 5.6 REPORT-02, REPORT-04, section 6

# F024 — Charts and insights

## 1. Identity and dates

- Branch: `f024-charts-and-insights`
- Capability area: reporting (spec 5.6 REPORT-02 charts on dashboards, REPORT-04 burndown, time series, trend analysis, work insights; low-level bullets: widget types KPI, metric comparison, bar/line/pie, burndown, timeline, workload; every chart declares dimensions, measures, aggregation, timezone, formatting, and empty/error state; hidden values excluded from aggregates)
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 6, 7; `docs/capability-contracts.md` row F024
- Aggregate: `chart`
- Module slug: `charts`

## 2. Requirement specification

### Problem and user outcome

The weekly review dashboard has a table and a note but no picture of the trend. Leaders want a bar chart of open risks by owner, a line of the "Open high risks" metric with a projection to quarter end, a sprint burndown, a timeline of milestones, and a workload heatmap per person, each computed from governed data the viewer may see and each explicit about what it aggregates and in which timezone.

As a report editor, I want to declare charts with dimensions, measures, aggregation, timezone, formatting, and empty/error states, and place KPI, comparison, chart, burndown, timeline, and workload widgets on dashboards, so that reviews read trends instead of raw tables.

### Functional requirements

- **FR-F024-01:** A `ChartSpec` is `{ kind: bar|line|pie|burndown|timeline|workload, source: { kind: report|metric|sheet, id }, dimensions: [{ field, bucket: none|day|week|month|quarter, label }], measures: [{ field?, metric_id?, aggregation: count|count_distinct|sum|avg|min|max, label }], timezone, formatting: { number: { kind, decimals, currency_code? }, date: short|medium|long }, empty_state: { message }, error_state: { message }, sort?, limit?, stacked? }`; every field listed is required except `sort`, `limit`, `stacked`, and a spec missing any of `dimensions`, `measures`, `aggregation`, `timezone`, `formatting`, `empty_state`, or `error_state` returns `400 invalid` naming the missing path.
- **FR-F024-02:** Kind limits: `bar` and `line` allow 1..2 dimensions and 1..5 measures; `pie` allows exactly 1 dimension and 1 measure; `burndown` requires `source.kind = sheet` plus `done_field`, `done_values[]`, `start`, `end`, and `scope: count|field`; `timeline` requires `start_field`, `end_field`, optional `group_field`; `workload` requires `person_field`, `bucket` (week or month), `measure` (count or sum of a numeric field), and optional `capacity_per_bucket`; violations return `400 invalid`.
- **FR-F024-03:** `POST /api/v1/charts/query` with `{ spec, from?, to? }` computes the chart for the caller's F021 `ViewerScope` and returns `ChartData { series: [{ label, points: [{ x, y, formatted }] }], meta: { computed_at, duration_ms, source_versions, stale: false, point_count, truncated, scope: viewer|owner } }`; series are capped at 20 and points at 1,000 per series with `truncated: true`; hidden rows and hidden fields never contribute to any point, and a measure over a hidden field yields `y: null` for every point.
- **FR-F024-04:** Chart widgets on dashboards (`kpi`, `metric_comparison`, `bar`, `line`, `pie`, `burndown`, `timeline`, `workload`) are resolved by resolvers this feature registers in the F023 `WidgetRegistry`; saving such a widget through `PUT /api/v1/dashboards/{id}/widgets` upserts a `chart_definitions` row keyed by `widget_id` and replaces its `chart_series` rows in the same transaction, one per series in spec order, carrying `position`, `label`, `source_kind`, `source_id`, the referenced `column_id`, and `axis`; `GET /api/v1/charts/{id}` returns the definition with `spec`, `series`, `widget_id`, `version`; `PATCH /api/v1/charts/{id}` updates `spec` and its series with `If-Match`, invalidates the widget's `widget_cache` rows, and publishes `chart.updated.v1`.
- **FR-F024-05:** The `kpi` resolver returns the F022 `values` response for the widget's `metric_id` under the viewer scope; the `metric_comparison` resolver returns both metrics' `current`, `formatted`, and a computed `delta_abs`, `delta_pct`, and `direction` using the first metric's `target.direction`; a metric the viewer cannot read yields widget status `denied`.
- **FR-F024-06:** `GET /api/v1/time-series/{metric_id}?from&to&grain?&horizon_days?&method=linear|moving_average` returns `{ actual: [{ ts, value }], projected: [{ ts, value, lower, upper }], meta: { run_id, computed_at, method, window, stale } }` from F022 `metric_values` plus `time_series_points` of kind `projected`; `horizon_days` is 1..90, the fit window is the last 12 complete buckets (fewer if unavailable, minimum 3, otherwise `projected: []`), `linear` uses least squares with a 80% interval from residual standard error, and `moving_average` uses the window mean.
- **FR-F024-07:** Projections are computed by the worker job `charts.project` enqueued when `time-series` is read with no projection for `(metric_id, scope_key, grain, method, horizon)` or when the projection is older than the metric's latest `metric.computed.v1`; the job writes `time_series_points`, records `run_id`, and publishes `time-series.projected.v1`; `meta.stale` is true while a newer metric run exists.
- **FR-F024-08:** `GET /api/v1/sheets/{sheet_id}/burndown?start&end&done_field&done_values&scope&timezone` returns daily `{ date, ideal, remaining, completed, added }` for the viewer-visible rows by reconstructing each row's `done` state at each local midnight from F008 `cell_history`; `start..end` spans at most 366 days, `scope: count` counts rows and `scope: field` sums a numeric field; rows created after `start` increment `added`; the response is cached 60 s per `(sheet_id, params, scope_key)`.
- **FR-F024-09:** `timeline` returns bars `{ row_id, label, start, end, group, milestone: bool }` for rows with a non-null `start_field` (a null `end_field` marks a milestone), limited to 500 bars sorted by `start`; `workload` returns cells `{ person, bucket_start, value, capacity, over_capacity }` for up to 200 people and 53 buckets, using `capacity_per_bucket` when given (default 40 hours for `sum`, none for `count`).
- **FR-F024-10:** `formatting` drives `formatted` on every point through the F049 formatter in the viewer locale; `timezone` (IANA) drives bucket boundaries and is echoed in `meta`; the web components render `empty_state.message` when every series is empty and `error_state.message` plus `correlation_id` when the query fails.
- **FR-F024-11:** The web app ships `BarChart`, `LineChart`, `PieChart`, `BurndownChart`, `TimelineChart`, `WorkloadHeatmap`, `KpiWidget`, and `MetricComparisonWidget` renderers registered in the F023 renderer registry, a `ChartSpecEditor` used by the widget config panel, and a `Show as table` toggle that renders the same data as an accessible table.
- **FR-F024-12:** Every chart query and widget resolve is authorized like its source: `report-viewer` or report ACL for report sources, metric read for metric sources, sheet read for sheet sources; for a saved chart the sources are read from its `chart_series` rows, so the permission filter is a join on `(source_kind, source_id)` rather than a scan of `spec`, and deleting a metric, report or sheet finds every affected chart through the same index; foreign-tenant ids return `404 not_found`; `chart.updated.v1` and `time-series.projected.v1` carry the contract envelope; chart `PATCH` requires `Idempotency-Key` and writes an audit row.

### Non-functional requirements

- **NFR-F024-01 Performance:** `POST /charts/query` over a 100,000-row report snapshot with 2 dimensions responds under 800 ms p95; burndown over 10,000 rows and 90 days responds under 2 s p95 (60 s cache after); `time-series` from cache under 300 ms p95; a projection job completes under 5 s; charts render 1,000 points under 100 ms on the reference laptop.
- **NFR-F024-02 Security/privacy:** every point is computed under the viewer scope; hidden fields yield null measures; projections are stored per `scope_key`; cross-tenant, viewer, restricted-source, and hidden-field negatives are in the harness.
- **NFR-F024-03 Accessibility:** every chart has an `aria-label` summary (kind, series count, min, max, latest), a keyboard-reachable data table alternative, colors from the token palette with 3:1 contrast plus pattern fills for series, tooltips reachable by keyboard, and reduced motion disabling transitions; axe reports zero serious violations.
- **NFR-F024-04 Reliability/observability:** projection and burndown jobs retry 3 times, dead-letter on the fourth failure, and are idempotent by `run_id`; spans carry `tenant_id`, `chart_id`, `metric_id`, `sheet_id`, `scope_key`; metrics `chart_query_duration_seconds`, `projection_failures_total`, `burndown_cache_hits_total`.

### Scope

Included: chart spec model and validation, ad-hoc chart query, chart definitions bound to widgets, KPI and metric comparison resolvers, bar/line/pie/burndown/timeline/workload resolvers, time-series projection worker, burndown reconstruction, chart and widget renderers, spec editor, table alternative.

Excluded: metric definitions (F022), dashboard layout and sharing (F023), export and drill-through (F025), portfolio health charts (F031), resource capacity planning beyond the workload heatmap (F033), natural-language chart generation (F039).

## 3. UX specification

- Entry points: dashboard builder palette items `KPI`, `Metric comparison`, `Bar`, `Line`, `Pie`, `Burndown`, `Timeline`, `Workload`; report viewer toolbar `Chart this report` opening `ChartSpecEditor` in a drawer for an ad-hoc preview; metric editor `Show trend`.
- Primary flow: in the builder add `Bar`, pick source report "Portfolio status", dimension `Projects.owner`, measure `count` of `Risks.id`, timezone `America/New_York`, number format `0 decimals`, empty message "No open risks", save; the widget renders bars per owner with a legend; add `Line` over metric "Open high risks" with a 30-day linear projection; add `Burndown` for sheet "Sprint 12" with done values `Done, Cancelled`.
- Loading: chart skeleton; Empty: `empty_state.message` centered with an icon; Error: `error_state.message`, `correlation_id`, retry; Denied: tile from F023; Stale: badge from F023; Truncated: note "Showing first 1,000 points"; Offline: cached render with an offline badge.
- Responsive: charts fill the widget frame; legends move below the plot under 480 px; the workload heatmap scrolls horizontally with a frozen person column.
- Keyboard: `Tab` into the chart, arrows move between points and announce "Dana, 7 risks", `T` toggles the table alternative, `Escape` leaves; focus ring tokens; reduced motion disables bar growth and line draw animations.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062); Lucide `BarChart3`, `LineChart`, `PieChart`, `TrendingDown`, `GanttChart`, `Users`, `Table`; series colors `--chart-1` to `--chart-8` and patterns from `apps/web/src/design/tokens.css`.

## 4. Technical specification

### Rust backend

- Domain entities in `crates/domain/src/charts/`: `ChartSpec` (per FR-F024-01), `ChartKind`, `Dimension { field: FieldRef, bucket: Bucket, label }`, `Measure { field, metric_id, aggregation: Aggregation, label }`, `Formatting`, `ChartDefinition { id, tenant_id, widget_id, spec, version, series: Vec<ChartSeries>, audit fields }`, `ChartSeries { id, tenant_id, chart_id, position, label, source_kind: Metric|Report|Sheet, source_id, column_id, axis: Primary|Secondary }`, `ChartData { series, meta }`, `TimeSeriesPoint { metric_id, scope_key, grain, method, horizon_days, ts, value, lower, upper, kind: Actual|Projected, run_id, computed_at }`, `BurndownPoint { date, ideal, remaining, completed, added }`.
- Use cases: `validate_spec`, `query_chart` (dispatch by kind), `get_chart`, `update_chart`, `read_time_series`, `project_time_series` (worker), `compute_burndown`, `query_timeline`, `query_workload`, `resolve_kpi`, `resolve_metric_comparison`.
- Adapters `crates/domain/src/charts/adapters/{report.rs, metric.rs, sheet.rs}`: `report.rs` reads F021 `read_rows` under the scope and folds by dimensions with `chrono-tz` buckets; `metric.rs` reads F022 `read_values` and rollups; `sheet.rs` reads visible rows and, for burndown, F008 `cell_history` through the F008 repository's per-day boundary query; no adapter holds SQL.
- Resolvers `crates/domain/src/charts/widgets.rs`: implement F023 `WidgetResolver` for the eight kinds and register in `WidgetRegistry` when `F024_FEATURE` is on; `validate` upserts `chart_definitions` by `widget_id`.
- Worker `services/worker/src/charts/{project_job.rs}`: consumes `charts.project`, fits `linear` (least squares) or `moving_average`, calls `TimeSeriesPointRepository::upsert_points` and `delete_superseded` in one `UnitOfWork`, publishes `time-series.projected.v1`; the job holds no SQL.
- Persistence (`crates/persistence/src/charts/`): `ChartDefinitionRepository` owns `chart_definitions` and `chart_series`; `TimeSeriesPointRepository` owns `time_series_points`. Each implements the shared `Repository` contract (`get`, `list` with cursor pagination, `insert`, `update` under an expected version, `soft_delete`, `restore`, `purge`) and adds named queries `find_by_widget(widget_id)`, `list_charts_using_source(source_kind, source_id)`, `replace_series(chart_id, series)` on the definition repository and `upsert_points(metric_id, scope_key, grain, method, horizon_days, points)`, `list_points(metric_id, scope_key, grain, from, to)`, `delete_superseded(metric_id, run_id)`, `delete_points_older_than(cutoff)` on the point repository; the tenant predicate, soft-delete filter, version check, audit row, and outbox enqueue come from the base contract. A definition upsert with its `replace_series` call, and a projection run's `upsert_points` with its supersede of the previous `run_id`, each run in one `UnitOfWork` that owns the transaction. Chart queries read F021 snapshots, F022 metric values, and F008 `cell_history` through those features' repositories: this feature issues no SQL against another feature's tables and holds none of its own outside `crates/persistence`. Per decision 2.1 the use cases above depend on these repository traits and contain no SQL: no SQL string, `sqlx::query*` call, or connection exists in `crates/domain/src/charts` or `services/api/src/charts`.
- API endpoints (`services/api/src/charts/`): `POST /api/v1/charts/query`, `GET /api/v1/charts/{id}`, `PATCH /api/v1/charts/{id}`, `GET /api/v1/sheets/{sheet_id}/burndown`, `GET /api/v1/time-series/{metric_id}`; DTOs `ChartQueryRequest { spec, from, to }`, `ChartDataResponse`, `ChartDefinitionResponse`, `UpdateChartRequest { spec }`, `BurndownResponse`, `TimeSeriesResponse`.
- Events: `chart.updated.v1` (with `widget_id`, `changed_fields`), `time-series.projected.v1` (with `metric_id`, `scope_key`, `grain`, `method`, `horizon_days`, `run_id`, `point_count`).
- Authorization: source-based per FR-F024-12; `report-editor` for `PATCH /charts/{id}`; `report-viewer` for queries; explicit deny wins; missing access maps to `not_found`.
- Validation limits: dimensions ≤ 2, measures ≤ 5, series ≤ 20, points ≤ 1,000 per series, `limit` ≤ 1,000, burndown span ≤ 366 days, timeline ≤ 500 bars, workload ≤ 200 people × 53 buckets, `horizon_days` ≤ 90, spec JSON ≤ 32 KB.
- Error mapping: `ChartError::MissingDeclaration(path) → 400 invalid`, `ChartError::KindLimit → 400 invalid`, `ChartError::StaleVersion → 409 conflict`, `ChartError::NotFound → 404 not_found`, `AuthzError::Denied → 403 denied`, `ProjectionError::InsufficientPoints` → `projected: []`, queue unavailable → `503 unavailable`.

### PostgreSQL/SQLx

- Migration `*_charts_*.sql` creates `chart_definitions(id uuid pk, tenant_id, widget_id uuid unique, kind text, spec jsonb, version bigint default 1, created_by, created_at, updated_by, updated_at, deleted_at)`, `chart_series(id uuid pk, tenant_id uuid not null, chart_id uuid not null references chart_definitions(id) on delete cascade, position smallint not null, label text not null, source_kind text not null check (source_kind in ('metric','report','sheet')), source_id uuid not null, column_id uuid null, axis text not null check (axis in ('primary','secondary')), created_by, created_at)`, and `time_series_points(tenant_id, metric_id, scope_key text, grain text, method text, horizon_days smallint, ts timestamptz, kind text, value numeric null, lower numeric null, upper numeric null, run_id uuid, computed_at, primary key (metric_id, scope_key, grain, method, horizon_days, kind, ts))`.
- `chart_definitions.spec` stays `jsonb`: it carries only the visual specification — axes, bucket and aggregation declarations, series styling, colours, display labels, legend, stacking, thresholds, `formatting`, `timezone`, and the `empty_state`/`error_state` messages — a widget-settings payload of arbitrary, per-kind shape that the database never filters, joins or aggregates. Every reference the product resolves, permission-checks, cascades on, or uses to decide staleness — the chart `source`, each measure's `metric_id`, and the referenced column — is projected out of the payload into `chart_series`.
- `chart_series` preserves two behaviours the JSON payload used to hide: "which charts break when this metric, report or sheet is deleted" (FR-F024-04 invalidation and FR-F024-07 staleness) becomes a join on `chart_series(source_kind, source_id)` instead of a JSON scan, and the per-series source authorization of FR-F024-12 filters on real foreign keys; the rendered chart is unchanged because all styling stays in `spec`.
- `time_series_points` is a derived, rebuildable cache and never the source of truth: F022 `metric_values` is authoritative for `actual` and the fit is reproducible from it. It serves `GET /api/v1/time-series/{metric_id}` and the projected series of `line` charts, and is rebuilt by the `charts.project` worker job of FR-F024-07; dropping and replaying it changes no answer.
- Invariants: `check (kind in ('bar','line','pie','burndown','timeline','workload','kpi','metric_comparison'))` on definitions; `unique (chart_id, position)` plus the `source_kind` and `axis` checks on `chart_series`; `check (kind in ('actual','projected'))` and `check (method in ('linear','moving_average'))` on points; `chart_definitions.widget_id` foreign key to `dashboard_widgets` `on delete cascade`; `chart_series.chart_id` foreign key to `chart_definitions` `on delete cascade`; `time_series_points.metric_id` foreign key to `metrics` `on delete cascade`.
- Indexes: `time_series_points(metric_id, scope_key, computed_at desc)`, `chart_definitions(tenant_id, widget_id)`, `chart_series(source_kind, source_id)` for the reverse-dependency lookup and `chart_series(tenant_id, chart_id)` for series load; burndown reads use the F008 `cell_history(row_id, column_id, changed_at)` index.
- Audit events: `chart.update`, `chart.query` (sampled 1 in 100 with spec hash), `time-series.project`, `burndown.compute`.
- Retention/deletion: projected points older than 90 days or superseded by a newer `run_id` deleted by the retention sweep and the projection job; definitions soft-delete with their widget and their `chart_series` rows cascade with the definition; rollback drops `chart_definitions`, `chart_series`, and `time_series_points`.

### React/TypeScript

- Components in `apps/web/src/features/charts/`: `BarChart`, `LineChart`, `PieChart`, `BurndownChart`, `TimelineChart`, `WorkloadHeatmap`, `KpiWidget` (wraps F022 `KpiCard`), `MetricComparisonWidget`, `ChartFrame` (states, legend, table toggle), `ChartDataTable`, `ChartSpecEditor`, `DimensionPicker`, `MeasurePicker`, `FormattingForm`, `StateMessagesForm`, `registerChartRenderers.ts` calling F023 `registerWidgetRenderer` for the eight kinds.
- Rendering: SVG built with `d3-scale` and `d3-shape` (no canvas), series colors and pattern fills from tokens, tooltips as `role="tooltip"` anchored to focused points.
- State: TanStack Query keys `['chart-query', specHash, from, to]` (staleTime 60 s), `['chart', id]`, `['time-series', metricId, grain, method, horizon]` (refetch every 3 s while `projected` is empty and `meta.stale`), `['burndown', sheetId, params]`.
- API client: generated `ChartsApi` with `queryChart`, `getChart`, `updateChart`, `getBurndown`, `getTimeSeries`.
- Telemetry: `chart_rendered` (with `kind`, `point_count`, `truncated`), `chart_table_toggled`, `chart_spec_saved`, `projection_viewed`, `burndown_viewed`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F024-01 through FR-F024-12 in `testing/features/F024/requirements/cases.md`
- [ ] Failure/edge-case tests: missing declaration, pie with two measures, burndown span 367 days, projection with 2 points, workload over 200 people, truncation at 1,000 points, DST bucket boundaries
- [ ] Permission-negative and tenant-isolation tests: cross-tenant `not_found`, hidden field null measure, restricted sheet rows excluded, metric denied for widget, projections per scope
- [ ] Rust unit tests: `crates/domain/src/charts/` spec validator, bucket folding, spec-to-`ChartSeries` projection, least squares fit, burndown reconstruction, workload capacity
- [ ] API contract/integration tests: every route above with success and each error code
- [ ] Database migration/constraint tests: definition uniqueness per widget, `unique (chart_id, position)` on `chart_series`, `source_kind`/`axis` check rejection, series cascade on definition delete, `list_charts_using_source` returning the charts that reference a deleted metric, point primary key, cascades, rollback dropping all three tables
- [ ] React component tests: each renderer with data, empty, error, truncated; spec editor validation; table toggle
- [ ] Browser E2E tests: add bar, line with projection, burndown, and workload widgets; verify renders and keyboard navigation
- [ ] Accessibility tests: axe on every renderer, summaries, table alternative, pattern fills
- [ ] Performance/load tests: chart query p95 under 800 ms on 100,000 rows, burndown under 2 s, 1,000-point render under 100 ms

### Fast fanout configuration

- Test harness path: `testing/features/F024/`
- Feature flag: `F024_FEATURE`
- Fixture/seed factory: `testing/fixtures/charts.rs` reuses the F021, F022, and F023 fixtures and adds sheet "Sprint 12" (200 rows, `Status` column with history over 14 days, `Points` numeric, `Assignee` person, `Start`/`End` dates), metric "Open high risks" with 52 weekly values, and dashboard "Weekly review" with one widget per chart kind
- Deterministic test data: fixed clock `2026-09-03T00:00:00Z`, timezone `America/New_York` with DST cases, seed `0x0F24`
- Mock/stub contracts: in-memory outbox recorder; JetStream stub for `charts.project`; real F021 scope and F022 values; F049 formatter fixtures
- Parallel isolation: one schema per test worker, tenant ID per test
- Targeted command: `cargo xtask test-feature F024`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F024/`

## 6. Acceptance criteria

```gherkin
Feature: Charts and insights

Scenario: Bar chart by owner excludes hidden values
  Given report "Portfolio status" with Budget.margin hidden from viewer Lee
  When Lee queries a bar chart with dimension Projects.owner and measures count(Risks.id) and sum(Budget.margin)
  Then the count series has one point per owner and every sum(Budget.margin) point has y null

Scenario: Line with projection
  Given metric "Open high risks" has 52 weekly values
  When Dana reads time-series with grain week, horizon 30 days, method linear
  Then projected contains 5 weekly points with lower and upper bounds and time-series.projected.v1 is in the outbox

Scenario: Sprint burndown from history
  Given sheet "Sprint 12" where 40 rows moved to Done between 2026-08-20 and 2026-09-02
  When Dana requests burndown from 2026-08-20 to 2026-09-03 in America/New_York with done values Done and Cancelled
  Then 15 daily points are returned, remaining decreases by the rows done each local day, and ideal is linear from 200 to 0

Scenario: Chart over a sheet the viewer cannot read
  Given viewer Lee has no access to sheet "Sprint 12"
  When Lee requests its burndown or a timeline over it
  Then the response is 404 not_found and no query is executed

Scenario: Charts referencing a deleted metric are found by series
  Given widget "Open high risks trend" is saved with a line series over metric "Open high risks"
  When the metric is deleted
  Then list_charts_using_source metric with that id returns the chart definition and its widget_cache rows are invalidated

Scenario: Spec without formatting rejected
  When Dana posts a chart query whose spec omits formatting and error_state
  Then the response is 400 invalid naming spec.formatting and spec.error_state
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F022 (metric values, rollups, `KpiCard`), F023 (widget registry, widget cache, renderer registry, dashboards); decisions sections 2, 3, 4, 6, 7; contracts row F024
- Blocks: none
- Conflicts with: none (disjoint owned paths)
- External dependencies: NATS JetStream for `charts.project`; `d3-scale` and `d3-shape` in the web app
- Risks and mitigations: burndown reconstruction over `cell_history` is expensive, so the query uses one window-function pass per day boundary, caps the span at 366 days, and caches 60 s; least squares on short or flat series produces misleading bands, so fewer than 3 points yields no projection and bands are clamped at zero for count metrics; two-dimension bar charts can explode series, so series are capped at 20 with `truncated: true`.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F022 and F023 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F024/`
- [ ] Migration file name and owned paths claimed
- [ ] Fixture factory `testing/fixtures/charts.rs` with the "Sprint 12" history available

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for chart updates and projections
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F024_FEATURE` (widgets fall back to the F023 unavailable state), stop the projection consumer, run down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Dashboards gain KPI, metric comparison, bar, line, pie, burndown, timeline, and workload widgets; every chart declares its dimensions, measures, aggregation, timezone, formatting, and empty/error states, and offers a table alternative.
- Metric trends can be projected up to 90 days ahead; sprint burndowns are reconstructed from cell history for the rows a viewer may see.
- Migration adds `chart_definitions`, `chart_series`, and `time_series_points`; rollback drops them. Feature is off by default behind `F024_FEATURE`.
