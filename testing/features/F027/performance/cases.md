# F027 performance cases

File: `testing/features/F027/performance/{purge_bench.rs,review_bench.rs,read_bench.rs}`. Runs against seeded tenant with fixed seed. Flag `F027_FEATURE`.

- `purge_100k_rows_under_10_minutes` — NFR-F027-01: 100,000 eligible rows plus 2,000 held; purge completes in under 10 minutes; no transaction exceeds 1,000 rows; lock wait p95 < 50 ms.
- `access_review_5000_principals_under_60s` — NFR-F027-01: 5,000 users and guests with shares and tokens; report generated in under 60 s with at most one query per principal kind.
- `retention_reads_p95` — NFR-F027-01: 200 `GET /retention-policies` and hold list requests; p95 < 500 ms.
- `export_and_purge_ack_under_2s` — NFR-F027-01: 50 export and purge proposals on the 100k fixture; acknowledgement p95 < 2 s.
- `tenant_export_1m_rows_within_4h` — FR-F027-07: 1 million rows across 20 sheets exported with manifest in under 4 hours (nightly lane only).

Evidence: criterion summaries under `testing/evidence/F027/performance/`.
