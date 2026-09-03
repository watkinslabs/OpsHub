# F039 performance cases

File: `testing/features/F039/performance/{retrieval_bench.rs,request_bench.rs,apply_bench.rs,read_bench.rs}`. Criterion against the seeded tenant with the `recorded` adapter returning a fixed 50 ms latency. Flag `F039_FEATURE`.

- `scope_for_twenty_sheets_under_300ms` — NFR-F039-01, FR-F039-07: `RetrievalScope::resolve` over 20 sheets and 400 columns with one batched `authz/check` completes under 300 ms p95.
- `envelope_build_and_redaction_under_150ms` — NFR-F039-01, FR-F039-08: schema cards plus the strict redaction pass over the 200-sample budget complete under 150 ms p95.
- `formula_request_p95_under_6s_excluding_provider` — NFR-F039-01: 100 formula requests including 5 F035 evaluate calls each; p95 under 6 s with provider latency subtracted.
- `query_compile_p95_under_6s_excluding_provider` — NFR-F039-01: 100 compilations including F021 validation and F035 parsing of calculated fields; p95 under 6 s excluding provider latency.
- `apply_p95_under_800ms` — NFR-F039-01, FR-F039-11: 200 applies through F035 `PUT /formula` measured to the response, excluding the queued recalculation job.
- `query_read_p95_under_300ms` — NFR-F039-01, FR-F039-05: 200 `GET /api/v1/ai/queries/{id}` requests over 5,000 stored queries.
- `expiry_job_scan_bounded` — NFR-F039-04, FR-F039-12: 100,000 proposals with 2,000 expiring; the scan uses `ai_proposals(tenant_id, status, expires_at)` and completes under 500 ms.
- `limit_check_adds_under_5ms` — NFR-F039-01, FR-F039-15: the pre-egress daily and monthly limit check against a warm `ai_usage` cache adds under 5 ms p99.

Evidence: criterion summaries and flamegraphs under `testing/evidence/F039/performance/`.
