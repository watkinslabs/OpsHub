# F022 performance cases

File: `testing/features/F022/performance/{metric_values_bench.rs,recompute_bench.rs}`. Runs against a 100,000-row source seeded with `0x0F22`. Flag `F022_FEATURE`.

- `metric_values_p95` — NFR-F022-01: 500 `GET /values` requests across 20 scopes; p95 < 300 ms from cache.
- `recompute_100k_rows_under_thirty_seconds` — NFR-F022-01: weekly count over 100,000 rows with 52 buckets completes < 30 s; acknowledged < 2 s.
- `rollup_quarter_from_daily_p95` — FR-F022-08: 90 daily buckets → quarter rollup p95 < 50 ms in-process.
- `scope_cap_eviction` — FR-F022-05: 250 distinct viewers → 200 cached scopes, oldest evicted, no error.

Evidence: criterion/k6 summaries under `testing/evidence/F022/performance/`.
