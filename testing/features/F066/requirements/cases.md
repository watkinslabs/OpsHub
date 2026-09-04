# F066 requirements cases

Feature: Service levels and error budgets. Flag `F066_FEATURE`. Every case maps to a ticket requirement ID. No case starts Prometheus, a database, the API, or a browser.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F066-REQ-001` | FR-F066-01 | api | `objectives.yml` loads with version, window, classes, objectives, burn_alerts, policy; unknown key, target 1.0, duplicate id, unreferenced class → `slo.schema` with the line |
| `F066-REQ-002` | FR-F066-02 | api | seven classes disjoint per `(route, method)`; `/api/v1/users` GET → `core_read`, PATCH → `core_write`; overlap → `slo.class_overlap`; `/api/v1/widgets` in the sample → `slo.route_unclassified` naming the route |
| `F066-REQ-003` | FR-F066-03 | api, e2e | availability ratio counts only non-5xx over `core_read` plus `core_write`; a 4xx stays good; all-500 `/api/v1/reports` leaves the ratio at 1 |
| `F066-REQ-004` | FR-F066-04 | api, e2e | `latency_core_read` divides the `le="0.5"` bucket rate by the `core_read` count rate at target 0.95; a fast 500 is counted bad |
| `F066-REQ-005` | FR-F066-05 | api, e2e | `latency_core_write` uses `le="0.8"` over `core_write` at target 0.95 |
| `F066-REQ-006` | FR-F066-06 | api, e2e | `ack_async` uses `status="202"` and `le="2"` at target 0.99; a 202 at 2.4 s is bad, a completed job at 40 s is irrelevant |
| `F066-REQ-007` | FR-F066-07 | api | window is 40,320 minutes; budgets are 201.6, 2,016, 2,016, and 403.2 minutes; `slo:budget:remaining_minutes28d` scales by them; overspend gives a negative remaining |
| `F066-REQ-008` | FR-F066-08 | api, performance | recording rules exist for all eight windows, expand classes into route alternations, keep no `route` label, and match the committed file; a hand edit → `slo.rule_drift` |
| `F066-REQ-009` | FR-F066-09 | api, e2e | four pairs with derived factors 13.44, 5.6, 2.8, 0.93 and `for` 2m, 15m, 1h, 6h; both windows required; edited factor → `slo.threshold_drift`; 1h/10m → `slo.window_pair` |
| `F066-REQ-010` | FR-F066-10 | e2e | fast burn pages, 3d burn only tickets, `SloNoData` pages after 15 minutes of an absent series, under 100 samples reports `insufficient_data` |
| `F066-REQ-011` | FR-F066-11 | api | every rule under `infra/alerts/` carries an `objective` label and a resolving `runbook` anchor; F004's `outbox_pending_events` rule without one → `slo.alert_unlinked` |
| `F066-REQ-012` | FR-F066-12 | api | missing `le="0.8"` series → `slo.bucket_missing` naming objective and boundary; non-histogram metric rejected; absent sample → `skipped:` and pass |
| `F066-REQ-013` | FR-F066-13 | api, frontend | static run prints the summary line, sorted `BLOCKED:` findings, or the single `--json` object; exits 0, 1, and 2 on the matching fixtures |
| `F066-REQ-014` | FR-F066-14 | api, e2e | `--budget` writes `slo-report.json` with per-objective ratio, remaining minutes, sample count, and state; exhausted → `REFUSED: slo.budget_exhausted` and exit 3; exit 2 writes nothing |
| `F066-REQ-015` | FR-F066-15 | api, e2e | guarded and exhausted policies enforced; only reliability, security, and rollback changes ship while frozen; recovery above 25% lifts it; exception needs owner, ticket, reason, and expiry ≤ 14 days |
| `F066-REQ-016` | FR-F066-16 | e2e, performance | `promtool test rules` over the committed rules proves the ratios and alert timings; recorded expositions and window snapshots cover every state; nothing is started |
| `F066-NFR-001` | NFR-F066-01 | performance | static run < 2 s over a 2 MiB exposition; snapshot budget run < 500 ms; promtool suite < 60 s; at most 40 recorded series, 8 classes, 6 objectives; `route` in output labels → `slo.cardinality` |
| `F066-NFR-002` | NFR-F066-02 | api, database | no tenant or user id in objectives, rules, or report; static mode opens no socket; no database connection; writes confined to `infra/slo/`, `infra/prometheus/rules/`, `infra/alerts/burn-rate.yml`, `testing/evidence/F066/` |
| `F066-NFR-003` | NFR-F066-03 | accessibility, frontend | ASCII only, `NO_COLOR` honoured, state printed as a word, no line over 200 characters, `--json` carries every table field, runbook headings and anchors resolve |
| `F066-NFR-004` | NFR-F066-04 | api, e2e | `SloNoData` covers the pipeline; every alert resolves to a runbook anchor; two report runs are byte-identical apart from `generated_at`; the report records the objectives SHA-256 |
| `F066-NFR-005` | NFR-F066-05 | api | exceptions bounded by owner, ticket, reason, and 14-day expiry; live exceptions listed beside their objective in the report; expired or foreign exception never suppresses a refusal |

Evidence: command, fixture path, exit code, and artifact recorded under `testing/evidence/F066/`.
