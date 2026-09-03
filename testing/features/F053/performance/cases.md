# F053 performance cases

File: `testing/features/F053/performance/{preview_bench.rs,sync_bench.rs,conflicts_bench.rs}`. Runs against generated 100,000-row source and target sheets with 5 % ambiguous keys and a mapping with 5,000 open conflicts. Flag `F053_FEATURE`.

- `preview_100k_by_100k_under_30s` — NFR-F053-01: preview over 100,000 × 100,000 rows returns counts in under 30 s; engine memory under 500 MB before spill.
- `sync_10k_changed_rows_under_2_minutes` — NFR-F053-01: 10,000 changed source rows synced with links in under 2 minutes; batches of 500.
- `sync_request_ack_p95_under_2s` — NFR-F053-01: 100 sync requests across 20 mappings; p95 of 202 responses under 2 s.
- `conflicts_list_p95` — NFR-F053-01: 200 `GET /mappings/{id}/conflicts?limit=100` over 5,000 open conflicts; p95 < 500 ms; index scan confirmed.
- `listener_debounce_holds_under_burst` — FR-F053-09: 1,000 source cell events in 30 s produce exactly one run per mapping.
- `retry_backoff_bounded` — NFR-F053-04: transient cell-service failures retry at 1 s, 4 s, 16 s and dead-letter on the fourth failure.

Evidence: criterion/k6 summaries under `testing/evidence/F053/performance/`.
