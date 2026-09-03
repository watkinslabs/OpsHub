# F004 performance cases

File: `testing/features/F004/performance/runtime_bench.rs`. Runs against the compose stack with 4 worker replicas and seeded outbox rows with a fixed seed. Flag `F004_FEATURE`.

- `readyz_p95_under_50ms` — NFR-F004-01: 1,000 `GET /readyz` with warm connections; p95 < 50 ms.
- `outbox_drain_10k_under_60s` — FR-F004-07: 10,000 unpublished rows, one relay; all published within 60 s.
- `outbox_lag_p95_at_200_eps` — NFR-F004-01: 200 events/s for 5 minutes; `outbox_publish_lag_seconds` p95 < 2 s.
- `job_throughput_500_per_second` — NFR-F004-01: 30,000 `sample` jobs across 4 workers complete at ≥ 500/s with `job_run_duration_seconds` overhead < 5 ms.
- `quota_enforcement_overhead` — FR-F004-09: per-tenant quota check adds < 1 ms p95 per job.

Evidence: criterion/k6 summaries under `testing/evidence/F004/performance/`.
