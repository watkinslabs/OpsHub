# F036 database cases

File: `testing/features/F036/database/migration_tests.rs`. Flag `F036_FEATURE`.

- `sharing_tables_exist_with_constraints` — T141: `shares`, `share_links`, `guest_invitations`, `guest_users` exist with tenant, version, and audit columns and the role, effect, and target-kind checks.
- `share_unique_per_target_principal` — FR-F036-02: duplicate `(tenant_id, target_kind, target_id, principal_kind, principal_id)` rejected.
- `guest_role_check_enforced` — FR-F036-06: `principal_kind = 'guest'` with `role = 'owner'` violates the check; `viewer` succeeds.
- `link_role_and_expiry_checks_enforced` — FR-F036-09: `share_links.role = 'editor'` rejected; `expires_at` 31 days after `created_at` rejected; 30 days accepted.
- `link_and_invitation_token_hash_unique` — NFR-F036-02: duplicate `token_hash` in `share_links` or `guest_invitations` rejected; column type is `bytea` of length 32.
- `guest_user_unique_per_tenant_email` — FR-F036-07: second `guest_users` row for the same `(tenant_id, email)` rejected; different tenant allowed.
- `share_lookup_uses_target_index` — NFR-F036-01: `EXPLAIN` on the grants-for-chain query uses `shares_tenant_target_idx` and `shares_tenant_principal_idx`.
- `expiry_partial_indexes_used_by_sweeper` — FR-F036-13: sweeper queries use `shares_expires_idx`, `share_links_expires_idx`, and `guest_invitations_expires_idx`.
- `audit_and_outbox_rows_written_in_transaction` — FR-F036-15: failing outbox insert rolls back the grant.
- `rollback_drops_tables` — T141: `sqlx migrate revert` removes the four tables and indexes.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F036/database/`.
