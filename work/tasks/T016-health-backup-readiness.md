---
id: T016
type: task
status: planned
parent_epic: E001
parent_feature: F004
parent_story: S008
depends_on: [T015]
owned_paths: [services/api/src/runtime/**, services/realtime/src/runtime/**, services/worker/src/**, infra/**, testing/features/F004/**]
feature_flag: F004_FEATURE
branch: t016-health-backup-readiness
started_at: null
finished_at: null
---

# T016 — Health/backup/readiness

## Identity

- Parent story: `S008` Observability
- Owner: platform
- Branch: `t016-health-backup-readiness`

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 7, 9
- Canonical contract: `docs/capability-contracts.md` row F004

## Objective

Implement `/healthz` and `/readyz` with component checks, the retention sweeper, nightly backups with WAL archiving, the PITR runbook, and the restore drill that CI runs weekly and stores as evidence.

## Specification

- Owned paths: `services/api/src/runtime/health.rs`, `services/realtime/src/runtime/health.rs`, `services/worker/src/runtime/{health.rs, retention.rs}`, `infra/backup/{backup.sh, restore.sh, restore.md, manifest.json}`, `infra/compose/docker-compose.yml` (backup sidecar), `Makefile` (`restore-drill`, `backup-now`), `testing/features/F004/{requirements/cases.md, e2e/restore_drill.spec.rs}`
- Contract/input: `GET /healthz` → `200 {"status":"ok"}`; `GET /readyz` → `ReadinessReport { status, components: { database, nats, object_storage, outbox } }` where each component is `{ status: "ok"|"error", latency_ms, reason? }`, checks `SELECT 1` within 500 ms, NATS `connected`, `HEAD` bucket `opshub-files`, outbox lag < 60 s; `backup.sh` runs `pg_basebackup -Ft -z` nightly and `archive_command` ships WAL to `s3://opshub-backups/wal/`; `restore.sh --target-time <ts>` restores base plus WAL into a scratch database; `manifest.json` records row counts for `tenants`, `users`, `outbox_events` at backup time; `runtime.retention` job deletes published outbox rows > 7 d and `job_runs` > 30 d.
- Output/behavior: readiness returns `503 unavailable` naming failing components within the 500 ms budget; both routes bypass the tenant gate, `ActorContext` extractor, rate limits, and MFA layer; compose healthchecks call `/readyz`; `make restore-drill` exits 0 when counts match the manifest and non-zero with a diff otherwise; retention 30 days for backups enforced by a lifecycle rule in `infra/minio/init.sh`; `restore.md` uses `#`/`##` headings and plain-text tables.
- Dependencies: T015 telemetry and metrics (readiness latency histogram); T013 compose and MinIO buckets; T014 outbox for lag.
- Feature flag: `F004_FEATURE` (health routes always mounted; the flag gates the retention job)

## TDD

- Failing test first: `testing/features/F004/api/health_tests.rs::healthz_always_ok_while_serving`, `::readyz_all_components_ok`, `::readyz_reports_failing_component`, `::readyz_honours_500ms_budget`, `::readyz_bypasses_tenant_gate_and_rate_limit`, `::readyz_never_exposes_secrets`; `testing/features/F004/e2e/restore_drill.spec.rs::backup_then_restore_drill_matches_manifest`, `::restore_to_timestamp_excludes_later_rows`; `testing/features/F004/api/retention_tests.rs::sweeper_deletes_only_published_and_old_rows`; `testing/features/F004/performance/runtime_bench.rs::readyz_p95_under_50ms`
- Targeted command: `cargo xtask test-feature F004`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: dependency fault injection for readiness; real MinIO and PostgreSQL 18 for the drill; seeded manifest

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Health routes mounted in api and realtime routers; restore drill executed in CI with evidence under `testing/evidence/F004/restore-drill/`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S008
- [ ] `finished_at` recorded
