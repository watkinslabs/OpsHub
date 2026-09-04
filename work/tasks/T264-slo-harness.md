---
id: T264
type: task
status: planned
parent_epic: E001
parent_feature: F066
parent_story: S132
depends_on: [S132]
owned_paths: [infra/slo/tests/**, testing/fixtures/slo/**, testing/features/F066/**]
feature_flag: F066_FEATURE
branch: t264-slo-harness
started_at: null
finished_at: null
---

# T264 — SLO harness

## Identity

- Parent story: `S132` Burn alerts and reporting
- Owner: platform
- Branch: `t264-slo-harness`
- Decision references: `docs/architecture-decisions.md` sections 9, 10; `docs/capability-contracts.md` row F066

## Objective

Build the offline harness that proves the objectives: `promtool test rules` suites over the committed generated rules, recorded `/metrics` expositions and instant-query snapshots, and the seven lane files under `testing/features/F066/` including the honest negative controls for the api, database, and frontend lanes.

## Specification

- Owned paths: `infra/slo/tests/{availability,latency,ack,no_data}.promtool.yml`, `testing/fixtures/slo/{objectives,expositions,rules,windows}/`, `testing/features/F066/{requirements,api,database,frontend,e2e,accessibility,performance}/`
- Contract/input: the committed `infra/prometheus/rules/slo-recording.yml` and `infra/alerts/burn-rate.yml`; Prometheus 3.4 `promtool`; integer-valued synthetic counter series so every ratio is exact.
- Output/behavior: `availability.promtool.yml` drives `core_read` and `core_write` counters through a 90%-success period of 65 minutes and asserts `slo:sli:ratio_rate1h`, `slo:burn_rate:ratio_rate1h`, that `SloFastBurn` fires at minute 7 with `severity: page` and `window: 1h/5m`, and that it resolves within 7 minutes of recovery because the 5m window clears first; it also drives an all-500 `/api/v1/reports` series and asserts `availability_core` stays at 1, proving analytics traffic cannot spend the core budget. `latency.promtool.yml` covers the `le="0.5"` and `le="0.8"` ratios and asserts that a 3% error rate sustained over three days fires only `SloBurn3d` at `severity: ticket`. `ack.promtool.yml` covers the `status="202"` and `le="2"` selector and the `insufficient_data` case under 100 samples. `no_data.promtool.yml` stops the `ack_async` series and asserts `SloNoData` fires after 15 minutes. Lane files: `requirements/cases.md` maps every FR-F066 and NFR-F066 id to a lane and a given/when/then; `api/cases.md` holds the CLI contract cases and the negative control that static mode opens no socket; `database/cases.md` holds the negative controls that no migration, table, or connection exists; `frontend/cases.md` holds the text-and-JSON report parity and the control that `apps/web/` and `openapi/v1.json` are untouched; `e2e/cases.md` runs the whole gate over a fixture tree; `accessibility/cases.md` covers ASCII, `NO_COLOR`, word-not-colour state, and runbook structure; `performance/cases.md` covers the run-time and series-count budgets. `feature.toml` and `README.md` name the flag, the two commands, the fixture set, and the lanes.
- Dependencies: T261 fixtures, T262 generated rules, T263 command behaviour; no Prometheus server, database, API, or browser is started by any case.
- Feature flag: `F066_FEATURE`; `cargo xtask test-feature F066` runs the Rust cases and the promtool suite together.

## TDD

- Failing test first: `infra/slo/tests/availability.promtool.yml::fast_burn_fires_at_minute_7`, `::fast_burn_resolves_within_seven_minutes`, `::analytics_errors_do_not_move_availability_core`; `infra/slo/tests/latency.promtool.yml::read_ratio_uses_le_0_5`, `::three_day_low_burn_fires_only_ticket_rule`; `infra/slo/tests/ack.promtool.yml::ack_ratio_counts_only_202_under_two_seconds`, `::under_100_samples_is_insufficient_data`; `infra/slo/tests/no_data.promtool.yml::no_data_pages_after_fifteen_minutes`; `testing/features/F066/api/harness_tests.rs::promtool_suite_passes_against_committed_rules`, `::exposition_fixtures_parse`, `::window_snapshots_cover_every_state`
- Targeted command: `cargo xtask test-feature F066`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/slo/expositions/{healthy,missing_bucket,unclassified_route,no_histogram}.txt`, `testing/fixtures/slo/windows/{ok,guarded,exhausted,insufficient_data,exception_live}.json`, `testing/fixtures/slo/objectives/{valid,overlap,bad_target,duplicate_id}.yml`, `testing/fixtures/slo/rules/{generated,hand_edited}.yml`; fixed clock `2026-09-03T00:00:00Z`

## Exit criteria

- [ ] Suites written before the implementation they cover and observed failing
- [ ] `promtool test rules infra/slo/tests/*.promtool.yml` passes and runs in under 60 seconds
- [ ] All seven lane files present with the required case counts, every FR and NFR id cited, and evidence paths named under `testing/evidence/F066/`
- [ ] No case starts Prometheus, PostgreSQL, the API, or a browser
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S132
- [ ] `finished_at` recorded
