# F004 database cases

File: `testing/features/F004/database/migration_tests.rs`. Flag `F004_FEATURE`.

- `runtime_tables_exist_with_constraints` — T014: `outbox_events`, `job_runs`, `dead_letters` exist with the columns and check constraints from ticket section 4.
- `event_name_check_constraint` — FR-F004-05: inserting `event_name = 'tenant.changed'` violates the regex check.
- `unpublished_outbox_delete_rejected` — NFR-F004-04: `DELETE` where `published_at is null` raises; published rows delete normally.
- `skip_locked_batches_do_not_overlap` — FR-F004-07: two concurrent `FOR UPDATE SKIP LOCKED LIMIT 500` selections return disjoint ids.
- `unpublished_partial_index_used` — NFR-F004-01: `EXPLAIN` for the relay query uses `outbox_events_unpublished_idx`.
- `job_run_attempt_unique` — FR-F004-09: duplicate `(job_id, attempt)` rejected.
- `job_idempotency_key_unique_per_tenant_kind` — FR-F004-10: duplicate `(tenant_id, kind, idempotency_key)` rejected; null keys allowed.
- `dead_letter_unique_per_job` — FR-F004-11: second `dead_letters` row for the same `job_id` rejected.
- `pitr_restore_drill_row_counts_match` — FR-F004-15: restored scratch database counts equal `manifest.json` for `tenants`, `users`, `outbox_events`.
- `rollback_drops_tables` — T014: `sqlx migrate revert` removes the three tables and the delete trigger.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F004/database/`.
