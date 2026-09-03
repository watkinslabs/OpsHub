# F032 performance cases

File: `testing/features/F032/performance/governance_bench.rs`. Runs against the seeded project and a generated 1,000-project tenant with fixed seed. Flag `F032_FEATURE`.

- `health_read_p95` — NFR-F032-01: 200 sequential `GET /health` and `GET /stage-gates`; p95 < 500 ms warm.
- `governance_writes_p95` — NFR-F032-01: 100 each of override, submit, decide, and intake writes; p95 < 800 ms.
- `single_project_recompute_under_5s` — NFR-F032-01: `row.updated.v1` to `project-health.computed.v1` within 5 s after the 60 s debounce window.
- `nightly_recompute_1000_projects_under_20m` — NFR-F032-01: nightly batch of 1,000 projects in groups of 50 completes under 20 minutes with no dead letters.
- `approval_sync_latency` — NFR-F032-04: `approval.decided.v1` to gate approved within 5 s p95 over 100 gates; `stage_gate_decision_latency_ms` metric exported.

Evidence: criterion/k6 summaries under `testing/evidence/F032/performance/`.
