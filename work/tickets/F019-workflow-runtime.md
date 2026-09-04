---
id: F019
type: feature
status: planned
priority: P1
owner: platform
estimate: 8
target_milestone: M3
parent_epic: E004
depends_on: [F018, F004]
blocks: [F020, F054]
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/workflow-runtime/**, crates/persistence/src/workflow-runtime/**, services/api/src/workflow-runtime/**, services/worker/src/workflow-runtime/**, apps/web/src/features/workflow-runtime/**, services/api/migrations/*_workflow-runtime_*.sql, testing/features/F019/**]
feature_flag: F019_FEATURE
flag_default: off
branch: f019-workflow-runtime
started_at: null
finished_at: null
---

# F019 — Workflow runtime

## 1. Identity and dates

- Branch: `f019-workflow-runtime`
- Capability area: automation execution (spec 5.5 AUTO-02, AUTO-03, low-level queue rules; section 4 `WorkflowRun` entity; section 6 reliability and observability)
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 7; `docs/capability-contracts.md` row F019
- Aggregate: `workflow-run`
- Module slug: `workflow-runtime`

## 2. Requirement specification

### Problem and user outcome

A published workflow is only useful if it runs reliably when its trigger fires, does not run twice for the same event, backs off when an action fails, and leaves an inspectable record. Teams need a durable queue that matches domain events, schedules, and inbound webhooks to published workflow versions, executes actions with per-tenant fairness, and exposes run history with retry and cancel controls.

As a workflow editor, I want every published workflow to execute exactly once per triggering event with visible status, bounded retries, and dead-letter recovery, so that automations move work without duplicate side effects or silent failures.

### Functional requirements

- **FR-F019-01:** The worker subscribes to `row.created.v1`, `row.updated.v1`, `form.submitted.v1`, and `approval.decided.v1` on JetStream and, for each event, resolves the published workflows on the affected sheet whose trigger matches; a matching workflow creates one `workflow_runs` row with `status: queued`, `workflow_version_id` pinned to the version published at event time, and emits `workflow-run.queued.v1`.
- **FR-F019-02:** The idempotency key of a run is `sha256(workflow_version_id || trigger_event_id)`; a second delivery of the same event creates no second run and returns the existing run ID, so redelivery from JetStream never duplicates side effects.
- **FR-F019-03:** `schedule` triggers are materialized by a scheduler tick every 60 seconds from `workflow_triggers(next_fire_at)` in the workflow's timezone; a missed tick fires at most one catch-up run and then advances `next_fire_at`; `date_reached` triggers evaluate the column value plus `offset_minutes` the same way.
- **FR-F019-04:** `POST /api/v1/webhooks/inbound/{token}` accepts a JSON body up to 256 KB for a `webhook_received` workflow, validates the HMAC-SHA256 `X-OpsHub-Signature` header against the token's secret, rejects invalid signatures with `denied`, replays with the same `X-OpsHub-Delivery-Id` within 24 hours with `200` and the original run ID, and rate-limits to 60 requests per minute per token with `rate_limited`.
- **FR-F019-05:** A run executes its steps in order; each step writes a `workflow_run_steps` row with `status`, `attempt`, `started_at`, `finished_at`, `output`, and, on failure, `error_code`, `error_message`, and `error_detail`; a step failure with `continue_on_error: false` fails the run, otherwise the run continues and records the step as `skipped_error`.
- **FR-F019-06:** A failed step retries with exponential backoff `min(2^attempt * 5 s, 15 min)` plus 0–20 % jitter up to 5 attempts; after the fifth failure the run moves to `dead_lettered`, emits `workflow-run.dead-lettered.v1`, and stays retryable for 30 days.
- **FR-F019-07:** A run that exceeds 120 seconds of wall time or a single step that exceeds 30 seconds is aborted with `error_code: timeout` and the timing detail in `error_message`, counts as a failed attempt, and follows the retry rule in FR-F019-06.
- **FR-F019-08:** Each tenant has a quota of 100 concurrent runs and 10,000 runs per hour (tenant-configurable by F048 later); runs beyond the quota stay `queued` and are dequeued fairly by round-robin across tenants, and an hourly overflow emits a `workflow_quota_exceeded` metric and audit event.
- **FR-F019-09:** Actions execute through typed executors: `update_fields`, `create_row`, `move_row`, `copy_row` call the F006/F008 row services with the run's service actor; `assign` sets a person column; `comment` calls F016; `request_approval` calls F020; `send_email`, `send_in_app`, `send_push` call F037; `call_webhook` signs with HMAC-SHA256 and retries per F028 rules; `invoke_integration` calls the F029/F030 adapter; every executor is idempotent on `(run_id, step_index, attempt)`.
- **FR-F019-10:** A run started by a workflow cannot trigger the same workflow version again within the same correlation chain beyond depth 5; the sixth nested run is rejected with `error_code: loop_detected` and the chain is recorded in `correlation_id` and `parent_run_id`.
- **FR-F019-11:** `GET /api/v1/workflow-runs` and `GET /api/v1/workflows/{id}/runs` page by cursor with `filter` on `status`, `workflow_id`, `started_after`, `started_before`, and `error_code` (the dead-letter console's failure-class filter, served by the `workflow_runs(tenant_id, error_code)` index) and return `id`, `workflow_id`, `workflow_version_no`, `status`, `trigger_kind`, `trigger`, `started_at`, `finished_at`, `duration_ms`, `error_code`, `error_message`; `GET /api/v1/workflow-runs/{id}` also returns the ordered steps.
- **FR-F019-12:** `POST /api/v1/workflow-runs/{id}/retry` on a `failed` or `dead_lettered` run re-queues it from the first failed step with the same pinned version and a new attempt series; `POST /api/v1/workflow-runs/{id}/cancel` on a `queued` or `running` run sets `status: cancelled` before the next step boundary; other transitions return `conflict`.
- **FR-F019-13:** Disabling or deleting a workflow (F018) stops new runs immediately; runs already `running` finish their current step and then stop with `status: cancelled` and `error_code: workflow_disabled`; run history remains readable.
- **FR-F019-14:** Every run state change emits the matching event (`workflow-run.queued.v1`, `workflow-run.started.v1`, `workflow-run.completed.v1`, `workflow-run.failed.v1`, `workflow-run.dead-lettered.v1`) through the outbox and writes an audit row attributing the automation actor and the originating human actor; the runs UI lists runs with status filters and lets a workflow editor retry or cancel while a workflow viewer sees read-only.

### Non-functional requirements

- **NFR-F019-01 Performance:** a queued run starts within 2 seconds p95 of the triggering event under 1,000 events per minute per tenant (spec section 6 async acknowledgement); run list p95 under 500 ms with 1,000,000 runs in a tenant; scheduler tick processes 10,000 due triggers in under 30 seconds.
- **NFR-F019-02 Security/privacy:** actions run as a per-tenant service actor whose permissions are the intersection of the publishing editor's permissions at publish time and the workflow's sheet scope; inbound webhook bodies are stored redacted per F027 policy; cross-tenant run IDs return `not_found`; webhook secrets are compared in constant time.
- **NFR-F019-03 Accessibility:** the runs list and run detail pass axe with no serious violations, status is conveyed by text and icon rather than color alone, and retry/cancel dialogs trap focus.
- **NFR-F019-04 Reliability/observability:** JetStream consumer is durable with explicit ack after the run row commits; metrics `workflow_run_total{status}`, `workflow_run_duration_ms`, `workflow_dead_letter_total`, `workflow_queue_depth{tenant}` are exported; every run and step carries a span with `tenant_id`, `workflow_id`, `run_id`, `correlation_id`; a worker crash mid-run resumes from the last committed step.

### Scope

Included: event, schedule, date-reached, webhook, and approval-decision trigger matching; run and step persistence; idempotency; exponential retry; dead letters; timeouts; per-tenant quotas; loop detection; action executors; inbound webhook endpoint; run history API and UI; retry and cancel.

Excluded: workflow authoring and validation (F018); approval quorum and escalation logic (F020); notification channel delivery (F037); integration adapters (F029, F030); multi-step cross-system orchestration (F054); assisted actions (F040).

## 3. UX specification

- Entry points: workflow list row `Runs` link; route `/w/{workspace_id}/sheets/{sheet_id}/workflows/{workflow_id}/runs`; tenant-wide `/w/{workspace_id}/automation/runs`; run detail `/runs/{run_id}`.
- Primary flow: open a workflow, click `Runs`, see the latest runs with status badges, open a `failed` run, read the failing step's `error_code` and `error_message`, click `Retry`, confirm, and watch the run move `queued` → `running` → `completed` via polling every 5 seconds while the page is visible.
- Loading: skeleton table; Empty: `No runs yet` with a link to the workflow's test panel; Error: banner with `correlation_id` and retry; Success: toast `Run re-queued`; Stale/conflict: retry on a run that already completed shows `This run already finished`; Offline: retry/cancel disabled with offline badge.
- Permission-denied: workflow viewers see runs read-only with `Retry` and `Cancel` hidden; no-access renders not-found.
- Responsive: table collapses to cards under 768 px with status, trigger, and duration; step timeline stacks vertically.
- Keyboard: arrow keys move between runs, `Enter` opens detail, `R` opens retry dialog, `C` opens cancel dialog on a focused run, `Escape` closes; focus ring from shared token; `prefers-reduced-motion` disables status pulse.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062); Lucide icons `Play`, `RotateCcw`, `XCircle`, `AlertTriangle`, `Clock`, `CheckCircle2`; tokens from `apps/web/src/design/tokens.css`.

- Design: `design/artboards/WorkflowRuns.dc.html` on the canvas indexed by `design/canvas.json`. The ticket is the contract and the artboard is the picture; when they disagree the ticket wins.

## 4. Technical specification

### Rust backend

- Domain entities in `crates/domain/src/workflow-runtime/`: `WorkflowRun { id, tenant_id, workflow_id, workflow_version_id, status: RunStatus, trigger_kind: TriggerKind, trigger: TriggerPayload, idempotency_key, correlation_id, parent_run_id, depth, attempt, queued_at, started_at, finished_at, error_code: Option<RunErrorCode>, error_message: Option<String>, error_detail: Option<ProviderSnapshot>, version, audit fields }`, `WorkflowRunStep { id, run_id, index, kind, status: StepStatus, attempt, started_at, finished_at, output: Option<ProviderSnapshot>, error_code: Option<RunErrorCode>, error_message: Option<String>, error_detail: Option<ProviderSnapshot> }`, `WorkflowTrigger { id, tenant_id, workflow_id, kind, next_fire_at, timezone, last_fired_at }`, `InboundWebhook { id, tenant_id, workflow_id, token, secret_ref, disabled_at }`, `RunStatus::{Queued, Running, Completed, Failed, DeadLettered, Cancelled}`, `StepStatus::{Pending, Running, Completed, Failed, SkippedError}`, `RunErrorCode::{ActionFailed, Timeout, LoopDetected, WorkflowDisabled, PermissionDenied, HeartbeatLost}`.
- Use cases: `match_event_to_workflows`, `enqueue_run`, `execute_run`, `execute_step`, `schedule_retry`, `dead_letter_run`, `tick_schedules`, `ingest_inbound_webhook`, `retry_run`, `cancel_run`, `list_runs`, `get_run`; executors implement `trait ActionExecutor { fn execute(&self, ctx: &StepContext) -> Result<StepOutput, StepError>; }`.
- Persistence (`crates/persistence/src/workflow-runtime/`): `WorkflowRunRepository` owns `workflow_runs` and `workflow_run_steps`; `WorkflowTriggerRepository` owns `workflow_triggers`; `InboundWebhookRepository` owns `inbound_webhooks` and `inbound_webhook_deliveries`. Each implements the shared `Repository` contract (`get`, `list` with cursor pagination, `insert`, `update` under an expected version, `soft_delete`, `restore`, `purge`) and adds named queries `enqueue_if_absent(tenant_id, idempotency_key, run)`, `claim_next_queued(limit)`, `claim_due_retries(now, limit)`, `record_step_attempt(run_id, index, attempt, outcome)`, `transition_status(run_id, from, to)`, `page_runs(filter, cursor)`, `claim_due_triggers(now, limit)`, `find_webhook_by_token(token)`, `record_delivery_if_absent(webhook_id, delivery_id)`, `expire_deliveries_before(cutoff)`; the tenant predicate, soft-delete filter, version check, audit row, and outbox enqueue come from the base contract. Each step write with its status transition and outbox event runs in one `UnitOfWork` that owns the transaction. Run idempotency comes from `enqueue_if_absent` on `(tenant_id, idempotency_key)`, never from a caller-written `ON CONFLICT`. Per decision 2.1 the use cases above depend on these repository traits and contain no SQL: no SQL string, `sqlx::query*` call, or connection exists in `crates/domain/src/workflow-runtime`, `services/api/src/workflow-runtime`, `services/worker/src/workflow-runtime`, or the F019 tests.
- Worker (`services/worker/src/workflow-runtime/`): durable JetStream consumer `workflow-runtime` on subjects `row.*.v1`, `form.submitted.v1`, `approval.decided.v1`, `workflow-run.queued.v1`; per-tenant token bucket for quotas over `claim_next_queued`; scheduler task every 60 seconds over `claim_due_triggers`; retry scheduler scanning `claim_due_retries` with JetStream delayed redelivery and dead-lettering through `transition_status`. The job holds no SQL and no connection: every read and write is one of the named repository queries above, and the row locks those queries take still serialize the same writers.
- API endpoints (`services/api/src/workflow-runtime/`): `GET /api/v1/workflow-runs`, `GET /api/v1/workflow-runs/{id}`, `POST /api/v1/workflow-runs/{id}/retry`, `POST /api/v1/workflow-runs/{id}/cancel`, `GET /api/v1/workflows/{id}/runs`, `POST /api/v1/webhooks/inbound/{token}`. DTOs: `RunResponse`, `RunDetailResponse`, `RunStepResponse`, `Page<RunResponse>`, `InboundWebhookResponse { run_id, delivery_id }`.
- Events: `workflow-run.queued.v1`, `workflow-run.started.v1`, `workflow-run.completed.v1`, `workflow-run.failed.v1`, `workflow-run.dead-lettered.v1` with `run_id`, `workflow_id`, `version_no`, `status`, `error_code`.
- Authorization: `workflow-viewer` for reads, `workflow-editor` for retry and cancel; inbound webhook authenticates by token plus HMAC and no user session; foreign tenant maps to `not_found`.
- Validation: inbound body ≤ 256 KB and valid JSON; `filter[status]` in the six statuses; `filter[error_code]` in the six run error codes; `limit` 1–200. Idempotency for retry/cancel stored in `idempotency_keys` for 24 hours; run idempotency stored in `workflow_runs.idempotency_key` unique index.
- Error mapping: `RunError::NotFound → 404 not_found`, `RunError::InvalidTransition → 409 conflict`, `WebhookError::BadSignature → 403 denied`, `WebhookError::RateLimited → 429 rate_limited`, `WebhookError::BodyTooLarge → 400 invalid`, `AuthzError::Denied → 403 denied`, quota exhaustion is never an HTTP error (runs stay queued).

### Interface

Exact shapes. Every field gives its JSON name, its type, whether it is required, and the constraint
that makes it invalid. `T?` is nullable; an absent optional field and an explicit `null` mean the
same thing. Ids are UUIDv7 strings, timestamps are RFC 3339 UTC. Unlisted fields are rejected with
`400 invalid`. `Page<T>`, the opaque cursor and `ListQuery` are F028's; the error body and the six
codes are the shared ones; `WorkflowDefinition`, `Trigger`, `ActionKind` and `ActionSpec` are F018's
and are replayed from the pinned version rather than restated here; `ActorContext` is F038's.

Four of the six routes take no request body: `GET /api/v1/workflow-runs`,
`GET /api/v1/workflow-runs/{id}` and `GET /api/v1/workflows/{id}/runs` are reads, and `retry` and
`cancel` are `POST`s with an empty body carrying only `Idempotency-Key` and `If-Match`. A non-empty
body on any of them is `400 invalid`. The one route with a caller-supplied body is the inbound
webhook, whose body is opaque.

**`RunResponse`** — the list item (FR-F019-11) and the envelope of `retry` and `cancel`

| Field | Type | Notes |
|---|---|---|
| `id` | uuid | the `workflow_runs` row |
| `workflow_id` | uuid | |
| `workflow_version_id` | uuid | the immutable F018 version this run is pinned to; editing the workflow never moves it |
| `workflow_version_no` | integer | that version's `version_no`, denormalised into the response for display |
| `status` | `"queued" \| "running" \| "completed" \| "failed" \| "dead_lettered" \| "cancelled"` | |
| `trigger_kind` | TriggerKind | one of the seven `workflow_runs.trigger_kind` members; `field_changed` and `date_reached` runs are recorded under the event that materialised them |
| `trigger` | object | the captured trigger event body, returned verbatim; its shape is the event's, not this feature's |
| `attempt` | integer | attempts consumed so far, 0 before the first execution, at most 5 (FR-F019-06) |
| `depth` | integer | 0 for a run started by a human or a schedule, incremented per nested run, capped at 5 |
| `parent_run_id` | uuid? | the run whose action started this one; `null` at the root of the chain |
| `correlation_id` | uuid | shared by every run in one chain and by the audit rows |
| `queued_at` | timestamp | |
| `started_at` / `finished_at` | timestamp? | `null` while `queued`; `finished_at` `null` while `running` |
| `duration_ms` | integer? | `finished_at − started_at`; present only on a terminal status |
| `next_attempt_at` | timestamp? | present only while `status` is `failed` and attempts remain; the backoff instant of FR-F019-06 |
| `error_code` | RunErrorCode? | see below; `null` on `completed` |
| `error_message` | string? | human text, never parsed; present exactly when `error_code` is |
| `version` | integer | pass as `If-Match` to `retry` or `cancel` |

**`RunErrorCode`** — the closed set a support engineer filters and branches on, matching the
`workflow_runs.error_code` check: `action_failed`, `timeout`, `loop_detected`, `workflow_disabled`,
`permission_denied`, `heartbeat_lost`. `timeout` carries the wall-time or step budget it exceeded in
`error_message` (FR-F019-07); `loop_detected` is the sixth nested run (FR-F019-10);
`workflow_disabled` is a run stopped at a step boundary by F018 (FR-F019-13); `heartbeat_lost` is set
by the reaper on a run whose worker died. The provider or executor response that produced the failure
is not in this envelope — it is `error_detail`, returned only on the step, so a list page never
carries a payload.

**`RunDetailResponse`** — `GET /api/v1/workflow-runs/{id}`: every field of `RunResponse` plus
`steps: RunStepResponse[]` in `index` order, one entry per step per attempt, and `error_detail`
(object?, the failing executor's response snapshot, present only when `error_code` is).

**`RunStepResponse`**

| Field | Type | Notes |
|---|---|---|
| `id` | uuid | |
| `index` | integer | the step's position in the pinned version's `workflow_steps`, 0-based |
| `kind` | ActionKind | F018's twelve action kinds; F020's `request_approval` and F054's connector steps appear here like any other |
| `status` | `"pending" \| "running" \| "completed" \| "failed" \| "skipped_error"` | `skipped_error` is a failed step whose `continue_on_error` was `true`, so the run continued (FR-F019-05) |
| `attempt` | integer | 1-based; the unique key is `(run_id, index, attempt)`, so a retried step is a new row, never an overwrite |
| `started_at` / `finished_at` | timestamp? | |
| `output` | object? | the executor's success snapshot, returned verbatim; absent on a failed step |
| `error_code` | RunErrorCode? | the same closed set as the run |
| `error_message` | string? | present exactly when `error_code` is |
| `error_detail` | object? | the executor or provider response that explains the failure — the field the dead-letter console shows and the reason it is a step field and not a run field |

**List routes.** `GET /api/v1/workflow-runs` and `GET /api/v1/workflows/{id}/runs` both return
`Page<RunResponse>` in F028's envelope `{ items, next_cursor, has_more, total? }`, sorted by
`queued_at` descending — the only sort key, because that is the order the
`workflow_runs(tenant_id, workflow_id, queued_at desc)` index serves — with `limit` 1–200. Filters,
each `400 invalid` with `field_errors.filter` when outside its set:

| Filter | Type | Constraint |
|---|---|---|
| `status` | RunStatus | one of the six |
| `workflow_id` | uuid | rejected on `/workflows/{id}/runs`, where the path already fixes it |
| `started_after` / `started_before` | timestamp | RFC 3339; `started_after` must not exceed `started_before` |
| `error_code` | RunErrorCode | one of the six; the dead-letter console's failure-class filter served by `workflow_runs(tenant_id, error_code)` |

**Inbound webhook** — `POST /api/v1/webhooks/inbound/{token}` (FR-F019-04). The body is arbitrary
JSON up to 256 KB, stored as the run's `trigger` and never interpreted by this feature. It carries no
session: `token` is the `inbound_webhooks.token` and the caller proves possession of the secret.

| Header | Type | Required | Constraint |
|---|---|---|---|
| `X-OpsHub-Signature` | string | yes | hex HMAC-SHA256 of the raw body under the token's `secret_ref` secret, compared in constant time; a mismatch is `403 denied` and no run is created |
| `X-OpsHub-Delivery-Id` | string | yes | 1–128 chars; a repeat within 24 hours returns `200` with the original `run_id` and creates no second run |
| `Content-Type` | string | yes | `application/json`; anything else is `400 invalid` |

**`InboundWebhookResponse`** `{ run_id: uuid, delivery_id: string }`, returned `202` on a new
delivery and `200` on a replay, so a sender can tell the two apart without parsing the body.

**Status codes**

| Status | `code` | Produced by |
|---|---|---|
| `202` | — | a new inbound webhook delivery accepted and queued |
| `400` | `invalid` | a filter value outside its set, a body over 256 KB or not valid JSON, a body on `retry` or `cancel`, an out-of-range `limit` or malformed cursor |
| `403` | `denied` | a `workflow-viewer` calling `retry` or `cancel`, which need `workflow-editor`; a webhook signature mismatch |
| `404` | `not_found` | unknown, foreign-tenant or invisible run, workflow or webhook token; an unknown token is never distinguished from a wrong one |
| `409` | `conflict` | `retry` on a run that is not `failed` or `dead_lettered`, `cancel` on a run that is not `queued` or `running`, stale `If-Match`, `Idempotency-Key` replayed with a different body |
| `429` | `rate_limited` | more than 60 inbound deliveries per minute for one token; carries `Retry-After` |
| `503` | `unavailable` | JetStream or the outbox is unreachable. Tenant quota exhaustion is **not** an error: those runs stay `queued` and are dequeued round-robin (FR-F019-08) |

### Use case signatures

In `crates/domain/src/workflow-runtime/`. Every one takes `ctx: &ActorContext` — for worker paths the
per-tenant service actor of NFR-F019-02 — takes a `UnitOfWork` for writes or a repository trait for
reads, never a pool or a connection, and returns the shared `DomainError`.

```rust
fn match_event_to_workflows(ctx: &ActorContext, repo: &dyn WorkflowVersionRepository, event: &ChangeEvent) -> Result<Vec<WorkflowVersionId>, DomainError>;
fn enqueue_run(ctx: &ActorContext, uow: &mut UnitOfWork, version: WorkflowVersionId, trigger: TriggerPayload, parent: Option<RunId>) -> Result<WorkflowRun, DomainError>;
fn execute_run(ctx: &ActorContext, uow: &mut UnitOfWork, registry: &ExecutorRegistry, id: RunId) -> Result<WorkflowRun, DomainError>;
fn execute_step(ctx: &ActorContext, uow: &mut UnitOfWork, registry: &ExecutorRegistry, id: RunId, index: StepIndex, attempt: Attempt) -> Result<StepOutcome, DomainError>;
fn schedule_retry(ctx: &ActorContext, uow: &mut UnitOfWork, id: RunId, attempt: Attempt) -> Result<Timestamp, DomainError>;
fn dead_letter_run(ctx: &ActorContext, uow: &mut UnitOfWork, id: RunId) -> Result<WorkflowRun, DomainError>;
fn tick_schedules(ctx: &ActorContext, uow: &mut UnitOfWork, now: Timestamp, limit: usize) -> Result<Vec<RunId>, DomainError>;
fn ingest_inbound_webhook(ctx: &ActorContext, uow: &mut UnitOfWork, token: &WebhookToken, delivery: DeliveryId, body: Bytes, signature: &str) -> Result<WorkflowRun, DomainError>;
fn retry_run(ctx: &ActorContext, uow: &mut UnitOfWork, id: RunId, expected: Version) -> Result<WorkflowRun, DomainError>;
fn cancel_run(ctx: &ActorContext, uow: &mut UnitOfWork, id: RunId, expected: Version) -> Result<WorkflowRun, DomainError>;
fn get_run(ctx: &ActorContext, repo: &dyn WorkflowRunRepository, id: RunId) -> Result<RunDetail, DomainError>;
fn list_runs(ctx: &ActorContext, repo: &dyn WorkflowRunRepository, filter: RunFilter, page: Cursor) -> Result<Page<WorkflowRun>, DomainError>;
```

**Transaction boundaries.** `enqueue_run` is one `UnitOfWork` covering the `enqueue_if_absent` insert
on `(tenant_id, idempotency_key)`, the audit row and the `workflow-run.queued.v1` outbox entry, and
the JetStream ack happens only after it commits — that boundary is exactly what makes FR-F019-02
hold, because a redelivery finds the row and a crash before commit leaves nothing to ack.
`execute_step` is one `UnitOfWork` per step attempt covering the `workflow_run_steps` row for
`(run_id, index, attempt)`, the run's status transition, `next_attempt_at`, and the outbox entry for
any state change; a step's own side effect is executed by its executor before that boundary and is
made idempotent on the same triple, so a worker that dies between the effect and the commit re-runs
the step without duplicating it. `ingest_inbound_webhook` writes the
`inbound_webhook_deliveries` row and the run in one boundary, so a replayed `X-OpsHub-Delivery-Id`
can never create a second run. `retry_run` and `cancel_run` each take one boundary over the status
transition under the expected version, the audit row and the outbox entry.

### PostgreSQL/SQLx

- Migration `*_workflow-runtime_*.sql` creates `workflow_runs(id uuid pk, tenant_id uuid not null, workflow_id uuid not null, workflow_version_id uuid not null, status text not null check (status in ('queued','running','completed','failed','dead_lettered','cancelled')), trigger_kind text not null check (trigger_kind in ('row_created','row_updated','form_submitted','approval_decided','schedule','date_reached','webhook_received')), trigger jsonb not null, idempotency_key bytea not null, correlation_id uuid not null, parent_run_id uuid null, depth int not null default 0, attempt int not null default 0, queued_at timestamptz not null, started_at, finished_at, next_attempt_at timestamptz null, error_code text null check (error_code in ('action_failed','timeout','loop_detected','workflow_disabled','permission_denied','heartbeat_lost')), error_message text null, error_detail jsonb null, version bigint not null default 1, created_by, created_at, updated_by, updated_at)`, `workflow_run_steps(id uuid pk, tenant_id, run_id not null, index int not null, kind text not null, status text not null, attempt int not null default 0, started_at, finished_at, output jsonb, error_code text null check (error_code in ('action_failed','timeout','loop_detected','workflow_disabled','permission_denied','heartbeat_lost')), error_message text null, error_detail jsonb null)`, `workflow_triggers(id uuid pk, tenant_id, workflow_id not null, kind text not null, next_fire_at timestamptz, timezone text not null default 'UTC', last_fired_at timestamptz)`, `inbound_webhooks(id uuid pk, tenant_id, workflow_id not null, token text not null, secret_ref text not null, disabled_at timestamptz, created_at)`, `inbound_webhook_deliveries(tenant_id, webhook_id, delivery_id text, run_id uuid, received_at, primary key (webhook_id, delivery_id))`.
- `jsonb` audit: `workflow_runs.trigger` stays `jsonb` — it is the captured trigger event payload, an explicitly allowed case in decision section 2, stored verbatim so a run can be replayed against the same body; every fact the product filters or joins on (`workflow_id`, `status`, `queued_at`, `correlation_id`, `parent_run_id`, `depth`) is already its own typed column, and the trigger class the run list and mobile cards render per row is projected into `trigger_kind` so it is never read out of the payload, which keeps only the event body. `workflow_run_steps.output` stays `jsonb` — the provider/action response snapshot kept for the run console and replay, never queried by key. `workflow_runs.error` and `workflow_run_steps.error` are not payloads: the FRs classify failures by a typed code (`timeout`, `loop_detected`, `workflow_disabled`) and the retry and dead-letter path branches on it, so each becomes `error_code` with a `check` over this ticket's codes plus a human `error_message`, and only the provider response snapshot stays in `error_detail jsonb` under the section 2 snapshot allowance. `inbound_webhooks.secret_ref` is a vault reference, never the secret itself.
- Invariants: unique `workflow_runs(tenant_id, idempotency_key)`; unique `workflow_run_steps(run_id, index, attempt)`; unique `inbound_webhooks(token)`; primary key `inbound_webhook_deliveries(webhook_id, delivery_id)`; `workflow_version_id` references `workflow_versions(id)` with `on delete restrict` so versions with history are never purged; `depth <= 5` check constraint; `error_code` non-null exactly when `status in ('failed','dead_lettered','cancelled')` and a failure class applies, enforced by the `check` above rather than by JSON shape.
- Indexes: `workflow_runs(tenant_id, status, queued_at) where status in ('queued','running')`, `workflow_runs(tenant_id, workflow_id, queued_at desc)`, `workflow_runs(next_attempt_at) where status = 'failed'`, `workflow_runs(tenant_id, error_code) where error_code is not null` so the run console filters by failure class without scanning a JSON document — the dead-letter triage the FRs describe is preserved as an index lookup, `workflow_triggers(next_fire_at) where next_fire_at is not null`, `workflow_run_steps(run_id, index)`.
- Audit events: `workflow-run.queue`, `workflow-run.start`, `workflow-run.complete`, `workflow-run.fail`, `workflow-run.dead-letter`, `workflow-run.retry`, `workflow-run.cancel`, `webhook.inbound.receive` with `run_id`, `workflow_id`, `version_no`, and originating actor.
- Retention/deletion: runs and steps older than the tenant retention window (default 90 days, dead letters 30 days after last attempt) are purged by the F027 job; `inbound_webhook_deliveries` rows expire after 24 hours through `InboundWebhookRepository::expire_deliveries_before`; rollback drops `workflow_runs`, `workflow_run_steps`, `workflow_triggers`, `inbound_webhooks`, and `inbound_webhook_deliveries` together with the `workflow_runs(tenant_id, error_code)` index.

### React/TypeScript

- Routes in `apps/web/src/features/workflow-runtime/`: `/w/:workspaceId/automation/runs`, `/w/:workspaceId/sheets/:sheetId/workflows/:workflowId/runs`, `/runs/:runId`; components `RunListPage`, `RunTable`, `RunStatusBadge`, `RunDetailPage`, `StepTimeline`, `StepErrorPanel` (renders `error_code` as a labelled failure class with `error_message` beneath), `RetryRunDialog`, `CancelRunDialog`, `InboundWebhookCard` (shows token URL and rotate control).
- State: TanStack Query keys `['workflow-runs', workspaceId, filters, cursor]`, `['workflow-runs', 'byWorkflow', workflowId, cursor]`, `['workflow-run', runId]` with `refetchInterval: 5000` while a run is `queued` or `running` and the tab is visible.
- API client: generated `WorkflowRuntimeApi` with `listRuns`, `listWorkflowRuns`, `getRun`, `retryRun`, `cancelRun`.
- Optimistic updates: retry sets status `queued` locally and rolls back on `conflict` with the finished-run banner.
- Telemetry: `run_list_opened`, `run_detail_opened`, `run_retried`, `run_cancelled`, `webhook_token_rotated` with `workflow_id`, `run_id`, `status`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F019-01 through FR-F019-14 in `testing/features/F019/requirements/cases.md`
- [ ] Failure/edge-case tests: duplicate event delivery, missed schedule tick, bad webhook signature, replayed delivery ID, step timeout, fifth failure to dead letter, nested loop depth 6, quota overflow, disable mid-run
- [ ] Permission-negative and tenant-isolation tests: viewer retry returns `denied`, foreign tenant run returns `not_found`, service actor cannot write a sheet outside scope
- [ ] Rust unit tests: `crates/domain/src/workflow-runtime/` backoff schedule, idempotency key derivation, state transitions, cron next-fire in DST timezone; repository tests in `crates/persistence/src/workflow-runtime/` for `enqueue_if_absent`, `claim_next_queued`, `claim_due_retries`, and `transition_status`
- [ ] API contract/integration tests: every route above with success and each error code
- [ ] Database migration/constraint tests: unique idempotency key, step attempt uniqueness, depth check, `error_code` and `trigger_kind` check constraints, partial indexes including `workflow_runs(tenant_id, error_code)`, rollback
- [ ] React component tests: `RunTable`, `RunDetailPage`, `StepTimeline`, `RetryRunDialog` states
- [ ] Browser E2E tests: trigger a run by editing a row, watch completion, fail and retry, cancel, viewer read-only
- [ ] Accessibility tests: axe on list and detail, status not color-only, dialog focus
- [ ] Performance/load tests: 1,000 events per minute start latency, 1,000,000-run list, 10,000 due triggers per tick

### Fast fanout configuration

- Test harness path: `testing/features/F019/`
- Feature flag: `F019_FEATURE`
- Fixture/seed factory: `testing/fixtures/workflow_runtime.rs` builds tenant, sheet, 8 published workflows from `testing/features/F018/fixtures/definitions.rs`, editor, viewer, foreign tenant, and an inbound webhook token
- Deterministic test data: fixed UUIDv7 seeds, controllable clock `2026-09-03T00:00:00Z` with `advance()`, timezone `America/New_York` for DST cases
- Mock/stub contracts: embedded NATS JetStream server per worker; recording executors for notification, approval, webhook, and integration actions; real row services from F006/F008
- Parallel isolation: one schema and one JetStream stream prefix per test worker, tenant ID per test
- Targeted command: `cargo xtask test-feature F019`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F019/`

## 6. Acceptance criteria

```gherkin
Feature: Workflow runtime

Scenario: Row update triggers exactly one run
  Given published workflow "Assign on approve" on sheet "Requests"
  When row "Kickoff" changes Status to "Approved" and JetStream delivers the event twice
  Then exactly one workflow_runs row exists with status completed
  And the Owner column is set once and workflow-run.completed.v1 is in the outbox

Scenario: Failing webhook action dead-letters after five attempts
  Given a published workflow whose only action calls an unreachable webhook
  When the run executes and the clock advances through the backoff schedule
  Then attempts 1 to 5 fail with increasing delays capped at 15 minutes
  And the run is dead_lettered and workflow-run.dead-lettered.v1 is published

Scenario: Viewer cannot retry
  Given a dead-lettered run visible to a workflow viewer
  When the viewer calls retry
  Then the response is 403 denied and the run stays dead_lettered

Scenario: Inbound webhook with bad signature is rejected
  Given a webhook_received workflow with token "tok_123"
  When a request arrives with an invalid X-OpsHub-Signature
  Then the response is 403 denied and no run is created

Scenario: Cross-tenant run is invisible
  Given a run in tenant A
  When an editor from tenant B requests it by id
  Then the response is 404 not_found
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F018 (published versions, `evaluate_condition`, `resolve_placeholders`), F004 (outbox, JetStream transport, worker baseline); decisions sections 2–4, 7; contracts row F019
- Blocks: F020, F054
- Conflicts with: none (disjoint owned paths)
- External dependencies: NATS JetStream from F004 compose; F016, F020, F037, F029/F030 executors are stubbed until those features ship and wired behind their flags
- Risks and mitigations: at-least-once delivery could duplicate side effects, so the run idempotency key and per-step `(run_id, index, attempt)` keys are enforced before any executor runs; a hot tenant could starve others, so dequeue is round-robin per tenant with quotas; a crashed worker could leave a run `running`, so a reaper marks runs with no heartbeat for 5 minutes as failed attempts with `error_code: heartbeat_lost`.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F018 and F004 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F019/`
- [ ] Migration file name and owned paths claimed
- [ ] Embedded JetStream harness and `testing/fixtures/workflow_runtime.rs` available

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for every run transition
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F019_FEATURE` (consumer stops, queued runs preserved), run down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Published workflows now execute on row, form, approval, schedule, date, and webhook triggers with visible run history, retry, cancel, and dead-letter recovery.
- Migration adds `workflow_runs`, `workflow_run_steps`, `workflow_triggers`, `inbound_webhooks`, and `inbound_webhook_deliveries`; rollback drops them. Feature is off by default behind `F019_FEATURE`.
