# F005 database cases

File: `testing/features/F005/database/migration_tests.rs`. Flag `F005_FEATURE`.

- `workspace_tables_exist_with_constraints` — T017: `workspaces`, `workspace_members`, `folders` exist with tenant, version, `tree_version`, audit, and soft-delete columns; `role` and `subject_kind` check constraints present.
- `duplicate_workspace_name_rejected` — FR-F005-02: `workspaces_tenant_name_idx` blocks case-insensitive duplicate while `deleted_at is null`; allows after delete.
- `folder_sibling_name_rejected` — FR-F005-08: `folders_sibling_name_idx` blocks "Q4" and "q4" under one parent and at root (null parent coalesced).
- `folder_depth_above_ten_rejected` — FR-F005-08: `depth = 11` violates the check constraint.
- `cycle_trigger_rejects_descendant_parent` — FR-F005-09: updating `parent_folder_id` to a descendant raises from `folders_check_cycle`.
- `folder_requires_existing_workspace_and_parent` — FR-F005-08: foreign keys reject orphan folders; `on delete restrict` blocks hard delete of a parent with children.
- `path_index_used_for_subtree_query` — NFR-F005-01: `EXPLAIN` on `where path like '<id>/%'` uses `folders_workspace_path_idx`.
- `soft_delete_cascade_and_restore_round_trip` — FR-F005-05, FR-F005-10: workspace delete stamps folders; restore clears; ids unchanged.
- `audit_and_outbox_rows_written_in_transaction` — FR-F005-13, NFR-F005-04: failing outbox insert rolls back the folder move and path rewrite.
- `rollback_drops_tables_and_trigger` — T017: `sqlx migrate revert` removes the three tables, indexes, and `folders_check_cycle`.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F005/database/`.
