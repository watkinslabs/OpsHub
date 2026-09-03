# F054 database cases

File: `testing/features/F054/database/migration_tests.rs`. Flag `F054_FEATURE`.

- `bridge_tables_exist_with_constraints` — T213: `bridge_flows`, `bridge_flow_versions`, `bridge_runs`, `bridge_run_steps` exist with tenant, version, audit, and soft-delete columns where specified.
- `duplicate_flow_name_rejected` — FR-F054-01: same name (case-insensitive) in one workspace while `deleted_at is null` violates the partial unique index; allowed after delete.
- `flow_version_unique_per_flow` — FR-F054-05: second `(flow_id, 1)` row rejected; versions are never updated (trigger raises on `UPDATE`).
- `run_idempotency_key_unique` — FR-F054-06: duplicate `(tenant_id, flow_id, idempotency_key)` rejected.
- `step_count_check_enforced` — FR-F054-01: `draft_steps` with 51 elements or 0 elements violates the check.
- `run_and_step_status_checks` — FR-F054-07: `status = 'exploded'` rejected on runs and steps.
- `step_attempt_rows_unique` — FR-F054-07: duplicate `(run_id, step_id, attempts)` rejected; three attempts stored as three rows.
- `run_list_uses_status_index` — NFR-F054-01: `EXPLAIN` on the filtered list uses `bridge_runs_tenant_status_created_idx`.
- `waiting_runs_partial_index_used` — FR-F054-09: resume scan uses `bridge_runs_waiting_idx`.
- `outbox_written_in_transaction` — FR-F054-12: failing outbox insert rolls back the run enqueue.
- `rollback_drops_tables` — T213: `sqlx migrate revert` removes the four tables and indexes.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F054/database/`.
