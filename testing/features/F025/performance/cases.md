# F025 performance cases

File: `testing/features/F025/performance/{drill_bench.rs,export_bench.rs,download_bench.rs}`. Runs against the seeded tenant with the deterministic render stub. Flag `F025_FEATURE`.

- `row_drill_p95_under_400ms` — NFR-F025-01: 200 row-target drills over the 100,000-row snapshot; p95 < 400 ms.
- `group_drill_p95_under_900ms` — NFR-F025-01: 200 group-target drills returning 200 rows each; p95 < 900 ms with one batched query per readable sheet.
- `export_ack_p95_under_500ms` — NFR-F025-01: 200 export creations; acknowledgement p95 < 500 ms and status reads p95 < 200 ms.
- `csv_50k_rows_under_20s` — NFR-F025-01: 50,000-row CSV render completes in under 20 s with steady memory.
- `csv_250k_rows_under_120s` — NFR-F025-01, FR-F025-11: 250,000-row CSV completes under 120 s and stays below the 200 MB cap.
- `dashboard_pdf_twelve_widgets_under_45s` — NFR-F025-01: 12-widget dashboard PDF completes under 45 s p95 excluding the refresh wait.
- `concurrency_cap_holds_under_load` — FR-F025-11: 10 simultaneous requests keep 3 renders running and return 429 for the rest without starving the queue.

Evidence: criterion summaries and render timings under `testing/evidence/F025/performance/`.
