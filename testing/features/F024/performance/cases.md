# F024 performance cases

File: `testing/features/F024/performance/{chart_query_bench.rs,burndown_bench.rs,time_series_bench.rs,render_bench.ts}`. Criterion for the Rust benches, a Playwright performance trace for the render bench. Flag `F024_FEATURE`.

- `chart_query_p95_under_800ms_on_100k_rows` — NFR-F024-01: 200 bar queries over the 100,000-row "Portfolio status" snapshot with 2 dimensions and 3 measures; p95 < 800 ms under the viewer scope.
- `burndown_10k_rows_90_days_under_2s` — NFR-F024-01: cold burndown over 10,000 rows and a 90-day span with `cell_history` replay; p95 < 2 s.
- `burndown_cached_call_under_100ms` — NFR-F024-01, FR-F024-08: the second identical call within 60 s returns from cache under 100 ms and increments `burndown_cache_hits_total`.
- `cached_time_series_p95_under_300ms` — NFR-F024-01: 200 reads of "Open high risks" with a stored projection; p95 < 300 ms.
- `projection_job_completes_under_5s` — NFR-F024-01: `charts.project` over a 10,000-point metric with a 90-day horizon completes in under 5 s.
- `line_1000_points_renders_under_100ms` — NFR-F024-01: `LineChart` with 1,000 points measured on the reference laptop; first paint under 100 ms.
- `workload_200_people_53_buckets_renders_under_100ms` — NFR-F024-01, FR-F024-09: full 10,600-cell heatmap paints under 100 ms with virtualized rows.
- `projection_scan_uses_scope_index` — NFR-F024-04: the latest-projection lookup over 1,000,000 `time_series_points` rows completes in under 50 ms using the `(metric_id, scope_key, computed_at desc)` index.
- `chart_query_duration_metric_emitted` — NFR-F024-04: `chart_query_duration_seconds` histogram observed for every benched query with `kind` and `source_kind` labels.

Evidence: criterion summaries, Playwright traces, and metric scrapes under `testing/evidence/F024/performance/`.
