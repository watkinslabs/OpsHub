# F009 database cases

File: `testing/features/F009/database/{migration_tests.rs,hierarchy_model_tests.rs}`. Flag `F009_FEATURE`.

- `links_tables_exist_with_constraints` — T033: `row_hierarchy`, `cell_links`, `rollup_rules` exist with tenant, version, audit, and enum check columns.
- `depth_over_20_rejected_by_check` — FR-F009-03: inserting `depth = 21` violates `row_hierarchy_depth_check`.
- `parent_from_other_sheet_rejected_by_trigger` — FR-F009-01: `parent_row_id` from another sheet raises from `row_hierarchy_same_sheet`.
- `path_unique_per_sheet` — FR-F009-01: duplicate `(sheet_id, path)` rejected by `row_hierarchy_sheet_path_idx`.
- `second_active_link_per_cell_rejected` — FR-F009-09: second `cell_links` row for the same `(source_row_id, source_column_id)` with `deleted_at null` violates the partial unique index; allowed after soft delete.
- `link_enum_checks_enforced` — FR-F009-09: invalid `link_type`, `sync_direction`, or `status` values are rejected.
- `duplicate_rollup_rule_per_column_rejected` — FR-F009-06: second `rollup_rules` row for one `column_id` violates the unique constraint; invalid `function` rejected by check.
- `subtree_scan_uses_path_index` — NFR-F009-01: `EXPLAIN` on `path LIKE '<prefix>%'` uses `row_hierarchy_sheet_path_idx`.
- `reverse_link_lookup_uses_target_index` — FR-F009-12: `EXPLAIN` on lookup by `(target_sheet_id, target_row_id)` uses the partial index.
- `cascade_delete_restore_round_trip` — FR-F009-05: subtree `deleted_at` set and cleared in one transaction; hierarchy rows untouched.
- `audit_and_outbox_rows_written_in_transaction` — FR-F009-16: failing outbox insert rolls back the indent write.
- `rewrite_subtree_paths` — FR-F009-01: model rewrites every descendant path and depth from a new parent path.
- `is_descendant_by_path_prefix` — FR-F009-03: prefix check identifies descendants and rejects self.
- `rollback_drops_tables` — T033: `sqlx migrate revert` removes the three tables, trigger, and indexes.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F009/database/`.
