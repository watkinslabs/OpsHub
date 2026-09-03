# F050 performance cases

File: `testing/features/F050/performance/{rows_bench.rs,edit_bench.rs,token_bench.rs}`. Runs against a 100,000-row seeded sheet with fixed seed. Flag `F050_FEATURE`.

- `filtered_rows_100k_p95` — NFR-F050-01: 200 sequential `GET /dynamic-views/{id}/rows?limit=500` with a three-predicate filter (`Vendor = current user AND Status in (open, blocked) AND Due < date`); p95 < 500 ms warm.
- `edit_row_p95` — NFR-F050-01: 200 edits spread across vendor rows through the view; p95 < 800 ms including edit record and outbox write.
- `token_resolve_under_20ms` — NFR-F050-01: 1,000 `GET /public/dynamic-views/{token}` resolutions; hash lookup and guard add < 20 ms over the equivalent authenticated rows call.
- `token_rate_limit_overhead` — FR-F050-08: 600 reads per minute per token sustained with rate-limit check adding < 2 ms p95.
- `predicate_compile_uses_index_narrowing` — NFR-F050-01: equality-only filter over 100k rows scans ≤ 2% of `cells` rows per `EXPLAIN ANALYZE`.

Evidence: criterion/k6 summaries under `testing/evidence/F050/performance/`.
