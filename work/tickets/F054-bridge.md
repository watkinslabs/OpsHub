---
id: F054
type: feature
status: planned
priority: P1
owner: platform
estimate: 8
target_milestone: M7
parent_epic: E008
depends_on: [F019, F030, F048]
blocks: []
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/bridge/**, crates/persistence/src/bridge/**, services/api/src/bridge/**, services/worker/src/bridge/**, apps/web/src/features/bridge/**, services/api/migrations/*_bridge_*.sql, testing/features/F054/**]
feature_flag: F054_FEATURE
flag_default: off
branch: f054-bridge
started_at: null
finished_at: null
---

# F054 — Bridge

## 1. Identity and dates

- Branch: `f054-bridge`
- Capability area: advanced modules (spec 5.11 Bridge "advanced multi-step cross-system workflows using the same event/action contracts"; 5.5 AUTO-02, AUTO-03; 5.9 INT-02, INT-03; section 2 non-goal "arbitrary code execution in workflows"; section 10 connector contract decision)
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 7, 9, 10; `docs/capability-contracts.md` row F054
- Module slug: `bridge`

## 2. Requirement specification

### Problem and user outcome

Single-trigger workflows (F018/F019) cannot express a process that spans several external systems: create a Jira issue, wait for an approval, post to Slack, then update the OpsHub row with the issue key. Teams script this outside the platform, losing audit, retry, and permission control. Bridge adds a multi-step orchestration layer that reuses the F019 runtime and the F030 connector actions instead of introducing a second execution engine.

As a workflow editor, I want to compose a published, versioned multi-step flow with connector actions, transforms, waits, and branches, run it on events or on demand, watch every step in a run console, and retry a failed step without re-running the whole flow, so that cross-system processes are observable, idempotent, and reversible.

### Functional requirements

- **FR-F054-01:** `POST /api/v1/bridge/flows` by a `workflow-editor` creates a draft flow with `name` (1–120 chars), `description`, and `steps[]` (1–50 items) where each step has `id` (unique within the flow), `kind` (`trigger`, `connector_action`, `opshub_action`, `transform`, `wait`, `branch`), `config`, and `next` (step id or `null`); the request and response keep the ordered `steps[]` array, which `BridgeFlowRepository` stores as one `bridge_flow_steps` row per step carrying `step_order`, `kind`, `next_step_id`, and `timeout_secs`, and reassembles in `step_order` on read. Exactly one `trigger` step must be first, more than 50 steps returns `400 invalid` with `field_errors.steps`.
- **FR-F054-02:** `trigger` config accepts `row_event` (`sheet_id`, `event`: `created|updated|deleted`), `schedule` (cron in the tenant timezone, minimum interval 5 minutes), `inbound_webhook` (issues a token served by the F019 route `POST /api/v1/webhooks/inbound/{token}`), or `sync_event` (`sync_id` from F030), stored as the step's `bridge_flow_step_triggers` row with `trigger_kind` and only the columns that kind uses; an unknown kind returns `400 invalid` with `field_errors.steps[i].config.kind`.
- **FR-F054-03:** `connector_action` config names an F030 adapter action (`jira.create_issue`, `jira.transition_issue`, `salesforce.update_record`, `slack.post_message`, `box.upload_file`, `dropbox.upload_file`, `google_drive.create_file`), a `connection_id` the flow owner may use, and an `input` mapping validated against the action's typed input schema at publish time; the action and connection are the step's `bridge_flow_step_connector_actions` row and each `input` entry is one `bridge_flow_step_mappings(target_field, source_expression)` row, while the API keeps `input` as a JSON object. A connection the owner cannot use returns `403 denied` with `field_errors.steps[i].config.connection_id`.
- **FR-F054-04:** `transform` config is a declarative field mapping using the F035 expression subset (text, date, arithmetic, conditional functions; no cross-sheet references, 500 AST nodes max) stored as `bridge_flow_step_mappings` rows; `for_each` is the step's `bridge_flow_step_transforms` row (`for_each_source_step_id`, `for_each_path`, `max_items` ≤ 1,000) iterating an array output of a prior step; loops are otherwise rejected at publish with `409 conflict` and `field_errors.steps = "cycle"`. A `branch` step stores one `bridge_flow_step_branches` row per condition with `branch_order` fixing evaluation order, and its `otherwise` target is the step's `next_step_id`.
- **FR-F054-05:** `POST /api/v1/bridge/flows/{id}/publish` validates the graph (single trigger, reachable steps, no cycles, schemas resolved, connection access) from the draft step rows, writes an immutable `bridge_flow_versions` row with `version` n and the frozen step snapshot, and writes an audit row `bridge.flow.publish`; drafts are edited with `PATCH /api/v1/bridge/flows/{id}` and `If-Match`, replacing the step rows in one transaction without affecting the published version.
- **FR-F054-06:** `POST /api/v1/bridge/flows/{id}/run` with `{ input, idempotency_key }` enqueues a run pinned to the latest published version and returns `202` with `run_id` within 2 seconds; the same idempotency key returns the original run; a flow without a published version returns `409 conflict`; a tenant beyond `max_runs_per_day` receives `429 rate_limited`.
- **FR-F054-07:** The worker executes steps in order on the F019 runtime with per-tenant quota, per-step timeout of at most 300 seconds (configurable per step, default 60), exponential retry (1 s, 4 s, 16 s) up to 3 attempts for `unavailable`/`rate_limited` errors, and marks the step `failed` and the run `failed` after the last attempt; every attempt writes a `bridge_run_steps` row through `BridgeRunStepRepository::append_step_attempt` with `status`, `attempts`, `input_snapshot`, `output_snapshot`, `error_code`, `started_at`, `finished_at`.
- **FR-F054-08:** Secrets (connection tokens, headers matching `authorization|token|secret|password`) are redacted to `***` in `input_snapshot`, `output_snapshot`, logs, and events before persistence.
- **FR-F054-09:** `wait` config supports `delay` (1 minute to 30 days, resumed by the F004 scheduler) and `approval` (creates an F020 approval and resumes on `approval.decided.v1`, following the decided branch); waiting runs consume no worker slot.
- **FR-F054-10:** `POST /api/v1/bridge/runs/{id}/retry-step` with `{ step_id }` on a run in `failed` state re-executes that step with its original input snapshot, resumes downstream steps, and emits `bridge-run.step-completed.v1` for the retried step; retrying a step that is not `failed` returns `409 conflict`.
- **FR-F054-11:** `GET /api/v1/bridge/runs` pages runs by cursor with filters `flow_id`, `status` (`queued|running|waiting|succeeded|failed|cancelled`), `from`, `to`; `GET /api/v1/bridge/runs/{id}` returns the run, its pinned `flow_version`, and ordered steps with redacted snapshots; `workflow-viewer` may read, `workflow-editor` may retry or cancel.
- **FR-F054-12:** Events `bridge-run.started.v1`, `bridge-run.step-completed.v1`, `bridge-run.completed.v1`, `bridge-run.failed.v1` are published through the outbox with `run_id`, `flow_id`, `flow_version`, `step_id` (where applicable), `correlation_id`; every flow mutation, publish, run, retry, and cancel writes an `audit_events` row.
- **FR-F054-13:** Every `/api/v1/bridge/*` route sits behind `RequireModule(ModuleSlug::Bridge)`; a tenant without an active `bridge` entitlement or with `F054_FEATURE` disabled receives `403 denied` with `field_errors.module`; entitlement limits `max_flows` and `max_steps_per_flow` are enforced on create, patch, and publish from `BridgeFlowRepository::count_flows_for_tenant` and `count_steps_for_flow` with `409 conflict` and `field_errors.limit`.
- **FR-F054-14:** Cross-tenant access to any flow, version, run, or step by ID returns `404 not_found`; a `workflow-viewer` attempting create, patch, publish, run, retry, or cancel receives `403 denied`.
- **FR-F054-15:** The web app provides a flow list, a step builder with typed configuration forms per step kind, and a run console with a step timeline, redacted payload viewer, `Retry step` and `Cancel run` actions, and live status refresh every 5 seconds while a run is active.

### Non-functional requirements

- **NFR-F054-01 Performance:** run enqueue acknowledges in under 2 seconds p95; a 10-step run with mocked connectors completes in under 30 seconds; `GET /api/v1/bridge/runs` responds in under 500 ms p95 with 100,000 runs in the tenant (spec section 6).
- **NFR-F054-02 Security/privacy:** connector actions execute only with connections the flow owner is authorized for at run time (re-checked per step, not only at publish); snapshots and logs are redacted; no step kind executes user-supplied code.
- **NFR-F054-03 Accessibility:** builder and console pass axe with zero serious violations; the step timeline is a keyboard-navigable list with status announced by text; live refresh uses a polite live region and respects `prefers-reduced-motion`.
- **NFR-F054-04 Reliability/observability:** runs are idempotent by key, retried with backoff, dead-lettered after quota or timeout exhaustion into the F019 `dead_letters` path, and every step span carries `tenant_id`, `flow_id`, `run_id`, `step_id`, `correlation_id`; metrics `bridge_run_total{status}`, `bridge_step_duration_seconds{kind}`, `bridge_step_retry_total{action}`.

### Scope

Included: flow CRUD and versioning, six step kinds, publish validation, run enqueue, worker execution on the F019 runtime, connector action invocation through F030, waits and approvals, per-step retry, cancel, run console, entitlement gating, audit, events, redaction.

Excluded: new connector adapters (F029/F030 own adapters; Bridge consumes `jira`, `salesforce`, `slack`, `box`, `dropbox`, `google_drive` actions they expose); arbitrary code steps; parallel fan-out branches beyond `for_each` (sequential); marketplace templates for flows (F015 template catalog).

## 3. UX specification

- Entry points: workspace navigation `Bridge` (shown only when `useModuleAllowed('bridge')`) → `/w/{workspace_id}/bridge`; `New flow`; run console at `/w/{workspace_id}/bridge/runs/{run_id}`; flow page tab `Runs`.
- Primary flow: editor creates flow `Jira intake`, adds trigger `row_event` on sheet `Requests`, adds `connector_action` `jira.create_issue` mapped from row fields, adds `wait` for approval by `Ops leads`, adds `slack.post_message`, adds `opshub_action` update field `Jira key`, publishes (version 1), clicks `Run now` with a test row, opens the run console, watches steps turn green, sees the Slack step fail with `rate_limited`, clicks `Retry step`, run completes.
- Loading: skeleton rows and step cards; Empty: `No flows yet` with `New flow`; Error: inline banner with `correlation_id` and retry; Success: toast on publish and run enqueue; Stale/conflict: banner `This flow changed` with `Reload`; Offline: builder edits disabled with offline badge; Not entitled: shared `ModuleNotEntitled` panel with reason.
- Permission-denied: viewers see flows and runs read-only; `Retry step`, `Cancel run`, `Publish` hidden; API `denied` shows an inline explanation.
- Responsive: builder canvas becomes a vertical list under 768 px; console timeline stacks steps with collapsible payloads under 640 px.
- Keyboard: `Tab` between steps, `Enter` opens the step form, `Escape` closes, `Alt+ArrowUp/Down` reorders a step, `R` on a failed step focuses `Retry step`; focus ring from shared tokens.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062), Lucide icons `Workflow`, `Play`, `RotateCcw`, `XCircle`, `Clock`, `GitBranch`, `Plug`; tokens from `apps/web/src/design/tokens.css`.

## 4. Technical specification

Canonical contract: `docs/capability-contracts.md` row F054 (aggregate `bridge-workflow`, module `bridge`, roles `workflow-editor`; reads by `workflow-viewer` per F019 conventions).

### Rust backend

- Data access (decision section 2.1): `crates/persistence/src/bridge/` holds `BridgeFlowRepository` (owns `bridge_flows`, `bridge_flow_steps`, `bridge_flow_step_triggers`, `bridge_flow_step_connector_actions`, `bridge_flow_step_opshub_actions`, `bridge_flow_step_transforms`, `bridge_flow_step_waits`, `bridge_flow_step_branches`, `bridge_flow_step_mappings`), `BridgeFlowVersionRepository` (`bridge_flow_versions`), `BridgeRunRepository` (`bridge_runs`), and `BridgeRunStepRepository` (`bridge_run_steps`); the step, config, branch, and mapping tables are children of the flow object type and are written only by `BridgeFlowRepository`, so no two classes write the same table. Named queries: `list_flows_for_workspace`, `find_flow_with_steps`, `replace_draft_steps`, `count_flows_for_tenant`, `count_steps_for_flow`, `find_flow_by_name`, `insert_version`, `find_latest_published_version`, `load_version_snapshot`, `insert_run`, `find_run_by_idempotency_key`, `list_runs_by_filters`, `count_runs_since`, `mark_run_status`, `list_waiting_runs_due`, `append_step_attempt`, `list_steps_for_run`, `latest_attempt_for_step`, `mark_pending_steps_cancelled` — there is no generic query entry point.
- Every use case below depends on those repository traits and contains no SQL; `services/api/src/bridge` handlers, `services/worker/src/bridge` executor and step runner, the retry path, the scheduler resume path, and the harness fixtures reach PostgreSQL only through these repositories. A flow create, patch, or publish writes the flow row, its step rows, per-kind config rows, mapping and branch rows, the version row, the audit row, and the outbox row in one `UnitOfWork`; a step attempt writes the `bridge_run_steps` row, the run status transition, the audit row, and the event in the same `UnitOfWork` so a retried or redelivered step cannot half-commit.
- Domain entities in `crates/domain/src/bridge/`: `BridgeFlow { id, tenant_id, workspace_id, name, description, owner_id, draft_steps: Vec<Step>, published_version: Option<i64>, version, audit fields, deleted_at }`, `Step { id: StepId, kind: StepKind, config: StepConfig, next: Option<StepId>, timeout_secs: u32 }`, `StepKind` enum, `StepConfig` enum (`Trigger(TriggerConfig)`, `ConnectorAction { action: ActionRef, connection_id, input: FieldMapping }`, `OpshubAction(WorkflowAction)`, `Transform { mapping: FieldMapping, for_each: Option<ForEach> }`, `Wait(WaitConfig)`, `Branch { conditions: Vec<(Condition, StepId)>, otherwise: StepId }`), `BridgeFlowVersion { id, flow_id, version, steps_snapshot, published_by, published_at }`, `BridgeRun { id, tenant_id, flow_id, flow_version, status: RunStatus, idempotency_key, input, current_step_id, correlation_id, started_at, finished_at, error_code }`, `BridgeRunStep { id, run_id, step_id, kind, status: StepStatus, attempts, input_snapshot, output_snapshot, error_code, started_at, finished_at }`. `draft_steps` and the config, mapping, and branch collections inside `Step` are in-memory projections assembled by `BridgeFlowRepository::find_flow_with_steps` from the step tables and written back by `replace_draft_steps`; the domain types hold no SQLx types.
- Use cases: `create_flow`, `update_flow`, `publish_flow` (calls `validate_graph` and `resolve_action_schemas`), `enqueue_run`, `list_runs`, `get_run`, `retry_step`, `cancel_run`, `redact(value) -> Value`; pure `validate_graph(steps) -> Result<(), GraphError>` covers single trigger, reachability, cycles, `for_each` bounds, step count.
- Worker in `services/worker/src/bridge/`: `BridgeExecutor` consumes the F019 JetStream subject `workflow-run.bridge` with the F019 quota and idempotency middleware; `StepRunner` dispatches by kind: connector actions call `opshub_connectors::ActionInvoker::invoke(connection_id, action, input)` from F030, OpsHub actions call the F018 action executor, waits schedule a resume via the F004 scheduler or subscribe to `approval.decided.v1`, transforms evaluate through the F035 expression evaluator in restricted mode. The executor loads the pinned version through `BridgeFlowVersionRepository::load_version_snapshot`, records progress through `BridgeRunRepository` and `BridgeRunStepRepository`, and issues no SQL of its own.
- API endpoints (`services/api/src/bridge/`): `GET /api/v1/bridge/flows`, `POST /api/v1/bridge/flows`, `PATCH /api/v1/bridge/flows/{id}`, `POST /api/v1/bridge/flows/{id}/publish`, `POST /api/v1/bridge/flows/{id}/run`, `GET /api/v1/bridge/runs`, `GET /api/v1/bridge/runs/{id}`, `POST /api/v1/bridge/runs/{id}/retry-step`. DTOs: `CreateFlowRequest`, `UpdateFlowRequest`, `PublishResponse { version }`, `RunFlowRequest { input, idempotency_key }`, `RunAccepted { run_id, status }`, `RetryStepRequest { step_id }`, `FlowResponse`, `RunResponse { run, flow_version, steps }`, `Page<RunResponse>`. Cancel reuses the F019 route `POST /api/v1/workflow-runs/{id}/cancel` because Bridge runs share the F019 run identifier namespace; the Bridge executor observes the cancellation and marks pending steps `cancelled`.
- Events: `bridge-run.started.v1`, `bridge-run.step-completed.v1`, `bridge-run.completed.v1`, `bridge-run.failed.v1`; payload per contract conventions plus `flow_id`, `flow_version`, `step_id`.
- Authorization: `RequireModule(ModuleSlug::Bridge)` on the router; `workflow-editor` on the workspace for mutations; `workflow-viewer` for reads; connection access checked with F029 `integration_connections` ACL at publish and per step at run time; explicit deny wins; foreign tenant → `not_found`.
- Validation: name 1–120 chars; steps 1–50; `timeout_secs` 5–300; `for_each` ≤ 1,000 items; transform expressions ≤ 500 AST nodes; schedule interval ≥ 5 minutes; `input` ≤ 256 KB.
- Error mapping: `GraphError::* → 409 conflict` with `field_errors.steps`, `BridgeError::NotPublished → 409 conflict`, `BridgeError::StepNotFailed → 409 conflict`, `BridgeError::LimitExceeded → 409 conflict` with `field_errors.limit`, `BridgeError::QuotaExceeded → 429 rate_limited`, `ConnectionError::Denied → 403 denied`, `NotFound → 404`, `StaleVersion → 409`, validation → `400 invalid`.

### PostgreSQL/SQLx

- Migration `*_bridge_*.sql` creates `bridge_flows(id uuid pk, tenant_id uuid not null, workspace_id uuid not null references workspaces(id) on delete restrict, name text not null, description text, owner_id uuid not null references users(id) on delete restrict, published_version bigint, version bigint not null default 1, created_by, created_at, updated_by, updated_at, deleted_at)`, `bridge_flow_versions(id uuid pk, tenant_id, flow_id uuid not null references bridge_flows(id) on delete cascade, version bigint not null, steps_snapshot jsonb not null, published_by uuid not null references users(id) on delete restrict, published_at timestamptz not null)`, `bridge_runs(id uuid pk, tenant_id, flow_id uuid not null references bridge_flows(id) on delete restrict, flow_version bigint not null, status text not null check (status in ('queued','running','waiting','succeeded','failed','cancelled')), idempotency_key text not null, input jsonb, current_step_id text, correlation_id uuid not null, error_code text, started_at, finished_at, created_at, foreign key (flow_id, flow_version) references bridge_flow_versions(flow_id, version) on delete restrict)`, `bridge_run_steps(id uuid pk, tenant_id, run_id uuid not null references bridge_runs(id) on delete cascade, step_id text not null, kind text not null check (kind in ('trigger','connector_action','opshub_action','transform','wait','branch')), status text not null check (status in ('pending','running','waiting','succeeded','failed','skipped','cancelled')), attempts int not null default 0, input_snapshot jsonb, output_snapshot jsonb, error_code text, started_at, finished_at)`. Runs use `on delete restrict` on the flow because a run is retained history that outlives flow deletion until the F027 retention purge removes it; versions, steps, and step rows cannot outlive their parent and cascade.
- Normalized step model (decision section 2, no repeating groups): the ordered step list replaces `bridge_flows.draft_steps jsonb` with `bridge_flow_steps(id uuid pk, tenant_id, flow_id uuid not null references bridge_flows(id) on delete cascade, step_id text not null, step_order int not null check (step_order between 1 and 50), kind text not null check (kind in ('trigger','connector_action','opshub_action','transform','wait','branch')), next_step_id text, timeout_secs int not null default 60 check (timeout_secs between 5 and 300), unique (flow_id, step_id), unique (flow_id, step_order) deferrable initially deferred, foreign key (flow_id, next_step_id) references bridge_flow_steps(flow_id, step_id) on delete restrict deferrable initially deferred)`. Per-kind configuration is one row keyed `(flow_id, step_id)` with a composite foreign key to `bridge_flow_steps` `on delete cascade`: `bridge_flow_step_triggers(flow_id, step_id, trigger_kind text check (trigger_kind in ('row_event','schedule','inbound_webhook','sync_event')), sheet_id uuid references sheets(id) on delete restrict, row_event text check (row_event in ('created','updated','deleted')), cron_expression text, cron_timezone text, inbound_token_hash bytea, sync_id uuid references sync_configs(id) on delete restrict, primary key (flow_id, step_id))`; `bridge_flow_step_connector_actions(flow_id, step_id, action_ref text not null check (action_ref in ('jira.create_issue','jira.transition_issue','salesforce.update_record','slack.post_message','box.upload_file','dropbox.upload_file','google_drive.create_file')), connection_id uuid not null references integration_connections(id) on delete restrict, primary key (flow_id, step_id))`; `bridge_flow_step_opshub_actions(flow_id, step_id, action_type text not null check (action_type in ('update_field','create_row','assign','notify')), target_sheet_id uuid references sheets(id) on delete restrict, target_field text, primary key (flow_id, step_id))`; `bridge_flow_step_transforms(flow_id, step_id, for_each_source_step_id text, for_each_path text, max_items int check (max_items between 1 and 1000), primary key (flow_id, step_id))`; `bridge_flow_step_waits(flow_id, step_id, wait_kind text not null check (wait_kind in ('delay','approval')), delay_seconds int check (delay_seconds between 60 and 2592000), approval_group_id uuid references groups(id) on delete restrict, primary key (flow_id, step_id))`.
- Normalized sets inside a step: `bridge_flow_step_mappings(flow_id, step_id, target_field text not null, source_expression text not null, primary key (flow_id, step_id, target_field))` replaces the `input`/`mapping` object on `connector_action` and `transform` steps; `bridge_flow_step_branches(flow_id, step_id, branch_order smallint not null check (branch_order between 1 and 20), condition_expression text not null, target_step_id text not null, primary key (flow_id, step_id, branch_order), foreign key (flow_id, target_step_id) references bridge_flow_steps(flow_id, step_id) on delete restrict deferrable initially deferred)` replaces the `conditions` list and fixes evaluation order; a branch step's `otherwise` target is its `bridge_flow_steps.next_step_id`. `CreateFlowRequest`, `UpdateFlowRequest`, and `FlowResponse` keep `steps[]`, `config`, `input`, and `conditions[]` in their existing JSON shapes, so no externally visible behaviour changes: `BridgeFlowRepository::replace_draft_steps` fans a submitted flow out to these rows inside one `UnitOfWork` (delete removed rows, insert current rows, constraints deferred until commit so the graph may be rewritten in any order) and `find_flow_with_steps` reassembles the arrays in `step_order` and `branch_order`.
- `jsonb` audit: `bridge_flow_versions.steps_snapshot` stays `jsonb` — it is the frozen published version deserialized whole and replayed verbatim by the executor, never filtered, joined, sorted, or constrained; graph queries run against the draft step tables and run history against `bridge_run_steps`. `bridge_runs.input` stays `jsonb` — the caller-supplied trigger payload, opaque to the product and capped at 256 KB. `bridge_run_steps.input_snapshot` and `output_snapshot` stay `jsonb` — the redacted provider request and response record for one attempt, read only for display. `bridge_flows.draft_steps` was a queried structure (validated, ordered, retried, permission-checked per step) and becomes the step, config, mapping, and branch tables above; no other `jsonb` column remains in this module.
- Invariants: unique `bridge_flows(tenant_id, workspace_id, lower(name)) where deleted_at is null`; unique `bridge_flow_versions(flow_id, version)`, which the `bridge_runs(flow_id, flow_version)` foreign key pins against; unique `bridge_runs(tenant_id, flow_id, idempotency_key)`; unique `bridge_run_steps(run_id, step_id, attempts)`; unique `bridge_flow_steps(flow_id, step_id)` and `(flow_id, step_order)` give exactly one row per step in one order, and the 1–50 step-count limit is the `step_order` check plus `BridgeFlowRepository::count_steps_for_flow` at create, patch, and publish, replacing the former `jsonb_array_length(draft_steps)` check; exactly one `trigger` step per flow with `step_order = 1`, enforced by the partial unique index `bridge_flow_steps(flow_id) where kind = 'trigger'` and the `validate_graph` reachability check; a step's config row must exist for and match its `kind`, checked by `replace_draft_steps` and by the constraint tests; `bridge_flow_step_mappings` and `bridge_flow_step_branches` primary keys block a duplicate target field or duplicate branch position.
- Indexes: `bridge_runs(tenant_id, flow_id, created_at desc)`, `bridge_runs(tenant_id, status, created_at desc)`, `bridge_run_steps(run_id, started_at)`, `bridge_runs(status) where status = 'waiting'`, `bridge_flow_steps(flow_id, step_order)` for ordered assembly, `bridge_flow_steps(flow_id, kind)` for trigger and step-kind lookups, `bridge_flow_step_connector_actions(connection_id)` for the reverse "which flows use this connection" check when a connection is revoked, `bridge_flow_step_triggers(sheet_id)` and `bridge_flow_step_triggers(sync_id)` for dispatching row and sync events to flows, `bridge_flow_step_mappings(flow_id, step_id)`, `bridge_flow_step_branches(flow_id, step_id, branch_order)`.
- Audit events: `bridge.flow.create`, `bridge.flow.update`, `bridge.flow.publish`, `bridge.run.enqueue`, `bridge.run.retry-step`, `bridge.run.cancel` with diffs.
- Retention/deletion: flows soft-delete; runs and steps follow the tenant workflow-run retention policy (F027 purge); rollback drops the twelve tables children before parents (`bridge_flow_step_branches`, `bridge_flow_step_mappings`, the five per-kind config tables, `bridge_flow_steps`, `bridge_run_steps`, `bridge_runs`, `bridge_flow_versions`, `bridge_flows`) with no data before this feature.

### React/TypeScript

- Routes: `/w/:workspaceId/bridge`, `/w/:workspaceId/bridge/:flowId`, `/w/:workspaceId/bridge/runs/:runId` in `apps/web/src/features/bridge/`; components `BridgeListPage`, `FlowBuilderPage`, `StepCanvas`, `StepCard`, `StepForm` (`TriggerForm`, `ConnectorActionForm`, `OpshubActionForm`, `TransformForm`, `WaitForm`, `BranchForm`), `PublishDialog`, `RunNowDialog`, `RunConsolePage`, `RunList`, `RunFilters`, `StepTimeline`, `PayloadViewer`, `RetryStepButton`, `CancelRunDialog`.
- State: TanStack Query keys `['bridge-flows', workspaceId]`, `['bridge-flow', id]`, `['bridge-runs', filters, cursor]`, `['bridge-run', id]` with `refetchInterval` 5,000 ms while status is `queued|running|waiting`; mutations invalidate by key and update cached `version`.
- API client: generated `BridgeApi` with `listFlows`, `createFlow`, `updateFlow`, `publishFlow`, `runFlow`, `listRuns`, `getRun`, `retryStep`.
- Gating: `useModuleAllowed('bridge')` from `apps/web/src/features/entitlements`; not allowed renders `ModuleNotEntitled`.
- Telemetry: `bridge_flow_created`, `bridge_flow_published`, `bridge_run_started`, `bridge_step_retried`, `bridge_run_cancelled`, `bridge_console_opened` with `flow_id`, `run_id`, `step_kind`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F054-01 through FR-F054-15 in `testing/features/F054/requirements/cases.md`
- [ ] Failure/edge-case tests: 51 steps, cycle, two triggers, unpublished run, idempotent replay, retry on non-failed step, `for_each` over 1,001 items, timeout at 300 s, quota exceeded
- [ ] Permission-negative and tenant-isolation tests: viewer mutations denied, foreign tenant runs not found, connection revoked between publish and run, module guard denial
- [ ] Rust unit tests: `validate_graph`, `redact`, retry backoff schedule, branch condition evaluation
- [ ] API contract/integration tests: every route above with success and each error code
- [ ] Database migration/constraint tests: uniqueness, status and kind checks, one trigger step per flow, `(flow_id, step_order)` uniqueness, config row matching its step kind, duplicate mapping target field and duplicate branch order rejected, `next_step_id` and branch target foreign keys, `bridge_runs(flow_id, flow_version)` pin, cascade and restrict behaviour, indexes, rollback ordering
- [ ] React component tests: `FlowBuilderPage`, `StepForm` variants, `RunConsolePage`, `StepTimeline` states
- [ ] Browser E2E tests: build, publish, run, fail, retry step, cancel, viewer read-only
- [ ] Accessibility tests: axe on builder and console, timeline keyboard navigation, live region
- [ ] Performance/load tests: enqueue p95 < 2 s, 10-step run < 30 s, run list p95 < 500 ms at 100k runs

### Fast fanout configuration

- Test harness path: `testing/features/F054/`
- Feature flag: `F054_FEATURE`
- Fixture/seed factory: `testing/fixtures/bridge.rs` writes every row through the `crates/persistence/src/bridge/` repositories and builds tenant A (editor, viewer), tenant B, active `bridge` entitlement with `max_flows 10`, `max_steps_per_flow 50`, `max_runs_per_day 100`, mocked Jira/Slack/Salesforce connections, a seeded 5-step flow, and 200 historical runs
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, UTC, connector mocks return scripted responses by call index
- Mock/stub contracts: F030 `ActionInvoker` mock recording calls; F019 queue in-process; outbox recorded in memory; F020 approval decided by test helper
- Parallel isolation: one schema per test worker, tenant ID per test, unique JetStream subject suffix per worker
- Targeted command: `cargo xtask test-feature F054`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F054/`

## 6. Acceptance criteria

```gherkin
Feature: Bridge multi-step flows

Scenario: Publish and run a five-step flow
  Given an editor with an active bridge entitlement and a Jira connection
  When they publish flow "Jira intake" and run it with a test row
  Then the run reaches status succeeded with five step rows in order
  And bridge-run.started.v1, five bridge-run.step-completed.v1, and bridge-run.completed.v1 are in the outbox

Scenario: Retry a failed connector step
  Given a run whose slack.post_message step failed with rate_limited after 3 attempts
  When the editor posts retry-step for that step
  Then the step re-executes with its original input snapshot, downstream steps resume, and the run succeeds

Scenario: Viewer cannot run or retry
  Given a workflow-viewer in the workspace
  When they POST run or retry-step
  Then the response is 403 denied and no run or step row changes

Scenario: Cycle rejected at publish
  Given a draft whose last step points back to step 2
  When the editor publishes
  Then the response is 409 conflict with field_errors.steps cycle and no version is created

Scenario: Not entitled
  Given a tenant whose bridge entitlement is suspended
  When any user calls GET /api/v1/bridge/flows
  Then the response is 403 denied with field_errors.module suspended
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F019 (runtime queue, quotas, dead letters, inbound webhooks), F030 (connector framework, action schemas, connection ACL), F048 (`RequireModule`, entitlement limits); decisions sections 2–4, 7, 9, 10; contracts row F054
- Blocks: none
- Conflicts with: none (disjoint owned paths)
- External dependencies: Jira, Salesforce, Slack, Box, Dropbox, Google Drive sandboxes mocked in tests; live smoke runs use the F030 mocked connector suite
- Risks and mitigations: connector rate limits can stall long runs, so retries use backoff with jitter and a waiting step releases the worker slot; a published version referencing a revoked connection would fail at run time, so each step re-checks connection access and the console explains `denied` per step; large `for_each` outputs could bloat snapshots, so snapshots are capped at 256 KB per step with a truncation marker.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F019, F030, and F048 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F054/`
- [ ] Migration file name and owned paths claimed, including `crates/persistence/src/bridge/**` and `services/worker/src/bridge/**`
- [ ] F030 action schema registry and F019 queue subjects available to the harness

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/worker/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for every mutation and run transition
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F054_FEATURE` (routes unmounted, worker consumer stops, waiting runs preserved), run down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Workflow editors can build, publish, run, and monitor multi-step cross-system flows with connector actions, approvals, waits, branches, and per-step retry.
- Migration adds `bridge_flows`, `bridge_flow_steps` with its per-kind config, mapping, and branch child tables, `bridge_flow_versions`, `bridge_runs`, and `bridge_run_steps`; rollback drops them children first. Feature is off by default behind `F054_FEATURE` and requires the `bridge` entitlement.
