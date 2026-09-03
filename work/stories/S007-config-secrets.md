---
id: S007
type: story
status: planned
parent_epic: E001
parent_feature: F004
depends_on: [F001]
owned_paths: [infra/**, services/worker/src/**, services/api/src/runtime/**, crates/events/src/runtime/**, crates/persistence/src/runtime/**, services/api/migrations/*_runtime_*.sql, testing/features/F004/**]
feature_flag: F004_FEATURE
branch: s007-config-secrets
started_at: null
finished_at: null
---

# S007 — Config/secrets

## Identity

- Parent feature: `F004` Runtime operations
- Owner: platform
- Branch: `s007-config-secrets`

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 7
- Canonical contract: `docs/capability-contracts.md` row F004

## Vertical slice

As an operator, I want a compose stack that boots every dependency and service from typed configuration with secrets resolved from a secret manager, and a transactional outbox plus JetStream job transport consumed by a worker, so that later features can commit an event or a job in the same transaction as their data and trust it will be delivered exactly once.

## Requirements

- **SR-S007-01:** `docker compose -f infra/compose/docker-compose.yml up -d --wait` reaches `healthy` for postgres, nats, minio, mailpit, api, worker, realtime, and web within 120 s on a clean machine (covers FR-F004-01).
- **SR-S007-02:** `RuntimeConfig` loads every `OPSHUB_` variable from `.env.example`, exits 78 naming a missing variable without its value, and resolves `secret://` references through `SecretSource` with `file`, `env`, and `vault` backends; secrets are redacted in `Debug` and logs (FR-F004-02, FR-F004-03).
- **SR-S007-03:** Distroless, non-root, read-only images for api, worker, realtime, and web build from `infra/docker/` and print their version (FR-F004-04).
- **SR-S007-04:** `enqueue(tx, OutboxEvent)` writes `outbox_events` in the caller's transaction with a validated `EventName`; the relay drains with `SKIP LOCKED` batches, `Nats-Msg-Id` dedupe, `published_at` marking, and `outbox.published.v1` batch summaries; 10,000 rows drain within 60 s and two relays publish each row once (FR-F004-05, FR-F004-06, FR-F004-07).
- **SR-S007-05:** `Job` trait, `enqueue_job`, `OPSHUB_JOBS` consumer, per-tenant quotas, backoff 1 s to 5 m, timeout cancellation, `job_runs` transitions, and `dead_letters` after 5 attempts work end to end (FR-F004-08, FR-F004-09).
- **SR-S007-06:** `SIGKILL` mid-job redelivers within 30 s with `attempt + 1` and no duplicate side effect; `SIGTERM` drains within 30 s; `opshub-worker replay` re-enqueues once (FR-F004-10, FR-F004-11).
- **SR-S007-07:** `enqueue_job` without a tenant scope returns `JobError::MissingTenant`; NATS credentials restrict api to publish and worker to consume (FR-F004-16, NFR-F004-02).

## Surfaces

- Infrastructure/container: `infra/compose/{docker-compose.yml, .env.example}`, `infra/docker/{api,worker,realtime,web}.Dockerfile`, `infra/nats/{streams.json, permissions.conf}`, `infra/minio/init.sh`, `Makefile` targets `up`, `down`, `logs`, `ps`
- Rust service/API: `crates/persistence/src/runtime/{mod.rs, config.rs, secrets.rs, pool.rs, redaction.rs}`; `crates/events/src/runtime/{mod.rs, event_name.rs, outbox.rs, relay.rs, publisher.rs, job.rs, enqueue.rs, registry.rs, retry.rs, quota.rs, dead_letter.rs, streams.rs}`; `services/worker/src/{main.rs, runtime/bootstrap.rs, runtime/consumer.rs, runtime/relay_task.rs, runtime/shutdown.rs, runtime/quota.rs}`; `services/api/src/runtime/state.rs`
- Data/migration: `services/api/migrations/<ts>_runtime_create_tables.sql` creating `outbox_events`, `job_runs`, `dead_letters` with indexes and the unpublished-delete trigger
- React/UI: none (no UI)
- Mocks/fixtures: `testing/fixtures/runtime.rs` test containers, per-test stream prefixes, recording `sample` job, fault-injecting publisher, in-memory `SecretSource`

## TDD harness

- Test path: `testing/features/F004/{api,database,frontend,e2e,performance}/`
- Feature flag: `F004_FEATURE`
- Targeted command: `cargo xtask test-feature F004`
- Full command: `cargo xtask test-all`
- First failing tests: `compose_stack_healthy_within_120s`, `config_missing_var_exits_78_without_value`, `secret_reference_resolved_and_redacted`, `outbox_enqueue_in_caller_transaction`, `relay_publishes_once_with_two_instances`, `job_retries_then_dead_letters_without_side_effect`, `worker_sigkill_redelivers_within_30s`, `enqueue_job_without_tenant_refused`

## Exit criteria

- [ ] Requirement tests SR-S007-01 through SR-S007-07 written first and failing
- [ ] Tasks T013 and T014 complete; relay and consumer run inside `services/worker`
- [ ] Unit, API, database, CLI, stack E2E, and permission tests pass in targeted and full modes
- [ ] Production call path named: `services/worker/src/main.rs` `run` command starting `runtime/relay_task.rs` and `runtime/consumer.rs`; `crates/events/src/runtime/outbox.rs::enqueue` called from `services/api` handlers through `services/api/src/runtime/state.rs`
- [ ] Handoff evidence recorded in the F004 ticket
