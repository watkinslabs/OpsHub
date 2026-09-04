---
id: T015
type: task
status: planned
parent_epic: E001
parent_feature: F004
parent_story: S008
depends_on: [T014]
owned_paths: [crates/persistence/src/runtime/**, services/api/src/runtime/**, services/realtime/src/runtime/**, services/worker/src/**, infra/**, testing/features/F004/api/**, testing/features/F004/accessibility/**, testing/features/F004/performance/**]
feature_flag: F004_FEATURE
branch: t015-tracing-metrics
started_at: null
finished_at: null
---

# T015 — Tracing/metrics

## Identity

- Parent story: `S008` Observability
- Owner: platform
- Branch: `t015-tracing-metrics`

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 3, 7, 9
- Canonical contract: `docs/capability-contracts.md` row F004

## Objective

Install the shared tracing subscriber with OTLP export, JSON logs, correlation-id middleware, and the Prometheus metrics server on an isolated port across api, realtime, and worker, plus the alert rules that consume those metrics.

## Specification

- Owned paths: `crates/persistence/src/runtime/telemetry.rs`, `services/api/src/runtime/{telemetry.rs, metrics_server.rs}`, `services/realtime/src/runtime/{telemetry.rs, metrics_server.rs}`, `services/worker/src/runtime/metrics.rs`, `infra/alerts/rules.yml`, `infra/compose/docker-compose.yml` (metrics network)
- Contract/input: `Telemetry::install(service_name, config)` building `tracing-subscriber` with the `RedactionLayer`, JSON formatter (fields `service`, `tenant_id`, `actor_id`, `correlation_id`, `worker_id`, `job_kind`, `attempt`), and OTLP gRPC exporter that degrades to a warning when `OPSHUB_OTLP_ENDPOINT` is unset; `CorrelationLayer` Axum middleware honouring a valid UUID `X-Correlation-Id` or generating UUIDv7 and echoing it; `MetricsServer::bind(port)` serving `GET /metrics` on its own listener; metric families `http_request_duration_seconds{route,method,status}`, `outbox_publish_lag_seconds`, `outbox_pending_events`, `job_run_duration_seconds{kind}`, `job_runs_total{kind,status}`, `dead_letters_total{kind}`, `db_pool_in_use`, `db_pool_idle`, `nats_connected`; the gauges sourced from the database (`outbox_publish_lag_seconds`, `outbox_pending_events`, `db_pool_in_use`, `db_pool_idle`) read `OutboxRepository::lag_seconds` and the pool statistics `crates/persistence` exposes, so no metrics or telemetry module holds a SQL string or `sqlx::query*` call (decision 2.1).
- Output/behavior: one request yields a log line, a span, and metric samples sharing `correlation_id`; `/metrics` on the API port and through the web proxy returns `404 not_found`; relay and consumer update outbox and job metrics from the values their `OutboxRepository` and `JobRunRepository` calls return; `rules.yml` alerts `OutboxBacklog` (`outbox_pending_events > 1000` for 5 m), `DeadLetterIncrease`, `ReadinessFailing`; CLI and logs honour `NO_COLOR` and use words for state.
- Dependencies: T014 relay and consumer for job and outbox metrics; T013 compose for the internal metrics network.
- Feature flag: `F004_FEATURE` (telemetry always installs; the flag gates only relay and consumer metrics registration)

## TDD

- Failing test first: `testing/features/F004/api/telemetry_tests.rs::correlation_id_honoured_and_echoed`, `::invalid_correlation_header_replaced`, `::span_log_and_metric_share_correlation`, `::secrets_absent_from_span_fields`, `::otlp_missing_endpoint_degrades_with_warning`; `testing/features/F004/api/metrics_tests.rs::metrics_only_on_internal_port`, `::metric_families_present_after_traffic`, `::outbox_gauges_read_lag_seconds_query`, `::alert_rules_fire_on_pending_outbox`; `testing/features/F004/accessibility/operator_output_tests.rs::log_state_words_not_colour`, `::no_color_respected`; `testing/features/F004/performance/runtime_bench.rs::outbox_lag_p95_at_200_eps`, `::job_throughput_500_per_second`
- Targeted command: `cargo xtask test-feature F004`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: in-memory OTLP collector, scraped metrics registry, `promtool test rules` for alert rule tests

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Telemetry installed in `services/api/src/main.rs`, `services/realtime/src/main.rs`, and `services/worker/src/main.rs`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S008
- [ ] `finished_at` recorded
