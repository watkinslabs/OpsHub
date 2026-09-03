# F052 performance cases

File: `testing/features/F052/performance/{import_bench.rs,run_list_bench.rs,ack_bench.rs}`. Runs against the seeded `Budget` sheet, a generated 100,000-row CSV in MinIO, and a flow with 1,000 runs. Flag `F052_FEATURE`.

- `import_100k_rows_under_10_minutes` — NFR-F052-01: 100,000-row, 50-column CSV with `update` strategy completes `succeeded` in under 10 minutes on the reference worker; peak worker memory under 512 MB.
- `run_request_ack_p95_under_2s` — NFR-F052-01: 200 run requests across 20 flows; p95 of 202 responses under 2 s.
- `run_list_p95` — NFR-F052-01: 200 `GET /flows/{id}/runs?limit=100` over 1,000 runs; p95 < 500 ms; `EXPLAIN` uses the flow/created index.
- `scheduler_tick_under_1s_with_500_flows` — FR-F052-06: 500 due schedules; one tick claims all within 1 s without duplicate runs.
- `retry_backoff_bounded` — NFR-F052-04: transient storage failures retry at 1 s, 4 s, 16 s and dead-letter on the fourth failure.

Evidence: criterion/k6 summaries under `testing/evidence/F052/performance/`.
