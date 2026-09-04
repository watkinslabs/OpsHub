---
id: T085
type: task
status: planned
parent_epic: E005
parent_feature: F022
parent_story: S043
depends_on: [S043]
owned_paths: [services/api/migrations/*_metrics_*.sql, crates/domain/src/metrics/**, crates/persistence/src/metrics/**, services/api/src/metrics/**, testing/features/F022/database/**, testing/features/F022/api/**]
feature_flag: F022_FEATURE
branch: t085-metric-definitions
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4
- Capability contract: `docs/capability-contracts.md` row F022

# T085 — Metric definitions

## Identity

- Parent story: `S043` KPIs
- Owner: platform
- Branch: `t085-metric-definitions`
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4; `docs/capability-contracts.md` row F022

## Objective

Create the metrics schema, the typed `Metric` model with its validator, and the four definition routes with authorization, idempotency, concurrency, audit, and `metric.updated.v1`.

## Specification

- Owned paths: `services/api/migrations/<ts>_metrics_create_tables.sql`, `services/api/migrations/<ts>_metrics_create_tables.down.sql`, `crates/domain/src/metrics/{mod.rs, metric.rs, validate.rs, errors.rs, service.rs, schema.rs}` (no SQL), `crates/persistence/src/metrics/{mod.rs, metric_repository.rs}` holding every statement against `metrics` and `metric_filters`, `services/api/src/metrics/{mod.rs, routes.rs, handlers_metric.rs, dto.rs}`
- Contract/input: `CreateMetricRequest { name, workspace_id, source, measure, filters?, period, format, target?, comparison, scope_policy? }`, `UpdateMetricRequest` with the same optional fields, list query `{ cursor?, limit? ≤ 100, workspace_id, source_id?, name_prefix? }`; headers `Idempotency-Key`, `If-Match`; tenant policy `reports.aggregate_hidden_values` from F002 tenant settings.
- Output/behavior: DDL creates `metrics`, `metric_filters`, `metric_values`, `metric_runs`, `metric_run_sources` with the measure/period/format/target check constraints, `unique (metric_id, role, node_path)` on `metric_filters`, `(metric_id, scope_key, period_start)` primary key, `(run_id, source_kind, source_id)` primary key, `metric_runs_active_idx`, and cascades; `validate_metric` enforces measure/column type compatibility from the F007 catalog or F021 definition, filter limits, ISO 4217 codes, `decimals` 0..4, at least one `of_filter` row for `percent_of`, and `scope_policy owner` only with tenant policy; routes `GET /api/v1/metrics`, `POST /api/v1/metrics`, `PATCH /api/v1/metrics/{id}`, `DELETE /api/v1/metrics/{id}` return `MetricResponse { id, workspace_id, name, source, measure, filters, period, format, target, comparison, scope_policy, version, created_at, updated_at, deleted_at }`; the nested response shape is unchanged and composed by `MetricRepository` from typed columns and `metric_filters` rows through `load_definition`, `replace_filters`, and `page_metrics`; a change to the measure, filter, period, or source columns calls `delete_values_for_metric` for all scopes; audit rows and `metric.updated.v1` are written in the same `UnitOfWork`; errors map per ticket section 4.
- Dependencies: F021 tables and `ReportDefinition` column catalog; F003 `authz::require(actor, Permission::ReportEdit, workspace)`; F004 outbox writer.
- Feature flag: `F022_FEATURE` gates router mounting (migration runs regardless).
- Large-table note: `metric_values` and `metric_runs` are derived, rebuildable caches serving `GET /api/v1/metrics/{id}/values` and rebuilt by `metrics.recompute`; `metric_values` holds up to 200 scopes × 90 buckets per metric and `prune_unread_scopes` prunes by `(metric_id, scope_key)` in one statement.

## TDD

- Failing test first: `testing/features/F022/database/migration_tests.rs::metrics_tables_exist_with_constraints`, `::second_active_run_same_scope_rejected`, `::metric_filters_unique_node_path`, `::rollback_drops_metric_tables`; `testing/features/F022/api/metric_tests.rs::metric_create_returns_version_one`, `::metric_sum_on_text_column_invalid`, `::metric_owner_scope_requires_tenant_policy`, `::metric_update_measure_invalidates_values`, `::metric_stale_version_conflicts`, `::metric_cross_tenant_not_found`
- Targeted command: `cargo xtask test-feature F022`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: schema-per-worker database; F021 fixture report with column catalog; tenant settings fixture with the policy on and off

## Exit criteria

- [ ] Tests written before the migration and routes and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; router mounted in `services/api/src/router.rs`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S043
- [ ] `finished_at` recorded
