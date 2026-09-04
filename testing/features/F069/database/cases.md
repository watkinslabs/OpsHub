# F069 database cases

File: `testing/features/F069/database/{migration_tests.rs,constraint_tests.rs,index_tests.rs}`. Flag `F069_FEATURE`.

- `home_tables_exist_with_constraints` — T274: `favorites` and `recent_items` exist with `tenant_id`, `user_id`, the eight-value `target_kind` check, `label_cache`, and the audit and version columns the ticket specifies.
- `target_kind_check_rejects_a_ninth_kind` — FR-F069-05: inserting `target_kind = 'chart'` violates the check, so adding a kind is a migration rather than a silent write.
- `favorite_unique_per_user_and_target` — FR-F069-05: a second live pin of the same `(tenant_id, user_id, target_kind, target_id)` violates the partial unique index; a soft-deleted predecessor does not block a new pin.
- `recent_upsert_is_single_statement` — FR-F069-07: the primary key `(tenant_id, user_id, target_kind, target_id)` makes `record_visits` one `insert ... on conflict do update`, verified by statement count.
- `visit_count_must_be_positive` — FR-F069-08: `visit_count = 0` violates the check constraint.
- `last_visited_not_before_first_visited` — FR-F069-08: a row whose `last_visited_at` precedes `first_visited_at` is rejected.
- `rows_cascade_on_user_delete` — NFR-F069-02: deleting the user removes their favourites and recents, so a departing member takes both private surfaces with them.
- `no_array_or_payload_column_in_this_module` — FR-F069-11: `information_schema` shows neither table carries an array or schema-less column; every column is one the product filters, sorts, or constrains on.
- `favorites_list_uses_user_created_index` — NFR-F069-01: `EXPLAIN` on the newest-20 read uses `favorites(tenant_id, user_id, created_at desc) where deleted_at is null`.
- `recents_list_uses_last_visited_index` — NFR-F069-01: `EXPLAIN` on the newest-12 read uses `recent_items(tenant_id, user_id, last_visited_at desc)`.
- `prune_sweep_uses_target_index` — FR-F069-10: `EXPLAIN` on the purged-target sweep uses the `(tenant_id, target_kind, target_id)` index on both tables.
- `rollback_drops_home_tables` — T274: `sqlx migrate revert` removes both tables and their five indexes and leaves no orphan constraint.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F069/database/`.
