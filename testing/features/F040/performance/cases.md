# F040 performance cases

File: `testing/features/F040/performance/{scan_bench.rs,insight_read_bench.rs,action_run_bench.rs,token_budget_bench.rs}`. Runs against the seeded tenant with the F039 provider stub. Flag `F040_FEATURE`.

- `scan_twenty_thousand_rows_under_ten_minutes` — NFR-F040-01: all six detectors over the 20,000-row generator complete within 10 minutes p95 with the stub answering in 200 ms per narration batch.
- `insight_list_p95_under_400ms` — NFR-F040-01: 200 list requests against 5,000 open insights with the default sort; p95 under 400 ms using the `(tenant_id, status, severity desc, last_seen_at desc)` index.
- `insight_detail_p95_under_300ms` — NFR-F040-01: 200 detail requests on an insight with 20 evidence rows; p95 under 300 ms.
- `confirm_to_run_start_under_5s` — NFR-F040-01: 100 confirmations; time from `ai-action.confirmed.v1` to the run row reaching `running` p95 under 5 s at concurrency 1 per tenant.
- `detector_pass_under_15000_prompt_tokens` — NFR-F040-05: a 1,000-row `schedule_risk` pass reports at most 15,000 prompt tokens because candidates are summarised in Rust.
- `permission_filtered_list_scales` — NFR-F040-01, NFR-F040-02: with 40% of evidence pointing at sheets the caller cannot read, list p95 stays under 400 ms and the filtered count is exact.
- `rate_limiter_and_breaker_overhead_under_5ms` — FR-F040-15: the per-request limiter and circuit-breaker checks add under 5 ms p99.

Evidence: criterion summaries and stub timing logs under `testing/evidence/F040/performance/`.
