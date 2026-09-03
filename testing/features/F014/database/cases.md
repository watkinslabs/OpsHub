# F014 database cases

File: `testing/features/F014/database/migration_tests.rs`. Flag `F014_FEATURE`.

- `forms_tables_exist_with_constraints` — T053: `forms`, `form_versions`, `form_fields`, `form_submissions` exist with tenant, version, audit, and soft-delete columns.
- `version_number_unique_per_form` — FR-F014-04: second `(form_id, version_number = 1)` insert rejected.
- `field_key_unique_per_version` — FR-F014-02: duplicate `(version_id, key)` rejected; same key allowed on another version.
- `field_requires_existing_column` — FR-F014-02: foreign key rejects orphan `column_id`; `on delete restrict` blocks column hard delete.
- `published_version_update_rejected_by_trigger` — FR-F014-04: `UPDATE form_fields` on a version with `published_at` set raises; draft version updates succeed.
- `submission_status_transition_enforced` — FR-F014-10: `received → accepted` and `received → rejected` allowed; `accepted → received` and payload edits raise.
- `submission_idempotency_key_unique` — FR-F014-11: duplicate `(tenant_id, form_id, idempotency_key)` rejected.
- `token_hash_unique_and_indexed` — FR-F014-05: duplicate `submission_token_hash` rejected; `EXPLAIN` on token lookup uses `form_versions_token_idx`.
- `submissions_received_index_used` — FR-F014-17: `EXPLAIN` on the submissions list uses `form_submissions_form_received_idx`.
- `expired_drafts_purged` — FR-F014-14: purge query removes rows with `draft_token` and `expires_at < now()` only.
- `rollback_drops_tables_and_triggers` — T053: `sqlx migrate revert` removes the four tables, indexes, and both triggers.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F014/database/`.
