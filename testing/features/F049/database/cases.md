# F049 database cases

File: `testing/features/F049/database/migration_tests.rs`. Flag `F049_FEATURE`.

- `i18n_tables_exist_with_checks` — T193: `tenant_locales`, `user_locales`, `message_catalogs` exist with version, audit, and check constraints on `locale`, `hour_cycle`, `first_day_of_week`.
- `tenant_creation_seeds_locale_row` — FR-F049-04: inserting a `tenants` row fires the trigger and creates a `tenant_locales` row with `en-US`, `UTC`, `monday`, `h12`, `USD`.
- `unsupported_locale_rejected_by_check` — FR-F049-02: `locale = 'xx-YY'` on either settings table violates the check constraint.
- `user_locale_primary_key_per_tenant_user` — FR-F049-03: second row for the same `(tenant_id, user_id)` rejected; `user_id` foreign key blocks orphan rows.
- `catalog_messages_must_be_object` — FR-F049-08: inserting `messages = '[]'` violates `jsonb_typeof = 'object'`; `(locale, version)` duplicate rejected.
- `catalog_latest_version_index_used` — NFR-F049-01: `EXPLAIN` for latest catalog by locale uses `message_catalogs_locale_version_idx`.
- `text_columns_store_nfc` — FR-F049-07: NFD input written through the domain layer reads back as NFC bytes.
- `audit_and_outbox_rows_written_in_transaction` — FR-F049-12: failing outbox insert rolls back the `user_locales` update.
- `rollback_drops_tables` — T193: `sqlx migrate revert` removes the trigger, three tables, and indexes.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F049/database/`.
