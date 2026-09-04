---
id: S132
type: story
status: planned
parent_epic: E001
parent_feature: F066
depends_on: [S131]
owned_paths: [automation/xtask/src/slo.rs, infra/slo/exceptions.yml, infra/slo/runbook.md, infra/slo/README.md, infra/slo/tests/**, testing/fixtures/slo/**, testing/features/F066/**]
feature_flag: F066_FEATURE
branch: s132-burn-alerts-and-reporting
started_at: null
finished_at: null
---

# S132 — Burn alerts and reporting

## Identity

- Parent feature: `F066` Service levels and error budgets
- Owner: platform
- Branch: `s132-burn-alerts-and-reporting`
- Decision references: `docs/architecture-decisions.md` sections 3, 9, 10; `docs/capability-contracts.md` row F066

## Vertical slice

As an operator, I want each burn-rate pair to carry a stated meaning and a runbook anchor, F004's existing symptom alerts linked to the objective they threaten, and `cargo xtask verify-slo --budget` to print how many budget minutes are left and refuse the release when they are gone, so that an alert tells the on-call what to do and a release decision rests on the account rather than on optimism.

## Requirements

- **SR-S132-01:** `infra/slo/runbook.md` states the meaning of each pair with its consequence: 13.44 over 1h/5m exhausts the 28-day budget in 50 hours and pages the on-call at any hour; 5.6 over 6h/30m exhausts it in 5 days and pages with a 30-minute response expectation; 2.8 over 24h/2h opens a ticket by the next working day for the owning module's feature owner; 0.93 over 3d/6h opens a ticket for the weekly operations review. Each severity has its own heading anchor, and every generated alert's `runbook` annotation resolves to one of them (covers FR-F066-10, FR-F066-11).
- **SR-S132-02:** `SloNoData` fires at `severity: page` after `for: 15m` on `absent(slo:sli:ratio_rate5m{objective="<id>"})` for every objective, and an objective whose 28-day denominator is under 100 requests reports `insufficient_data` rather than `breached` and is excluded from the freeze (FR-F066-10, FR-F066-14).
- **SR-S132-03:** `check_alert_links` walks every alerting rule under `infra/alerts/` — including F004's `rules.yml`, which this story reads and never writes — and reports `slo.alert_unlinked` for any rule without an `objective` label naming a declared id and a `runbook` annotation resolving to an existing anchor; the runbook records that `outbox_pending_events` and dead-letter growth threaten `ack_async` and that `/readyz` failure threatens `availability_core` (FR-F066-11).
- **SR-S132-04:** `cargo xtask verify-slo [--metrics PATH] [--json]` runs the static gate and follows the F041 output contract exactly: `BLOCKED: <code> <path>:<line>: <message>` on stderr sorted by path then line then code, `verify-slo passed (4 objectives, 7 classes)` on stdout, one `{ "command", "ok", "checked", "findings", "duration_ms" }` object under `--json`, and exit codes 0 clean, 1 findings, 2 usage or I/O error, 3 refusal (FR-F066-13).
- **SR-S132-05:** `cargo xtask verify-slo --budget --source <file|url>` writes `testing/evidence/F066/slo-report.json` with per-objective `ratio`, `remaining_ratio`, `remaining_minutes`, `budget_minutes`, `sample_count`, and `state` in `ok | guarded | exhausted | insufficient_data`, prints the same data as a five-column text table, records the SHA-256 of `objectives.yml`, and is byte-identical across two runs on one snapshot apart from `generated_at` (FR-F066-14, NFR-F066-04).
- **SR-S132-06:** An `exhausted` objective without a live exception prints `REFUSED: slo.budget_exhausted <id>` and exits 3 after the full table; `--budget` without `XTASK_ROLE=operator` and outside CI on `main` runs every check, prints `dry run: operator role required to record`, exits 3, and writes nothing; an exception in `infra/slo/exceptions.yml` suppresses the refusal only for its own objective, only while unexpired, and only with `owner`, `ticket`, `reason`, and `expires_at` at most 14 days out, otherwise `slo.exception_expired` (FR-F066-14, FR-F066-15, NFR-F066-05).
- **SR-S132-07:** The policy in the runbook is operational, not a slogan: `guarded` requires a named second reviewer and a verified rollback entry for changes to the failing objective's modules and forbids turning a feature flag on in production; `exhausted` allows only `reliability`, `security`, and `rollback` changes, makes the report's largest burn contributor the first item of the next iteration, and lifts automatically when the rolling window recovers above 25% remaining (FR-F066-15).
- **SR-S132-08:** `infra/slo/tests/{availability,latency,ack,no_data}.promtool.yml` prove the expressions and the burn arithmetic against the committed generated rules with `promtool test rules` and no running Prometheus, database, or API; recorded expositions and instant-query snapshots under `testing/fixtures/slo/` cover healthy, guarded, exhausted, insufficient-data, and live-exception windows (FR-F066-16).
- **SR-S132-09:** Output is ASCII, honours `NO_COLOR`, states every objective's state as a word rather than by colour, wraps no line beyond 200 characters, and the `--json` form carries every field the table shows; the runbook uses a heading hierarchy and plain-text tables (NFR-F066-03).

## Surfaces

- Infrastructure/configuration: `infra/slo/runbook.md` (meanings, routing, policy, anchors), `infra/slo/exceptions.yml`, `infra/slo/README.md` (the `main.rs` dispatch line and the `gates.yml` step text), `infra/slo/tests/*.promtool.yml`
- Rust service/API: `automation/xtask/src/slo.rs` — `check_alert_links`, `Snapshot`, `Report`, `budget_report`, `verify_slo` argument parsing, text and JSON renderers over F041's `support::OutputFormat`
- Data/migration: none; the only durable state is `infra/slo/exceptions.yml` and `testing/evidence/F066/slo-report.json`
- React/UI: none; the text table and the JSON object are the two renderings of the report
- Mocks/fixtures: `testing/fixtures/slo/windows/{ok,guarded,exhausted,insufficient_data,exception_live}.json`, a loopback listener returning a canned instant-query body for the single live-URL case, fixed clock `2026-09-03T00:00:00Z`

## TDD harness

- Test path: `testing/features/F066/{api,database,frontend,e2e,accessibility}/`
- Feature flag: `F066_FEATURE`
- Targeted command: `cargo xtask test-feature F066`
- Full command: `cargo xtask test-all`
- First failing tests: `fast_burn_pages_after_two_minutes`, `fast_burn_clears_when_short_window_recovers`, `slow_burn_only_opens_a_ticket`, `no_data_pages_after_fifteen_minutes`, `f004_rule_without_objective_label_is_unlinked`, `runbook_anchor_missing_reports_alert_unlinked`, `exhausted_budget_refuses_with_exit_3`, `live_exception_allows_release`, `expired_exception_does_not_suppress_refusal`, `budget_without_operator_role_runs_dry`, `report_is_deterministic_across_runs`, `text_and_json_report_carry_the_same_fields`

## Exit criteria

- [ ] Requirement tests SR-S132-01 through SR-S132-09 written first and observed failing
- [ ] Tasks T263 and T264 complete; `promtool test rules infra/slo/tests/*.promtool.yml` passes
- [ ] Exit codes 0, 1, 2, and 3 each demonstrated against a fixture, with the `--json` shape asserted for each
- [ ] Negative controls pass: no migration added, no database connection opened, no socket opened in static mode, `apps/web/` and `openapi/v1.json` unchanged
- [ ] Production call path named: `verify-slo` dispatched from `automation/xtask/src/main.rs` and executed as a step in `.github/workflows/gates.yml`
- [ ] Handoff evidence recorded in the F066 ticket
