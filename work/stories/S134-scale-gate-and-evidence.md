---
id: S134
type: story
status: planned
parent_epic: E000
parent_feature: F067
depends_on: [F043, F044]
owned_paths: [automation/xtask/src/load/**, testing/load/gate/**, testing/evidence/F067/**, testing/features/F067/**]
feature_flag: F067_FEATURE
branch: s134-scale-gate-and-evidence
started_at: null
finished_at: null
---

# S134 — Scale gate and evidence

## Identity

- Parent feature: `F067` System scale and load validation
- Owner: platform
- Branch: `s134-scale-gate-and-evidence`
- Decision references: `docs/architecture-decisions.md` sections 7, 9, 10; `docs/capability-contracts.md` row F067

## Vertical slice

As a release manager, I want `cargo xtask load-test <profile>` to run a profile against the load environment, gate on the saturation signals that fail before latency does, refuse to look like a pass when the environment is missing, and record every run under `testing/evidence/F067/` so the next run can be compared against it, so that a milestone decision rests on a measured, reproducible, and comparable scale result.

## Requirements

- **SR-S134-01:** The gate evaluates latency and throughput over the hold window only — `http_read_p95_ms` < 500, `http_write_p95_ms` < 800, `http_read_p99_ms` < 1500, `async_ack_p95_ms` < 2000, `achieved_rate_ratio` ≥ 0.99, plus `ws_broadcast_p95_ms` < 250 and `ws_session_drop_rate` < 0.005 on the editing profiles (covers FR-F067-07, NFR-F067-02).
- **SR-S134-02:** The gate also evaluates the resources that saturate first — `db_pool_wait_p99_ms` < 50, `db_pool_in_use_ratio_p99` < 0.85, `outbox_lag_seconds_p99` < 5 with `outbox_backlog_rows` under 1,000 within 120 s of ramp-down, `job_queue_depth_p99` < 5,000, `job_oldest_age_seconds_p99` < 60, `replication_lag_bytes_p99` < 33554432, `replication_lag_seconds_p99` < 10, `rss_slope_mib_per_hour` < 2.0 on `soak`, `http_5xx_rate` < 0.001, `dead_letter_count` = 0, and `version_conflict_rate` < 0.03 on `concurrent-edit` (FR-F067-08).
- **SR-S134-03:** Server-side metrics come from the Prometheus range queries in `testing/load/gate/metrics.toml` over the hold window; a query returning no series exits 2 with `metric.absent` and the run is `failed`, so a dead exporter can never read as a clean result (FR-F067-09, NFR-F067-04).
- **SR-S134-04:** Preflight checks `LOAD_ENV_URL`, `LOAD_ENV_TOKEN`, a 200 from `GET {LOAD_ENV_URL}/readyz` within 30 s, the pinned k6 version, a current dataset manifest, and the run lock, and on failure writes `status: "skipped"` with `reason_code` in `env_unset`, `env_unreachable`, `runner_missing`, `dataset_missing`, `dataset_stale`, `concurrent_run` and exits 0; `--require-env` turns the same condition into exit 2 for the scheduled job (FR-F067-11, FR-F067-10).
- **SR-S134-05:** The gate runs only from `.github/workflows/load.yml` on `schedule` (nightly `tier1` `steady-read` and `concurrent-edit`; weekly `tier1` `bulk-automation` and `soak`) and `workflow_dispatch`, never from `gates.yml` and never on a pull request; `verify-release --milestone M#` requires a `passed` `full`-dataset run per profile within 14 days on an ancestor commit and reports `release.scale_missing`, `release.scale_stale`, or `release.scale_failed` otherwise, accepting no `skipped` run (FR-F067-12).
- **SR-S134-06:** Every run writes `testing/evidence/F067/runs/<run_id>/` with `result.json`, `summary.json`, `metrics.ndjson.zst`, `server-metrics.json`, `environment.json`, `dataset.json`, `commands.log`, and `report.md`, where `run_id = <YYYYMMDDTHHMMSSZ>-<profile>-<dataset>-<commit12>`; the small records are tracked and the bulk artifacts stay untracked as `testing/evidence/README.md` prescribes (FR-F067-13, FR-F067-16).
- **SR-S134-07:** Regression comparison uses the median of the last three `passed` runs of the same profile and dataset, or the promoted baseline when fewer exist, with the four rules of FR-F067-14; an absolute breach fails at once, while a comparison-only regression yields `regressed_unconfirmed` at exit 0 and only becomes `regressed` at exit 1 when the next run regresses on the same metric id (FR-F067-14).
- **SR-S134-08:** `--promote-baseline` requires three consecutive `passed` runs and `XTASK_ROLE=maintainer` with `XTASK_OWNER`, or CI on `main`, writes `testing/evidence/F067/baseline/<profile>-<dataset>.json` with `promoted_from`, and archives the superseded file; otherwise it exits 3 with `baseline.role_required` and writes nothing (FR-F067-15).
- **SR-S134-09:** One run at a time per environment through a PostgreSQL advisory lock plus `testing/load/gate/.run.lock`; a second run is `skipped` with `concurrent_run`, a lost lock or dead k6 process yields `status: "aborted"` at exit 1, and an aborted run is excluded from the comparison reference set (FR-F067-17, NFR-F067-02).
- **SR-S134-10:** Output is machine- and reader-safe: `--json` writes only `result.json` to stdout, verdicts print the words `pass`, `fail`, `skip`, or `regressed` alongside any symbol, exit codes separate the outcomes without reading text, `report.md` carries the sections `Verdict`, `Environment`, `Dataset`, `Thresholds`, `Comparison`, `Findings` with real table header cells, and `LOAD_ENV_TOKEN` is redacted everywhere (NFR-F067-05, NFR-F067-03).

## Surfaces

- Infrastructure/container: `.github/workflows/load.yml` scheduled and dispatch triggers (added by the F001 workflow owner from this specification); the load environment's Prometheus queried read-only; no change to `gates.yml`
- Rust service/API: no route and no service change; `automation/xtask/src/load/{runner.rs, metrics.rs, thresholds.rs, compare.rs, evidence.rs, report.rs, lock.rs, preflight.rs}`
- Data/migration: no migration, no owned table, and no repository added; `pg_stat_activity`, `pg_stat_replication`, `outbox_events`, `job_runs`, and `dead_letters` are read through the load environment's exporter only, so `runner.rs`, `metrics.rs`, `thresholds.rs`, `compare.rs`, `evidence.rs`, `report.rs`, `lock.rs`, and `preflight.rs` write no table and contain no SQL beyond the session-level advisory lock of SR-S134-09 (decision 2.1)
- React/UI: none; the only reader-facing artifact is the plain-Markdown `report.md`, whose sections and table headers are asserted in the frontend lane
- Mocks/fixtures: `testing/fixtures/load.rs` readiness stub returning 200, 503, and a timeout; Prometheus stub returning empty, partial, and complete series; fake k6 with scripted exit codes; a synthetic 8-hour sample stream for the reporter budget

## TDD harness

- Test path: `testing/features/F067/{api,e2e,accessibility,performance}/`
- Feature flag: `F067_FEATURE`
- Targeted command: `cargo xtask test-feature F067`
- Full command: `cargo xtask test-all`
- First failing tests: `threshold_breach_on_outbox_lag_fails_run`, `absent_prometheus_series_fails_not_passes`, `missing_env_url_skips_with_env_unset`, `require_env_turns_skip_into_exit_two`, `skipped_run_rejected_by_milestone_gate`, `first_regression_is_unconfirmed_second_is_confirmed`, `promote_baseline_requires_maintainer_role`, `second_run_skips_with_concurrent_run`, `aborted_run_excluded_from_reference_set`, `report_md_has_required_sections_and_headers`

## Exit criteria

- [ ] Requirement tests SR-S134-01 through SR-S134-10 written first and failing
- [ ] Tasks T267 and T268 complete and wired through the `load-test` arm in `automation/xtask/src/main.rs`
- [ ] Skip, fail, pass, unconfirmed-regression, confirmed-regression, and abort paths each proven with a stored evidence directory under `testing/features/F067/`
- [ ] `verify-release --milestone M0` reads `testing/evidence/F067/index.json` and rejects a `skipped` scale run
- [ ] Production call path named: `automation/xtask/src/main.rs` dispatches `load-test` into `automation/xtask/src/load/runner.rs`, which writes `testing/evidence/F067/runs/<run_id>/result.json` that `automation/xtask/src/release.rs` reads for the milestone gate
- [ ] Handoff evidence recorded in the F067 ticket
