# F031 performance cases

File: `testing/features/F031/performance/rollup_bench.rs`. Runs against a generated 500-project portfolio with fixed seed. Flag `F031_FEATURE`.

- `rollup_read_500_projects_p95` — NFR-F031-01: 200 sequential `GET /rollup` requests as admin and as viewer; p95 < 500 ms warm.
- `refresh_100_projects_under_30s` — NFR-F031-01: refresh of a 100-project portfolio completes and publishes `portfolio.rollup-refreshed.v1` within 30 s.
- `refresh_enqueue_ack_under_2s` — NFR-F031-01: 50 refresh requests across 50 portfolios; every 202 returned within 2 s.
- `refresh_batches_and_time_budget` — FR-F031-07: 500-project refresh reads in batches of 25 and stops at the 120 s budget with remaining rows `state: error`.
- `portfolio_list_index_scan` — FR-F031-02: 10,000 portfolios in a tenant; list page uses `portfolios_tenant_workspace_updated_idx`, p95 < 300 ms.

Evidence: criterion/k6 summaries under `testing/evidence/F031/performance/`.
