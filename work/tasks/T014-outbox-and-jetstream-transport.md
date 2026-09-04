---
id: T014
type: task
status: planned
parent_epic: E001
parent_feature: F004
parent_story: S007
depends_on: [T013]
owned_paths: [services/api/migrations/*_runtime_*.sql, crates/events/src/runtime/**, services/worker/src/**, testing/features/F004/api/**, testing/features/F004/database/**, testing/features/F004/e2e/**]
feature_flag: F004_FEATURE
branch: t014-outbox-and-jetstream-transport
started_at: null
finished_at: null
---

# T014 — Outbox and JetStream transport

## Identity

- Parent story: `S007` Config/secrets
- Owner: platform
- Branch: `t014-outbox-and-jetstream-transport`

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 7
- Canonical contract: `docs/capability-contracts.md` row F004

## Objective

Create the `outbox_events`, `job_runs`, and `dead_letters` tables with their `crates/persistence/src/runtime/` repositories and implement the outbox writer and relay, the JetStream streams, the `Job` trait with quotas, retries, timeouts, and dead letters, and the worker skeleton with graceful shutdown and the replay CLI.

## Specification

- Owned paths: `services/api/migrations/<ts>_runtime_create_tables.sql` and `.down.sql`, `crates/persistence/src/runtime/{outbox_repository.rs, job_run_repository.rs, dead_letter_repository.rs}`, `crates/events/src/runtime/{mod.rs, event_name.rs, outbox.rs, relay.rs, publisher.rs, job.rs, enqueue.rs, registry.rs, retry.rs, quota.rs, dead_letter.rs, streams.rs, schema.rs}`, `services/worker/src/{main.rs, runtime/mod.rs, runtime/bootstrap.rs, runtime/consumer.rs, runtime/relay_task.rs, runtime/shutdown.rs, runtime/quota.rs, runtime/replay.rs}`
- Contract/input: DDL per F004 ticket section 4 including the unpublished-delete trigger and partial index, with `outbox_events.payload` and `dead_letters.payload` kept `jsonb` as opaque payloads that are never filtered, joined, or constrained by key; `OutboxRepository` (`outbox_events`) exposing `enqueue`, `claim_unpublished_batch`, `mark_published`, `record_attempt_failure`, `lag_seconds`, `JobRunRepository` (`job_runs`) exposing the status transitions and `sweep_stuck_runs`, and `DeadLetterRepository` (`dead_letters`) exposing `record`, `list_dead_letters`, `mark_replayed`; `EventName::new_const("tenant.created.v1")`; `enqueue(tx, OutboxEvent)`; `enqueue_job(tx, kind, TenantScope, payload, JobOptions { max_attempts ≤ 5, timeout, idempotency_key })`; `trait Job { const KIND; type Payload; async fn run(JobContext, Payload) }`; streams `OPSHUB_EVENTS` (`events.>`, file, 7 d, dedupe 2 min) and `OPSHUB_JOBS` (`jobs.>`, work queue, `max_deliver 5`, `ack_wait 30 s`); CLI `opshub-worker run|replay --id|dead-letters --tenant|enqueue-sample`.
- Output/behavior: relay polls every 200 ms through `claim_unpublished_batch`, whose `FOR UPDATE SKIP LOCKED LIMIT 500` statement lives in `crates/persistence` and appears nowhere else, publishes with `Nats-Msg-Id`, sets `published_at` via `mark_published`, records `attempts`/`last_error` via `record_attempt_failure`, emits `outbox.published.v1` per batch; consumer enforces per-tenant quotas (100 concurrent, 1,000/min), transitions `job_runs` through `JobRunRepository`, retries 1 s, 5 s, 25 s, 2 m, 5 m, cancels on timeout, dead-letters after attempt 5 through `DeadLetterRepository::record`; `crates/events`, `services/worker`, and the tests hold no SQL string or `sqlx::query*` call (decision 2.1); `SIGTERM` drains ≤ 30 s; `replay` re-enqueues once through `mark_replayed` and exits 65 on a second replay; `enqueue_job` without `TenantScope` returns `JobError::MissingTenant`.
- Dependencies: T013 config, pool, compose stack, NATS permissions.
- Feature flag: `F004_FEATURE` gates relay and consumer startup; tables migrate regardless.

## TDD

- Failing test first: `testing/features/F004/database/migration_tests.rs::runtime_tables_exist_with_constraints`, `::unpublished_outbox_delete_rejected`, `::skip_locked_batches_do_not_overlap`, `::payload_jsonb_round_trips_byte_for_byte`, `::rollback_drops_tables`; `testing/features/F004/api/outbox_tests.rs::outbox_enqueue_in_caller_transaction`, `::relay_claims_batch_through_outbox_repository`, `::invalid_event_name_rejected`, `::relay_publishes_once_with_two_instances`, `::relay_survives_nats_outage`; `testing/features/F004/api/job_tests.rs::job_retries_then_dead_letters_without_side_effect`, `::job_timeout_cancels_and_retries`, `::tenant_quota_limits_concurrency`, `::enqueue_job_without_tenant_refused`, `::replay_twice_exits_65`; `testing/features/F004/e2e/stack.spec.rs::worker_sigkill_redelivers_within_30s`
- Targeted command: `cargo xtask test-feature F004`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/runtime.rs` per-test stream prefixes, recording `sample` job, fault-injecting publisher, tokio paused time for backoff

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; worker `run` starts relay and consumer behind the flag; `cargo xtask check-persistence` passes with all runtime SQL inside `crates/persistence/src/runtime/`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S007
- [ ] `finished_at` recorded
