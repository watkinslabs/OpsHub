# F056 performance cases

File: `testing/features/F056/performance/pivot_bench.rs`. Runs against the 100,000-row generator with fixed seed. Flag `F056_FEATURE`.

- `outputs_read_5k_cells_p95` — NFR-F056-01: 200 sequential `GET /outputs` on a 5,000-cell output; p95 < 500 ms warm.
- `compute_100k_rows_under_30s` — NFR-F056-01: 3 dimensions, 5 measures over 100,000 rows; p95 < 30 s on the reference worker.
- `compute_ack_under_2s` — FR-F056-05: 100 compute requests; p95 acknowledgement < 2 s.
- `source_too_large_fails_fast` — FR-F056-07: 100,001-row source fails within 5 s without materializing cells.
- `scheduler_tick_enqueues_500_pivots` — FR-F056-12: 500 due pivots enqueued in one tick under 3 s with no duplicate jobs.

Evidence: criterion/k6 summaries under `testing/evidence/F056/performance/`.
