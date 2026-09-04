# F063 performance cases

File: `testing/features/F063/performance/{group_sync_bench.rs,mail_bench.rs,connection_read_bench.rs}`. Runs against the seeded tenant with the mock Entra authority and mock Graph. Flag `F063_FEATURE`.

- `delta_sync_500_groups_50000_members_under_10_minutes` — NFR-F063-01, FR-F063-07: 500 mapped groups and 50,000 members with the mock returning `429` and `Retry-After: 1` every 50th call; the run completes inside 10 minutes at per-tenant concurrency 4.
- `graph_mail_ack_p95_under_3s` — NFR-F063-01: 500 notifications through the `graph` transport; acknowledgement to the F037 queue p95 < 3 s including template rendering.
- `connection_read_p95_under_300ms` — NFR-F063-01: 200 `GET /api/v1/entra/connection` requests; p95 < 300 ms with no Graph call made.
- `test_connection_within_10s_budget` — NFR-F063-01: 50 `POST /connection/test` runs with 500 ms of mocked provider latency per round trip; every run inside the 10 s budget.
- `mail_log_index_used_for_tenant_recent_calls` — NFR-F063-04: 200,000 `entra_mail_log` rows; the recent-calls read uses `(tenant_id, occurred_at desc)` and returns in under 300 ms.
- `sync_resume_after_restart_costs_one_delta_page` — NFR-F063-04: restarting mid-run resumes from the stored delta token and re-reads a single page, not the full directory.
- `breaker_bounds_failing_tenant_cost` — FR-F063-09: a connection failing every call issues at most 5 requests before the breaker opens and none for the next 5 minutes.

Evidence: criterion summaries under `testing/evidence/F063/performance/`.
