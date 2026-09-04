# F071 performance cases

File: `testing/features/F071/performance/{analysis_bench.rs,preview_bench.rs,commit_bench.rs,memory_bench.rs}`. Runs against a seeded tenant with generated workbooks. Flag `F071_FEATURE`.

- `twenty_tab_analysis_under_ninety_seconds` — NFR-F071-01: a 20-tab, 200,000-cell workbook analyses in under 90 s including inference and issue writing.
- `preview_p95_under_800ms_at_fifty_tabs` — NFR-F071-01: 200 `GET /api/v1/migrations/{id}` calls on a 50-tab, 2,000-column-map migration; p95 under 800 ms.
- `hundred_thousand_row_commit_under_fifteen_minutes` — NFR-F071-01: 100,000 rows across 10 tabs commit in under 15 minutes at 1,000 rows per chunk.
- `both_mutations_acknowledged_under_two_seconds` — NFR-F071-01: create and commit each return their `202` in under 2 s at the 50-tab size.
- `parser_peak_memory_under_512mb` — NFR-F071-01: peak resident memory over a 200 MB workbook stays under 512 MB, proving the reader streams rather than materialising.
- `sampler_cost_is_bounded_by_the_cap` — FR-F071-05, NFR-F071-01: inference time over a 100,000-row column matches a 2,000-row column within 15 %.
- `resume_claim_bounded_at_scale` — FR-F071-11, NFR-F071-01: 10,000 migration sheet rows; the resume claim returns in under 100 ms using the partial index.
- `issue_panel_query_bounded_at_scale` — FR-F071-15, NFR-F071-01: 5,000 issues on one migration; the grouped panel page returns in under 200 ms.
- `commit_job_idempotent_under_restart_load` — NFR-F071-04: 20 forced restarts during a 50,000-row commit produce no duplicate rows and the four metrics are emitted throughout.

Evidence: criterion summaries and memory traces under `testing/evidence/F071/performance/`.
