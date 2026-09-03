# F027 database cases

File: `testing/features/F027/database/{migration_tests.rs,constraint_tests.rs}`. Flag `F027_FEATURE`.

- `compliance_tables_exist_with_constraints` — T105: `retention_policies`, `legal_holds`, `tenant_exports`, `purge_requests`, `purge_batches`, `access_reviews` exist with tenant, version, and audit columns.
- `retention_policy_unique_per_kind` — FR-F027-01: second `(tenant_id, kind)` row rejected.
- `purge_after_less_than_soft_delete_rejected` — FR-F027-01: `purge_after_days 10` with `soft_delete_days 30` violates the check constraint.
- `audit_events_policy_floor_enforced` — FR-F027-01: `kind = 'audit_events'` with `purge_after_days 100` rejected by the check.
- `one_running_export_per_tenant` — FR-F027-06: second `queued` export violates the partial unique index; allowed after the first is `completed`.
- `purge_completed_requires_confirmed_at` — FR-F027-10: trigger rejects `status = 'completed'` with null `confirmed_at`.
- `purge_batches_checkpoint_key` — NFR-F027-04: duplicate `(purge_id, batch_no)` rejected; resume query reads max `batch_no`.
- `active_hold_index_used` — FR-F027-04: `EXPLAIN` on `is_held` uses `legal_holds(tenant_id, scope_kind, scope_id) where released_at is null`.
- `rollback_drops_compliance_tables` — T105: `sqlx migrate revert` removes the six tables and the trigger.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F027/database/`.
