# F038 performance cases

File: `testing/features/F038/performance/auth_bench.rs`. Runs against a tenant with 10,000 users, 50,000 sessions, and 5,000 tokens seeded with a fixed seed. Flag `F038_FEATURE`.

- `callback_p95` — NFR-F038-01: 200 callbacks through the in-process mock provider; p95 < 800 ms excluding provider time.
- `session_lookup_p95` — NFR-F038-01: 1,000 cookie-authenticated `GET /api/v1/sessions`; extractor p95 < 20 ms.
- `bearer_lookup_p95` — NFR-F038-01: 1,000 bearer requests; hash lookup p95 < 20 ms with one `last_used_at` write per minute.
- `rate_limiter_overhead` — FR-F038-13, NFR-F038-01: bucket check adds < 2 ms p95 under 50 concurrent logins.
- `session_sweep_bounded` — NFR-F038-04: hourly sweep of 50,000 expired rows completes in < 5 s using `sessions_tenant_expires_idx`.

Evidence: criterion/k6 summaries under `testing/evidence/F038/performance/`.
