# F024 api cases

File: `testing/features/F024/api/{spec_tests.rs,query_tests.rs,definition_tests.rs,time_series_tests.rs,project_job_tests.rs,burndown_tests.rs,timeline_workload_tests.rs,negative_tests.rs}`. Flag `F024_FEATURE`.

- `spec_missing_formatting_and_error_state_rejected` — FR-F024-01: 400 `invalid` with `field_errors` keys `spec.formatting` and `spec.error_state`.
- `spec_over_32kb_rejected` — FR-F024-01: 33 KB spec JSON → 400 `invalid`; 31 KB accepted.
- `pie_with_two_measures_rejected` — FR-F024-02: `ChartError::KindLimit` → 400; one measure accepted.
- `bar_with_three_dimensions_rejected` — FR-F024-02: three dimensions → 400; two fold into stacked series.
- `burndown_without_done_field_rejected` — FR-F024-02: `source.kind = sheet` but no `done_field`/`done_values` → 400.
- `bar_query_folds_by_owner_under_viewer_scope` — FR-F024-03: dimension `Projects.owner`, measure `count(Risks.id)` → one point per owner, `meta.scope: viewer`.
- `hidden_field_measure_yields_null_points` — FR-F024-03, NFR-F024-02: `sum(Budget.margin)` hidden from Lee → every `y` null, series still labelled.
- `restricted_rows_absent_from_points` — NFR-F024-02: rows Lee cannot read change no owner's count.
- `series_capped_at_twenty_sets_truncated` — FR-F024-03: 35 owners → 20 series and `meta.truncated: true`.
- `points_capped_at_one_thousand_per_series` — FR-F024-03: 1,500 day buckets → 1,000 points, `meta.point_count: 1000`.
- `week_bucket_respects_dst_boundary` — FR-F024-10: `America/New_York` DST day yields one bucket, `meta.timezone` echoed.
- `chart_widget_save_upserts_definition_by_widget_id` — FR-F024-04: `PUT /dashboards/{id}/widgets` twice → one `chart_definitions` row, `version` 2.
- `patch_chart_publishes_updated_event_and_purges_cache` — FR-F024-04: `chart.updated.v1` with `widget_id` and `changed_fields`; the widget's `widget_cache` rows deleted.
- `patch_chart_stale_if_match_conflicts` — FR-F024-04: stale `If-Match` → 409 `conflict`, spec unchanged.
- `patch_chart_without_idempotency_key_invalid` — FR-F024-12: missing header → 400; replay of the same key returns the first result and writes one audit `chart.update`.
- `metric_comparison_computes_delta_and_direction` — FR-F024-05: two metrics → `delta_abs`, `delta_pct`, `direction` from the first metric's `target.direction`.
- `denied_metric_widget_returns_denied_status` — FR-F024-05: metric Lee cannot read → widget status `denied`, no values in the body.
- `time_series_returns_actual_from_metric_values` — FR-F024-06: 52 weekly values → 52 `actual` points bucketed to `grain`.
- `linear_projection_has_five_weekly_points_with_bounds` — FR-F024-06: horizon 30 days, `linear` → 5 projected points with `lower` < `value` < `upper`.
- `moving_average_uses_window_mean` — FR-F024-06: `moving_average` repeats the 12-bucket mean.
- `projection_with_two_points_returns_empty` — FR-F024-06: 2 available buckets → `projected: []`, no error.
- `horizon_over_ninety_days_rejected` — FR-F024-06: `horizon_days=120` → 400 `invalid`.
- `job_writes_points_and_publishes_projected_event` — FR-F024-07: `charts.project` → `time_series_points` of kind `projected` and `time-series.projected.v1` with `run_id` and `point_count`.
- `job_replay_with_same_run_id_is_noop` — NFR-F024-04: redelivery writes no duplicate rows and publishes once.
- `job_dead_letters_after_three_retries` — NFR-F024-04: fourth failure dead-letters and increments `projection_failures_total`.
- `stale_flag_true_until_projection_catches_up` — FR-F024-07: a newer `metric.computed.v1` keeps `meta.stale: true` until the job reruns.
- `projections_isolated_per_scope_key` — NFR-F024-02: Dana and Lee reading the same metric get separate `time_series_points` rows.
- `burndown_replays_cell_history_per_local_midnight` — FR-F024-08: 40 rows moved to Done between 2026-08-20 and 2026-09-02 → `remaining` falls on the matching local day.
- `burndown_ideal_is_linear_from_start_total` — FR-F024-08: `ideal` runs 200 → 0 across 15 daily points.
- `burndown_counts_rows_added_after_start` — FR-F024-08: rows created mid-span appear in `added` and raise `remaining`.
- `burndown_scope_field_sums_numeric_column` — FR-F024-08: `scope: field` over `Points` sums instead of counting.
- `burndown_span_over_366_days_rejected` — FR-F024-08: 367-day span → 400 `invalid`.
- `burndown_second_call_served_from_cache` — FR-F024-08, NFR-F024-01: identical params within 60 s hit the cache and increment `burndown_cache_hits_total`.
- `timeline_marks_null_end_as_milestone` — FR-F024-09: null `End` → `milestone: true`; bars sorted by `start`.
- `timeline_truncates_at_500_bars` — FR-F024-09: 600 dated rows → 500 bars and `truncated: true`.
- `workload_over_capacity_flagged_at_forty_hours` — FR-F024-09: `sum(Points)` above the default 40 h capacity → `over_capacity: true`.
- `workload_caps_at_200_people` — FR-F024-09: 250 assignees → 200 people and `truncated: true`.
- `restricted_sheet_burndown_not_found` — FR-F024-12: Lee without sheet read → 404 `not_found` and no history query executed.
- `foreign_tenant_ids_not_found` — FR-F024-12: tenant B `chart_id`, `sheet_id`, and `metric_id` → 404 on query, get, patch, burndown, and time-series.
- `report_source_without_viewer_role_denied` — FR-F024-12: no `report-viewer` and no ACL grant → 403 `denied`.
- `queue_unavailable_returns_503` — FR-F024-07: JetStream stub down on projection enqueue → 503 `unavailable`.

Evidence: JUnit output, outbox dumps, and audit rows under `testing/evidence/F024/api/`.
