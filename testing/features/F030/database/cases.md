# F030 database cases

File: `testing/features/F030/database/{migration_tests.rs,constraint_tests.rs,retention_tests.rs}`. Flag `F030_FEATURE`.

- `connectors_tables_exist_with_constraints` — T117: `syncs`, `sync_mappings`, `sync_runs`, `sync_cursors`, `sync_conflicts`, `sync_record_links` exist with tenant, version, and audit columns where specified.
- `active_sync_tuple_unique` — NFR-F030-05: a second non-paused sync on the same `(connection_id, source_object, target_sheet_id, direction)` is rejected; allowed once the first is `paused`.
- `mapping_unique_per_direction` — FR-F030-05: duplicate `(sync_id, external_field, direction)` and duplicate `(sync_id, column_id, direction)` are both rejected.
- `mapping_cap_enforced_at_three_hundred` — NFR-F030-05: inserting a 301st mapping for one sync violates the statement trigger.
- `deletion_column_required_for_mark_deleted` — FR-F030-15: `deletion_policy = 'mark_deleted'` with null `deletion_column_id` violates the check constraint.
- `run_state_check_rejects_unknown_state` — FR-F030-11: `sync_runs.state = 'retrying'` violates the check; the six legal states insert.
- `cursor_primary_key_is_sync_and_direction` — FR-F030-09: a second `sync_cursors` row for the same `(sync_id, direction)` violates the primary key.
- `record_link_unique_per_sync_row` — FR-F030-12: duplicate `(sync_id, external_id)` and duplicate `(sync_id, row_id)` are both rejected.
- `cascade_delete_removes_children` — FR-F030-02: deleting a sync removes its mappings, runs, cursors, conflicts, and record links.
- `conflict_index_used_for_open_queue` — NFR-F030-01: `EXPLAIN` on the open-conflict listing uses `sync_conflicts(sync_id, state, detected_at desc)`.
- `run_history_index_used` — NFR-F030-01: `EXPLAIN` on the last 20 runs uses `sync_runs(sync_id, started_at desc)`.
- `retention_sweep_removes_old_runs_and_samples` — FR-F030-11, NFR-F030-02: runs older than 90 days deleted, `debug_payloads` samples expired at 7 days, resolved conflicts removed at 180 days.
- `rollback_drops_connectors_tables` — T117: `sqlx migrate revert` removes the six tables and their indexes and leaves the F029 `integrations` tables intact.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F030/database/`.
