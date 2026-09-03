# F033 database cases

File: `testing/features/F033/database/migration_tests.rs`. Flag `F033_FEATURE`.

- `resource_tables_exist_with_constraints` — T129: `resources`, `resource_skills`, `resource_availability`, `cost_rates`, `allocations` exist with tenant, version, audit, and soft-delete columns; `btree_gist` installed.
- `duplicate_active_user_link_rejected` — FR-F033-01: partial unique index blocks a second active resource with the same `user_id`; allows when the first is inactive or deleted.
- `fte_and_level_checks` — FR-F033-01, FR-F033-03: `fte 1.5` and `level 6` violate checks.
- `availability_overlap_rejected_by_exclusion` — FR-F033-04: overlapping date ranges for one resource violate `resource_availability_no_overlap`; adjacent ranges are allowed.
- `cost_rate_overlap_rejected_by_exclusion` — FR-F033-05: overlapping effective ranges violate `cost_rates_no_overlap`; open-ended rate blocks any later rate.
- `allocation_planned_check_and_range_check` — FR-F033-08: both or neither of hours/percent rejected; `end_date < start_date` and 367-day span rejected.
- `allocation_foreign_keys_restrict` — FR-F033-08: unknown `resource_id`, `project_sheet_id`, or `row_id` rejected; deleting a resource with allocations blocked.
- `allocation_gist_index_used_for_overlap` — NFR-F033-01: `EXPLAIN` on the overlap query uses `allocations_resource_daterange_gist`.
- `audit_and_outbox_rows_written_in_transaction` — NFR-F033-04: failing outbox insert rolls back the allocation write.
- `rollback_drops_tables` — T129: `sqlx migrate revert` removes the five tables, exclusion constraints, and indexes.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F033/database/`.
