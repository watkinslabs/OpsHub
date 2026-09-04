# F066 api cases

This feature owns no HTTP route, so this lane is the CLI contract for `cargo xtask verify-slo` plus the unit cases behind it, and it carries the negative control that the gate is offline. File: `testing/features/F066/api/{objectives_tests.rs,budget_tests.rs,exposition_tests.rs,render_tests.rs,burn_tests.rs,gate_tests.rs,link_tests.rs,report_tests.rs,harness_tests.rs}`. Flag `F066_FEATURE`.

- `objectives_schema_rejects_unknown_key` — FR-F066-01: an extra `windows:` key → `slo.schema` at its line; the valid fixture loads.
- `target_of_one_rejected` — FR-F066-01: `target: 1.0` → `slo.schema` (a target of 1 makes the budget zero and every burn rate infinite).
- `duplicate_objective_id_rejected` — FR-F066-01: two `ack_async` entries → `slo.schema` naming the id.
- `class_overlap_on_route_and_method_rejected` — FR-F066-02: `/api/v1/users` GET in both `core_read` and `analytics` → `slo.class_overlap`.
- `classify_returns_core_read_for_get_users` — FR-F066-02: `(GET, /api/v1/users)` → `core_read`; `(PATCH, /api/v1/users/{id})` → `core_write`.
- `classify_returns_async_ack_only_for_202_responders` — FR-F066-02: `/api/v1/tenants/{id}/suspend` → `async_ack`; the same route with a 200 fixture is not counted in the ack denominator.
- `unclassified_route_names_the_route` — FR-F066-02: `/api/v1/widgets` in the exposition → `slo.route_unclassified` with the route in the message.
- `analytics_and_integration_are_excluded_from_denominators` — FR-F066-03: the rendered availability selector contains no analytics or integration route.
- `budget_minutes_are_201_6_for_availability_core` — FR-F066-07: 0.005 × 40,320 = 201.6.
- `latency_budget_is_2016_minutes` — FR-F066-07: 0.05 × 40,320 for both latency objectives.
- `ack_budget_is_403_2_minutes` — FR-F066-07: 0.01 × 40,320.
- `remaining_ratio_is_negative_when_overspent` — FR-F066-07: ratio 0.9938 against 0.995 → remaining -0.24, clamped only for display.
- `missing_le_0_8_bucket_reports_bucket_missing` — FR-F066-12: exposition without `le="0.8"` → `slo.bucket_missing` naming `latency_core_write` and 0.8.
- `non_histogram_metric_rejected` — FR-F066-12: `http_request_duration_seconds` exposed as a gauge → `slo.bucket_missing`.
- `absent_sample_is_skipped_not_failed` — FR-F066-12: no `--metrics` → `skipped: metrics sample absent` and exit 0.
- `recording_rules_match_committed_file` — FR-F066-08: rendering `objectives.yml` reproduces `infra/prometheus/rules/slo-recording.yml` byte for byte.
- `rules_cover_all_eight_windows` — FR-F066-08: `5m, 30m, 1h, 2h, 6h, 24h, 3d, 28d` present for each of the four objectives.
- `rules_keep_no_route_label` — NFR-F066-01: every rule aggregates `sum by (objective)`; a renderer keeping `route` → `slo.cardinality`.
- `burn_factors_derive_to_13_44_5_6_2_8_0_93` — FR-F066-09: `consumed * 672 / long_hours` for the four pairs; no literal factor in the source.
- `hand_edited_burn_factor_reports_threshold_drift` — FR-F066-09: 5.6 changed to 10 → `slo.threshold_drift` with expected 5.6 and found 10.
- `short_window_not_one_twelfth_reports_window_pair` — FR-F066-09: `1h/10m` → `slo.window_pair`.
- `alert_carries_objective_severity_and_window_labels` — FR-F066-09: each generated alert has `objective`, `severity`, `window`, and `summary`, `budget_minutes`, `runbook` annotations.
- `f004_rule_without_objective_label_is_unlinked` — FR-F066-11: F004's `outbox_pending_events` rule with no `objective` label → `slo.alert_unlinked`; `infra/alerts/rules.yml` is read, never written.
- `runbook_anchor_missing_reports_alert_unlinked` — FR-F066-11: a `runbook` annotation pointing at an absent anchor → `slo.alert_unlinked`.
- `clean_tree_exits_zero_with_summary_line` — FR-F066-13: `verify-slo passed (4 objectives, 7 classes)` on stdout, exit 0.
- `findings_are_sorted_by_path_line_code` — FR-F066-13: three findings emitted out of order arrive sorted on stderr.
- `json_object_matches_f041_shape` — FR-F066-13: exactly one object with `command`, `ok`, `checked`, `findings[{code,path,line,message}]`, `duration_ms`.
- `unknown_flag_exits_two` — FR-F066-13: `--budgets` → usage line on stderr, exit 2, nothing written.
- `static_mode_opens_no_socket` — NFR-F066-02: the run is wrapped by a loopback listener on port 0 that fails the test on any accepted connection; no route, client, or database handle exists in this feature.
- `exhausted_budget_refuses_with_exit_3` — FR-F066-14: the exhausted snapshot prints the full table then `REFUSED: slo.budget_exhausted availability_core` at exit 3.
- `guarded_state_reported_between_zero_and_quarter` — FR-F066-14: remaining 0.18 → `guarded`, exit 0.
- `insufficient_data_excluded_from_freeze` — FR-F066-10: 40 samples → `insufficient_data`, never `exhausted`.
- `live_exception_allows_release` — FR-F066-15: an exception with owner, ticket, and a 7-day expiry → exit 0 and the exception listed in the report.
- `expired_exception_does_not_suppress_refusal` — NFR-F066-05: expiry in the past → `slo.exception_expired` and the refusal stands.
- `exception_for_other_objective_does_not_suppress` — NFR-F066-05: an exception on `ack_async` does not release a frozen `availability_core`.
- `budget_without_operator_role_runs_dry` — FR-F066-14: no `XTASK_ROLE=operator` outside CI on `main` → every check runs, `dry run: operator role required to record`, exit 3, no file written.
- `report_is_deterministic_across_runs` — NFR-F066-04: two runs on one snapshot differ only in `generated_at`; the objectives SHA-256 is recorded.
- `promtool_suite_passes_against_committed_rules` — FR-F066-16: `promtool test rules infra/slo/tests/*.promtool.yml` exits 0.

Evidence: JUnit output, captured stdout and stderr, and exit codes under `testing/evidence/F066/api/`.
