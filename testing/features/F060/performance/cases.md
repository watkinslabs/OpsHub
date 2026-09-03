# F060 performance cases

File: `testing/features/F060/performance/{formatting_bench.rs,materialize_bench.rs,paint_bench.ts}`. Criterion for the Rust lanes and Playwright tracing for the paint lane, against the seeded tenant. Flag `F060_FEATURE`.

- `compile_hundred_rule_set_under_5ms` — NFR-F060-01: compiling `stress_100` from a cold cache takes under 5 ms; the second compile is served from the cache keyed by `rules_version`.
- `evaluate_hundred_rules_over_five_hundred_rows_under_25ms` — NFR-F060-01: 100 rules over a 500-row page evaluate in under 25 ms p95 across 200 runs.
- `view_row_page_p95_within_ten_percent` — NFR-F060-01: `GET /api/v1/views/{id}/rows` with `include=formatting` over a 100,000-row sheet stays within 10% of the unformatted p95 and under 550 ms.
- `materialize_hundred_thousand_rows_under_90s` — NFR-F060-01: a full materialization of 100,000 rows against 100 rules finishes in under 90 s with per-sheet concurrency 1 and batches of 500.
- `incremental_materialize_after_bulk_edit_under_2s` — NFR-F060-01, FR-F060-10: a 200-cell bulk edit refreshes only the affected `(rule_id, row_id)` pairs in under 2 s.
- `viewport_paint_frames_under_16ms` — NFR-F060-01: scrolling 500 formatted rows produces no frame over 16 ms and no layout recalculation beyond the custom-property write.
- `budget_guard_caps_page_cost_at_150ms` — FR-F060-13: a rule set engineered past the budget returns a degraded page rather than exceeding 150 ms of evaluation, measured over 100 pages.
- `stale_repair_queue_drains_without_backlog` — NFR-F060-04: 10,000 stale states repair in under 60 s while `formatting_states_stale_total` returns to zero.

Evidence: criterion summaries, Playwright traces, and metric snapshots under `testing/evidence/F060/performance/`.
