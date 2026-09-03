# F028 performance cases

File: `testing/features/F028/performance/{dispatch_bench.rs,list_bench.rs,openapi_bench.rs}`. Runs against seeded tenant with the harness receiver. Flag `F028_FEATURE`.

- `dispatch_1000_per_minute_p95` — NFR-F028-01: 1,000 outbox events per minute for 5 minutes; p95 from outbox commit to first attempt < 5 s; zero duplicates.
- `openapi_served_under_50ms` — NFR-F028-01: 500 requests for `/api/v1/openapi.json`; p95 < 50 ms with `ETag` hits.
- `list_conventions_overhead_under_20ms` — NFR-F028-01: 10,000-row sheet list with filter, sort, and fields versus raw query; added p95 < 20 ms.
- `rate_limiter_under_load` — FR-F028-07: 20 applications at 600/min concurrently; limiter decisions p95 < 2 ms; no false 429 below the limit.
- `retry_backlog_drains_after_outage` — FR-F028-10: receiver down 30 minutes with 5,000 pending deliveries; backlog drains within 10 minutes of recovery under the per-tenant quota.

Evidence: criterion and k6 summaries under `testing/evidence/F028/performance/`.
