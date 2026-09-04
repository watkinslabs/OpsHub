# F066 e2e cases

End to end here means the whole gate over a fixture repository tree plus the rule suites over the committed rules — no cluster, no Prometheus server, no browser. Files: `infra/slo/tests/{availability,latency,ack,no_data}.promtool.yml` run by `promtool test rules`, driven from `testing/features/F066/e2e/gate_e2e.rs`. Flag `F066_FEATURE`.

- `edit_objectives_regenerate_and_pass` — FR-F066-01, FR-F066-08, FR-F066-09: an operator changes `latency_core_read` to 0.96 in a fixture tree, runs `verify-slo --write-rules`, and both rule files change; the second run without `--write-rules` exits 0; reverting only the alert file makes it exit 1 with `slo.rule_drift`.
- `fast_burn_pages_and_clears` — FR-F066-09, FR-F066-10: core availability at 90% for 65 minutes; `SloFastBurn{objective="availability_core"}` fires at minute 7 with `severity: page` and `window: 1h/5m`, and after recovery it resolves within 7 minutes because the 5m window clears first.
- `analytics_outage_does_not_burn_the_core_budget` — FR-F066-03: every `/api/v1/reports` request returns 500 for two hours while core traffic succeeds; `slo:sli:ratio_rate1h{objective="availability_core"}` stays at 1 and no burn alert fires.
- `slow_burn_only_opens_a_ticket` — FR-F066-05, FR-F066-09, FR-F066-10: a 3% error rate sustained for three days fires `SloBurn3d` at `severity: ticket` and never `SloFastBurn`.
- `write_latency_regression_fires_the_write_objective_only` — FR-F066-04, FR-F066-05: `core_write` p95 crosses 800 ms while reads stay under 500 ms; only `latency_core_write` burns.
- `ack_breach_measures_the_202_not_the_job` — FR-F066-06: 202 responses drift to 2.4 s while `job_run_duration_seconds` stays flat; `ack_async` burns and no other objective moves.
- `silent_pipeline_pages` — FR-F066-10, NFR-F066-04: the `ack_async` series stops; `SloNoData` fires after 15 minutes at `severity: page`.
- `exhausted_budget_blocks_the_release_then_recovers` — FR-F066-14, FR-F066-15: the exhausted snapshot refuses with exit 3; adding a 7-day exception with owner and ticket exits 0; expiring the exception refuses again; a recovered snapshot above 25% remaining exits 0 with no exception at all.
- `full_gate_on_the_live_repository` — FR-F066-13, FR-F066-16: `cargo xtask verify-slo` and the promtool suite both exit 0 on the committed tree, and the run is recorded as evidence.

Evidence: promtool output, gate stdout and stderr with exit codes, and the rule diffs under `testing/evidence/F066/e2e/`.
