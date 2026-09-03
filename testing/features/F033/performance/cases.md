# F033 performance cases

File: `testing/features/F033/performance/capacity_bench.rs`. Runs against generated fixtures with fixed seeds. Flag `F033_FEATURE`.

- `capacity_52_weeks_200_allocations_p95` — NFR-F033-01: 200 sequential `GET /capacity?granularity=week` over 52 weeks for a resource with 200 allocations; p95 < 500 ms warm.
- `resource_list_5000_p95` — NFR-F033-01: `GET /resources?limit=200` over 5,000 resources with skill filter; p95 < 500 ms.
- `allocation_create_with_recompute_p95` — NFR-F033-01: 200 allocation creates across 20 resources; p95 < 800 ms including capacity recompute and outbox write.
- `working_day_cache_hit_ratio` — NFR-F033-04: 1,000 capacity reads after warm-up hit the working-day cache above 99 percent; cache invalidates on `working-calendar.updated.v1`.
- `allocation_overlap_query_index_scan` — FR-F033-09: overlap list over 1,000,000 allocations uses the gist index; p95 < 300 ms.

Evidence: criterion/k6 summaries under `testing/evidence/F033/performance/`.
