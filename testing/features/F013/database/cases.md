# F013 database cases

File: `testing/features/F013/database/migration_tests.rs`. Flag `F013_FEATURE`.

- `views_tables_exist_with_constraints` — T049: `views` and `view_shares` exist with tenant, version, audit, soft-delete columns and `kind`/`visibility`/`principal_kind`/`role` check constraints.
- `second_default_view_rejected` — FR-F013-08: inserting a second `is_default` view for a sheet violates `views_default_per_sheet_idx`; allowed after the first is soft-deleted.
- `duplicate_name_same_owner_rejected` — FR-F013-01: same owner, same sheet, name differing only by case → unique violation; another owner may reuse the name.
- `share_check_constraints_enforced` — FR-F013-10: link share without `token_hash` or `expires_at` rejected; user share with null `principal_id` rejected; duplicate `token_hash` rejected.
- `view_requires_existing_sheet` — FR-F013-01: foreign key rejects a view for a missing sheet; `on delete restrict` blocks hard delete of a sheet with views.
- `settings_gin_index_finds_column_usage` — FR-F013-03: `EXPLAIN` on `settings @> '{"columns": ["<id>"]}'` uses the GIN index for column-deletion pruning.
- `view_list_uses_sheet_updated_index` — NFR-F013-01: `EXPLAIN` on the sheet view list uses `views_tenant_sheet_updated_idx`.
- `soft_delete_revokes_shares_in_transaction` — FR-F013-09: deleting a view sets `deleted_at` and `revoked_at` on its shares atomically; a failing outbox insert rolls both back.
- `audit_and_outbox_rows_written_in_transaction` — FR-F013-12: failing outbox insert rolls back the view write.
- `rollback_drops_tables` — T049: `sqlx migrate revert` removes both tables and their indexes.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F013/database/`.
