---
id: T093
type: task
status: planned
parent_epic: E005
parent_feature: F024
parent_story: S047
depends_on: [S047]
owned_paths: [crates/domain/src/charts/**, services/api/src/charts/**, services/api/migrations/*_charts_*.sql, testing/features/F024/api/**, testing/features/F024/database/**]
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

- Owned paths: `services/api/migrations/<ts>_charts_create_tables.sql` and `.down.sql`; `crates/domain/src/charts/{mod.rs, spec.rs, kinds.rs, data.rs, errors.rs, fold.rs, service.rs, widgets.rs, adapters/{mod.rs, report.rs, metric.rs, sheet.rs}}`; `services/api/src/charts/{mod.rs, routes.rs, handlers_query.rs, handlers_definition.rs, dto.rs}`.
- Contract/input: `ChartQueryRequest { spec: ChartSpec, from?: DateTime<Utc>, to?: DateTime<Utc> }` where `ChartSpec = { kind, source { kind, id }, dimensions[{ field, bucket, label }], measures[{ field?, metric_id?, aggregation, label }], timezone, formatting { number { kind, decimals, currency_code? }, date }, empty_state { message }, error_state { message }, sort?, limit?, stacked? }`; `UpdateChartRequest { spec }` with `If-Match` and `Idempotency-Key` headers.
- Output/behavior: `POST /api/v1/charts/query` returns `ChartDataResponse { series[{ label, points[{ x, y, formatted }] }], meta { computed_at, duration_ms, source_versions, stale, point_count, truncated, scope } }`; `GET /api/v1/charts/{id}` returns `ChartDefinitionResponse { id, widget_id, kind, spec, version }`; `PATCH /api/v1/charts/{id}` bumps `version`, purges the widget's `widget_cache` rows, writes audit `chart.update`, and publishes `chart.updated.v1` with `widget_id` and `changed_fields`.
- Validation: required declarations `dimensions`, `measures`, `aggregation`, `timezone`, `formatting`, `empty_state`, `error_state`; kind limits per FR-F024-02; dimensions ≤ 2, measures ≤ 5, series ≤ 20, points ≤ 1,000 per series, `limit` ≤ 1,000, spec JSON ≤ 32 KB. Errors map `ChartError::MissingDeclaration(path) → 400 invalid` (path in `field_errors`), `ChartError::KindLimit → 400 invalid`, `ChartError::StaleVersion → 409 conflict`, `ChartError::NotFound → 404 not_found`, `AuthzError::Denied → 403 denied`.
- Adapters: `report.rs` calls F021 `read_rows` under the caller's `ViewerScope` and folds by dimension with `chrono-tz` `none|day|week|month|quarter` buckets; `metric.rs` calls F022 `read_values` and rollups; `sheet.rs` reads visible rows only. Hidden rows never contribute; a measure over a hidden field emits `y: null` on every point. `widgets.rs` implements the F023 `WidgetResolver` for `kpi`, `metric_comparison`, `bar`, `line`, `pie`, `burndown`, `timeline`, `workload`, registers them in `WidgetRegistry` behind the flag, and its `validate` hook upserts `chart_definitions` by `widget_id`; `metric_comparison` computes `delta_abs`, `delta_pct`, and `direction` from the first metric's `target.direction`, and an unreadable metric yields widget status `denied`.
- DDL: `chart_definitions(id uuid pk, tenant_id, widget_id uuid unique references dashboard_widgets on delete cascade, kind text check (kind in ('bar','line','pie','burndown','timeline','workload','kpi','metric_comparison')), spec jsonb, version bigint default 1, created_by, created_at, updated_by, updated_at, deleted_at)` with index `chart_definitions(tenant_id, widget_id)`; `time_series_points` created in the same migration per ticket section 4 for T094 to write.
- Authorization: source-based — `report-viewer` or report ACL for report sources, metric read for metric sources, sheet read for sheet sources; `report-editor` for `PATCH`; explicit deny wins; foreign-tenant ids map to `not_found`.
- Dependencies: F021 `ViewerScope` and `read_rows`; F022 `read_values`; F023 `WidgetRegistry` and `widget_cache`; F049 formatter for `formatted`; F028 outbox and correlation IDs.
- Feature flag: `F024_FEATURE` gates routes and resolver registration; the migration runs regardless.

## TDD

- Failing test first: `testing/features/F024/api/spec_tests.rs::spec_missing_formatting_and_error_state_rejected`, `::spec_over_32kb_rejected`, `::pie_with_two_measures_rejected`, `::bar_with_three_dimensions_rejected`, `::burndown_without_done_field_rejected`; `testing/features/F024/api/query_tests.rs::bar_query_folds_by_owner_under_viewer_scope`, `::hidden_field_measure_yields_null_points`, `::restricted_rows_absent_from_points`, `::series_capped_at_twenty_sets_truncated`, `::points_capped_at_one_thousand_per_series`, `::week_bucket_respects_dst_boundary`, `::foreign_tenant_report_query_not_found`; `testing/features/F024/api/definition_tests.rs::chart_widget_save_upserts_definition_by_widget_id`, `::patch_chart_publishes_updated_event_and_purges_cache`, `::patch_chart_stale_if_match_conflicts`, `::patch_chart_without_idempotency_key_invalid`, `::metric_comparison_computes_delta_and_direction`, `::denied_metric_widget_returns_denied_status`; `testing/features/F024/database/migration_tests.rs::charts_tables_exist_with_constraints`, `::definition_unique_per_widget`, `::definition_cascades_on_widget_delete`, `::rollback_drops_charts_tables`
- Targeted command: `cargo xtask test-feature F024`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/charts.rs` — report "Portfolio status" with `Budget.margin` hidden from viewer Lee, dashboard "Weekly review", metric "Open high risks"; fixed clock `2026-09-03T00:00:00Z`; timezone `America/New_York`; seed `0x0F24`; in-memory outbox recorder

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; routes mounted in `services/api/src/router.rs`; resolvers registered in the F023 `WidgetRegistry` behind `F024_FEATURE`
- [ ] OpenAPI regenerated without drift; audit `chart.update` and `chart.query` sampling verified
- [ ] Owned-path check passes; no file exceeds 500 lines; lint and security gates pass
- [ ] Handoff evidence recorded in S047 with artifacts under `testing/evidence/F024/`
- [ ] `finished_at` recorded
