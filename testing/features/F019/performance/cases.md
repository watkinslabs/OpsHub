# F019 performance cases

File: `testing/features/F019/performance/{start_latency_bench.rs,run_list_bench.rs,scheduler_bench.rs,quota_bench.rs}`. Fixed seed `0x0F19`. Flag `F019_FEATURE`.

- `run_start_latency_p95` — NFR-F019-01: 1,000 `row.updated.v1` events per minute for 5 minutes; queued-to-started p95 < 2 s.
- `run_list_1m_p95` — NFR-F019-01: 1,000,000 seeded runs; 200 `GET /api/v1/workflow-runs?limit=100` with status filter; p95 < 500 ms.
- `scheduler_tick_10k_triggers` — NFR-F019-01: 10,000 due `workflow_triggers`; one tick enqueues all in < 30 s.
- `quota_fairness_two_tenants` — FR-F019-08: tenant A floods 5,000 runs; tenant B's 10 runs all start within 5 s.
- `dead_letter_retry_throughput` — FR-F019-06: 1,000 dead-lettered runs retried; all re-queued in < 10 s.

Evidence: criterion and k6 summaries under `testing/evidence/F019/performance/`.
