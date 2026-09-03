# F008 database cases

File: `testing/features/F008/database/migration_tests.rs`. Flag `F008_FEATURE`.

- `grid_tables_exist_with_constraints` — T029: `cell_history`, `edit_batches`, `sheet_user_layouts` exist with tenant, version, actor, and timestamp columns; `sheets.change_version` and `cells.change_version` added.
- `cell_history_version_unique` — FR-F008-02: duplicate `(row_id, column_id, version)` rejected.
- `edit_batch_kind_check` — FR-F008-05: `kind = 'other'` rejected by the check constraint; five allowed kinds accepted.
- `edit_batch_requires_existing_sheet` — FR-F008-05: foreign key rejects orphan batch; `on delete restrict` blocks hard delete of a sheet with batches.
- `layout_frozen_count_check` — FR-F008-10: `frozen_column_count = 6` and `-1` rejected; primary key `(tenant_id, sheet_id, user_id)` blocks duplicates.
- `change_version_increments_per_applied_cell` — FR-F008-08: three applied cells → `sheets.change_version` +3 and each cell carries a distinct `change_version`.
- `history_index_used_for_cell_lookup` — FR-F008-09: `EXPLAIN` on history query uses `cell_history_row_column_occurred_idx`.
- `undo_stack_index_used` — FR-F008-06: `EXPLAIN` on latest not-undone batch uses the partial index on `(sheet_id, actor_id, created_at desc)`.
- `history_and_batch_written_in_transaction` — NFR-F008-04: failing outbox insert rolls back cells, history, and batch together.
- `rollback_drops_tables` — T029: `sqlx migrate revert` removes the three tables and the two added columns.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F008/database/`.
