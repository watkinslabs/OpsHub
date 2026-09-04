# F066 performance cases

The gate runs on every pull request and the rules run on every Prometheus evaluation interval, so both have budgets of their own. File: `testing/features/F066/performance/{gate_bench.rs,render_bench.rs}`. Flag `F066_FEATURE`.

- `static_gate_under_two_seconds` — NFR-F066-01: `verify-slo` over `objectives.yml`, both rule files, `infra/alerts/rules.yml`, and a 2 MiB exposition completes in under 2 s on `ubuntu-latest`.
- `budget_run_on_snapshot_under_500ms` — NFR-F066-01: `--budget --source testing/fixtures/slo/windows/ok.json` completes in under 500 ms including writing the report.
- `budget_run_against_live_prometheus_under_five_seconds` — NFR-F066-01: four instant queries against the loopback stub complete in under 5 s including connection setup.
- `promtool_suite_under_sixty_seconds` — NFR-F066-01, FR-F066-16: the four rule suites run in under 60 s in CI.
- `generated_series_count_at_most_40` — NFR-F066-01: four objectives across eight windows plus the two budget rules produce at most 40 recorded series regardless of how many routes each class lists.
- `series_count_is_flat_in_route_count` — NFR-F066-01, FR-F066-08: growing `core_read` from 9 to 200 routes leaves the recorded series count unchanged, because every rule aggregates `route` and `status` away.
- `renderer_rejects_route_label_in_output` — NFR-F066-01: a rule whose aggregation would retain `route` fails as `slo.cardinality` before it can be committed.
- `class_and_objective_limits_enforced` — NFR-F066-01: a ninth class or a seventh objective fails the schema, keeping the cardinality bound provable rather than incidental.
- `render_and_diff_under_two_seconds` — NFR-F066-01: regenerating both rule files and diffing them against the committed copies completes in under 2 s.

Evidence: criterion summaries, promtool timings, and the series-count report under `testing/evidence/F066/performance/`.
