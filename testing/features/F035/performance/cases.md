# F035 performance cases

File: `testing/features/F035/performance/{parse_bench.rs,recalc_bench.rs}`. Runs against a 100,000-row seeded sheet with 10 formula columns and fixed seed. Flag `F035_FEATURE`.

- `parse_1000_nodes_under_20ms` — NFR-F035-01: 1,000-node expression parsed 500 times; p95 < 20 ms.
- `incremental_recalc_100k_p95` — NFR-F035-01: 200 single-cell edits on random rows; dependent recalculation p95 < 2,000 ms end to end from event to result row.
- `full_recalc_100k_under_60s` — NFR-F035-01, FR-F035-14: `POST /recalculate` on the 100k sheet completes within 60 s; ack under 2 s; editing requests stay under 800 ms p95 during the job.
- `timeout_budget_enforced` — FR-F035-11: pathological column stops within 2,100 ms wall clock and marks remaining cells `timeout`.
- `recalc_storm_coalesced` — NFR-F035-04: 1,000 `cell.updated.v1` events in 1 s for one column produce ≤ 8 recalculation batches.

Evidence: criterion/k6 summaries under `testing/evidence/F035/performance/`.
