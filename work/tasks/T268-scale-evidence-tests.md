---
id: T268
type: task
status: planned
parent_epic: E000
parent_feature: F067
parent_story: S134
depends_on: [S134]
owned_paths: [automation/xtask/src/load/**, testing/evidence/F067/**, testing/features/F067/api/**, testing/features/F067/frontend/**, testing/features/F067/e2e/**, testing/features/F067/performance/**]
feature_flag: F067_FEATURE
branch: t268-scale-evidence-tests
started_at: null
finished_at: null
---

# T268 — Scale evidence tests

## Identity

- Parent story: `S134` Scale gate and evidence
- Owner: platform
- Branch: `t268-scale-evidence-tests`
- Decision references: `docs/architecture-decisions.md` sections 9, 10; `docs/capability-contracts.md` row F067

## Objective

Implement and prove the evidence layer: the run directory and result document, the run index, the Markdown report, baseline promotion with role gating, the regression comparison with its unconfirmed-then-confirmed rule, and the milestone hook `verify-release` reads.

## Specification

- Owned paths: `automation/xtask/src/load/{evidence.rs, compare.rs, report.rs}`, `testing/evidence/F067/{runs/, baseline/, datasets/, index.json}`
- Contract/input: `RunResult { run_id, status, profile, dataset, seed, commit, started_at, finished_at, metrics: Vec<MetricVerdict>, reason_code?, reason? }` where `status` is one of `passed`, `failed`, `regressed`, `regressed_unconfirmed`, `skipped`, `aborted`; `MetricVerdict { id, statistic, value, threshold, verdict, baseline_value, comparison_verdict }`; `run_id = <YYYYMMDDTHHMMSSZ>-<profile>-<dataset>-<commit12>`.
- Output/behavior: each run writes `testing/evidence/F067/runs/<run_id>/` holding `result.json`, `summary.json`, `metrics.ndjson.zst`, `server-metrics.json`, `environment.json` (image digests, `max_connections`, `shared_buffers`, `work_mem`, `checkpoint_timeout`, replica count), `dataset.json`, `commands.log`, and `report.md`; `result.json`, `environment.json`, `dataset.json`, `report.md`, `baseline/**`, and `index.json` are tracked while the three bulk artifacts stay untracked. Re-running an existing `run_id` exits 2 with `run.exists` rather than overwriting. `index.json` keeps the last 30 runs per profile and dataset with `run_id`, status, commit, `finished_at`, and key metrics. `report.md` renders the sections `Verdict`, `Environment`, `Dataset`, `Thresholds`, `Comparison`, and `Findings`, where `Thresholds` and `Comparison` are Markdown tables with header cells for metric id, statistic, value, threshold or reference, and verdict word. Comparison takes the median of the last three `passed` runs of the same profile and dataset, falling back to the promoted baseline, and excludes `aborted` and `skipped` runs: latency and lag regress above `reference * 1.10 + 15`, throughput and `achieved_rate_ratio` regress below `reference * 0.90`, saturation metrics regress above `reference * 1.25`, error rates regress above `max(reference * 2, 0.001)`; an absolute breach fails immediately, a comparison-only regression is `regressed_unconfirmed` at exit 0 and becomes `regressed` at exit 1 only when the next run of the same profile and dataset regresses on the same metric id. `--promote-baseline` requires three consecutive `passed` runs plus `XTASK_ROLE=maintainer` with `XTASK_OWNER`, or CI on `main`, writes `baseline/<profile>-<dataset>.json` with `promoted_from`, `promoted_by`, `commit`, metric values, and a reason, archives the superseded file under `baseline/archive/`, and otherwise exits 3 with `baseline.role_required` writing nothing. `automation/xtask/src/release.rs` reads `index.json` and the referenced `result.json` files so `verify-release --milestone M#` requires one `passed` `full`-dataset run per profile within 14 days on an ancestor commit and reports `release.scale_missing`, `release.scale_stale`, or `release.scale_failed`, never accepting a `skipped` run. Negative controls assert that no route, migration, React module, or OpenAPI operation is added for this feature.
- Dependencies: T267 runner and metric collection; F043 `collect-artifacts` for lane pickup; F044 `verify-release` for the milestone hook.
- Feature flag: `F067_FEATURE` gates the subcommand; evidence files are inert data read by the release verifier.

## TDD

- Failing test first: `testing/features/F067/api/evidence_tests.rs::run_directory_contains_every_required_file`, `::rerunning_existing_run_id_exits_run_exists`, `::index_keeps_last_thirty_per_profile_and_dataset`, `::aborted_and_skipped_runs_excluded_from_reference_set`; `testing/features/F067/api/compare_tests.rs::latency_band_allows_ten_percent_plus_fifteen_ms`, `::saturation_regresses_above_one_point_two_five`, `::first_regression_is_unconfirmed_second_is_confirmed`, `::absolute_breach_fails_without_waiting_for_confirmation`; `testing/features/F067/api/baseline_tests.rs::promote_baseline_requires_maintainer_role`, `::promote_baseline_requires_three_consecutive_passes`, `::superseded_baseline_archived`; `testing/features/F067/frontend/report_tests.rs::report_md_has_required_sections_and_headers`, `::no_web_feature_module_or_openapi_operation_for_f067`; `testing/features/F067/e2e/milestone_gate_tests.rs::skipped_run_rejected_by_milestone_gate`, `::stale_full_run_reports_scale_stale`; `testing/features/F067/performance/reporter_tests.rs::eight_hour_stream_renders_under_sixty_seconds`
- Targeted command: `cargo xtask test-feature F067`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/load.rs` recorded run directories for pass, fail, skip, abort, and two-run regression sequences; a synthetic 8-hour sample stream of 2.9 million rows; a fake git history for ancestor and age checks; role and CI environment stubs

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Pass, fail, skip, abort, unconfirmed-regression, and confirmed-regression runs each stored and asserted
- [ ] `verify-release --milestone M0` proven to reject a `skipped` scale run and a run older than 14 days
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S134
- [ ] `finished_at` recorded
