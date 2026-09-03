# F020 database cases

File: `testing/features/F020/database/migration_tests.rs`. Flag `F020_FEATURE`.

- `approval_tables_exist_with_constraints` — T077: `approvals`, `approval_decisions`, `approval_policies`, `escalation_timers` exist with tenant, version, audit columns and status/kind/on_expiry check constraints.
- `duplicate_decision_same_approver_rejected` — FR-F020-03: second `(approval_id, approver_id)` violates the unique index.
- `decision_update_rejected` — FR-F020-12: `UPDATE approval_decisions` raises `approval_decision_immutable`; `DELETE` raises too.
- `duplicate_timer_level_rejected` — FR-F020-08: second `(approval_id, kind, level)` rejected.
- `policy_constraints_enforced` — FR-F020-07: `max_escalations: 4` and `on_expiry: 'later'` rejected by check constraints; duplicate policy name per tenant rejected.
- `approvers_gin_index_used_for_assigned_to_me` — NFR-F020-01: `EXPLAIN` on `approvers @> '[{"user_id": ...}]'` uses the GIN index.
- `unfired_timer_index_used_for_sweep` — NFR-F020-04: `EXPLAIN` on `fired_at is null and fire_at <= now()` uses the partial index.
- `decision_and_outbox_written_in_transaction` — FR-F020-04: failing outbox insert rolls back the decision row and status change.
- `rollback_drops_tables` — T077: `sqlx migrate revert` removes the four tables and the trigger function.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F020/database/`.
