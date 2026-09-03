# F021 performance cases

File: `testing/features/F021/performance/{report_rows_bench.rs,refresh_bench.rs}`. Runs against three 100,000-row, 500-column sheets seeded with `0x0F21`. Flag `F021_FEATURE`.

- `report_rows_100k_p95` — NFR-F021-01: 200 sequential `GET /rows?limit=500` requests as the restricted viewer; p95 < 500 ms warm.
- `three_sheet_refresh_under_sixty_seconds` — NFR-F021-01: refresh joining three 100,000-row sheets with 5 calculated fields completes < 60 s and is acknowledged < 2 s.
- `definition_save_with_25_calculated_fields_p95` — NFR-F021-01: 100 saves; parse and validate p95 < 800 ms.
- `group_at_read_cache_hit_ratio` — FR-F021-11: repeated grouped reads within 60 s hit the `(snapshot_id, scope_key)` cache ≥ 95%.
- `join_fanout_cap_enforced_in_time` — FR-F021-03: non-unique key join exceeding 1,000,000 rows fails within 10 s with `join_fanout_exceeded`.

Evidence: criterion/k6 summaries under `testing/evidence/F021/performance/`.
