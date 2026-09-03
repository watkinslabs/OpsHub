# F060 database cases

File: `testing/features/F060/database/{migration_tests.rs,constraint_tests.rs,index_tests.rs}`. Flag `F060_FEATURE`.

- `formatting_tables_exist_with_constraints` — T237: `formatting_rules` and `formatting_states` exist with tenant, version, and audit columns and `sheets.formatting_rules_version` defaults to 0.
- `position_unique_per_scope` — FR-F060-06: two sheet-scoped rules cannot share a position; the same position value is allowed under a different `view_id`.
- `view_cascade_removes_view_scoped_rules` — FR-F060-08: deleting the `views` row cascades its formatting rules; sheet-scoped rules survive.
- `states_cascade_on_rule_delete` — FR-F060-10: deleting a `formatting_rules` row removes its `formatting_states` rows.
- `states_cascade_on_row_delete` — FR-F060-10: deleting a `rows` row removes its `formatting_states` rows.
- `state_primary_key_blocks_duplicate_pairs` — NFR-F060-04: a second `(rule_id, row_id)` row violates the primary key, which is what makes the materialize upsert idempotent.
- `rules_version_increments_once_per_mutation` — FR-F060-07: create, update, reorder, and delete each add exactly 1 to `sheets.formatting_rules_version` inside the write transaction.
- `scope_index_used_for_rule_list` — NFR-F060-01: `EXPLAIN` on the ordered rule list uses `formatting_rules(tenant_id, sheet_id, position) where deleted_at is null`.
- `state_lookup_index_used_for_row_page` — NFR-F060-01: `EXPLAIN` on the 500-row state fetch uses `formatting_states(sheet_id, row_id)` and not a sequential scan.
- `condition_gin_index_used_for_column_lookup` — FR-F060-10: the `column.deleted.v1` lookup for rules referencing a column uses the GIN index on `formatting_rules.condition`.
- `rollback_drops_formatting_objects` — T237: `sqlx migrate revert` removes both tables, their indexes, and the `sheets.formatting_rules_version` column.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F060/database/`.
