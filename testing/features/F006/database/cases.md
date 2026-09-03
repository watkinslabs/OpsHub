# F006 database cases

File: `testing/features/F006/database/migration_tests.rs`. Flag `F006_FEATURE`.

- `sheets_tables_exist_with_constraints` — T021: `sheets`, `sheet_groups`, `rows`, `cells` exist with tenant, version, audit, and soft-delete columns.
- `duplicate_name_same_folder_rejected` — FR-F006-02: unique partial index blocks case-insensitive duplicate while `deleted_at is null`; allows after delete.
- `second_default_group_rejected` — FR-F006-09: inserting a second `is_default` group for a sheet violates the partial unique index.
- `row_requires_existing_sheet_and_group` — FR-F006-06: foreign keys reject orphan rows; `on delete restrict` blocks hard delete of a sheet with rows.
- `cells_primary_key_row_column` — FR-F006-07: duplicate `(row_id, column_id)` rejected.
- `position_index_used_for_list` — NFR-F006-01: `EXPLAIN` on the row list uses `rows_sheet_position_idx`.
- `soft_delete_restore_round_trip` — FR-F006-05: `deleted_at` set and cleared; ids unchanged.
- `audit_and_outbox_rows_written_in_transaction` — FR-F006-11: failing outbox insert rolls back the sheet write.
- `rollback_drops_tables` — T021: `sqlx migrate revert` removes the four tables and indexes.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F006/database/`.
