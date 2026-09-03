# F029 performance cases

File: `testing/features/F029/performance/{calendar_sync_bench.rs,notify_bench.rs,read_bench.rs}`. Runs against seeded tenant with mock providers. Flag `F029_FEATURE`.

- `calendar_sync_1000_rows_under_5_minutes` — NFR-F029-01: 1,000 changed rows with the mock returning `429` every 50th call; sync completes in under 5 minutes with per-connection concurrency 1.
- `notification_send_p95_under_3s` — NFR-F029-01: 500 notifications across the three providers; p95 < 3 s including template rendering.
- `connection_reads_p95` — NFR-F029-01: 200 provider and connection list requests; p95 < 500 ms.
- `callback_processing_under_2s` — NFR-F029-01: 100 callbacks against the mock exchange; processing excluding provider latency p95 < 2 s.
- `refresh_job_scan_bounded` — FR-F029-05: 10,000 connections; the expiring-token scan uses `oauth_tokens(expires_at)` and completes in under 500 ms.

Evidence: criterion summaries under `testing/evidence/F029/performance/`.
