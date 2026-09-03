# F024 database cases

File: `testing/features/F024/database/{migration_tests.rs,constraint_tests.rs,index_tests.rs}`. Flag `F024_FEATURE`; the migration runs regardless of the flag.

- `charts_tables_exist_with_constraints` — T093: `chart_definitions` and `time_series_points` exist with tenant, version, and audit columns from ticket section 4.
- `definition_kind_check_rejects_unknown_kind` — FR-F024-04: inserting `kind = 'sankey'` violates `check (kind in ('bar','line','pie','burndown','timeline','workload','kpi','metric_comparison'))`.
- `definition_unique_per_widget` — FR-F024-04: a second `chart_definitions` row for the same `widget_id` violates the unique constraint.
- `definition_cascades_on_widget_delete` — FR-F024-04: deleting the `dashboard_widgets` row removes its definition.
- `point_primary_key_blocks_duplicate_bucket` — FR-F024-07: a second row for `(metric_id, scope_key, grain, method, horizon_days, kind, ts)` is rejected; a different `scope_key` is accepted.
- `point_kind_and_method_checks` — FR-F024-06: `kind = 'forecast'` and `method = 'arima'` violate their check constraints.
- `points_cascade_on_metric_delete` — FR-F024-07: deleting the `metrics` row removes its projected points.
- `projection_lookup_uses_scope_index` — NFR-F024-01: `EXPLAIN` for the latest projection uses `time_series_points(metric_id, scope_key, computed_at desc)`.
- `burndown_history_read_uses_cell_history_index` — NFR-F024-01: `EXPLAIN` on the per-day boundary query uses the F008 `cell_history(row_id, column_id, changed_at)` index.
- `projected_points_older_than_90_days_deleted` — FR-F024-07: the job removes points past 90 days and points superseded by a newer `run_id`.
- `definition_soft_deletes_with_widget` — FR-F024-04: a soft-deleted widget leaves `deleted_at` set and hides the definition from reads.
- `scope_key_separates_tenants` — NFR-F024-02: tenant B rows are invisible to a tenant A query on the same `metric_id`.
- `rollback_drops_charts_tables` — T093: `sqlx migrate revert` removes both tables and their indexes.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F024/database/`.
