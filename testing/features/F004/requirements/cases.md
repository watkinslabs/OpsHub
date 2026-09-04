# F004 requirements cases

Feature: Runtime operations. Flag `F004_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F004-REQ-001` | FR-F004-01 | e2e, frontend | clean machine, `make up` → eight services `healthy` within 120 s; `compose ps --format json` confirms |
| `F004-REQ-002` | FR-F004-02 | frontend, api | unset `OPSHUB_DATABASE_URL` → exit 78, log names the variable only; `.env.example` covers every field |
| `F004-REQ-003` | FR-F004-03 | api | `secret://s3-secret` resolved via file, env, vault backends; `Debug` and logs show `[redacted]` |
| `F004-REQ-004` | FR-F004-04 | e2e, frontend | images non-root uid 65532, read-only root, `--version` prints crate version, git SHA label |
| `F004-REQ-005` | FR-F004-05 | api, database | `enqueue` inside tx → row after commit only; `tenant.changed` name → `InvalidName` |
| `F004-REQ-006` | FR-F004-06 | api | relay batch of 500 with `Nats-Msg-Id`; NATS down → `attempts` +1, row kept; `outbox.published.v1` per batch |
| `F004-REQ-007` | FR-F004-07 | api, performance | 10,000 rows drain < 60 s; two relays → each row published once |
| `F004-REQ-008` | FR-F004-08 | api, database | `enqueue_job` writes `job_runs` queued and publishes `jobs.<tenant>.<kind>` in one tx |
| `F004-REQ-009` | FR-F004-09 | api | 5 failures → statuses queued→running→failed×4→dead, backoff 1 s/5 s/25 s/2 m/5 m, `dead_letters` row |
| `F004-REQ-010` | FR-F004-10 | e2e | `SIGKILL` mid-job → redelivered < 30 s, `attempt` 2, one side effect; `SIGTERM` drains ≤ 30 s, exit 0 |
| `F004-REQ-011` | FR-F004-11 | api, frontend | `replay --id` re-enqueues with `attempt` 1 and `replayed_at`; second replay exits 65 |
| `F004-REQ-012` | FR-F004-12 | api | `X-Correlation-Id` honoured/generated and echoed; span, log, trace share ids |
| `F004-REQ-013` | FR-F004-13 | api, e2e | nine metric families on port 9464; `/metrics` on 8080 and via proxy → 404 |
| `F004-REQ-014` | FR-F004-14 | api, performance | `/healthz` 200; `/readyz` 200 all `ok`; database down → 503 naming `database` |
| `F004-REQ-015` | FR-F004-15 | e2e | nightly backup + WAL to `opshub-backups`; `make restore-drill` restores to timestamp and matches manifest |
| `F004-REQ-016` | FR-F004-16 | api | `enqueue_job` without `TenantScope` → `MissingTenant`, no `job_runs` row |
| `F004-NFR-001` | NFR-F004-01 | performance | `/readyz` p95 < 50 ms; lag p95 < 2 s at 200 eps; 500 jobs/s across 4 workers, < 5 ms overhead |
| `F004-NFR-002` | NFR-F004-02 | api, e2e | non-root images; no secret in logs, traces, readiness; NATS permissions enforced; backups encrypted |
| `F004-NFR-003` | NFR-F004-03 | accessibility | readiness and CLI use words, honour `NO_COLOR`; runbook headings and plain tables |
| `F004-NFR-004` | NFR-F004-04 | api, e2e | unpublished rows never deleted; dead letters visible; weekly drill evidence; alert rules fire |

| `F004-REQ-017` | FR-F004-17 | api, database | a seeded secret and a seeded cell value appear in neither the log sink nor a trace span; a log line carries only the permitted field list; retention is set on the sink for logs, traces and metrics; a tenant purge removes its telemetry rows |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F004/`.
