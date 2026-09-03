# F015 performance cases

File: `testing/features/F015/performance/{provision_bench.rs,baseline_bench.rs}`. Runs with fixed-seed manifests and a 100,000-row seeded sheet. Flag `F015_FEATURE`.

- `provision_ack_p95` — NFR-F015-01: 100 provision requests of the 120-row manifest; `202` returned p95 < 2 s.
- `provision_500_rows_under_60s` — NFR-F015-01: 500-row, 200-dependency manifest; run reaches `completed` under 60 s with the in-process worker.
- `baseline_capture_100k_under_30s` — NFR-F015-01: capture on the 100,000-row sheet completes under 30 s in one transaction; `baseline_capture_rows` metric equals 100,000.
- `variance_read_500_p95` — NFR-F015-01: 200 sequential `GET /variance?limit=500` requests; p95 < 500 ms warm.
- `provision_step_replay_no_duplicates` — NFR-F015-04: redelivering every step message twice adds zero extra objects and no more than 10 % wall-clock overhead.

Evidence: criterion/k6 summaries under `testing/evidence/F015/performance/`.
