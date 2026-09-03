# F008 performance cases

File: `testing/features/F008/performance/{cell_write_bench.rs,bulk_bench.rs,concurrent_editors.rs,scroll_bench.spec.ts}`. Runs against a 100,000-row, 500-column seeded sheet with fixed seed. Flag `F008_FEATURE`.

- `single_cell_patch_p95` — NFR-F008-01: 500 sequential single-cell patches across random rows; p95 < 800 ms warm.
- `bulk_5000_cells_under_5s` — NFR-F008-01: `cells/bulk` with 5,000 target cells `mode: set`; wall time < 5 s, one event.
- `bulk_rows_1000_p95` — FR-F008-04: 20 runs of 1,000-row bulk set; p95 < 5 s.
- `changes_feed_1000_p95` — NFR-F008-01: 200 feed reads of 1,000 changes; p95 < 500 ms.
- `thousand_editors_p95_under_800ms` — NFR-F008-02: 1,000 concurrent editors patching for 60 s; p95 < 800 ms, zero lost updates, conflicts counted.
- `history_lookup_p95` — FR-F008-09: cell with 10,000 history rows; first page p95 < 300 ms using the history index.
- `scroll_100k_rows_frame_budget` — FR-F008-13: Playwright scrolls 100,000 rows for 10 s; no frame over 32 ms, DOM rows ≤ 60.

Evidence: criterion/k6 summaries and trace frame timings under `testing/evidence/F008/performance/`.
