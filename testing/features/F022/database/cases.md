# F022 database cases

File: `testing/features/F022/database/migration_tests.rs`. Flag `F022_FEATURE`.

- `metrics_tables_exist_with_constraints` — T085: `metrics`, `metric_values`, `metric_runs` exist with check constraints on `scope_policy`, `comparison`, `source_kind`.
- `value_primary_key_per_scope_and_period` — FR-F022-05: duplicate `(metric_id, scope_key, period_start)` rejected.
- `second_active_run_same_scope_rejected` — FR-F022-04: two `queued` runs for one `(metric_id, scope_key)` violate `metric_runs_active_idx`; different scopes allowed.
- `values_cascade_on_metric_delete` — FR-F022-11: hard delete of a metric removes its values.
- `values_index_used_for_series_read` — NFR-F022-01: `EXPLAIN` on the series query uses `metric_values_metric_scope_period_idx`.
- `values_and_run_written_in_transaction` — FR-F022-04: failing run finalize rolls back inserted values.
- `runs_pruned_after_thirty_days` — FR-F022-12: prune statement deletes runs older than 30 days only.
- `rollback_drops_metric_tables` — T085: `sqlx migrate revert` removes the three tables.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F022/database/`.
