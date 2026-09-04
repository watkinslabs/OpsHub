# F070 database cases

File: `testing/features/F070/database/{migration_tests.rs,constraint_tests.rs,index_tests.rs}`. Flag `F070_FEATURE`.

- `trash_entries_exists_with_constraints` — T277, FR-F070-03: the table carries `tenant_id`, `kind`, `item_id`, `title`, parent pair, `deleted_at`, `deleted_by`, `expires_at`, `state`, `blocked_reason`, `held`, `source_event_id`, `source_version`, `projection_epoch` and `projected_at`, and no `version` column, because a projection has nothing to lock.
- `duplicate_kind_and_item_rejected` — FR-F070-03: a second row for the same `(tenant_id, kind, item_id)` violates the unique key, which is what makes the projector idempotent.
- `upsert_predicate_ignores_lower_source_version` — FR-F070-03: the `on conflict do update ... where excluded.source_version > trash_entries.source_version` statement leaves the newer row intact.
- `state_requires_blocked_reason` — FR-F070-07: `state = 'blocked'` with a null `blocked_reason` violates the check; `held` state with `held = false` violates its check.
- `parent_pair_is_all_or_nothing` — FR-F070-07: `parent_kind` set with a null `parent_id` violates the check constraint.
- `no_check_constraint_pins_kind` — FR-F070-05: inserting the test-double kind through the repository succeeds without a migration, while the same insert with an unregistered key is refused by `upsert_from_event`, so the closed set lives in the registry rather than in DDL.
- `sweep_index_used_for_expiry_scan` — FR-F070-08: `EXPLAIN` of the expiry batch uses `trash_entries(tenant_id, expires_at) where state <> 'held'`.
- `blocked_children_index_used_for_parent_restore` — FR-F070-07: `EXPLAIN` of the blocked-children lookup uses `trash_entries(tenant_id, parent_kind, parent_id) where state = 'blocked'`.
- `epoch_index_used_for_previous_epoch_delete` — FR-F070-04: `delete_previous_epoch` is a single indexed statement, not a scan.
- `deleted_by_foreign_key_restricts` — NFR-F070-02: deleting a user row referenced by an entry is refused, so an entry never loses its attribution.
- `rollback_drops_trash_entries` — T277: `sqlx migrate revert` removes the table and its six indexes and touches no other feature's data.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F070/database/`.
