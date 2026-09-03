# F016 database cases

File: `testing/features/F016/database/migration_tests.rs`. Flag `F016_FEATURE`.

- `comments_tables_exist_with_constraints` — T061: `comment_threads`, `comments`, `mentions`, `activity_entries` exist with tenant, version, audit, and soft-delete columns and the `target_kind` and `actor_kind` check constraints.
- `parent_comment_must_share_thread` — FR-F016-02: trigger `comments_parent_same_thread` rejects a `parent_comment_id` from a different thread.
- `body_length_check_enforced` — FR-F016-03: inserting a 10,001-char body violates `check (char_length(body) <= 10000)`.
- `mention_unique_per_comment_principal` — FR-F016-04: duplicate `(comment_id, mentioned_kind, mentioned_id)` rejected; deleting the comment cascades mentions.
- `activity_source_event_unique` — FR-F016-10: second insert with the same `(tenant_id, source_event_id)` is a no-op under `on conflict do nothing`.
- `thread_list_uses_target_index` — NFR-F016-01: `EXPLAIN` on the thread list uses `comment_threads_tenant_target_idx`.
- `activity_list_uses_target_occurred_index` — NFR-F016-01: `EXPLAIN` on the activity query uses `activity_entries_tenant_target_occurred_idx`.
- `audit_and_outbox_rows_written_in_transaction` — FR-F016-11: failing outbox insert rolls back the comment write.
- `rollback_drops_tables` — T061: `sqlx migrate revert` removes the four tables, trigger, and indexes.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F016/database/`.
