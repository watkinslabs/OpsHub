# F048 database cases

File: `testing/features/F048/database/migration_tests.rs`. Flag `F048_FEATURE`.

- `entitlement_tables_exist_with_constraints` — T189: `entitlements`, `feature_flags`, `flag_overrides` exist with tenant (where applicable), version, and audit columns; `feature_flags` has no `tenant_id`.
- `duplicate_entitlement_per_module_rejected` — FR-F048-02: second `(tenant_id, 'data-shuttle')` row violates the unique index.
- `trial_without_end_date_rejected` — FR-F048-02: `state = 'trial'` with null `trial_ends_at` violates the check constraint.
- `retired_flag_requires_cleanup_ticket` — FR-F048-05: `rollout_state = 'retired'` with null `cleanup_ticket` or short `disable_procedure` violates the check.
- `rollout_percent_bounded` — FR-F048-05: `rollout_percent = 101` rejected.
- `override_cascades_on_flag_delete` — FR-F048-06: deleting a flag removes its overrides; duplicate `(tenant_id, flag_key)` rejected.
- `seed_registry_matches_plan` — FR-F048-03: seeded keys equal `F048_FEATURE`, `F039_FEATURE`, `F040_FEATURE`, `F050_FEATURE`..`F057_FEATURE`, all `draft`.
- `expired_override_index_used_by_prune` — FR-F048-13: `EXPLAIN` on the prune query uses `flag_overrides_expires_idx`; prune deletes only expired, non-suspended rows.
- `audit_and_outbox_written_in_transaction` — FR-F048-11: failing outbox insert rolls back the entitlement upsert.
- `rollback_drops_tables` — T189: `sqlx migrate revert` removes the three tables, indexes, and seed rows.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F048/database/`.
