# F032 database cases

File: `testing/features/F032/database/migration_tests.rs`. Flag `F032_FEATURE`.

- `governance_tables_exist_with_constraints` — T125: `health_models`, `project_health`, `stage_gates`, `stage_gate_decisions`, `project_intake_requests` exist with tenant, version, and audit columns.
- `second_tenant_default_model_rejected` — FR-F032-01: unique partial index on `(tenant_id, scope)` blocks a second `tenant_default` while `deleted_at is null`.
- `colour_check_rejects_unknown_value` — FR-F032-03: `project_health.colour = 'blue'` violates the check; `unknown` is accepted.
- `gate_status_check_and_sequence_unique` — FR-F032-07: `status = 'skipped'` rejected; duplicate `(project_sheet_id, sequence)` rejected.
- `decision_rows_are_insert_only` — FR-F032-09: `UPDATE stage_gate_decisions` raises from the guard trigger; duplicate `(gate_id, attempt)` rejected.
- `intake_status_check` — FR-F032-12: `status = 'archived'` rejected; the six documented statuses accepted.
- `approval_indexes_used_for_sync` — FR-F032-10: `EXPLAIN` on lookup by `approval_id` uses `stage_gates_approval_idx` and `project_intake_requests_approval_idx`.
- `override_stored_as_jsonb_with_expiry` — FR-F032-06: override JSON round-trips `colour`, `reason`, `set_by`, `set_at`, `expires_at`.
- `audit_and_outbox_rows_written_in_transaction` — FR-F032-13: failing outbox insert rolls back the decision write.
- `rollback_drops_tables` — T125: `sqlx migrate revert` removes the five tables, trigger, and indexes.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F032/database/`.
