# F034 database cases

File: `testing/features/F034/database/{migration_tests.rs,constraint_tests.rs,index_tests.rs}` against CI PostgreSQL 18. Migration `services/api/migrations/<ts>_workload_create_tables.sql`. Flag `F034_FEATURE`.

- `workload_tables_exist_with_columns_and_defaults` — FR-F034-02, FR-F034-04, FR-F034-10: `time_entries`, `effort_summaries`, and `workload_conflicts` exist; `reconciliation_state` defaults to `none`, `workload_conflicts.status` to `open`, `effort_summaries.stale` to false.
- `hours_check_rejects_out_of_range_and_non_quarter_values` — FR-F034-04: 0.1, 24.25, and 6.1 are rejected; 0.25, 6.25, and 24.00 are accepted.
- `source_check_requires_external_ref_pairing` — FR-F034-06: `source = 'external'` without `source_system` or `external_id` is rejected, and `source = 'native'` with either set is rejected.
- `external_ref_partial_unique_index_blocks_duplicates` — FR-F034-06: a second live row with the same `(tenant_id, source_system, external_id)` is rejected; the same values are reusable after the first row is soft-deleted.
- `reconciliation_state_check_limits_values` — FR-F034-07: only `none`, `pending`, `accepted`, `rejected`, and `superseded` are accepted.
- `reconciliation_fields_are_immutable_once_set` — FR-F034-14: updating `reconciled_by`, `reconciled_at`, `resolution`, or `reason` on a reconciled row raises from the statement trigger; the first write succeeds.
- `superseded_native_row_is_retained_and_readable` — FR-F034-14: after `accept_external` the native row still exists with `superseded_by` pointing at the external entry.
- `conflict_unique_per_resource_and_period` — FR-F034-02: a second `(resource_id, period_start)` row is rejected; the upsert updates `over_hours` and `allocation_ids` instead.
- `conflict_status_check_limits_values` — FR-F034-02: only `open` and `resolved` are accepted.
- `effort_summary_primary_key_is_tenant_scope_and_period` — FR-F034-10: a duplicate `(tenant_id, scope, scope_id, period_start)` is rejected; `source_versions` is required.
- `foreign_keys_restrict_resource_row_and_sheet_deletes` — FR-F034-04: deleting a `resources`, `rows`, or `sheets` parent with entries raises a restrict violation.
- `entry_indexes_are_used_for_resource_and_row_ranges` — NFR-F034-01: `EXPLAIN` for a single-resource date range uses `time_entries(resource_id, entry_date) where deleted_at is null`, and the pending queue uses the partial `reconciliation_state` index.
- `audit_rows_written_for_every_workload_mutation` — FR-F034-11: `time-entry.create`, `time-entry.update`, `time-entry.delete`, `time-entry.import`, `time-entry.reconcile`, `workload-conflict.open`, and `workload-conflict.resolve` appear in `audit_events` with before and after states.
- `migration_down_drops_tables_and_trigger` — FR-F034-14: the down migration removes the three tables and the immutability trigger and leaves no orphaned type or index.

Evidence: migration logs, `EXPLAIN` output, and constraint failures under `testing/evidence/F034/database/`.
