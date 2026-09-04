# F068 performance cases

Two budgets are measured: the gate must be cheap enough to run on every branch, and the shared contract must not cost more than the hand-written statement it replaces. Files: `testing/features/F068/performance/{gate_bench.rs,pagination_bench.rs,roundtrip_bench.rs}`, run against a seeded tenant on a throwaway PostgreSQL 18 with the fixed clock. Flag `F068_FEATURE`.

- `gate_completes_under_two_seconds` — NFR-F068-01: `check-persistence` over the whole repository on `ubuntu-latest` with 2 vCPU finishes in under 2 seconds, reading each file once; a 4 MiB generated migration is streamed rather than loaded whole.
- `keyset_page_cost_is_constant` — NFR-F068-01: over 100,000 users, page 2,000 and page 2 are within 10 percent of each other and both under 30 ms p95, because the predicate is `(display_name, id) > ($k, $id)` and no statement contains `offset`.
- `list_uses_the_tenant_status_name_index` — NFR-F068-01: `EXPLAIN` on the default `list` shows an index scan on F002's `users(tenant_id, status, display_name)`, not a sequential scan, at 100,000 rows.
- `mutation_adds_no_extra_round_trip` — NFR-F068-01: a successful `update` issues exactly one statement plus the audit and outbox inserts on the same connection; the re-read appears only when zero rows were affected, measured by statement count.
- `insert_is_one_batch_of_three_statements` — NFR-F068-01: an `insert` through the pool handle issues one `begin`, three statements, and one `commit`, and never more.
- `conformance_suite_scales_with_registry` — NFR-F068-05: the eight-case suite over the registered specifications runs in under 90 seconds on one worker and in parallel across workers with one database each, so adding a repository stays affordable.
- `gate_output_is_deterministic_under_load` — NFR-F068-04: ten concurrent gate runs over copies of the same tree produce byte-identical output, so ordering never depends on file-system enumeration order.

Evidence: criterion summaries, `EXPLAIN` output, and statement counts under `testing/evidence/F068/performance/`.
