# F055 database cases

File: `testing/features/F055/database/{migration_tests.rs,constraint_tests.rs,index_tests.rs}`. Flag `F055_FEATURE`.

- `calendar_tables_exist_with_columns` — FR-F055-01: `calendars`, `calendar_sources`, `calendar_publications` exist with tenant, version, and audit columns as specified.
- `calendar_name_unique_per_workspace` — FR-F055-01: second live calendar named `Launch` in one workspace is rejected; allowed after the first is soft-deleted.
- `source_kind_requires_matching_reference` — FR-F055-02: `kind: 'view'` with a null `view_id` violates the check constraint.
- `source_count_capped_at_twenty` — FR-F055-02: inserting a 21st source for one calendar fires the trigger and fails.
- `publication_expiry_capped_at_thirty_days` — FR-F055-07: `expires_at` 31 days after `created_at` violates the check.
- `one_active_publication_per_calendar` — FR-F055-07: a second row with `revoked_at is null` violates the partial unique index; allowed once the first is revoked.
- `publication_token_hash_unique` — NFR-F055-02: duplicate `token_hash` rejected; the lookup index is partial on `revoked_at is null`.
- `event_window_uses_typed_date_index` — NFR-F055-01: `EXPLAIN` for a 31-day window uses the F007 typed date index on `cells`, not a sequential scan.
- `rollback_drops_calendar_tables` — FR-F055-01: `sqlx migrate revert` removes the three tables and their indexes.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F055/database/`.
