# F007 performance cases

File: `testing/features/F007/performance/{column_list_bench.rs,validate_job_bench.rs}`. Runs against a 500-column sheet and a 100,000-row sheet with fixed seed. Flag `F007_FEATURE`.

- `column_list_500_p95` — NFR-F007-01: 200 sequential `GET /api/v1/sheets/{sheet_id}/columns` on a 500-column sheet; p95 < 500 ms warm.
- `column_create_p95` — NFR-F007-01: 200 column creates across 20 sheets; p95 < 800 ms including option inserts.
- `validate_100k_rows_under_60s` — FR-F007-11, NFR-F007-01: validate a regex-ruled text column over 100,000 rows; acknowledgement < 2 s; job completes < 60 s; one state row per cell.
- `type_change_sync_threshold_holds_budget` — FR-F007-06: `text` → `number` on 10,000 rows completes synchronously in < 800 ms p95; 10,001 rows dispatches async.
- `regex_budget_bounds_pathological_pattern` — NFR-F007-02: pattern `(a+)+$` on a 5,000-char cell finishes under the 10 ms per-cell budget with RE2 semantics.

Evidence: criterion/k6 summaries under `testing/evidence/F007/performance/`.
