# F022 api cases

File: `testing/features/F022/api/{metric_tests.rs,values_tests.rs,rollup_tests.rs,calculation_tests.rs,permission_tests.rs}`. Flag `F022_FEATURE`.

- `metric_create_returns_version_one` — FR-F022-01: POST `/api/v1/metrics` with count over report → 201, `version: 1`.
- `metric_sum_on_text_column_invalid` — FR-F022-01: `sum` over `Projects.owner` → 400 `measure.column_ref`.
- `percent_of_matches_hand_computed_ratio` — FR-F022-02: 3 critical of 12 open → 25.0.
- `percent_of_zero_denominator_null` — FR-F022-02: filters matching no rows → `value: null`.
- `metric_unreadable_source_not_found` — FR-F022-03: restricted viewer creates metric over "Risks" → 404.
- `metric_recompute_writes_values_and_run` — FR-F022-04: 52 `metric_values` rows, run `succeeded` with `rows_scanned 120`, `metric.computed.v1`.
- `metric_recompute_active_conflicts` — FR-F022-04: second recompute for the same scope → 409.
- `metric_owner_scope_requires_tenant_policy` — FR-F022-05: `scope_policy owner` without policy → 400; with policy → 201 and one shared value set.
- `metric_values_hidden_column_null_for_viewer` — FR-F022-05: viewer `current.value` null, editor 41000.
- `metric_values_missing_scope_enqueues_run` — FR-F022-06: first read by a new viewer → `current: null`, `meta.status computing`, one queued run.
- `metric_values_stale_when_source_advances` — FR-F022-07: Risks version 4 → 5 → `meta.stale true`.
- `stale_sweeper_enqueues_once_per_five_minutes` — FR-F022-07: three reads in 5 minutes → one run.
- `rollup_week_aligns_to_timezone_and_week_start` — FR-F022-08: daily buckets → Monday-start weeks in `America/New_York`.
- `rollup_avg_weighted_by_sample_count` — FR-F022-08: avg of (10×3 rows, 20×1 row) → 12.5.
- `rollup_finer_grain_invalid` — FR-F022-08: metric grain week, query `grain=day` → 400.
- `comparison_direction_down_is_good` — FR-F022-09: 7 vs 9 → `delta_abs -2`, `direction better`.
- `comparison_flat_under_half_percent` — FR-F022-09: 1000 vs 1003 → `flat`.
- `formatted_follows_locale` — FR-F022-10: `de-DE` EUR → `41.000,00 €`; `en-US` → `€41,000.00`.
- `metric_update_measure_invalidates_values` — FR-F022-11: PATCH measure → 0 `metric_values` rows for every scope, `metric.updated.v1`.
- `metric_stale_version_conflicts` — FR-F022-11: `If-Match: 1` vs version 2 → 409.
- `metric_cross_tenant_not_found` — FR-F022-11: tenant B on every route → 404.
- `metric_idempotent_replay_returns_original` — FR-F022-12: same key twice → one row; different body → 409.
- `recompute_job_dead_letters_after_four_failures` — FR-F022-12: injected failures → 3 retries then dead letter.
- `recompute_job_idempotent_by_run_id` — FR-F022-12: redelivery → no duplicate values.
- `metric_viewer_mutation_denied` — NFR-F022-02: viewer PATCH/DELETE/recompute → 403.
- `two_viewers_never_share_scope_values` — NFR-F022-02: viewer A and restricted viewer B read different `current` and distinct `scope_key`.
- `expected_values_match_for_all_cases` — FR-F022-08, FR-F022-09: 40 hand-computed cases from `expected_values.json`.
- `dst_week_buckets_have_seven_days` — FR-F022-08: weeks of 2026-03-08 and 2026-11-01 span exactly 7 local days.
- `request_span_carries_metric_ids` — NFR-F022-04: span has `tenant_id`, `metric_id`, `run_id`, `scope_key`.

Evidence: JUnit output and request logs under `testing/evidence/F022/api/`.
