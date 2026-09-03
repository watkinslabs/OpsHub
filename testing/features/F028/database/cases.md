# F028 database cases

File: `testing/features/F028/database/{migration_tests.rs,constraint_tests.rs}`. Flag `F028_FEATURE`.

- `public_api_tables_exist_with_constraints` — T109: `api_applications`, `webhooks`, `webhook_deliveries` exist with tenant, version, audit, and soft-delete columns.
- `application_name_unique_per_tenant` — FR-F028-02: duplicate `lower(name)` while `deleted_at is null` rejected; allowed after soft delete.
- `application_client_id_unique` — FR-F028-02: duplicate `(tenant_id, client_id)` rejected.
- `delivery_unique_per_webhook_event` — NFR-F028-04: second `(webhook_id, event_id)` with null `replay_of` rejected; replay rows allowed.
- `attempt_count_capped_at_five` — FR-F028-10: `attempt_count 6` violates the check constraint.
- `retry_index_used_for_due_deliveries` — NFR-F028-01: `EXPLAIN` on due deliveries uses `webhook_deliveries(next_attempt_at) where status = 'failed'`.
- `secret_stored_as_ciphertext` — NFR-F028-02: `secret_ciphertext` never equals the plaintext and `secret_key_id` references the envelope key.
- `rollback_drops_public_api_tables` — T109: `sqlx migrate revert` removes the three tables and indexes.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F028/database/`.
