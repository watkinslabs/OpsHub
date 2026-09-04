# F067 e2e cases

End to end for this feature is a whole `cargo xtask load-test <profile>` invocation at `smoke` scale against a stubbed environment, plus the milestone hook `verify-release` applies to the stored result.

File: `testing/features/F067/e2e/{smoke_profile_tests.rs,skip_path_tests.rs,milestone_gate_tests.rs,trigger_tests.rs}`. Flag `F067_FEATURE`. Fixtures: `smoke` dataset at 1/100 scale, fake k6, Prometheus and readiness stubs, a fake git history.

- `each_profile_runs_at_smoke_scale` — FR-F067-02: `steady-read`, `concurrent-edit`, `bulk-automation`, and `soak` (time-compressed to 8 min) each complete and write a full run directory.
- `passing_run_writes_complete_evidence_and_exits_zero` — FR-F067-13: every threshold met → `status: "passed"`, eight files present, `index.json` appended.
- `failing_run_reports_the_breaching_metric` — FR-F067-08: the stub raises outbox lag to 11.4 s → exit 1 naming `outbox_lag_seconds_p99`, its value, and its threshold.
- `skipped_run_writes_reason_and_exits_zero` — FR-F067-11: no `LOAD_ENV_URL` → exit 0 with `env_unset` and a stored result record.
- `skipped_run_rejected_by_milestone_gate` — FR-F067-12: `verify-release --milestone M0` over that record reports `release.scale_missing`.
- `stale_full_run_reports_scale_stale` — FR-F067-12: a `passed` `full` run 15 days old → `release.scale_stale`.
- `non_ancestor_commit_rejected` — FR-F067-12: a `passed` run on a commit that is not an ancestor of the milestone head → `release.scale_missing`.
- `failed_full_run_reports_scale_failed` — FR-F067-12: a `failed` run within the window → `release.scale_failed`.
- `gate_absent_from_pull_request_triggers` — FR-F067-12: `gates.yml` references no load command and the load workflow declares only `schedule` and `workflow_dispatch`.
- `scheduled_invocation_uses_require_env` — FR-F067-11: the scheduled job passes `--require-env`, so a missing environment exits 2 instead of skipping quietly.
- `regression_sequence_blocks_only_on_confirmation` — FR-F067-14: two consecutive regressing runs move the milestone from allowed to blocked.
- `collect_artifacts_picks_up_the_run_directory` — FR-F067-13: F043 `collect-artifacts` copies `testing/evidence/F067/runs/<run_id>/**` with per-file sha256.

Evidence: command transcripts, exit codes, and run directories under `testing/evidence/F067/e2e/`.
