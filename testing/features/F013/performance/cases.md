# F013 performance cases

File: `testing/features/F013/performance/view_rows_bench.rs`. Runs against a 100,000-row seeded sheet with fixed seed and 5,000 dated rows in one month. Flag `F013_FEATURE`.

- `view_rows_filtered_100k_p95` — NFR-F013-01: 200 sequential `GET /views/{id}/rows?limit=500` with a 3-leaf filter and 2 sorts; p95 < 500 ms warm.
- `card_lane_move_p95` — NFR-F013-01: 200 lane moves (cell patch with `If-Match`) spread across lanes; p95 < 800 ms.
- `calendar_month_5k_rows_p95` — NFR-F013-01: 200 month-range requests over 5,000 dated rows in `America/New_York`; p95 < 500 ms.
- `filter_compile_50_leaves_under_5ms` — FR-F013-02: compiling a 50-leaf AST to a predicate takes under 5 ms and produces one parameterized query.
- `view_list_index_scan` — FR-F013-11: 100 views per sheet across 1,000 sheets; list page uses `views_tenant_sheet_updated_idx`, p95 < 300 ms.

Evidence: criterion/k6 summaries under `testing/evidence/F013/performance/`.
