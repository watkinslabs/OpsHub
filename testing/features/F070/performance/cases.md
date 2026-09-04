# F070 performance cases

File: `testing/features/F070/performance/{trash_bench.rs,projection_bench.rs,rebuild_bench.rs}`. Runs against a seeded tenant with 200,000 entries across the three live kinds. Flag `F070_FEATURE`.

- `first_page_p95_under_400ms_over_200k_entries` — NFR-F070-01: 200 requests for the default page; p95 under 400 ms with the ACL join in place and `trash_entries(tenant_id, deleted_at desc, id)` used.
- `filtered_page_p95_under_400ms` — NFR-F070-01: the `kind`, `deleted_by` and `workspace_id` filters each stay within the same budget and use their own index rather than the default one.
- `acl_prefilter_does_not_short_a_page` — NFR-F070-01, FR-F070-02: with 90 percent of entries hidden, every page still returns `limit` rows while visible rows remain, which is the property a post-filter would break.
- `projection_lag_within_bounds_under_burst` — NFR-F070-01, NFR-F070-04: a 5,000-event burst keeps publish-to-visible lag under 5 s p95 and 120 s p99, and `trash_projection_lag_seconds` matches the measured value.
- `rebuild_200k_entries_under_3_minutes` — NFR-F070-01, FR-F070-04: a full rebuild completes in under 3 minutes with readers served throughout from the previous epoch.
- `sweep_batch_bounded_and_steady` — FR-F070-08: 50,000 expired entries sweep in batches of 500 without a transaction exceeding one batch and without lag on the index read.

Evidence: criterion summaries, lag histograms and `EXPLAIN` output under `testing/evidence/F070/performance/`.
