---
id: T073
type: task
status: planned
parent_epic: E004
parent_feature: F019
parent_story: S037
depends_on: [S037]
owned_paths: [services/api/migrations/*_workflow-runtime_*.sql, crates/domain/src/workflow-runtime/**, crates/persistence/src/workflow-runtime/**, services/worker/src/workflow-runtime/**, testing/features/F019/database/**, testing/features/F019/api/**]
feature_flag: F019_FEATURE
branch: t073-worker-queue
started_at: null
finished_at: null
---

# T073 — Worker queue

## Identity

- Parent story: `S037` Queued runs
- Owner: platform
- Branch: `t073-worker-queue`
- Decision references: `docs/architecture-decisions.md` sections 2, 7; `docs/capability-contracts.md` row F019

## Objective

Create the run, step, trigger, and webhook tables, their repositories, and the JetStream consumer that turns domain events and scheduler ticks into queued runs and executes their steps in order with per-tenant quotas.

## Specification

- Owned paths: `services/api/migrations/<ts>_workflow-runtime_create_tables.sql`, `services/api/migrations/<ts>_workflow-runtime_create_tables.down.sql`, `crates/domain/src/workflow-runtime/{mod.rs, run.rs, step.rs, trigger.rs, executor.rs, errors.rs, service.rs}`, `crates/persistence/src/workflow-runtime/{mod.rs, workflow_run_repository.rs, workflow_trigger_repository.rs, inbound_webhook_repository.rs}`, `services/worker/src/workflow-runtime/{mod.rs, streams.rs, consumer.rs, scheduler.rs, quota.rs, executors/{rows.rs, comment.rs, approval.rs, notify.rs, webhook.rs, integration.rs}}`
- Contract/input: DDL per F019 ticket section 4: `workflow_runs`, `workflow_run_steps`, `workflow_triggers`, `inbound_webhooks`, `inbound_webhook_deliveries` with `status`, `trigger_kind`, and `error_code` check constraints, `error_message` and the `error_detail` provider snapshot beside them, the verbatim `trigger` payload, unique `(tenant_id, idempotency_key)`, unique `(run_id, index, attempt)`, unique `inbound_webhooks(token)`, primary key `inbound_webhook_deliveries(webhook_id, delivery_id)`, `depth <= 5`, partial indexes including `workflow_runs(tenant_id, error_code) where error_code is not null`, `workflow_version_id` foreign key `on delete restrict`. Repository surface: `WorkflowRunRepository` (`workflow_runs`, `workflow_run_steps`) with `enqueue_if_absent`, `claim_next_queued`, `claim_due_retries`, `record_step_attempt`, `transition_status`, `page_runs`; `WorkflowTriggerRepository` (`workflow_triggers`) with `claim_due_triggers`; `InboundWebhookRepository` (`inbound_webhooks`, `inbound_webhook_deliveries`) with `find_webhook_by_token`, `record_delivery_if_absent`, `expire_deliveries_before`. Consumer input: JetStream messages on `row.created.v1`, `row.updated.v1`, `form.submitted.v1`, `approval.decided.v1`, `workflow-run.queued.v1`; scheduler input: `workflow_triggers` rows due at tick.
- Output/behavior: matching workflows via F018 `evaluate_condition` produce one `workflow_runs` row each through `enqueue_if_absent` with pinned version, typed `trigger_kind`, `workflow-run.queued.v1` in the outbox from the same `UnitOfWork`, explicit ack after commit; `execute_run` transitions `queued → running → completed|failed`, writes one step row per attempt through `record_step_attempt` with `output` as the provider snapshot and typed `error_code`/`error_message`/`error_detail` on failure, honours `continue_on_error`, emits `workflow-run.started.v1` and `workflow-run.completed.v1`; quota token bucket per tenant (100 concurrent, 10,000 per hour) over `claim_next_queued` and round-robin dequeue; `depth > 5` rejects with `error_code: loop_detected`; scheduler fires due triggers once per window in the workflow timezone through `claim_due_triggers`, whose row lock still serializes competing schedulers. The consumer and scheduler hold no SQL string, `sqlx::query*` call, or connection; all SQL lives in `crates/persistence/src/workflow-runtime/`.
- Dependencies: F018 versions and evaluator; F004 outbox writer and JetStream client; F006/F008 row services; recording stubs for F016, F020, F037, F029/F030 executors.
- Feature flag: `F019_FEATURE` gates consumer registration in `services/worker/src/main.rs`.
- Large-table note: `workflow_runs` grows unbounded; partial indexes on active statuses keep `claim_next_queued` bounded, and `workflow_runs(tenant_id, error_code) where error_code is not null` keeps dead-letter triage an index lookup instead of a JSON scan.

## TDD

- Failing test first: `testing/features/F019/database/migration_tests.rs::runtime_tables_exist_with_constraints`, `::duplicate_idempotency_key_rejected`, `::depth_over_five_rejected`, `::error_code_check_rejects_unknown_code`, `::rollback_drops_tables`; `testing/features/F019/api/queue_tests.rs::row_event_enqueues_one_run`, `::run_executes_steps_in_order`, `::continue_on_error_records_skipped_step`, `::quota_holds_excess_runs_queued`, `::nested_run_depth_six_loop_detected`, `::schedule_tick_fires_due_trigger_once`
- Targeted command: `cargo xtask test-feature F019`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: schema-per-worker database; embedded JetStream; `testing/fixtures/workflow_runtime.rs`; controllable clock

## Exit criteria

- [ ] Tests written before the migration and consumer and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; consumer registered behind the flag
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S037
- [ ] `finished_at` recorded
