# F002 database cases

File: `testing/features/F002/database/migration_tests.rs`. Flag `F002_FEATURE`.

- `tenants_tables_exist_with_constraints` — T005: `tenants`, `users`, `groups`, `group_members` exist with tenant, version, audit, and soft-delete columns; `citext` extension installed.
- `duplicate_slug_rejected` — FR-F002-02: `tenants_slug_idx` blocks a second `acme` while `deleted_at is null`.
- `duplicate_email_same_tenant_rejected_case_insensitive` — FR-F002-05: `citext` unique index rejects `OPS@acme.test` after `ops@acme.test`; same email in tenant B is allowed.
- `duplicate_group_name_rejected_lower` — FR-F002-09: `groups_tenant_lower_name_idx` rejects `Finance` after `finance`.
- `cross_tenant_group_member_rejected_by_trigger` — FR-F002-10: inserting a tenant B user into a tenant A group raises `tenant_mismatch`.
- `invalid_region_rejected_by_check` — FR-F002-02: `region = 'eu-west'` violates the check constraint.
- `user_delete_restricted_group_delete_cascades` — FR-F002-08: deleting a user with memberships fails with `restrict`; deleting a group removes its `group_members`.
- `audit_and_outbox_rows_written_in_transaction` — FR-F002-12: a failing outbox insert rolls back the user insert.
- `user_list_uses_status_display_name_index` — NFR-F002-01: `EXPLAIN` on the users list uses `users_tenant_status_display_name_idx`.
- `rollback_drops_tables_and_extension` — T005: `sqlx migrate revert` removes the trigger, four tables, and `citext`.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F002/database/`.
