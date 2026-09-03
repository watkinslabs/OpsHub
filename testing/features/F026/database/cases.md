# F026 database cases

File: `testing/features/F026/database/{migration_tests.rs,constraint_tests.rs}`. Flag `F026_FEATURE`.

- `sso_tables_exist_with_constraints` — T101: `identity_connections`, `identity_connection_domains`, `saml_certificates`, `saml_assertion_ids`, `scim_tokens`, `scim_sync_log`, `group_mappings` exist with tenant, version, audit, and soft-delete columns where specified.
- `domain_unique_across_active_connections` — FR-F026-02: inserting `example.com` for a second active connection violates `identity_connection_domains` primary key; allowed after the first is disabled.
- `one_active_scim_token_per_connection` — FR-F026-09: second unrevoked, unexpired token violates the partial unique index.
- `certificate_fingerprint_unique_per_connection` — FR-F026-06: same PEM twice on one connection rejected; allowed on another connection.
- `assertion_id_replay_key` — FR-F026-04: duplicate `(tenant_id, assertion_id)` rejected; expired rows removed by the cleanup statement.
- `group_mapping_unique_external_id` — FR-F026-14: duplicate `(connection_id, external_id)` rejected.
- `sync_log_index_used_for_recent_entries` — NFR-F026-04: `EXPLAIN` on last 50 entries per connection uses `scim_sync_log(connection_id, occurred_at desc)`.
- `login_audit_written_in_transaction` — FR-F026-08: failing outbox insert rolls back the audit row and the session.
- `rollback_drops_sso_tables` — T101: `sqlx migrate revert` removes the seven tables and indexes.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F026/database/`.
