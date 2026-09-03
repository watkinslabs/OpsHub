# F002 performance cases

File: `testing/features/F002/performance/user_list_bench.rs`. Runs against a 100,000-user tenant seeded with a fixed seed. Flag `F002_FEATURE`.

- `user_list_100k_p95` — NFR-F002-01: 200 sequential `GET /api/v1/users?limit=200` with `sort=display_name`; p95 < 500 ms warm.
- `group_members_replace_5000_p95` — NFR-F002-01: 50 replacements of a 5,000-member set with 10% churn; p95 < 800 ms.
- `user_create_p95` — NFR-F002-01: 200 invites; p95 < 800 ms including audit and outbox writes.
- `tenant_gate_cache_overhead` — FR-F002-04: `TenantGate` adds < 1 ms p95 per request with a warm 30-second status cache.

Evidence: criterion/k6 summaries under `testing/evidence/F002/performance/`.
