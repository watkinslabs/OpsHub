# F003 performance cases

File: `testing/features/F003/performance/{authz_bench.rs,audit_bench.rs}`. Runs against a tenant with 5,000 resources, 50,000 ACL entries, and 10,000,000 audit rows across 12 partitions with a fixed seed. Flag `F003_FEATURE`.

- `check_cached_p95` — NFR-F003-01: 10,000 repeated checks; p95 < 5 ms from the 30-second cache.
- `check_uncached_four_levels_p95` — NFR-F003-01: 1,000 distinct checks over the 4-level ancestry; p95 < 30 ms.
- `record_audit_overhead_p95` — NFR-F003-01: 1,000 mutations with and without audit; delta p95 < 10 ms.
- `audit_list_10m_rows_p95` — NFR-F003-01: 200 `GET /api/v1/audit-events?limit=200` with a 7-day range; p95 < 500 ms via pruning.
- `acl_replace_500_entries_p95` — FR-F003-04: 100 replacements of 500-entry ACLs; p95 < 800 ms.

Evidence: criterion/k6 summaries under `testing/evidence/F003/performance/`.
