# F066 — Service levels and error budgets harness

Feature-gated tests for `F066`. Keep test code in this directory.

- Gate: `F066_FEATURE`
- Targeted: `cargo xtask test-feature F066`
- Full: `cargo xtask test-all`
- What is proved here: the PromQL of `infra/prometheus/rules/slo-recording.yml`, the burn arithmetic of `infra/alerts/burn-rate.yml`, and the behaviour of `cargo xtask verify-slo` — never the infrastructure. No case starts Prometheus, PostgreSQL, the API, the worker, or a browser.
- Fixtures: `testing/fixtures/slo/objectives/{valid,overlap,bad_target,duplicate_id}.yml` (schema cases), `testing/fixtures/slo/expositions/{healthy,missing_bucket,unclassified_route,no_histogram}.txt` (recorded F004 `/metrics` text), `testing/fixtures/slo/windows/{ok,guarded,exhausted,insufficient_data,exception_live}.json` (recorded instant-query snapshots), `testing/fixtures/slo/rules/{generated,hand_edited}.yml` (drift baseline). Fixed clock `2026-09-03T00:00:00Z`; every case runs in a temporary tree holding its own copy of `infra/slo/` and `infra/alerts/`.
- Rule suites: `infra/slo/tests/{availability,latency,ack,no_data}.promtool.yml` executed with Prometheus 3.4 `promtool test rules` against the committed generated rules.
- Lanes: `requirements/` (traceability for every FR-F066 and NFR-F066 id), `api/` (CLI contract and unit cases, plus the no-network control), `database/` and `frontend/` (negative controls — this feature owns no table and no component), `e2e/` (the whole gate over a fixture tree), `accessibility/` (text output and runbook structure), `performance/` (run-time and cardinality budgets). Each `cases.md` lists the test names in that lane and the requirement ids they prove.
- Evidence: `testing/evidence/F066/` holding `slo-report.json`, promtool output, and the generated-versus-committed rule diff.
