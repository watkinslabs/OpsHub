# F017 database cases

File: `testing/features/F017/database/migration_tests.rs`. Flag `F017_FEATURE`.

- `files_tables_exist_with_constraints` — T065: `files`, `file_versions`, `file_scans`, `proofs`, `proof_decisions`, `file_upload_tickets` exist with tenant, version, audit, and soft-delete columns and the `target_kind` check.
- `scan_state_check_enforced` — FR-F017-04: inserting `scan_state = 'unknown'` or `preview_state = 'done'` is rejected.
- `file_version_primary_key_unique` — FR-F017-08: duplicate `(file_id, version)` rejected; `on delete restrict` blocks hard delete of a file with versions.
- `storage_key_unique_per_tenant` — NFR-F017-02: two versions sharing a `storage_key` in one tenant are rejected.
- `single_open_proof_per_file` — FR-F017-11: partial unique index `proofs(file_id) where state = 'open'` rejects a second open proof and allows one after supersession.
- `proof_decision_unique_per_reviewer` — FR-F017-12: duplicate `(proof_id, reviewer_id)` rejected; deleting the proof cascades decisions.
- `reviewer_array_bounds_enforced` — FR-F017-11: empty array and 21 reviewers violate the check constraint.
- `target_file_list_uses_index` — NFR-F017-01: `EXPLAIN` on the target list uses `files_tenant_target_created_idx` with the `deleted_at is null` predicate.
- `pending_scan_partial_index_used` — NFR-F017-04: the worker's pending-version query uses `file_versions_tenant_pending_idx`.
- `audit_and_outbox_rows_written_in_transaction` — FR-F017-15: failing outbox insert rolls back the `file_versions` write.
- `rollback_drops_tables` — T065: `sqlx migrate revert` removes the six tables and indexes.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F017/database/`.
