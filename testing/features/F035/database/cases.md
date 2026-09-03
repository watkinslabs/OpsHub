# F035 database cases

File: `testing/features/F035/database/migration_tests.rs`. Flag `F035_FEATURE`.

- `formula_tables_exist_with_constraints` — T137: `formula_definitions`, `formula_dependencies`, `formula_results` exist with tenant, version, audit columns and the status and error_code check constraints.
- `node_count_over_limit_rejected_by_check` — FR-F035-03: inserting `node_count = 10001` violates the check constraint.
- `one_definition_per_column` — FR-F035-06: second `formula_definitions` row for the same `column_id` violates the unique index.
- `dependencies_cascade_on_definition_delete` — FR-F035-06: deleting the definition removes its `formula_dependencies` rows.
- `error_code_null_iff_status_not_error` — FR-F035-08: `status = ok` with an error_code and `status = error` without one are both rejected.
- `results_primary_key_row_column` — FR-F035-08: duplicate `(row_id, column_id)` rejected; upsert updates `batch_id` and `source_version`.
- `reverse_dependency_index_used` — FR-F035-09: `EXPLAIN` for dependents lookup by `(to_sheet_id, to_column_id)` uses `formula_dependencies_target_idx`.
- `results_hidden_with_soft_deleted_row` — FR-F035-08: soft-deleting a row hides its results from the cell read view; restore shows them again.
- `rollback_drops_tables` — T137: `sqlx migrate revert` removes the three tables and indexes.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F035/database/`.
