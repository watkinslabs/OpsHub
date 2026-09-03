# F016 performance cases

File: `testing/features/F016/performance/{thread_list_bench.rs,activity_bench.rs}`. Runs against a seeded row with 100 threads and 1,000 comments and a 50,000-entry activity history with fixed seed. Flag `F016_FEATURE`.

- `thread_list_1000_comments_p95` — NFR-F016-01: 200 sequential `GET /api/v1/row/{id}/comments?limit=100` requests; p95 < 500 ms warm.
- `comment_create_p95` — NFR-F016-01: 200 comment creates with 3 mentions each; p95 < 800 ms including mention resolution.
- `activity_projection_lag_p95` — NFR-F016-01, NFR-F016-04: 5,000 `row.updated.v1` events published in 10 s; lag from outbox publish to entry visible p95 < 2 s; consumer batch size 200.
- `activity_list_50k_entries_index_scan` — FR-F016-09: `GET /activity?limit=200&actor_kind=automation` on 50,000 entries uses the target index; p95 < 300 ms.
- `mention_check_many_bounded` — FR-F016-04: 50 mention tokens resolve in one `check_many` round trip under 150 ms.

Evidence: criterion/k6 summaries under `testing/evidence/F016/performance/`.
