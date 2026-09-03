# F007 database cases

File: `testing/features/F007/database/migration_tests.rs`. Flag `F007_FEATURE`.

- `columns_tables_exist_with_constraints` — T025: `columns`, `column_options`, `cell_validation_states` exist with tenant, version, audit, and soft-delete columns; `cells.normalized` added nullable.
- `duplicate_label_same_sheet_rejected` — FR-F007-03: `columns_sheet_label_idx` blocks case-insensitive duplicate while `deleted_at is null`; allows after soft delete.
- `second_primary_column_rejected` — FR-F007-13: second `is_primary` for one sheet violates `columns_sheet_primary_idx`.
- `unknown_type_rejected_by_check` — FR-F007-01: insert type `money` fails the check constraint; all twelve names succeed.
- `width_check_enforced` — FR-F007-01: width 39 and 1001 rejected; 40 and 1000 accepted.
- `validation_state_primary_key_and_check` — FR-F007-10: duplicate `(row_id, column_id)` rejected; state `unknown` rejected.
- `column_requires_existing_sheet` — FR-F007-01: orphan `sheet_id` rejected; `on delete restrict` blocks hard delete of a sheet with columns.
- `option_label_unique_unless_archived` — FR-F007-07: duplicate active option label rejected; archived duplicate allowed.
- `position_index_used_for_column_list` — NFR-F007-01: `EXPLAIN` on the column list uses `columns_sheet_position_idx`.
- `invalid_count_uses_state_index` — FR-F007-11: `EXPLAIN` on invalid count uses `cell_validation_states_column_state_idx`.
- `outbox_failure_rolls_back_column_write` — NFR-F007-04: failing outbox insert leaves no `columns` row.
- `rollback_drops_tables_and_normalized_column` — T025: `sqlx migrate revert` removes the three tables, their indexes, and `cells.normalized`.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F007/database/`.
