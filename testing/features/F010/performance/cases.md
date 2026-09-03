# F010 performance cases

File: `testing/features/F010/performance/{search_bench.rs,index_lag_bench.rs,import_bench.rs,export_bench.rs}`. Runs against fixed-seed fixtures (`0xF010`) with MinIO per worker. Flag `F010_FEATURE`.

- `search_1m_documents_p95` — NFR-F010-01: 500 queries from a fixed term list against 1,000,000 documents; p95 < 500 ms; plan uses the GIN indexes.
- `index_lag_p95_under_5s` — NFR-F010-01: 1,000 `row.updated.v1` events published; time to searchable document p95 < 5 s.
- `import_100k_rows_under_10_minutes` — NFR-F010-01: 100,000-row CSV committed; completes < 10 min; `processed_rows = 100000`, `error_count = 2000`.
- `resume_after_kill_no_duplicates` — FR-F010-09, NFR-F010-04: worker killed after chunk 37, restarted; final row count 98,000; zero duplicate `target_row_id`; total time still < 10 min.
- `export_100k_csv_under_60s` — NFR-F010-01: 100,000-row CSV export completes < 60 s; checksum stable across two runs.
- `export_100k_pdf_paginates_with_header_repeat` — FR-F010-14: 100,000-row PDF completes < 300 s; every page has the header row and footer.
- `commit_ack_under_2s_under_load` — FR-F010-08, FR-F010-13: 50 concurrent commit and export requests; every acknowledgement < 2 s.

Evidence: criterion/k6 summaries under `testing/evidence/F010/performance/`.
