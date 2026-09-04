---
id: T263
type: task
status: planned
parent_epic: E001
parent_feature: F066
parent_story: S132
depends_on: [S132]
owned_paths: [automation/xtask/src/slo.rs, infra/slo/exceptions.yml, infra/slo/runbook.md, infra/slo/README.md, testing/features/F066/api/**, testing/features/F066/database/**, testing/features/F066/frontend/**]
feature_flag: F066_FEATURE
branch: t263-verify-slo-gate
started_at: null
finished_at: null
---

# T263 — verify-slo gate

## Identity

- Parent story: `S132` Burn alerts and reporting
- Owner: platform
- Branch: `t263-verify-slo-gate`
- Decision references: `docs/architecture-decisions.md` sections 9, 10; `docs/capability-contracts.md` row F066

## Objective

Implement `cargo xtask verify-slo` in both modes — the static gate and the budget report — with the shared 0/1/2/3 exit codes, the F041 text and JSON output contract, alert-to-objective linkage over `infra/alerts/`, and the error-budget policy that refuses a release while a budget is exhausted.

## Specification

- Owned paths: the command half of `automation/xtask/src/slo.rs`, `infra/slo/exceptions.yml`, `infra/slo/runbook.md`, `infra/slo/README.md`
- Contract/input: `verify-slo [--metrics PATH|URL] [--write-rules] [--json]` and `verify-slo --budget --source PATH|URL [--json]`; `XTASK_ROLE=operator` or CI on `main` to record; `infra/slo/exceptions.yml` entries `{ objective, reason, owner, ticket, expires_at }`; instant-query snapshot JSON carrying `slo:sli:ratio_rate28d`, `slo:budget:remaining_ratio28d`, and the sample count per objective.
- Output/behavior: static mode runs schema, class, drift, threshold, window-pair, alert-link, bucket, and cardinality checks and prints `verify-slo passed (4 objectives, 7 classes)` or one `BLOCKED: <code> <path>:<line>: <message>` line per finding sorted by path then line then code, closing with `verify-slo failed: <n> findings`; `--json` prints exactly one `{ "command", "ok", "checked", "findings": [{ "code", "path", "line", "message" }], "duration_ms" }` object. `check_alert_links` reads every rule file under `infra/alerts/`, including F004's `rules.yml`, and reports `slo.alert_unlinked` for a missing `objective` label or a `runbook` annotation whose anchor is absent from `infra/slo/runbook.md`. Budget mode computes per-objective `state` (`ok` above 0.25 remaining, `guarded` in `(0, 0.25]`, `exhausted` at or below 0, `insufficient_data` under 100 samples), prints the five-column table `objective | target | 28d ratio | remaining | state`, writes `testing/evidence/F066/slo-report.json` with the SHA-256 of `objectives.yml`, and exits 3 with `REFUSED: slo.budget_exhausted <id>` when any objective is exhausted without an unexpired matching exception, or with `dry run: operator role required to record` when the role is absent. An expired, malformed, or wrong-objective exception is `slo.exception_expired` and never suppresses the refusal. Exit codes: 0 clean, 1 findings, 2 usage or I/O error, 3 refusal. `infra/slo/runbook.md` carries the per-severity anchors, the F004 symptom-alert mapping, and the guarded and exhausted policies; `infra/slo/README.md` carries the exact `main.rs` dispatch line and `gates.yml` step text.
- Dependencies: T261's model, T262's renderers, F041's `support::OutputFormat` and reporter, F044's exit-code convention and role-gated recording, F004's `infra/alerts/rules.yml` as a read-only input and its secret source for the optional Prometheus bearer token.
- Feature flag: `F066_FEATURE` gates the CI step; disabling it skips the gate without removing the command.

## TDD

- Failing test first: `testing/features/F066/api/gate_tests.rs::clean_tree_exits_zero_with_summary_line`, `::findings_are_sorted_by_path_line_code`, `::json_object_matches_f041_shape`, `::unknown_flag_exits_two`, `::unreadable_objectives_file_exits_two`, `::static_mode_opens_no_socket`; `testing/features/F066/api/link_tests.rs::f004_rule_without_objective_label_is_unlinked`, `::runbook_anchor_missing_reports_alert_unlinked`, `::linked_rules_pass`; `testing/features/F066/api/report_tests.rs::exhausted_budget_refuses_with_exit_3`, `::guarded_state_reported_between_zero_and_quarter`, `::insufficient_data_excluded_from_freeze`, `::live_exception_allows_release`, `::expired_exception_does_not_suppress_refusal`, `::exception_for_other_objective_does_not_suppress`, `::budget_without_operator_role_runs_dry`, `::report_is_deterministic_across_runs`; `testing/features/F066/database/no_persistence_tests.rs::no_slo_migration_file_exists`, `::verify_slo_opens_no_database_connection`; `testing/features/F066/frontend/report_render_tests.rs::text_and_json_report_carry_the_same_fields`, `::no_color_output_has_no_escape_sequences`
- Targeted command: `cargo xtask test-feature F066`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/slo/windows/{ok,guarded,exhausted,insufficient_data,exception_live}.json`; per-case temporary copies of `infra/slo/` and `infra/alerts/`; a loopback listener on port 0 that fails the test on any accepted connection in static mode; fixed clock `2026-09-03T00:00:00Z`

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Exit codes 0, 1, 2, and 3 each demonstrated against a fixture with the `--json` shape asserted
- [ ] `infra/slo/runbook.md` anchors resolve for every generated alert and for every F004 rule under `infra/alerts/`
- [ ] Owned-path check passes; `infra/alerts/rules.yml` is read and never written
- [ ] File limit and lint gates pass; `automation/xtask/src/slo.rs` stays under 500 lines
- [ ] Handoff evidence recorded in S132
- [ ] `finished_at` recorded
