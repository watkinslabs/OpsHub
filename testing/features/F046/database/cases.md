# F046 database cases

File: `testing/features/F046/database/migration_tests.rs`. Flag `F046_FEATURE`.

- `realtime_tables_exist_with_constraints` — T181: `collaboration_sessions`, `presence_leases`, `document_changes` exist with tenant columns, `target_type` check, and `(document_id, rev)` primary key.
- `duplicate_change_hash_rejected` — FR-F046-05: second `(document_id, hash)` violates the unique index.
- `duplicate_rev_rejected` — FR-F046-04: second `(document_id, rev)` violates the primary key.
- `lease_requires_session` — FR-F046-03: `presence_leases` insert with unknown `session_id` fails the foreign key.
- `change_requires_existing_document` — FR-F046-04: `document_changes` insert for a missing document fails; document delete with changes is restricted.
- `advisory_lock_serializes_rev_assignment` — FR-F046-04: two transactions appending concurrently → revs N+1 and N+2, never equal.
- `active_session_index_used` — NFR-F046-01: `EXPLAIN` on sessions by `(tenant_id, target_type, target_id) where closed_at is null` uses the partial index.
- `lease_expiry_index_used_for_sweep` — FR-F046-03: `EXPLAIN` on `expires_at < now()` uses `presence_leases_expires_idx`.
- `change_and_outbox_written_in_transaction` — NFR-F046-04: failing outbox insert rolls back the change row.
- `rollback_drops_tables` — T181: `sqlx migrate revert` removes the three tables and indexes.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F046/database/`.
