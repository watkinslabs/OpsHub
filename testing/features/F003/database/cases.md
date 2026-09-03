# F003 database cases

File: `testing/features/F003/database/{migration_tests.rs,audit_tests.rs}`. Flag `F003_FEATURE`.

- `authz_tables_exist_with_constraints` — T009: `roles`, `role_bindings`, `resource_acls`, partitioned `audit_events` exist with the columns from ticket section 4.
- `system_roles_seeded_per_tenant` — FR-F003-01: inserting a tenant creates seven `is_system` roles with the fixed permission sets.
- `role_slug_unique_per_tenant` — FR-F003-02: second `reviewer` in the same tenant rejected; allowed in tenant B.
- `acl_entry_unique_per_principal_effect` — FR-F003-04: duplicate `(resource, principal, effect)` rejected by `resource_acls_entry_idx`.
- `audit_update_and_delete_raise_immutable` — FR-F003-10: `UPDATE` and `DELETE` on `audit_events` raise `audit_immutable`.
- `audit_partitions_created_for_four_months` — FR-F003-10: current plus three future monthly partitions exist after migration.
- `partition_job_creates_next_month` — FR-F003-10: running `PartitionJob` with the clock advanced adds the missing partition idempotently.
- `audit_list_uses_partition_pruning` — NFR-F003-01: `EXPLAIN` for a 7-day range touches one partition and `audit_events_tenant_occurred_idx`.
- `acl_lookup_uses_resource_index` — NFR-F003-01: `EXPLAIN` on effective ACL uses `resource_acls_tenant_resource_idx`.
- `rollback_drops_tables` — T009: `sqlx migrate revert` removes tables, triggers, seed function, and partitions.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F003/database/`.
