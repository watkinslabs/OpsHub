# F065 database cases

File: `testing/features/F065/database/{migration_tests.rs,constraint_tests.rs,retention_tests.rs}`. Flag `F065_FEATURE`.

- `signup_tables_exist_with_constraints` — T257: `signup_requests`, `signup_tokens`, and `reserved_slugs` exist with the columns, defaults, and status checks from ticket section 4.
- `soft_reservation_index_blocks_second_pending_slug` — FR-F065-07: a second `pending` row with the same `lower(requested_slug)` violates the partial unique index; the same slug is accepted once the first row is `abandoned`.
- `token_hash_is_unique` — FR-F065-08: a duplicate `token_hash` violates `signup_tokens_hash_idx`.
- `attempts_and_resends_bounded` — FR-F065-08, FR-F065-09: `attempts = 6` and `resend_count = 4` violate their check constraints.
- `status_and_tenant_id_agree` — FR-F065-10: `status = 'provisioned'` without `tenant_id`, and `tenant_id` set on a `pending` row, both violate the agreement check.
- `tokens_cascade_on_request_delete` — FR-F065-14: deleting a `signup_requests` row removes its `signup_tokens` children.
- `seeded_reserved_slugs_present` — FR-F065-06: the migration seeds 240 rows including `www`, `api`, `admin`, `billing`, `security`, and `opshub`, none with `reason = 'pinned'`.
- `pinned_reservation_expires` — FR-F065-15: a `pinned` row past `expires_at` is removed by the sweep and the slug becomes available.
- `email_hash_index_used_for_per_address_limit` — FR-F065-03: `EXPLAIN` on the 24-hour count per `email_hash` uses `signup_requests(email_hash, created_at desc)`.
- `sweep_index_used_for_status_scan` — NFR-F065-01: `EXPLAIN` on the nightly candidate scan uses `signup_requests(status, created_at)`.
- `scrub_leaves_only_non_identifying_columns` — FR-F065-14: after the 7-day scrub the row's identifying columns are null and `scrubbed_at` is set exactly once on repeat runs.
- `rollback_drops_signup_tables` — T257: `sqlx migrate revert` removes the three tables and their indexes and leaves `tenants` and `users` untouched.

Evidence: migration log, `EXPLAIN` output, and row dumps under `testing/evidence/F065/database/`.
