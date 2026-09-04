---
id: T267
type: task
status: planned
parent_epic: E000
parent_feature: F067
parent_story: S134
depends_on: [S134]
owned_paths: [automation/xtask/src/load/**, testing/load/gate/**, testing/features/F067/api/**, testing/features/F067/accessibility/**]
feature_flag: F067_FEATURE
branch: t267-load-test-gate
started_at: null
finished_at: null
---

# T267 — Load-test gate

## Identity

- Parent story: `S134` Scale gate and evidence
- Owner: platform
- Branch: `t267-load-test-gate`
- Decision references: `docs/architecture-decisions.md` sections 7, 9, 10; `docs/capability-contracts.md` row F067

## Objective

Implement `cargo xtask load-test <profile>`: preflight and skip classification, the run lock, k6 process control, metric collection from k6 and Prometheus, threshold evaluation, exit codes, and the command's output contract.

## Specification

- Owned paths: `automation/xtask/src/load/{runner.rs, preflight.rs, lock.rs, metrics.rs, thresholds.rs}`, `testing/load/gate/{metrics.toml, environment.toml, thresholds.toml}`, and the `load-test` dispatch arm registered from `automation/xtask/src/load/mod.rs`
- Contract/input: `cargo xtask load-test <profile> [--dataset <name>] [--seed <u64>] [--baseline <path>] [--compare <run_id>] [--promote-baseline] [--require-env] [--dry-run] [--json]`; environment `LOAD_ENV_URL`, `LOAD_ENV_TOKEN`, `XTASK_ROLE`, `XTASK_OWNER`; `testing/load/gate/metrics.toml` mapping each metric id to one Prometheus range query.
- Output/behavior: preflight checks, in order, `LOAD_ENV_URL` and `LOAD_ENV_TOKEN` present, a 200 from `GET {LOAD_ENV_URL}/readyz` within 30 s, the pinned k6 version, a dataset manifest whose `generator_sha256` matches the current generator, and a free run lock; a failure yields `status: "skipped"` with `reason_code` in `env_unset`, `env_unreachable`, `runner_missing`, `dataset_missing`, `dataset_stale`, `concurrent_run`, prints `load-test <profile>: skipped (<reason_code>)`, and exits 0, while `--require-env` makes the same condition exit 2. Locking uses `pg_try_advisory_lock` on a hash of `LOAD_ENV_URL` plus `testing/load/gate/.run.lock` carrying pid, run id, and start time. k6 is spawned with the rendered profile JSON on a file descriptor, its NDJSON stdout parsed into 10-second samples, and its process group killed on cancellation, which writes `status: "aborted"` and exits 1. Server metrics come from the `metrics.toml` range queries evaluated over the hold window only, retried three times with exponential backoff; an empty series exits 2 with `metric.absent` and marks the run `failed`. Thresholds evaluated: `http_read_p95_ms` < 500, `http_write_p95_ms` < 800, `http_read_p99_ms` < 1500, `async_ack_p95_ms` < 2000, `achieved_rate_ratio` ≥ 0.99, `ws_broadcast_p95_ms` < 250, `ws_session_drop_rate` < 0.005, `db_pool_wait_p99_ms` < 50, `db_pool_in_use_ratio_p99` < 0.85, `outbox_lag_seconds_p99` < 5, `outbox_backlog_rows` < 1000 within 120 s of ramp-down, `job_queue_depth_p99` < 5000, `job_oldest_age_seconds_p99` < 60, `replication_lag_bytes_p99` < 33554432, `replication_lag_seconds_p99` < 10, `rss_slope_mib_per_hour` < 2.0 on `soak`, `http_5xx_rate` < 0.001, `dead_letter_count` = 0, `version_conflict_rate` < 0.03 on `concurrent-edit`. Exit codes: 0 for `passed`, `skipped`, and `regressed_unconfirmed`; 1 for `failed`, `regressed`, and `aborted`; 2 for usage, profile, dataset, and metric-collection errors; 3 for `role_required`. `--dry-run` prints the scenario plan and every threshold and contacts nothing. `--json` writes only the result document to stdout; human output prints the verdict word alongside any symbol; `LOAD_ENV_TOKEN` is redacted from `commands.log` and every emitted file.
- Dependencies: T265 dataset manifests; T266 profiles and scripts; F004 `outbox_events`, `job_runs`, and `dead_letters` exposed through the load environment's exporter; F043 `collect-artifacts` for lane pickup.
- Feature flag: `F067_FEATURE` gates the subcommand; `gates.yml` never references it and no pull request triggers it.

## TDD

- Failing test first: `testing/features/F067/api/preflight_tests.rs::missing_env_url_skips_with_env_unset`, `::unreachable_readyz_skips_with_env_unreachable`, `::stale_dataset_manifest_skips_with_dataset_stale`, `::require_env_turns_skip_into_exit_two`, `::wrong_k6_version_skips_with_runner_missing`; `testing/features/F067/api/lock_tests.rs::second_run_skips_with_concurrent_run`, `::killed_k6_marks_run_aborted`; `testing/features/F067/api/threshold_tests.rs::threshold_breach_on_outbox_lag_fails_run`, `::ramp_window_samples_excluded_from_statistics`, `::absent_prometheus_series_fails_not_passes`, `::exit_codes_map_to_statuses`; `testing/features/F067/accessibility/output_tests.rs::json_mode_emits_only_the_result_document`, `::verdict_words_present_without_color`, `::token_redacted_from_commands_log`
- Targeted command: `cargo xtask test-feature F067`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/load.rs` readiness stub returning 200, 503, and a timeout; Prometheus stub returning empty, partial, and complete series; fake k6 with scripted exit codes and a recorded NDJSON stream; per-worker advisory-lock key

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Skip, pass, fail, and abort paths each proven with a recorded exit code
- [ ] `.github/workflows/load.yml` scheduled and dispatch triggers requested from the `.github/workflows/**` owner (F001) against this specification, invoking the gate with `--require-env`, and `gates.yml` confirmed unchanged
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S134
- [ ] `finished_at` recorded
