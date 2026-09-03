# F023 database cases

File: `testing/features/F023/database/migration_tests.rs`. Flag `F023_FEATURE`.

- `dashboards_tables_exist_with_constraints` — T089: `dashboards`, `dashboard_widgets`, `widget_cache` exist with kind and status checks.
- `duplicate_dashboard_name_same_folder_rejected` — FR-F023-01: partial unique index blocks duplicate while `deleted_at is null`.
- `widget_position_out_of_range_rejected` — FR-F023-02: `pos_w 13` and `pos_x 8, pos_w 6` violate the check constraint.
- `widget_kind_check_rejects_unknown` — FR-F023-03: kind `gauge` rejected.
- `widget_cache_primary_key_per_scope` — FR-F023-05: duplicate `(widget_id, scope_key)` rejected; two scopes allowed.
- `widget_cache_cascades_on_widget_delete` — FR-F023-10: hard delete of a widget removes its cache rows.
- `scheduler_scan_uses_scope_computed_index` — FR-F023-07: `EXPLAIN` on "scopes read in 24 h" uses `widget_cache_scope_computed_idx`.
- `widgets_and_outbox_written_in_transaction` — FR-F023-11: failing outbox insert rolls back the widget replace.
- `rollback_drops_dashboard_tables` — T089: `sqlx migrate revert` removes the three tables.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F023/database/`.
