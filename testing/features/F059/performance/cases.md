# F059 performance cases

File: `testing/features/F059/performance/publish_bench.rs`. Runs against the 12-widget dashboard and 10,000-row view fixtures with MinIO. Flag `F059_FEATURE`.

- `render_dashboard_12_widgets_p95` — NFR-F059-01: 500 public renders from snapshot; p95 < 500 ms.
- `refresh_10k_row_view_under_10s` — NFR-F059-01: 20 refresh jobs; p95 < 10 s including hidden-column stripping.
- `rate_limit_enforced_at_61` — FR-F059-12: 61 requests in one minute; the 61st is 429 within 50 ms.
- `token_resolution_p95` — FR-F059-02: 5,000 resolutions; p95 < 20 ms with the hash index.
- `scheduler_tick_1000_publications` — NFR-F059-04: 1,000 due publications enqueued in one tick under 3 s with no duplicates.

Evidence: criterion/k6 summaries under `testing/evidence/F059/performance/`.
