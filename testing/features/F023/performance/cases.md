# F023 performance cases

File: `testing/features/F023/performance/{dashboard_get_bench.rs,widget_data_bench.rs,refresh_bench.rs}` and `testing/features/F023/e2e/perf.spec.ts`. Runs against a 40-widget dashboard generated with seed `0x0F23`. Flag `F023_FEATURE`.

- `dashboard_get_40_widgets_p95` — NFR-F023-01: 200 `GET /dashboards/{id}` requests; p95 < 500 ms.
- `widget_data_cache_hit_p95` — NFR-F023-01: 1,000 `GET /widgets/{id}/data` hits across 10 scopes; p95 < 300 ms.
- `full_refresh_40_widgets_under_sixty_seconds` — NFR-F023-01: one scope refresh with 8-way parallel resolve completes < 60 s.
- `drag_keeps_sixty_fps` — NFR-F023-01: Playwright trace of a 40-widget drag shows frame time p95 < 16.7 ms.
- `scheduler_scan_10k_scopes` — FR-F023-07: scan of 10,000 cache scopes selects 24-hour readers in < 200 ms.

Evidence: criterion/k6 summaries and traces under `testing/evidence/F023/performance/`.
