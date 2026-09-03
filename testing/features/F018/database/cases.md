# F018 database cases

File: `testing/features/F018/database/migration_tests.rs`. Flag `F018_FEATURE`.

- `workflow_tables_exist_with_constraints` — T069: `workflows`, `workflow_versions`, `workflow_steps` exist with tenant, version, audit, soft-delete columns and the `state` check constraint.
- `published_version_update_rejected` — FR-F018-06: `UPDATE workflow_versions SET definition = ...` raises `workflow_version_immutable`; `DELETE` raises too.
- `duplicate_version_no_rejected` — FR-F018-07: second `(workflow_id, version_no)` violates the unique index.
- `duplicate_step_index_rejected` — FR-F018-07: two `workflow_steps` with the same `(version_id, index)` rejected.
- `duplicate_workflow_name_same_sheet_rejected` — FR-F018-01: same lower-cased name on one sheet rejected while `deleted_at is null`; allowed after delete.
- `published_version_fk_enforced` — FR-F018-07: `published_version_id` must reference an existing version row.
- `publish_and_outbox_written_in_transaction` — NFR-F018-04: failing outbox insert rolls back the version row.
- `state_index_used_for_list` — NFR-F018-01: `EXPLAIN` on list by `(tenant_id, sheet_id, state)` uses `workflows_tenant_sheet_state_idx`.
- `rollback_drops_tables` — T069: `sqlx migrate revert` removes the three tables and the trigger function.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F018/database/`.
