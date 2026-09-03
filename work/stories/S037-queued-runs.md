---
id: S037
type: story
status: planned
parent_epic: E004
parent_feature: F019
depends_on: [F018, F004]
owned_paths: [crates/domain/src/workflow-runtime/**, services/api/src/workflow-runtime/**, services/worker/src/workflow-runtime/**, services/api/migrations/*_workflow-runtime_*.sql, testing/features/F019/**]
feature_flag: F019_FEATURE
branch: s037-queued-runs
started_at: null
finished_at: null
---

# S037 — Queued runs

## Identity

- Parent feature: `F019` Workflow runtime
- Owner: platform
- Branch: `s037-queued-runs`
- Decision references: `docs/architecture-decisions.md` sections 2–4, 7; `docs/capability-contracts.md` row F019

## Vertical slice

As a workflow editor, I want a row change, form submission, schedule, date, webhook, or approval decision to enqueue exactly one run of the matching published workflow and execute its steps in order with visible status, so that automations run without duplicates and the run record can be inspected.

## Requirements

- **SR-S037-01:** The worker consumes `row.created.v1`, `row.updated.v1`, `form.submitted.v1`, and `approval.decided.v1`, matches published workflows through F018 `evaluate_condition`, inserts `workflow_runs` with `status: queued` and the pinned `workflow_version_id`, and emits `workflow-run.queued.v1` (covers FR-F019-01).
- **SR-S037-02:** The run idempotency key `sha256(workflow_version_id || trigger_event_id)` is unique per tenant; a redelivered event returns the existing run and inserts nothing (FR-F019-02).
- **SR-S037-03:** The scheduler tick every 60 seconds fires due `schedule` and `date_reached` triggers from `workflow_triggers.next_fire_at` in the workflow timezone with at most one catch-up run per missed window (FR-F019-03).
- **SR-S037-04:** `POST /api/v1/webhooks/inbound/{token}` validates HMAC-SHA256, deduplicates by `X-OpsHub-Delivery-Id` for 24 hours, enforces 256 KB and 60 requests per minute, and returns `{ run_id, delivery_id }` (FR-F019-04).
- **SR-S037-05:** `execute_run` runs steps in order through typed executors, writes `workflow_run_steps` per attempt, honours `continue_on_error`, and emits `workflow-run.started.v1` and `workflow-run.completed.v1` (FR-F019-05, FR-F019-09).
- **SR-S037-06:** Per-tenant quotas of 100 concurrent and 10,000 hourly runs hold excess runs in `queued` with round-robin dequeue across tenants; nested runs beyond depth 5 fail with `loop_detected` (FR-F019-08, FR-F019-10).
- **SR-S037-07:** `GET /api/v1/workflow-runs`, `GET /api/v1/workflows/{id}/runs`, and `GET /api/v1/workflow-runs/{id}` page, filter, and return steps; foreign tenants receive `404 not_found` (FR-F019-11, NFR-F019-02).

## Surfaces

- Infrastructure/container: NATS JetStream stream `workflow-runtime` and durable consumer declared in `services/worker/src/workflow-runtime/streams.rs` on the F004 compose baseline
- Rust service/API: `crates/domain/src/workflow-runtime/{run.rs, step.rs, trigger.rs, idempotency.rs, executor.rs, errors.rs, service.rs}`; `services/worker/src/workflow-runtime/{consumer.rs, scheduler.rs, quota.rs, executors/*.rs}`; `services/api/src/workflow-runtime/{routes.rs, handlers_runs.rs, handlers_webhook.rs, dto.rs}`
- Data/migration: `services/api/migrations/<ts>_workflow-runtime_create_tables.sql` creating the five tables with indexes from ticket section 4
- React/UI: none in this story (S038 and T076 cover UI)
- Mocks/fixtures: `testing/fixtures/workflow_runtime.rs`; embedded JetStream per worker; recording executors for notification, approval, webhook, integration actions

## TDD harness

- Test path: `testing/features/F019/api/`, `testing/features/F019/database/`, `testing/features/F019/requirements/`
- Feature flag: `F019_FEATURE`
- Targeted command: `cargo xtask test-feature F019`
- Full command: `cargo xtask test-all`
- First failing tests: `row_event_enqueues_one_run`, `duplicate_event_delivery_creates_no_second_run`, `schedule_tick_fires_due_trigger_once`, `inbound_webhook_bad_signature_denied`, `run_executes_steps_in_order`, `quota_holds_excess_runs_queued`, `run_cross_tenant_not_found`

## Exit criteria

- [ ] Requirement tests SR-S037-01 through SR-S037-07 written first and failing
- [ ] Tasks T073 and T074 complete and wired through `services/worker` main and `services/api` router
- [ ] Unit, API, database, permission tests pass in targeted and full modes
- [ ] Production call path named: `services/worker/src/workflow-runtime/consumer.rs` registered in `services/worker/src/main.rs`; `services/api/src/workflow-runtime/routes.rs` mounted in `services/api/src/router.rs`
- [ ] Handoff evidence recorded in the F019 ticket
