# F052 database cases

File: `testing/features/F052/database/migration_tests.rs`. Flag `F052_FEATURE`.

- `shuttle_tables_exist_with_constraints` — T205: `shuttle_flows`, `shuttle_schedules`, `shuttle_runs`, `shuttle_archives` exist with tenant, version, audit, and soft-delete columns where specified.
- `duplicate_flow_name_rejected` — FR-F052-01: case-insensitive duplicate name in a workspace violates the partial unique index while `deleted_at is null`.
- `direction_and_status_checks` — FR-F052-01, FR-F052-07: `direction = 'both'` and `status = 'done'` rejected by check constraints.
- `second_active_run_rejected` — FR-F052-06: inserting a second `queued` or `running` run for a flow violates the partial unique index; a `succeeded` run does not.
- `succeeded_checksum_unique_per_flow` — FR-F052-07: second `succeeded` non-replay run with the same `file_checksum` rejected; replay runs exempt.
- `schedule_index_used_for_due_query` — FR-F052-03: `EXPLAIN` on `next_run_at <= now()` uses `shuttle_schedules_next_run_idx`.
- `retention_index_used_for_purge` — FR-F052-08: `EXPLAIN` on the purge query uses `shuttle_archives_retain_idx`; one archive per run enforced.
- `run_history_index_used` — FR-F052-10: `EXPLAIN` on the run list uses `shuttle_runs_flow_created_idx`.
- `audit_and_outbox_written_in_transaction` — FR-F052-11: failing outbox insert rolls back the flow write.
- `rollback_drops_tables` — T205: `sqlx migrate revert` removes the four tables and indexes.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F052/database/`.
