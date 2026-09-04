---
id: S043
type: story
status: planned
parent_epic: E005
parent_feature: F022
depends_on: [F021]
owned_paths: [crates/domain/src/metrics/**, crates/persistence/src/metrics/**, services/api/src/metrics/**, services/worker/src/metrics/**, services/api/migrations/*_metrics_*.sql, testing/features/F022/**]
feature_flag: F022_FEATURE
branch: s043-kpis
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 7
- Capability contract: `docs/capability-contracts.md` row F022

# S043 — KPIs

## Identity

- Parent feature: `F022` Metrics and summaries
- Owner: platform
- Branch: `s043-kpis`
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 7; `docs/capability-contracts.md` row F022

## Vertical slice

As a report editor, I want to define a metric over a report or sheet with an aggregation, filters, period, format, target, and comparison, and have a worker compute its current value per viewer scope, so that a KPI number exists that leaders can trust and that never reveals hidden data.

## Requirements

- **SR-S043-01:** `POST /api/v1/metrics` validates measure/column type compatibility, filter limits, period, format, target, comparison, and `scope_policy` against tenant policy and returns `MetricResponse` with `version` 1; the nested body is unchanged and `MetricRepository` writes it as typed columns (`measure_fn`, `measure_column_id`, `period_grain`, `period_timezone`, `week_start`, `format_kind`, `format_decimals`, `format_currency_code`, `target_value`, `target_direction`) plus `metric_filters` rows (FR-F022-01, FR-F022-05).
- **SR-S043-02:** `source.kind = report` reads the latest succeeded F021 snapshot through F021's snapshot repository with the viewer scope and `source.kind = sheet` reads live rows through the F006/F007 repositories; this feature runs no SQL against those tables and unreadable sources return `404 not_found` (FR-F022-03).
- **SR-S043-03:** `POST /api/v1/metrics/{id}/recompute` returns `202 { run_id, status }` under 2 seconds and `409 conflict` from `MetricRunRepository::find_active_run` while a run for the same `scope_key` is active (FR-F022-04).
- **SR-S043-04:** The recompute job folds rows into period buckets for the trailing window per grain, computes `percent_of` with a null result on zero denominator, calls `claim_recompute`, `upsert_values`, and the run recorder — a `metric_runs` row with `duration_ms` and `rows_scanned` plus one `metric_run_sources` row per source version — in one `UnitOfWork`, and publishes `metric.computed.v1` with `source_versions` assembled from those rows; it holds no SQL and is idempotent by `run_id` and dead-letters after the fourth failure (FR-F022-02, FR-F022-04, FR-F022-12).
- **SR-S043-05:** `GET /api/v1/metrics/{id}/values` returns `current`, `comparison`, `series`, and `meta` for the viewer's `scope_key`; a missing scope returns `current: null`, `meta.status = "computing"`, and enqueues a run (FR-F022-06, FR-F022-09).
- **SR-S043-06:** `GET /api/v1/metrics`, `PATCH`, and `DELETE` behave per FR-F022-11 and FR-F022-12, including `delete_values_for_metric` invalidation on a measure, filter, period, or source change inside the `PATCH` `UnitOfWork`, and foreign-tenant `404`.
- **SR-S043-07:** A viewer without access to `Budget.margin` receives `null` for a `sum(Budget.margin)` metric while the editor receives the numeric total (FR-F022-05, NFR-F022-02).

## Surfaces

- Infrastructure/container: JetStream subject `metrics.recompute` declared in `services/worker/src/metrics/mod.rs`
- Rust service/API: `crates/domain/src/metrics/{mod.rs, metric.rs, validate.rs, aggregate.rs, compare.rs, format.rs, errors.rs, service.rs}` (no SQL); `crates/persistence/src/metrics/{mod.rs, metric_repository.rs, metric_value_repository.rs, metric_run_repository.rs}` holding every SQL statement for `metrics`, `metric_filters`, `metric_values`, `metric_runs`, `metric_run_sources`; `services/api/src/metrics/{mod.rs, routes.rs, handlers_metric.rs, handlers_values.rs, dto.rs}`; `services/worker/src/metrics/{mod.rs, recompute_job.rs}`
- Data/migration: `services/api/migrations/<ts>_metrics_create_tables.sql` creating `metrics`, `metric_filters`, `metric_values`, `metric_runs`, `metric_run_sources` with the checks and indexes from ticket section 4
- React/UI: none in this story (S044 covers the KPI card and editor)
- Mocks/fixtures: `testing/fixtures/metrics.rs` on top of the F021 three-sheet fixture; in-memory outbox recorder; JetStream stub; F049 formatter fixtures

## TDD harness

- Test path: `testing/features/F022/api/` and `testing/features/F022/database/`
- Feature flag: `F022_FEATURE`
- Targeted command: `cargo xtask test-feature F022`
- Full command: `cargo xtask test-all`
- First failing tests: `metric_create_returns_version_one`, `metric_sum_on_text_column_invalid`, `metric_recompute_writes_values_and_run`, `metric_values_hidden_column_null_for_viewer`, `metric_values_missing_scope_enqueues_run`, `metric_cross_tenant_not_found`

## Exit criteria

- [ ] Requirement tests SR-S043-01 through SR-S043-07 written first and failing
- [ ] Tasks T085 and T086 complete and wired through `services/api` router and the worker consumer registry
- [ ] Unit, API, database, permission, and worker tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/metrics/routes.rs` mounted in `services/api/src/router.rs`; `services/worker/src/metrics/recompute_job.rs` registered in `services/worker/src/consumers.rs`
- [ ] Handoff evidence recorded in the F022 ticket
