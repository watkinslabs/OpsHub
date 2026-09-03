# F009 performance cases

File: `testing/features/F009/performance/{hierarchy_bench.rs,rollup_bench.rs}`. Runs against seeded trees with fixed seed. Flag `F009_FEATURE`.

- `children_10k_descendants_p95` — NFR-F009-01: 200 sequential `GET /children?depth=all&limit=500` requests on a 10,000-descendant subtree; p95 < 500 ms warm; `EXPLAIN` confirms path index range scan.
- `indent_subtree_p95` — NFR-F009-01: 200 indents of a row carrying 1,000 descendants; p95 < 800 ms including path rewrites in 5,000-row chunks.
- `rollup_recompute_5000_rows_under_5s` — NFR-F009-01: one leaf edit on a 5,000-row tree with 5 roll-up rules; ancestors recomputed and `rollup.recomputed.v1` emitted in under 5 s.
- `rollup_bulk_edit_coalesces_events` — FR-F009-07, NFR-F009-04: 1,000 cell edits in 1 s on the same column produce ≤ 8 recompute batches through the 250 ms debounce.
- `link_list_by_target_index_scan` — FR-F009-10: 50,000 links, list by `target_sheet_id` page uses the partial index, p95 < 300 ms.
- `broken_link_detection_on_sheet_delete` — FR-F009-12: deleting a target sheet referenced by 10,000 links marks all broken in under 10 s.

Evidence: criterion/k6 summaries under `testing/evidence/F009/performance/`.
