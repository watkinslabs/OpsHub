---
id: T094
type: task
status: planned
parent_epic: E005
parent_feature: F024
parent_story: S047
depends_on: [S047]
owned_paths: [services/worker/src/charts/**, crates/domain/src/charts/**, services/api/src/charts/**, testing/features/F024/api/**, testing/features/F024/performance/**]
feature_flag: F024_FEATURE
branch: t094-time-series-projections
started_at: null
finished_at: null
---

# T094 — Time-series read and projection job

## Identity

- Parent story: `S047` Charts and time series
- Owner: platform
- Branch: `t094-time-series-projections`
- Decision references: `docs/architecture-decisions.md` sections 3, 4, 6, 7; `docs/capability-contracts.md` row F024

## Objective

Implement `GET /api/v1/time-series/{metric_id}` over F022 `metric_values` plus stored `time_series_points`, and the `charts.project` worker job that fits linear and moving-average projections, writes projected points idempotently by `run_id`, and publishes `time-series.projected.v1`.

## Specification

- Owned paths: `crates/domain/src/charts/projection.rs` and `crates/domain/src/charts/adapters/metric.rs`; `services/api/src/charts/handlers_time_series.rs` plus its `TimeSeriesResponse` DTO in `services/api/src/charts/dto.rs`; `services/worker/src/charts/{mod.rs, project_job.rs}`.
- Contract/input: query `from`, `to`, `grain` (`day|week|month|quarter`, default the metric's grain), `horizon_days` (1..90, default 30), `method` (`linear|moving_average`, default `linear`); job message `{ tenant_id, metric_id, scope_key, grain, method, horizon_days, correlation_id }` on subject `charts.project`.
- Output/behavior: `{ actual[{ ts, value }], projected[{ ts, value, lower, upper }], meta { run_id, computed_at, method, window, stale } }`. `actual` comes from F022 `metric_values` bucketed to `grain`; `projected` comes from `time_series_points` of kind `projected` for `(metric_id, scope_key, grain, method, horizon_days)`. The fit window is the last 12 complete buckets, fewer when unavailable, minimum 3; with fewer than 3 the job records `ProjectionError::InsufficientPoints` and the response returns `projected: []` rather than an error. `linear` is ordinary least squares over bucket index with an 80% band from the residual standard error; `moving_average` repeats the window mean with the band at the window standard deviation. Bands are clamped at zero for count-typed metrics. `horizon_days` outside 1..90 is `400 invalid`; a queue outage is `503 unavailable`.
- Job behavior: enqueue on read when no row exists for the key or the stored `computed_at` predates the metric's latest `metric.computed.v1`; the job writes all projected points for a `run_id` in one transaction, deletes points superseded by an older `run_id` and projected points older than 90 days, publishes `time-series.projected.v1` with `metric_id`, `scope_key`, `grain`, `method`, `horizon_days`, `run_id`, `point_count`, and writes audit `time-series.project`. Re-delivery of the same `run_id` is a no-op. Failures retry 3 times with backoff and dead-letter on the fourth, incrementing `projection_failures_total`. `meta.stale` is true while a newer metric run exists; the web client refetches `['time-series', metricId, grain, method, horizon]` every 3 s while `projected` is empty and `meta.stale`.
- Storage: `time_series_points(tenant_id, metric_id, scope_key, grain, method, horizon_days, ts, kind, value, lower, upper, run_id, computed_at)` with primary key `(metric_id, scope_key, grain, method, horizon_days, kind, ts)`, checks `kind in ('actual','projected')` and `method in ('linear','moving_average')`, `metric_id` foreign key to `metrics` on delete cascade, index `(metric_id, scope_key, computed_at desc)`.
- Authorization and isolation: metric read is required, an unreadable or foreign-tenant `metric_id` returns `404 not_found`, and every point is written and read under the caller's `scope_key` so two viewers of the same metric never share projections.
- Observability: spans carry `tenant_id`, `metric_id`, `scope_key`, `run_id`; `chart_query_duration_seconds` and `projection_failures_total` are emitted; cached time-series reads answer under 300 ms p95 and a projection job completes under 5 s.
- Dependencies: F022 `metric_values`, `metric.computed.v1`, and rollups; F004 job transport (NATS JetStream); F028 outbox and correlation IDs.
- Feature flag: `F024_FEATURE` gates the route and the job consumer registration.

## TDD

- Failing test first: `testing/features/F024/api/time_series_tests.rs::time_series_returns_actual_from_metric_values`, `::linear_projection_has_five_weekly_points_with_bounds`, `::moving_average_uses_window_mean`, `::projection_with_two_points_returns_empty`, `::horizon_over_ninety_days_rejected`, `::stale_flag_true_until_projection_catches_up`, `::foreign_tenant_metric_time_series_not_found`, `::projections_isolated_per_scope_key`; `testing/features/F024/api/project_job_tests.rs::job_writes_points_and_publishes_projected_event`, `::job_replay_with_same_run_id_is_noop`, `::job_deletes_superseded_and_expired_points`, `::job_dead_letters_after_three_retries`, `::queue_unavailable_returns_503`; `testing/features/F024/performance/time_series_bench.rs::cached_time_series_p95_under_300ms`, `::projection_job_completes_under_5s`
- Targeted command: `cargo xtask test-feature F024`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/charts.rs` metric "Open high risks" with 52 weekly values (plus a flat 2-point variant and a 10,000-point variant for the bench); JetStream stub for `charts.project`; in-memory outbox recorder; fixed clock `2026-09-03T00:00:00Z`; seed `0x0F24`

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Route mounted in `services/api/src/router.rs` and the consumer registered in `services/worker/src/registry.rs` behind `F024_FEATURE`
- [ ] `time-series.projected.v1` envelope verified in the outbox; audit `time-series.project` written
- [ ] Owned-path check passes; no file exceeds 500 lines; lint and security gates pass
- [ ] Handoff evidence recorded in S047 with artifacts under `testing/evidence/F024/`
- [ ] `finished_at` recorded
