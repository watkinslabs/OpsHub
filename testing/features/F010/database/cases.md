# F010 database cases

File: `testing/features/F010/database/migration_tests.rs`. Flag `F010_FEATURE`.

- `dataio_tables_exist_with_constraints` — T037: `search_documents`, `import_jobs`, `import_rows`, `export_jobs` exist with tenant, version, audit columns and the `kind`, `status`, `duplicate_strategy`, `format` check constraints.
- `search_body_gin_index_used` — NFR-F010-01: `EXPLAIN` on the search query uses `search_documents_body_idx` and `search_documents_body_simple_idx`.
- `search_document_primary_key_per_kind` — FR-F010-03: duplicate `(tenant_id, kind, entity_id)` rejected; same `entity_id` with different `kind` allowed.
- `stale_source_version_upsert_is_noop` — FR-F010-03: upsert with lower `source_version` leaves `body` and `indexed_at` unchanged.
- `import_rows_target_row_unique_per_job` — FR-F010-09: two `import_rows` with the same `target_row_id` for one `import_id` violate the partial unique index.
- `import_cursor_required_while_committing` — FR-F010-08: setting status `committing` with null `cursor` violates the check constraint.
- `export_storage_key_required_when_completed` — FR-F010-13: status `completed` with null `storage_key` rejected.
- `export_expiry_index_used_by_sweep` — FR-F010-15: `EXPLAIN` on the expiry sweep query uses `export_jobs_expires_at_idx`.
- `tenant_predicate_on_every_dataio_query` — NFR-F010-02: query log for search, import, export handlers shows `tenant_id =` on every statement.
- `rollback_drops_tables` — T037: `sqlx migrate revert` removes the four tables and GIN indexes.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F010/database/`.
