# F036 performance cases

File: `testing/features/F036/performance/{evaluate_bench.rs,link_bench.rs}`. Runs against a tenant seeded with 2,000 users, 50 groups, a workspace with a 6-level folder chain, and 20,000 grants with fixed seed. Flag `F036_FEATURE`.

- `evaluate_access_overhead_p95` — NFR-F036-01: 10,000 authorization checks for a user in 8 groups on a sheet 6 folders deep; added latency from `ShareGrantSource` p95 ≤ 5 ms with the per-request cache, ancestry loaded once.
- `share_list_200_grants_p95` — NFR-F036-01: 200 sequential `GET /api/v1/sheet/{id}/shares?limit=200` on a sheet with 200 direct and 300 inherited grants; p95 < 500 ms.
- `link_resolve_p95_under_rate_limit` — NFR-F036-01: 50 requests per minute from 20 IPs against 20 links; p95 < 300 ms; zero 429 responses.
- `link_resolve_rate_limit_ceiling` — FR-F036-11: 120 requests per minute from one IP; requests 61 onward return 429 within 20 ms each.
- `sweeper_20k_expired_grants_bounded` — FR-F036-13: sweeper removes 20,000 expired grants in batches of 500 in under 30 s and publishes one event per grant.

Evidence: criterion/k6 summaries under `testing/evidence/F036/performance/`.
