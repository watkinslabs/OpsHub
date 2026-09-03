# F012 performance cases

File: `testing/features/F012/performance/{critical_path_bench.rs,shift_bench.rs}`. Runs against a 10,000-row, 20,000-dependency seeded sheet with fixed seed. Flag `F012_FEATURE`.

- `critical_path_10k_p95` — NFR-F012-01: 100 sequential `GET /critical-path` requests; p95 < 500 ms warm; `critical_path_duration_ms` histogram populated.
- `shift_1000_successors_p95` — NFR-F012-01: 100 committed shifts on a 1,000-successor chain (reverted between runs); p95 < 800 ms.
- `dependency_list_1000_p95` — NFR-F012-01: 200 `GET /dependencies?limit=1000` requests; p95 < 500 ms.
- `shift_budget_rejects_under_2s` — FR-F012-13: 10,001-row chain → 503 `shift_budget` returned within 2.2 s and no writes.
- `sheet_limit_check_constant_time` — FR-F012-05: insert into a sheet at 19,999 links under 100 ms; the count check uses the side index.

Evidence: criterion/k6 summaries under `testing/evidence/F012/performance/`.
