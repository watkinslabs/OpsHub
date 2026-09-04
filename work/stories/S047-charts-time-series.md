---
id: S047
type: story
status: planned
parent_epic: E005
parent_feature: F024
depends_on: [F024]
owned_paths: [crates/domain/src/charts/**, crates/persistence/src/charts/**, services/api/src/charts/**, services/worker/src/charts/**, services/api/migrations/*_charts_*.sql, testing/features/F024/**]
feature_flag: F024_FEATURE
branch: s047-charts-time-series
started_at: null
finished_at: null
---

# S047 — Charts and time series

## Identity

- Parent feature: `F024` Charts and insights
- Owner: platform
- Branch: `s047-charts-time-series`
- Child tasks: `T093` chart query adapters, `T094` time-series projections
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 6, 7; `docs/capability-contracts.md` row F024; `docs/product-capability-spec.md` section 5.6 REPORT-02, REPORT-04

## Vertical slice

As a report editor, I want to declare a chart spec with explicit dimensions, measures, aggregation, timezone, formatting, and empty/error states, query it as bar, line, or pie over a report, metric, or sheet under my own viewer scope, bind it to a dashboard widget, and read a metric time series with a linear or moving-average projection, so that a dashboard shows a governed trend instead of a raw table.

The slice runs end to end: `POST /api/v1/charts/query` → `crates/domain/src/charts/` validator and adapters → F021 scoped row reads and F022 metric values → `ChartData` with `formatted` points; `PUT /api/v1/dashboards/{id}/widgets` on a chart widget → `ChartDefinitionRepository` upsert of `chart_definitions` plus `chart_series` → `chart.updated.v1`; `GET /api/v1/time-series/{metric_id}` → `charts.project` job → `time_series_points` → `time-series.projected.v1`.

## Requirements

- **SR-S047-01:** `ChartSpec` is parsed and validated in `crates/domain/src/charts/spec.rs`: `kind`, `source`, `dimensions`, `measures`, `timezone`, `formatting`, `empty_state`, and `error_state` are required; a missing one returns `400 invalid` whose `field_errors` key is the JSON path (`spec.formatting`, `spec.error_state`); spec JSON over 32 KB is rejected (covers FR-F024-01).
- **SR-S047-02:** Kind limits are enforced before any query runs: `bar`/`line` 1..2 dimensions and 1..5 measures, `pie` exactly 1 dimension and 1 measure, `burndown` requires `source.kind = sheet` plus `done_field`, `done_values[]`, `start`, `end`, `scope`; `timeline` requires `start_field` and `end_field`; `workload` requires `person_field`, a `week`/`month` bucket, and a `count`/`sum` measure; each violation is `400 invalid` with `ChartError::KindLimit` (covers FR-F024-02).
- **SR-S047-03:** `POST /api/v1/charts/query` with `{ spec, from?, to? }` returns `ChartData { series[{ label, points[{ x, y, formatted }] }], meta { computed_at, duration_ms, source_versions, stale, point_count, truncated, scope } }` computed under the caller's F021 `ViewerScope`; series cap 20 and points cap 1,000 per series set `truncated: true`; hidden rows never contribute and a measure over a hidden field yields `y: null` on every point (covers FR-F024-03, NFR-F024-02).
- **SR-S047-04:** The eight chart widget kinds (`kpi`, `metric_comparison`, `bar`, `line`, `pie`, `burndown`, `timeline`, `workload`) are registered as F023 `WidgetResolver`s in `crates/domain/src/charts/widgets.rs` when `F024_FEATURE` is on; saving one through `PUT /api/v1/dashboards/{id}/widgets` upserts `chart_definitions` by `widget_id` through `ChartDefinitionRepository::find_by_widget` and `replace_series`, projecting the chart source and each measure's `metric_id` and referenced column into `chart_series` rows (`position`, `label`, `source_kind`, `source_id`, `column_id`, `axis`) in one `UnitOfWork` while `spec` keeps only the visual specification; `GET /api/v1/charts/{id}` returns `{ spec, series, widget_id, version }` and `PATCH /api/v1/charts/{id}` requires `If-Match` and `Idempotency-Key`, invalidates the widget's `widget_cache` rows, writes audit `chart.update`, and publishes `chart.updated.v1` with `widget_id` and `changed_fields`; a stale `If-Match` is `409 conflict` (covers FR-F024-04, FR-F024-12).
- **SR-S047-05:** The `kpi` resolver returns the F022 `values` payload for the widget's `metric_id` under the viewer scope; `metric_comparison` returns both metrics' `current` and `formatted` plus computed `delta_abs`, `delta_pct`, and `direction` derived from the first metric's `target.direction`; a metric the viewer cannot read yields widget status `denied` rather than an error page (covers FR-F024-05).
- **SR-S047-06:** `GET /api/v1/time-series/{metric_id}?from&to&grain&horizon_days&method` returns `{ actual[{ ts, value }], projected[{ ts, value, lower, upper }], meta { run_id, computed_at, method, window, stale } }`; `horizon_days` outside 1..90 is `400 invalid`; the fit window is the last 12 complete buckets, minimum 3, and fewer than 3 yields `projected: []` (covers FR-F024-06).
- **SR-S047-07:** The worker job `charts.project` is enqueued when no projection exists for `(metric_id, scope_key, grain, method, horizon)` or the stored projection predates the metric's latest `metric.computed.v1`; it fits least squares with an 80% band from residual standard error, or a window mean for `moving_average`, writes `time_series_points` of kind `projected` through `TimeSeriesPointRepository::upsert_points` with `delete_superseded` in one `UnitOfWork` keyed by `run_id`, publishes `time-series.projected.v1`, retries 3 times, and dead-letters on the fourth failure; `meta.stale` stays true while a newer metric run exists (covers FR-F024-07, NFR-F024-04).
- **SR-S047-08:** Authorization is source-based: report sources need `report-viewer` or a report ACL grant, metric sources need metric read, sheet sources need sheet read, resolved for a saved chart from its `chart_series` rows so the filter joins `(source_kind, source_id)` instead of scanning `spec`; `report-editor` is required for `PATCH /api/v1/charts/{id}`; explicit deny wins; foreign-tenant `chart_id` or `metric_id` returns `404 not_found` before any query executes; projections are stored and read per `scope_key` (covers FR-F024-12, NFR-F024-02).
- **SR-S047-09:** `formatting` drives `formatted` on every point through the F049 formatter in the viewer locale, `timezone` (IANA) drives bucket boundaries through `chrono-tz` including DST transition days, and both are echoed in `meta`; `chart_query_duration_seconds`, `projection_failures_total`, and spans carrying `tenant_id`, `chart_id`, `metric_id`, `scope_key` are emitted on every query and job run (covers FR-F024-10, NFR-F024-01, NFR-F024-04).

## Surfaces

- Rust domain: `crates/domain/src/charts/{mod.rs, spec.rs, kinds.rs, data.rs, errors.rs, service.rs, fold.rs, projection.rs, widgets.rs, adapters/{mod.rs, report.rs, metric.rs, sheet.rs}}`
- Rust API: `services/api/src/charts/{mod.rs, routes.rs, handlers_query.rs, handlers_definition.rs, handlers_time_series.rs, dto.rs}` mounted at `/api/v1/charts` and `/api/v1/time-series`
- Worker: `services/worker/src/charts/{mod.rs, project_job.rs}` consuming subject `charts.project` and calling `upsert_points`/`delete_superseded`; the job file holds no SQL
- Persistence: `crates/persistence/src/charts/{mod.rs, chart_definition_repository.rs, time_series_point_repository.rs}` — `ChartDefinitionRepository` owns `chart_definitions` and `chart_series` with `find_by_widget`, `list_charts_using_source`, `replace_series`; `TimeSeriesPointRepository` owns `time_series_points` with `upsert_points`, `list_points`, `delete_superseded`, `delete_points_older_than`; all SQL for this feature lives here and F021/F022/F008 tables are reached through their own repositories
- Data/migration: `services/api/migrations/<ts>_charts_create_tables.sql` and `.down.sql` creating `chart_definitions`, `chart_series`, and `time_series_points` with the checks, foreign keys, and indexes in ticket section 4
- Events/audit: `chart.updated.v1`, `time-series.projected.v1` through the F028 outbox; audit `chart.update`, `chart.query` (sampled 1 in 100 with spec hash), `time-series.project`
- Mocks/fixtures: `testing/fixtures/charts.rs` with metric "Open high risks" (52 weekly values), report "Portfolio status" (100,000 rows, `Budget.margin` hidden from viewer Lee), JetStream stub for `charts.project`, F049 formatter fixtures, fixed clock `2026-09-03T00:00:00Z`, seed `0x0F24`

## TDD harness

- Test path: `testing/features/F024/{requirements,api,database,performance}/`
- Feature flag: `F024_FEATURE`
- Targeted command: `cargo xtask test-feature F024`
- Full command: `cargo xtask test-all`
- First failing tests: `spec_missing_formatting_and_error_state_rejected`, `pie_with_two_measures_rejected`, `bar_query_folds_by_owner_under_viewer_scope`, `hidden_field_measure_yields_null_points`, `series_capped_at_twenty_sets_truncated`, `chart_widget_save_upserts_definition_by_widget_id`, `chart_widget_save_projects_measures_into_chart_series`, `list_charts_using_source_finds_charts_for_deleted_metric`, `patch_chart_stale_if_match_conflicts`, `time_series_linear_projection_has_bounds`, `projection_with_two_points_returns_empty`, `foreign_tenant_metric_time_series_not_found`

## Exit criteria

- [ ] Requirement tests SR-S047-01 through SR-S047-09 written first and observed failing
- [ ] Tasks T093 and T094 complete and wired
- [ ] Unit, API, database, permission-negative, and performance lanes pass in targeted and full modes
- [ ] Production call path named: `services/api/src/charts/routes.rs` mounted in `services/api/src/router.rs`; `services/worker/src/charts/project_job.rs` registered in `services/worker/src/registry.rs`; resolvers registered through F023 `WidgetRegistry`
- [ ] Migration applies and reverts on CI PostgreSQL 18; OpenAPI regenerated without drift
- [ ] Handoff evidence recorded in the F024 ticket with artifacts under `testing/evidence/F024/`
