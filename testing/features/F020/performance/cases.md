# F020 performance cases

File: `testing/features/F020/performance/{inbox_bench.rs,sweep_bench.rs,decide_bench.rs}`. Fixed seed `0x0F20`. Flag `F020_FEATURE`.

- `inbox_100k_p95` — NFR-F020-01: 100,000 approvals, 200 `GET /api/v1/approvals?filter[assigned_to_me]=true&limit=100`; p95 < 500 ms using the GIN index.
- `decide_p95` — NFR-F020-01: 200 decisions on distinct approvals with notification withdrawal; p95 < 800 ms.
- `create_with_group_expansion_p95` — NFR-F020-01: 200 creates with a 50-member group; p95 < 800 ms including 50 notification rows.
- `sweep_10k_timers_under_60s` — NFR-F020-01: 10,000 due timers across reminders and escalations; one sweeper drains them in < 60 s.
- `concurrent_decisions_lock_wait` — FR-F020-04: 20 approvers deciding one `all` approval concurrently; all succeed, p95 < 800 ms.

Evidence: criterion and k6 summaries under `testing/evidence/F020/performance/`.
