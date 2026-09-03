# F061 performance cases

File: `testing/features/F061/performance/{public_scope_bench.rs,submit_bench.rs,list_bench.rs,reminder_bench.rs}`. Runs against the seeded tenant with the recorded notification service. Flag `F061_FEATURE`.

- `scope_read_200x20_under_300ms` — NFR-F061-01: 200 reads of a 200-row × 20-column scope; p95 under 300 ms including the token hash lookup and scope projection.
- `submit_50_cells_under_900ms` — NFR-F061-01: 100 submissions of 50 cells each through the F008 apply path; p95 under 900 ms end to end.
- `request_list_p95_under_500ms` — NFR-F061-01: 10,000 requests seeded in the tenant; 200 filtered list calls; p95 under 500 ms with cursor paging.
- `claim_scan_over_100k_schedules_under_2s` — NFR-F061-01: 100,000 `reminder_schedules` rows with 500 due; the claim query completes under 2 s and `EXPLAIN` shows the partial index.
- `reminder_batch_throughput` — FR-F061-10: 5,000 due schedules processed in batches of 200 within 60 s with four workers and no duplicate sends.
- `token_lookup_constant_time` — NFR-F061-02: timing spread between a valid and an invalid token lookup stays within 5 percent over 1,000 samples.

Evidence: criterion summaries and `EXPLAIN` plans under `testing/evidence/F061/performance/`.
