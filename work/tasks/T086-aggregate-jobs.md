---
id: T086
type: task
status: planned
parent_epic: E005
parent_feature: F022
parent_story: S043
depends_on: [T085]
owned_paths: [crates/domain/src/metrics/**, services/api/src/metrics/**, services/worker/src/metrics/**, testing/features/F022/api/**]
feature_flag: F022_FEATURE
branch: t086-aggregate-jobs
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 3, 4, 7
- Capability contract: `docs/capability-contracts.md` row F022

# T086 — Aggregate jobs

## Identity

- Parent story: `S043` KPIs
- Owner: platform
- Branch: `t086-aggregate-jobs`
- Decision references: `docs/architecture-decisions.md` sections 3, 4, 7; `docs/capability-contracts.md` row F022

## Objective

Implement the per-scope aggregation worker, the recompute and values routes, and run bookkeeping so metric values are computed, cached, and served without leaking hidden data across viewers.

## Specification

- Owned paths: `crates/domain/src/metrics/{aggregate.rs, compare.rs, format.rs, values.rs}`, `services/api/src/metrics/handlers_values.rs`, `services/worker/src/metrics/{mod.rs, recompute_job.rs}`
- Contract/input: `RecomputeJob { tenant_id, metric_id, run_id, scope_key, actor_id, correlation_id }` on subject `metrics.recompute`; `ViewerScope` from `reports::scope`; rows from `reports::read_rows` (snapshot) or `sheets::list_rows` (live); `values` query `{ from?, to?, grain? }`.
- Output/behavior: `POST /api/v1/metrics/{id}/recompute` inserts a `queued` run for the actor's `scope_key`, publishes the job, returns `202 { run_id, status }`, and `409 conflict` while active; `aggregate.rs` folds rows into `chrono-tz` buckets for the trailing window (90 days, 52 weeks, 24 months, 8 quarters) applying `count`, `count_distinct`, `sum`, `avg`, `min`, `max`, and `percent_of` (null on zero denominator); `recompute_job.rs` writes `metric_values` and finalizes `metric_runs` with `duration_ms`, `source_versions`, `rows_scanned` in one transaction, publishes `metric.computed.v1`, retries 3 times, dead-letters on the fourth failure, and ignores redelivery of a finished `run_id`; `GET /api/v1/metrics/{id}/values` returns `MetricValuesResponse { current, comparison, series, meta }` for the caller's scope, `meta.status = "computing"` with an enqueued run when no values exist, and `formatted` from `format.rs`.
- Dependencies: T085 tables and routes; F021 `read_rows` and `ViewerScope`; F004 consumer registry; F049 formatter.
- Feature flag: `F022_FEATURE` gates the consumer registration in `services/worker/src/consumers.rs`.

## TDD

- Failing test first: `testing/features/F022/api/values_tests.rs::metric_recompute_writes_values_and_run`, `::metric_recompute_active_conflicts`, `::percent_of_zero_denominator_null`, `::metric_values_hidden_column_null_for_viewer`, `::metric_values_missing_scope_enqueues_run`, `::metric_values_scope_key_not_shared`, `::recompute_job_dead_letters_after_four_failures`, `::recompute_job_idempotent_by_run_id`
- Targeted command: `cargo xtask test-feature F022`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/metrics.rs` metrics "Open high risks" and "Budget margin"; JetStream stub with failure injection; editor, viewer, restricted viewer scopes

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Recompute consumer registered behind the flag; retry and dead-letter paths verified
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S043
- [ ] `finished_at` recorded
