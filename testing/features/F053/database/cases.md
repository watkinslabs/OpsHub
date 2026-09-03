# F053 database cases

File: `testing/features/F053/database/migration_tests.rs`. Flag `F053_FEATURE`.

- `datamesh_tables_exist_with_constraints` — T209: `datamesh_mappings`, `datamesh_matches`, `datamesh_runs`, `datamesh_conflicts` exist with tenant, version, audit, and soft-delete columns where specified.
- `same_sheet_mapping_rejected` — FR-F053-01: `source_sheet_id = target_sheet_id` violates the check constraint.
- `duplicate_mapping_name_rejected` — FR-F053-01: case-insensitive duplicate name in a workspace violates the partial unique index while `deleted_at is null`.
- `policy_and_kind_checks` — FR-F053-01, FR-F053-08: `unmatched_policy = 'merge'` and conflict `kind = 'other'` rejected.
- `target_row_matched_once` — FR-F053-03: second match row with the same `(mapping_id, target_row_id)` rejected; `(mapping_id, source_row_id)` is the primary key.
- `second_active_run_rejected` — FR-F053-05: second `queued`/`running` run for a mapping violates the partial unique index.
- `succeeded_cursor_unique_per_mapping` — FR-F053-05: second `succeeded` run with the same `source_version_cursor` rejected.
- `duplicate_open_conflict_rejected` — FR-F053-08: same rows, column, and kind while `open` rejected; allowed after `resolved`.
- `listener_index_used_for_source_lookup` — FR-F053-09: `EXPLAIN` on enabled mappings by `source_sheet_id` uses `datamesh_mappings_source_idx`.
- `conflicts_index_used_for_list` — NFR-F053-01: `EXPLAIN` on open conflicts newest first uses `datamesh_conflicts_mapping_status_idx`.
- `audit_and_outbox_written_in_transaction` — FR-F053-11: failing outbox insert rolls back the mapping write.
- `rollback_drops_tables` — T209: `sqlx migrate revert` removes the four tables and indexes.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F053/database/`.
