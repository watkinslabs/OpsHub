# F006 performance cases

File: `testing/features/F006/performance/row_list_bench.rs`. Runs against a 100,000-row seeded sheet with fixed seed. Flag `F006_FEATURE`.

- `row_list_100k_p95` — NFR-F006-01: 200 sequential `GET /rows?limit=500` requests; p95 < 500 ms warm.
- `row_create_p95` — NFR-F006-01: 200 row creates spread across groups; p95 < 800 ms.
- `row_move_rebalance_bounded` — FR-F006-08: 1,000 inserts at the same position; rebalance count ≤ 16 and each under 200 ms.
- `sheet_list_index_scan` — FR-F006-03: 10,000 sheets in a workspace; list page uses index, p95 < 300 ms.

Evidence: criterion/k6 summaries under `testing/evidence/F006/performance/`.
