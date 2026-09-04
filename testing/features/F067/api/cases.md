# F067 api cases

F067 owns no HTTP route, so this lane tests the xtask `load` module that the surface `cargo xtask load-test <profile>` dispatches into, plus a negative control proving no route was added.

File: `testing/features/F067/api/{profile_tests.rs,script_tests.rs,preflight_tests.rs,lock_tests.rs,threshold_tests.rs,evidence_tests.rs,compare_tests.rs,baseline_tests.rs,no_route_tests.rs}`. Flag `F067_FEATURE`. Fixtures: fake k6, Prometheus stub, readiness stub, recorded run directories.

- `profile_weights_must_sum_to_one_hundred` — FR-F067-01: a mix of 60/15/10/10/4 → exit 2 `profile.invalid` naming the sum.
- `profile_duration_must_exceed_ramps` — FR-F067-01: `duration_s: 500` with 300 s up and 300 s down → `profile.invalid`.
- `profile_rejects_unknown_threshold_metric` — FR-F067-01: threshold on `cpu_p99` → `profile.invalid` listing the metric catalog.
- `profile_rejects_unknown_toml_key` — FR-F067-01: `warmup_s` key → `profile.invalid`, so a silently ignored knob cannot change a run.
- `profile_rejects_route_absent_from_catalog` — FR-F067-01: a mix entry on a route missing from `docs/capability-contracts.md` → `profile.invalid`.
- `four_shipped_profiles_parse_with_declared_mixes` — FR-F067-02: `steady-read` 2,000 req/s 60/15/10/10/5, `concurrent-edit` 2,000 sessions at one patch per 6 s, `bulk-automation` 200 × 10,000-row imports, `soak` 8 h at 800 req/s.
- `rendered_json_matches_profile_toml` — FR-F067-06: the JSON handed to k6 round-trips every field, so no rate lives in the script.
- `k6_script_scenarios_match_profile` — FR-F067-06: a script declaring three scenarios for a two-scenario profile → exit 2 `profile.script_mismatch`.
- `http_scenarios_use_constant_arrival_rate` — FR-F067-06: offered load stays 2,000 req/s when the stub adds 400 ms of latency.
- `ws_sessions_use_ramping_vus` — FR-F067-06: `concurrent-edit` reaches 2,000 held sessions and no HTTP scenario uses a VU executor.
- `missing_env_url_skips_with_env_unset` — FR-F067-11: no `LOAD_ENV_URL` → exit 0, `status: "skipped"`, `reason_code: "env_unset"`, evidence record written.
- `unreachable_readyz_skips_with_env_unreachable` — FR-F067-11: readiness stub returning 503 for 30 s → `env_unreachable`.
- `stale_dataset_manifest_skips_with_dataset_stale` — FR-F067-11: manifest `generator_sha256` from an older generator → `dataset_stale`.
- `wrong_k6_version_skips_with_runner_missing` — FR-F067-11: fake k6 reporting v0.53.0 → `runner_missing`.
- `require_env_turns_skip_into_exit_two` — FR-F067-11: each of the six reason codes under `--require-env` → exit 2.
- `second_run_skips_with_concurrent_run` — FR-F067-17: a held advisory lock and lock file → `concurrent_run` with the holding pid named.
- `killed_k6_marks_run_aborted` — FR-F067-17: k6 killed at minute 3 → `status: "aborted"`, exit 1, partial metrics stored.
- `threshold_breach_on_outbox_lag_fails_run` — FR-F067-08: `outbox_lag_seconds_p99` 11.4 with read p95 380 ms → `failed` on the saturation metric, exit 1.
- `pool_saturation_and_queue_depth_gated` — FR-F067-08: `db_pool_in_use_ratio_p99` 0.91 and `job_queue_depth_p99` 6,200 each fail independently.
- `replication_lag_and_dead_letters_gated` — FR-F067-08: 40 MiB replica lag fails; one dead letter fails.
- `rss_slope_gated_only_on_soak` — FR-F067-08: 3.1 MiB/h fails `soak` and is reported but not gated on `steady-read`; r² recorded.
- `version_conflict_rate_gated_on_concurrent_edit` — FR-F067-08: 4.2% conflicts fail; a retried conflict that fails twice fails.
- `ramp_window_samples_excluded_from_statistics` — FR-F067-07: a 2 s spike inside the ramp does not move the hold-window p95.
- `absent_prometheus_series_fails_not_passes` — FR-F067-09: an empty range result → exit 2 `metric.absent` with `status: "failed"`.
- `prometheus_query_retries_three_times` — FR-F067-09: two 502s then a series → success; three 502s → `metric.absent`.
- `exit_codes_map_to_statuses` — FR-F067-10: pass/skip/unconfirmed → 0, fail/regressed/aborted → 1, usage/profile/dataset/metric → 2, role → 3.
- `dry_run_prints_plan_and_contacts_nothing` — FR-F067-10: `--dry-run` makes zero network calls and prints every threshold.
- `run_directory_contains_every_required_file` — FR-F067-13: the eight files present with the `<timestamp>-<profile>-<dataset>-<commit12>` id.
- `rerunning_existing_run_id_exits_run_exists` — NFR-F067-02: a second write to the same `run_id` → exit 2 `run.exists`, no file mutated.
- `index_keeps_last_thirty_per_profile_and_dataset` — FR-F067-16: the 31st run evicts the oldest for that pair only.
- `aborted_and_skipped_runs_excluded_from_reference_set` — FR-F067-14: reference median skips them and falls back to the baseline.
- `latency_band_allows_ten_percent_plus_fifteen_ms` — FR-F067-14: reference 180 ms → 200 ms passes, 214 ms regresses.
- `saturation_regresses_above_one_point_two_five` — FR-F067-14: pool ratio 0.60 reference → 0.74 passes, 0.76 regresses.
- `first_regression_is_unconfirmed_second_is_confirmed` — FR-F067-14: 240 ms then 244 ms on `ws_broadcast_p95_ms` → exit 0 then exit 1.
- `absolute_breach_fails_without_waiting_for_confirmation` — FR-F067-14: 520 ms read p95 fails on its first occurrence.
- `promote_baseline_requires_maintainer_role` — FR-F067-15: no `XTASK_ROLE` → exit 3 `baseline.role_required`, baseline file unchanged.
- `promote_baseline_requires_three_consecutive_passes` — FR-F067-15: a `failed` run in the last three → exit 1, nothing written.
- `superseded_baseline_archived` — FR-F067-15: the previous file lands under `baseline/archive/` keyed by `promoted_at`.
- `run_records_environment_and_command_line` — NFR-F067-04: image digests, `max_connections`, `shared_buffers`, `work_mem`, `checkpoint_timeout`, replica count, dataset hash, and the k6 argv are all present.
- `gate_counters_emitted` — NFR-F067-04: `load_gate_runs_total` and `load_gate_metric_verdict_total` written for every run including a skip.
- `no_openapi_operation_carries_f067` — FR-F067-13: negative control — `openapi/v1.json` gains no operation with `x-opshub-feature: F067` and the catalog row exposes a Surface cell, not routes.

Evidence: JUnit output, fake-k6 transcripts, and stub request logs under `testing/evidence/F067/api/`.
