---
id: T262
type: task
status: planned
parent_epic: E001
parent_feature: F066
parent_story: S131
depends_on: [S131]
owned_paths: [infra/prometheus/rules/slo-recording.yml, infra/alerts/burn-rate.yml, automation/xtask/src/slo.rs, testing/features/F066/api/**, testing/features/F066/performance/**]
feature_flag: F066_FEATURE
branch: t262-recording-rules-and-burn-alerts
started_at: null
finished_at: null
---

# T262 — Recording rules and burn alerts

## Identity

- Parent story: `S131` Objectives and measurement
- Owner: platform
- Branch: `t262-recording-rules-and-burn-alerts`
- Decision references: `docs/architecture-decisions.md` sections 3, 9; `docs/capability-contracts.md` row F066

## Objective

Generate `infra/prometheus/rules/slo-recording.yml` and `infra/alerts/burn-rate.yml` from `infra/slo/objectives.yml`, with burn factors derived from the 28-day budget rather than typed in, and make any hand edit to either file fail the gate as drift.

## Specification

- Owned paths: `infra/prometheus/rules/slo-recording.yml`, `infra/alerts/burn-rate.yml`, the renderer half of `automation/xtask/src/slo.rs`
- Contract/input: the `Objectives` model from T261; windows `5m, 30m, 1h, 2h, 6h, 24h, 3d, 28d`; `burn_alerts` entries `{ severity, long, short, consumed }` for `1h/5m` at 0.02, `6h/30m` at 0.05, `24h/2h` at 0.10, and `3d/6h` at 0.10.
- Output/behavior: `render_recording_rules` emits, per objective and window, `slo:sli:ratio_rate<w>` built from `sum(rate(http_request_duration_seconds_count{...}[w]))` for availability and `sum(rate(http_request_duration_seconds_bucket{le="<threshold>",...}[w]))` for latency and acknowledgement, with each class expanded into an explicit `route=~"..."` and `method=~"..."` alternation and `label_replace` stamping `class`; then `slo:burn_rate:ratio_rate<w>` as `(1 - slo:sli:ratio_rate<w>) / (1 - <target>)`, and `slo:budget:remaining_ratio28d` and `slo:budget:remaining_minutes28d`. Every rule aggregates with `sum by (objective)` and keeps no `route` or `status` label; a renderer that would keep `route` fails as `slo.cardinality`. `render_burn_alerts` emits one alert per objective per pair, named `SloFastBurn`, `SloBurn6h`, `SloBurn24h`, and `SloBurn3d`, with `expr` requiring both windows over the factor, `for` of 2m, 15m, 1h, and 6h, labels `objective`, `severity` (`page`, `page`, `ticket`, `ticket`), and `window: <long>/<short>`, and annotations `summary`, `budget_minutes`, and `runbook`. Factors come from `consumed * 672.0 / long_hours`, giving 13.44, 5.6, 2.8, and 0.93 — no literal factor appears in the source. `--write-rules` writes both files; without it, a mismatch is `slo.rule_drift` naming the rule and `slo.threshold_drift` with expected and found factor, and a short window that is not one twelfth of its long window is `slo.window_pair`.
- Dependencies: T261's model and budget arithmetic; `promtool` 3.4 for PromQL validity in the harness; F004's metric names, which the rules read and never redefine.
- Feature flag: `F066_FEATURE`; the generated files are committed so a reviewer sees the promise change in the diff.

## TDD

- Failing test first: `testing/features/F066/api/render_tests.rs::recording_rules_match_committed_file`, `::rules_cover_all_eight_windows`, `::class_selector_expands_to_route_alternation`, `::rules_keep_no_route_label`, `::renderer_with_route_label_reports_cardinality`; `testing/features/F066/api/burn_tests.rs::burn_factors_derive_to_13_44_5_6_2_8_0_93`, `::hand_edited_burn_factor_reports_threshold_drift`, `::short_window_not_one_twelfth_reports_window_pair`, `::alert_carries_objective_severity_and_window_labels`, `::alert_expr_requires_both_windows`; `testing/features/F066/performance/render_bench.rs::generated_series_count_at_most_40`, `::render_and_diff_under_two_seconds`
- Targeted command: `cargo xtask test-feature F066`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/slo/rules/{generated,hand_edited}.yml`; the committed rule files themselves as the drift baseline; no Prometheus process is started

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] `cargo xtask verify-slo --write-rules` regenerates both committed files byte for byte and `promtool check rules` accepts them
- [ ] Owned-path check passes; `infra/alerts/rules.yml` is not modified by this task
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S131
- [ ] `finished_at` recorded
