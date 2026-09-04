# F072 database cases

File: `testing/features/F072/database/{migration_tests.rs,constraint_tests.rs,index_tests.rs}`. Flag `F072_FEATURE`.

- `inbound_email_tables_exist_with_constraints` — T285: `inbound_addresses`, `inbound_address_mappings`, `inbound_address_senders`, `inbound_messages`, `inbound_message_attachments`, `inbound_message_issues`, `inbound_reply_tokens` and `inbound_rate_windows` exist with tenant, version and audit columns where the ticket specifies them, and no column is an array type.
- `local_part_unique_across_revoked_rows` — FR-F072-01: inserting a second row with the same `lower(local_part)` and domain fails even when the first is `revoked`.
- `message_unique_per_provider_message_id` — FR-F072-04: a second `inbound_messages` row with the same `(provider, provider_message_id)` violates the unique index.
- `disposition_requires_row_or_comment` — FR-F072-11: `disposition = 'accepted'` with both `row_id` and `comment_id` null is refused, as is a non-accepted row carrying either.
- `rejection_reason_only_when_rejected` — FR-F072-05: an `accepted` or `quarantined` row with a `rejection_reason` is refused.
- `mapping_source_and_column_unique_per_address` — FR-F072-11: a duplicate `source` or a reused `column_id` on one address violates the primary key or the unique index.
- `allow_list_rejects_duplicate_pattern` — FR-F072-06: a repeated `(kind, pattern)` on one address violates the primary key.
- `attachment_position_unique_per_message` — FR-F072-12: a duplicate `(message_id, position)` is refused; `position` above 50 violates the check.
- `token_hash_unique_and_use_count_bounded` — FR-F072-14: a duplicate `token_hash` is refused and `use_count` 21 violates the check.
- `rate_window_counter_is_upserted_not_scanned` — FR-F072-08: `bump_window` upserts one row per `(address_id, bucket_key, window_start)` and the limit check reads a single row.
- `cascade_on_sheet_delete` — FR-F072-16: deleting the sheet removes its addresses, messages, attachments, issues, tokens and rate windows; `files` rows survive with `file_id` set null.
- `raw_expiry_index_used_by_sweep` — FR-F072-16: `EXPLAIN` on the retention scan uses the partial index on `raw_expires_at`.
- `log_index_used_for_address_history` — NFR-F072-01: `EXPLAIN` on the last 50 messages for an address uses `inbound_messages(address_id, received_at desc)`.
- `rollback_drops_inbound_email_tables` — T285: `sqlx migrate revert` removes the eight tables and their indexes and leaves `sheets`, `rows`, `columns`, `users` and `files` untouched.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F072/database/`.
