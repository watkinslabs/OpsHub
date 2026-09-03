# F050 database cases

File: `testing/features/F050/database/migration_tests.rs`. Flag `F050_FEATURE`.

- `dynamic_view_tables_exist_with_constraints` — T197: `dynamic_views`, `dynamic_view_policies`, `dynamic_view_edits` exist with tenant, version, audit, and soft-delete columns; foreign keys to `sheets` and `views`.
- `duplicate_view_name_per_sheet_rejected` — FR-F050-01: second view named `vendor updates` (case differs) on the same sheet violates the partial unique index; allowed after soft delete.
- `editable_not_subset_of_visible_rejected` — FR-F050-02: policy insert with `editable_fields` not contained in `visible_fields` violates the check.
- `assigned_rows_requires_assignment_column` — FR-F050-03: `edit_mode = 'assigned_rows'` with null `assignment_column_id` rejected; `allow_new_rows = true` with `edit_mode = 'none'` rejected.
- `token_hash_unique` — FR-F050-05: two views with the same `token_hash` rejected; null hashes allowed on many views.
- `edit_requires_exactly_one_actor` — FR-F050-07: edit row with both or neither of `actor_user_id`, `actor_token_id` rejected.
- `edit_row_rolls_back_when_cell_apply_fails` — NFR-F050-04: forced failure in the cell write leaves no `dynamic_view_edits` row.
- `rows_query_uses_cells_index_for_equality` — NFR-F050-01: `EXPLAIN` on the compiled equality predicate uses the `cells(column_id, raw)` index path.
- `policy_cascades_on_view_delete` — FR-F050-09: hard-deleting a view (purge) removes its policy; edits are restricted by foreign key.
- `rollback_drops_tables` — T197: `sqlx migrate revert` removes the three tables and indexes.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F050/database/`.
