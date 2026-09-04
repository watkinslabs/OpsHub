# F063 database cases

File: `testing/features/F063/database/{migration_tests.rs,constraint_tests.rs}`. Flag `F063_FEATURE`. PostgreSQL 18.

- `entra_tables_exist_with_constraints` — T249: `entra_connections`, `entra_group_map` and `entra_mail_log` exist with tenant, version and audit columns as specified.
- `one_connection_per_tenant` — FR-F063-02: a second `entra_connections` row for the same `tenant_id` violates the unique key.
- `cloud_check_rejects_unknown_value` — FR-F063-02: `cloud: 'germany'` violates the check; `global`, `us_gov` and `china` are accepted.
- `capabilities_subset_check_rejects_unknown` — FR-F063-02: `capabilities: '{teams}'` violates the check; subsets of `{sign_in,group_sync,mail}` are accepted.
- `sender_mailbox_required_when_mail_present` — FR-F063-08: `mail` in `capabilities` with a null `sender_mailbox` is rejected.
- `group_map_unique_per_connection_and_directory_group` — FR-F063-06: duplicate `(connection_id, directory_group_id)` rejected.
- `group_map_target_kind_check` — FR-F063-06: `target_kind` outside `{group,role}` rejected.
- `group_map_cascades_on_connection_delete` — FR-F063-10: deleting the connection removes its mapping rows and leaves `users` and `groups` untouched.
- `mail_log_index_used_for_recent_calls` — NFR-F063-04: `EXPLAIN` on the last 50 calls uses `entra_mail_log(tenant_id, occurred_at desc)`; the status filter uses `entra_mail_log(tenant_id, status_code)`.
- `mail_log_stores_domain_not_address` — NFR-F063-02: `recipient_domain` holds `contoso.com` and the table has no recipient address, subject or body column.
- `mail_log_retention_sweep_removes_rows_past_90_days` — NFR-F063-02: the F027 sweep deletes `entra_mail_log` rows older than 90 days.
- `rollback_drops_entra_tables` — T249: `sqlx migrate revert` removes the three tables and their indexes.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F063/database/`.
