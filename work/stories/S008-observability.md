---
id: S008
type: story
status: planned
parent_epic: E001
parent_feature: F004
depends_on: [S007]
owned_paths: [infra/**, services/worker/src/**, services/api/src/runtime/**, services/realtime/src/runtime/**, crates/persistence/src/runtime/**, testing/features/F004/**]
feature_flag: F004_FEATURE
branch: s008-observability
started_at: null
finished_at: null
---

# S008 — Observability

## Identity

- Parent feature: `F004` Runtime operations
- Owner: platform
- Branch: `s008-observability`

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 3, 7, 9
- Canonical contract: `docs/capability-contracts.md` row F004

## Vertical slice

As an operator, I want every request and job traced and logged with the same correlation id, Prometheus metrics on an isolated port, health and readiness routes that name the failing dependency, alert rules, nightly backups with WAL archiving, and a restore drill I can run, so that I can diagnose incidents and recover data to a point in time.

## Requirements

- **SR-S008-01:** Every HTTP request and job run executes inside a span with `tenant_id`, `actor_id`, `correlation_id`, `service`, `worker_id`; `X-Correlation-Id` is honoured or generated as UUIDv7 and echoed; spans export via OTLP and logs are JSON lines sharing the ids (covers FR-F004-12).
- **SR-S008-02:** `GET /metrics` on `OPSHUB_METRICS_PORT` serves the nine metric families from ticket section 4; the same path on the API port and through the web proxy returns `404` (FR-F004-13).
- **SR-S008-03:** `GET /healthz` returns `200` while serving; `GET /readyz` returns `200` with all components `ok` or `503 unavailable` naming each failing component and reason within a 500 ms budget; both bypass tenant gate and rate limits (FR-F004-14).
- **SR-S008-04:** `infra/backup/backup.sh` performs nightly `pg_basebackup` plus continuous WAL archive to `opshub-backups` with 30-day retention; `restore.md` documents PITR; `make restore-drill` restores to a target timestamp and verifies counts against the manifest (FR-F004-15).
- **SR-S008-05:** `infra/alerts/rules.yml` fires on `outbox_pending_events > 1000` for 5 min, `dead_letters_total` increases, and `/readyz` failure; the weekly CI restore drill stores evidence under `testing/evidence/F004/` (NFR-F004-04).
- **SR-S008-06:** Operator output uses words not colour, honours `NO_COLOR`, and runbooks use heading hierarchy and plain-text tables (NFR-F004-03).
- **SR-S008-07:** `/readyz` p95 < 50 ms, outbox lag p95 < 2 s at 200 events/s, and 500 jobs/s across 4 workers with < 5 ms overhead per job (NFR-F004-01).

## Surfaces

- Infrastructure/container: `infra/backup/{backup.sh, restore.sh, restore.md, manifest.json}`, `infra/alerts/rules.yml`, `infra/compose/docker-compose.yml` backup sidecar and metrics network, `Makefile` targets `restore-drill`, `backup-now`
- Rust service/API: `services/api/src/runtime/{health.rs, metrics_server.rs, telemetry.rs}`; `services/realtime/src/runtime/{health.rs, metrics_server.rs, telemetry.rs}`; `services/worker/src/runtime/metrics.rs`; `crates/persistence/src/runtime/telemetry.rs` (shared subscriber builder and correlation middleware)
- Data/migration: none new; `runtime.retention` sweeper job registered in the worker
- React/UI: none (no UI)
- Mocks/fixtures: `testing/fixtures/runtime.rs` extended with an in-memory OTLP collector, a scraped metrics registry, dependency fault injection for readiness, and a seeded backup manifest

## TDD harness

- Test path: `testing/features/F004/{api,frontend,e2e,accessibility,performance}/`
- Feature flag: `F004_FEATURE`
- Targeted command: `cargo xtask test-feature F004`
- Full command: `cargo xtask test-all`
- First failing tests: `correlation_id_honoured_and_echoed`, `span_log_and_metric_share_correlation`, `metrics_only_on_internal_port`, `readyz_reports_failing_component`, `readyz_bypasses_tenant_gate_and_rate_limit`, `restore_drill_matches_manifest`, `alert_rules_fire_on_pending_outbox`, `readyz_p95_under_50ms`

## Exit criteria

- [ ] Requirement tests SR-S008-01 through SR-S008-07 written first and failing
- [ ] Tasks T015 and T016 complete; telemetry applied to api, realtime, and worker
- [ ] Unit, API, CLI, stack E2E, accessibility, and performance tests pass
- [ ] Production call path named: `services/api/src/runtime/health.rs` mounted at `/healthz` and `/readyz` in `services/api/src/router.rs`; `services/api/src/runtime/telemetry.rs` installed in `services/api/src/main.rs`; `infra/backup/restore.sh` invoked by `make restore-drill`
- [ ] Handoff evidence recorded in the F004 ticket including the restore-drill log
