---
id: T093
type: task
status: planned
parent_epic: E005
parent_feature: F024
parent_story: S047
depends_on: [S047]
owned_paths: [crates/domain/src/charts/**, crates/persistence/src/charts/**, services/api/src/charts/**, services/api/migrations/*_charts_*.sql, testing/features/F024/api/**, testing/features/F024/database/**]
feature_flag: F024_FEATURE
branch: t093-chart-query-adapters
started_at: null
finished_at: null
---

# T093 — Chart spec, query and source adapters

## Identity

- Parent story: `S047` Charts and time series
- Owner: platform
- Branch: `t093-chart-query-adapters`
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 6; `docs/capability-contracts.md` row F024

## Objective

Create the `charts` schema and implement `ChartSpec` validation, the report/metric/sheet query adapters, the `POST /api/v1/charts/query` route, the chart-definition routes bound to F023 widgets, and the eight widget resolvers, so a dashboard widget or an ad-hoc drawer can compute a chart under the caller's viewer scope.

## Specification

- Owned paths: `services/api/migrations/<ts>_charts_create_tables.sql` and `.down.sql`; `crates/domain/src/charts/{mod.rs, spec.rs, kinds.rs, data.rs, errors.rs, fold.rs, service.rs, widgets.rs, adapters/{mod.rs, report.rs, metric.rs, sheet.rs}}`; `crates/persistence/src/charts/{mod.rs, chart_definition_repository.rs, time_series_point_repository.rs}`; `services/api/src/charts/{mod.rs, routes.rs, handlers_query.rs, handlers_definition.rs, dto.rs}`.
- Contract/input: `ChartQueryRequest { spec: ChartSpec, from?: DateTime<Utc>, to?: DateTime<Utc> }` where `ChartSpec = { kind, source { kind, id }, dimensions[{ field, bucket, label }], measures[{ field?, metric_id?, aggregation, label }], timezone, formatting { number { kind, decimals, currency_code? }, date }, empty_state { message }, error_state { message }, sort?, limit?, stacked? }`; `UpdateChartRequest { spec }` with `If-Match` and `Idempotency-Key` headers.
- Output/behavior: `POST /api/v1/charts/query` returns `ChartDataResponse { series[{ label, points[{ x, y, formatted }] }], meta { computed_at, duration_ms, source_versions, stale, point_count, truncated, scope } }`; `GET /api/v1/charts/{id}` returns `ChartDefinitionResponse { id, widget_id, kind, spec, series[{ position, label, source_kind, source_id, column_id, axis }], version }`; `PATCH /api/v1/charts/{id}` bumps `version`, purges the widget's `widget_cache` rows, writes audit `chart.update`, and publishes `chart.updated.v1` with `widget_id` and `changed_fields`.
- Validation: required declarations `dimensions`, `measures`, `aggregation`, `timezone`, `formatting`, `empty_state`, `error_state`; kind limits per FR-F024-02; dimensions ≤ 2, measures ≤ 5, series ≤ 20, points ≤ 1,000 per series, `limit` ≤ 1,000, spec JSON ≤ 32 KB. Errors map `ChartError::MissingDeclaration(path) → 400 invalid` (path in `field_errors`), `ChartError::KindLimit → 400 invalid`, `ChartError::StaleVersion → 409 conflict`, `ChartError::NotFound → 404 not_found`, `AuthzError::Denied → 403 denied`.
- Adapters: `report.rs` calls F021 `read_rows` under the caller's `ViewerScope` and folds by dimension with `chrono-tz` `none|day|week|month|quarter` buckets; `metric.rs` calls F022 `read_values` and rollups; `sheet.rs` reads visible rows only. Hidden rows never contribute; a measure over a hidden field emits `y: null` on every point. `widgets.rs` implements the F023 `WidgetResolver` for `kpi`, `metric_comparison`, `bar`, `line`, `pie`, `burndown`, `timeline`, `workload`, registers them in `WidgetRegistry` behind the flag, and its `validate` hook upserts `chart_definitions` by `widget_id` and calls `replace_series` so each series lands in `chart_series` with its `position`, `label`, `source_kind`, `source_id`, `column_id`, and `axis`; `metric_comparison` computes `delta_abs`, `delta_pct`, and `direction` from the first metric's `target.direction`, and an unreadable metric yields widget status `denied`.
- DDL: `chart_definitions(id uuid pk, tenant_id, widget_id uuid unique references dashboard_widgets on delete cascade, kind text check (kind in ('bar','line','pie','burndown','timeline','workload','kpi','metric_comparison')), spec jsonb, version bigint default 1, created_by, created_at, updated_by, updated_at, deleted_at)` with index `chart_definitions(tenant_id, widget_id)`; `chart_series(id uuid pk, tenant_id uuid not null, chart_id uuid not null references chart_definitions(id) on delete cascade, position smallint not null, label text not null, source_kind text not null check (source_kind in ('metric','report','sheet')), source_id uuid not null, column_id uuid null, axis text not null check (axis in ('primary','secondary')), created_by, created_at)` with `unique (chart_id, position)` and indexes `chart_series(source_kind, source_id)` and `chart_series(tenant_id, chart_id)`; `time_series_points` created in the same migration per ticket section 4 for T094 to write. `spec` stays `jsonb` because it holds only the visual specification — axes, buckets, aggregation declarations, series styling, colours, legend, stacking, thresholds, formatting, timezone, and the empty/error messages — which the database never filters, joins or aggregates; every resolved reference (chart `source`, measure `metric_id`, referenced column) lives in `chart_series`, so the reverse lookup and the permission filter are index joins and the rendered chart is unchanged.
- Persistence: `ChartDefinitionRepository` owns `chart_definitions` and `chart_series` and adds `find_by_widget(widget_id)`, `list_charts_using_source(source_kind, source_id)`, `replace_series(chart_id, series)` on top of the shared `Repository` contract; `TimeSeriesPointRepository` owns `time_series_points` with `upsert_points`, `list_points`, `delete_superseded`, `delete_points_older_than` (T094 uses the latter three). The definition upsert plus `replace_series` runs in one `UnitOfWork`. Per decision 2.1 no SQL string, `sqlx::query*` call, or connection exists in `crates/domain/src/charts` or `services/api/src/charts`; report, metric and sheet reads go through the F021, F022 and F008 repositories.
- Authorization: source-based — `report-viewer` or report ACL for report sources, metric read for metric sources, sheet read for sheet sources, taken for a saved chart from its `chart_series` rows so the check joins `(source_kind, source_id)`; `report-editor` for `PATCH`; explicit deny wins; foreign-tenant ids map to `not_found`.
- Dependencies: F021 `ViewerScope` and `read_rows`; F022 `read_values`; F023 `WidgetRegistry` and `widget_cache`; F049 formatter for `formatted`; F028 outbox and correlation IDs.
- Feature flag: `F024_FEATURE` gates routes and resolver registration; the migration runs regardless.

## TDD

- Failing test first: `testing/features/F024/api/spec_tests.rs::spec_missing_formatting_and_error_state_rejected`, `::spec_over_32kb_rejected`, `::pie_with_two_measures_rejected`, `::bar_with_three_dimensions_rejected`, `::burndown_without_done_field_rejected`; `testing/features/F024/api/query_tests.rs::bar_query_folds_by_owner_under_viewer_scope`, `::hidden_field_measure_yields_null_points`, `::restricted_rows_absent_from_points`, `::series_capped_at_twenty_sets_truncated`, `::points_capped_at_one_thousand_per_series`, `::week_bucket_respects_dst_boundary`, `::foreign_tenant_report_query_not_found`; `testing/features/F024/api/definition_tests.rs::chart_widget_save_upserts_definition_by_widget_id`, `::patch_chart_publishes_updated_event_and_purges_cache`, `::patch_chart_stale_if_match_conflicts`, `::patch_chart_without_idempotency_key_invalid`, `::metric_comparison_computes_delta_and_direction`, `::denied_metric_widget_returns_denied_status`; `::chart_widget_save_projects_measures_into_chart_series`, `::list_charts_using_source_finds_charts_for_deleted_metric`; `testing/features/F024/database/migration_tests.rs::charts_tables_exist_with_constraints`, `::definition_unique_per_widget`, `::definition_cascades_on_widget_delete`, `::chart_series_unique_position_per_chart`, `::chart_series_rejects_unknown_source_kind_and_axis`, `::chart_series_cascades_on_definition_delete`, `::rollback_drops_charts_tables`
- Targeted command: `cargo xtask test-feature F024`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/charts.rs` — report "Portfolio status" with `Budget.margin` hidden from viewer Lee, dashboard "Weekly review", metric "Open high risks"; fixed clock `2026-09-03T00:00:00Z`; timezone `America/New_York`; seed `0x0F24`; in-memory outbox recorder

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; routes mounted in `services/api/src/router.rs`; resolvers registered in the F023 `WidgetRegistry` behind `F024_FEATURE`
- [ ] OpenAPI regenerated without drift; audit `chart.update` and `chart.query` sampling verified
- [ ] Owned-path check passes; `cargo xtask check-persistence` passes with no SQL outside `crates/persistence/src/charts/`; no file exceeds 500 lines; lint and security gates pass
- [ ] Handoff evidence recorded in S047 with artifacts under `testing/evidence/F024/`
- [ ] `finished_at` recorded
