# F047 performance cases

File: `testing/features/F047/performance/{transport_bench.rs,resource_bench.rs,stream_bench.rs}`. Runs against the seeded tenant with the in-process stub client. Flag `F047_FEATURE`.

- `initialize_and_tools_list_under_100ms` — NFR-F047-01: 500 calls each against the in-memory manifest; p95 < 100 ms.
- `resources_list_hundred_under_300ms` — NFR-F047-01: 5,000 seeded resources, 200 paged calls with permission filtering; p95 < 300 ms per 100-descriptor page.
- `document_read_100kb_under_400ms` — NFR-F047-01: 200 reads of a 100 KB document including redaction; p95 < 400 ms.
- `tool_call_overhead_under_30ms` — NFR-F047-01: `get_record` through `tools/call` versus the equivalent REST use case over 300 samples; added p95 < 30 ms.
- `two_hundred_streams_under_200mb` — NFR-F047-01: 200 concurrent SSE streams for 60 seconds with 10 events/second; resident memory < 200 MB and no dropped heartbeat.
- `rate_bucket_check_under_2ms` — FR-F047-12: 10,000 bucket checks; p95 < 2 ms with the single-statement upsert.
- `audit_page_scan_bounded` — FR-F047-14: 1,000,000 `mcp_audit` rows across partitions; a 200-row newest-first page completes in under 300 ms using the tenant index.

Evidence: criterion summaries and memory samples under `testing/evidence/F047/performance/`.
