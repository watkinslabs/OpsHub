# F056 database cases

File: `testing/features/F056/database/migration_tests.rs`. Flag `F056_FEATURE`.

- `pivot_tables_exist_with_constraints` — T221: `pivots` and `pivot_outputs` exist with tenant, version, audit, and soft-delete columns.
- `four_row_dimensions_rejected` — FR-F056-01: check constraint rejects 4 row dimensions, 3 column dimensions, and 11 measures.
- `second_active_output_rejected` — FR-F056-05: inserting a second `queued`/`running` output for one pivot violates `pivot_outputs_one_active_idx`.
- `duplicate_pivot_name_in_workspace_rejected` — FR-F056-01: case-insensitive duplicate name blocked while `deleted_at is null`.
- `output_requires_existing_pivot` — FR-F056-08: foreign key rejects orphan outputs; `on delete restrict` blocks hard delete with outputs.
- `outputs_index_used_for_history` — NFR-F056-01: `EXPLAIN` on the outputs list uses `pivot_outputs_pivot_id_computed_at_idx`.
- `prune_and_insert_in_one_transaction` — FR-F056-08: failing insert of the 21st output leaves 20 rows unchanged.
- `hidden_values_absent_from_cells_jsonb` — FR-F056-06: stored `cells` contain no value from hidden rows.
- `rollback_drops_tables` — T221: `sqlx migrate revert` removes both tables and indexes.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F056/database/`.
