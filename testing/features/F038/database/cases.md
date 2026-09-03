# F038 database cases

File: `testing/features/F038/database/migration_tests.rs`. Flag `F038_FEATURE`.

- `auth_tables_exist_with_constraints` — T149: `sessions`, `refresh_tokens`, `mfa_factors`, `api_tokens`, `security_policies`, `rate_limit_buckets` exist with the columns from ticket section 4.
- `policy_default_row_created_by_trigger` — FR-F038-14: inserting a tenant creates a `security_policies` row with defaults 43200/3600/2592000/7776000.
- `refresh_token_hash_unique` — NFR-F038-02: duplicate `token_hash` rejected by `refresh_tokens_hash_idx`.
- `api_token_hash_unique` — NFR-F038-02: duplicate `token_hash` rejected by `api_tokens_hash_idx`.
- `webauthn_credential_id_unique` — FR-F038-08: duplicate `credential_id` rejected; null allowed for TOTP rows.
- `session_delete_cascades_refresh_tokens` — FR-F038-05: deleting a session removes its refresh tokens.
- `policy_range_checks_enforced` — FR-F038-14: `idle_timeout_seconds = 100` violates the check constraint.
- `session_lookup_uses_index` — NFR-F038-01: `EXPLAIN` on cookie lookup uses the primary key; expiry sweep uses `sessions_tenant_expires_idx`.
- `rate_limit_bucket_upsert_single_statement` — FR-F038-13: `INSERT ... ON CONFLICT DO UPDATE` refills and decrements atomically under 50 concurrent calls.
- `rollback_drops_tables` — T149: `sqlx migrate revert` removes the six tables and the policy trigger.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F038/database/`.
