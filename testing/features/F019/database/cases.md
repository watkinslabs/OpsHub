# F019 database cases

File: `testing/features/F019/database/migration_tests.rs`. Flag `F019_FEATURE`.

- `runtime_tables_exist_with_constraints` — T073: `workflow_runs`, `workflow_run_steps`, `workflow_triggers`, `inbound_webhooks`, `inbound_webhook_deliveries` exist with tenant, version, audit columns and status check constraints.
- `duplicate_idempotency_key_rejected` — FR-F019-02: second `(tenant_id, idempotency_key)` violates the unique index.
- `duplicate_step_attempt_rejected` — FR-F019-05: two rows with the same `(run_id, index, attempt)` rejected.
- `depth_over_five_rejected` — FR-F019-10: `depth: 6` violates the check constraint.
- `version_fk_restricts_purge` — FR-F019-01: deleting a `workflow_versions` row referenced by a run fails with `on delete restrict`.
- `duplicate_delivery_id_rejected` — FR-F019-04: second `(webhook_id, delivery_id)` rejected.
- `active_status_index_used_for_dequeue` — NFR-F019-01: `EXPLAIN` on dequeue by `(tenant_id, status, queued_at)` uses the partial index.
- `next_fire_index_used_for_scheduler` — FR-F019-03: `EXPLAIN` on `next_fire_at <= now()` uses `workflow_triggers_next_fire_idx`.
- `run_row_and_outbox_written_in_transaction` — NFR-F019-04: failing outbox insert rolls back the run insert.
- `rollback_drops_tables` — T073: `sqlx migrate revert` removes the five tables and indexes.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F019/database/`.
