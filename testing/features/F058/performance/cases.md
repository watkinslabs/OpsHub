# F058 performance cases

File: `testing/features/F058/performance/sync_bench.rs` and Lighthouse run in `testing/features/F058/performance/shell.lighthouse.json`. Flag `F058_FEATURE`.

- `sync_batch_100_ops_p95` — NFR-F058-01: 100 batches of 100 cell edits; p95 < 2 s including audit and outbox writes.
- `pull_500_rows_p95` — NFR-F058-01: 200 pulls of 500 changed rows; p95 < 500 ms.
- `shell_load_from_cache_under_1500ms` — NFR-F058-01: Lighthouse on a throttled mid-range profile; shell interactive < 1.5 s from cache.
- `sync_rejection_heavy_batch` — FR-F058-05: batch with 50 conflicts and 50 applied stays under 2.5 s and persists all rejections.
- `deep_link_resolve_p95` — FR-F058-09: 1,000 resolutions; p95 < 100 ms.

Evidence: criterion/k6 summaries and Lighthouse JSON under `testing/evidence/F058/performance/`.
