# F048 performance cases

File: `testing/features/F048/performance/{guard_bench.rs,evaluate_bench.rs,propagation_tests.rs}`. Runs against the seeded registry with fixed seed; propagation uses the F004 `two-api` compose profile. Flag `F048_FEATURE`.

- `warm_guard_p99_under_1ms` — NFR-F048-01: 100,000 `RequireModule` evaluations with a warm cache; p99 < 1 ms, zero database queries after warm-up.
- `evaluate_50_keys_p95` — NFR-F048-01: 200 sequential `GET /feature-flags/evaluate` with 50 keys and 20 modules; p95 < 100 ms.
- `flag_list_p95` — NFR-F048-01: 200 `GET /feature-flags` for a tenant with 11 flags and 11 overrides; p95 < 500 ms.
- `kill_propagates_to_second_instance_within_30s` — FR-F048-12: kill on instance 1; instance 2 denies within 30 s; instance 1 within 2 s; lag metric recorded.
- `cache_hit_ratio_above_99_percent` — NFR-F048-04: 10,000 mixed evaluations for 50 tenants; `flag_eval_cache_hit_ratio` ≥ 0.99.

Evidence: criterion/k6 summaries under `testing/evidence/F048/performance/`.
