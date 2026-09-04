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
owned_paths: [crates/domain/src/bridge/**, services/api/src/bridge/**, services/worker/src/bridge/**, apps/web/src/features/bridge/**, services/api/migrations/*_bridge_*.sql, testing/features/F054/**]
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
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 7, 9, 10; `docs/capability-contracts.md` row F054
- Module slug: `bridge`

## 2. Requirement specification

### Problem and user outcome

Single-trigger workflows (F018/F019) cannot express a process that spans several external systems: create a Jira issue, wait for an approval, post to Slack, then update the OpsHub row with the issue key. Teams script this outside the platform, losing audit, retry, and permission control. Bridge adds a multi-step orchestration layer that reuses the F019 runtime and the F030 connector actions instead of introducing a second execution engine.

As a workflow editor, I want to compose a published, versioned multi-step flow with connector actions, transforms, waits, and branches, run it on events or on demand, watch every step in a run console, and retry a failed step without re-running the whole flow, so that cross-system processes are observable, idempotent, and reversible.

### Functional requirements

- **FR-F054-01:** `POST /api/v1/bridge/flows` by a `workflow-editor` creates a draft flow with `name` (1–120 chars), `description`, and `steps[]` (1–50 items) where each step has `id` (unique within the flow), `kind` (`trigger`, `connector_action`, `opshub_action`, `transform`, `wait`, `branch`), `config`, and `next` (step id or `null`); exactly one `trigger` step must be first, more than 50 steps returns `400 invalid` with `field_errors.steps`.
- **FR-F054-02:** `trigger` config accepts `row_event` (`sheet_id`, `event`: `created|updated|deleted`), `schedule` (cron in the tenant timezone, minimum interval 5 minutes), `inbound_webhook` (issues a token served by the F019 route `POST /api/v1/webhooks/inbound/{token}`), or `sync_event` (`sync_id` from F030); an unknown kind returns `400 invalid` with `field_errors.steps[i].config.kind`.
- **FR-F054-03:** `connector_action` config names an F030 adapter action (`jira.create_issue`, `jira.transition_issue`, `salesforce.update_record`, `slack.post_message`, `box.upload_file`, `dropbox.upload_file`, `google_drive.create_file`), a `connection_id` the flow owner may use, and an `input` mapping validated against the action's typed input schema at publish time; a connection the owner cannot use returns `403 denied` with `field_errors.steps[i].config.connection_id`.
- **FR-F054-04:** `transform` config is a declarative field mapping using the F035 expression subset (text, date, arithmetic, conditional functions; no cross-sheet references, 500 AST nodes max); `for_each` iterates over an array output of a prior step with at most 1,000 items; loops are otherwise rejected at publish with `409 conflict` and `field_errors.steps = "cycle"`.
- **FR-F054-05:** `POST /api/v1/bridge/flows/{id}/publish` validates the graph (single trigger, reachable steps, no cycles, schemas resolved, connection access), writes an immutable `bridge_flow_versions` row with `version` n and the step snapshot, and writes an audit row `bridge.flow.publish`; drafts are edited with `PATCH /api/v1/bridge/flows/{id}` and `If-Match` without affecting the published version.
- **FR-F054-06:** `POST /api/v1/bridge/flows/{id}/run` with `{ input, idempotency_key }` enqueues a run pinned to the latest published version and returns `202` with `run_id` within 2 seconds; the same idempotency key returns the original run; a flow without a published version returns `409 conflict`; a tenant beyond `max_runs_per_day` receives `429 rate_limited`.
- **FR-F054-07:** The worker executes steps in order on the F019 runtime with per-tenant quota, per-step timeout of at most 300 seconds (configurable per step, default 60), exponential retry (1 s, 4 s, 16 s) up to 3 attempts for `unavailable`/`rate_limited` errors, and marks the step `failed` and the run `failed` after the last attempt; every step writes a `bridge_run_steps` row with `status`, `attempts`, `input_snapshot`, `output_snapshot`, `error_code`, `started_at`, `finished_at`.
- **FR-F054-08:** Secrets (connection tokens, headers matching `authorization|token|secret|password`) are redacted to `***` in `input_snapshot`, `output_snapshot`, logs, and events before persistence.
- **FR-F054-09:** `wait` config supports `delay` (1 minute to 30 days, resumed by the F004 scheduler) and `approval` (creates an F020 approval and resumes on `approval.decided.v1`, following the decided branch); waiting runs consume no worker slot.
- **FR-F054-10:** `POST /api/v1/bridge/runs/{id}/retry-step` with `{ step_id }` on a run in `failed` state re-executes that step with its original input snapshot, resumes downstream steps, and emits `bridge-run.step-completed.v1` for the retried step; retrying a step that is not `failed` returns `409 conflict`.
- **FR-F054-11:** `GET /api/v1/bridge/runs` pages runs by cursor with filters `flow_id`, `status` (`queued|running|waiting|succeeded|failed|cancelled`), `from`, `to`; `GET /api/v1/bridge/runs/{id}` returns the run, its pinned `flow_version`, and ordered steps with redacted snapshots; `workflow-viewer` may read, `workflow-editor` may retry or cancel.
- **FR-F054-12:** Events `bridge-run.started.v1`, `bridge-run.step-completed.v1`, `bridge-run.completed.v1`, `bridge-run.failed.v1` are published through the outbox with `run_id`, `flow_id`, `flow_version`, `step_id` (where applicable), `correlation_id`; every flow mutation, publish, run, retry, and cancel writes an `audit_events` row.
- **FR-F054-13:** Every `/api/v1/bridge/*` route sits behind `RequireModule(ModuleSlug::Bridge)`; a tenant without an active `bridge` entitlement or with `F054_FEATURE` disabled receives `403 denied` with `field_errors.module`; entitlement limits `max_flows` and `max_steps_per_flow` are enforced on create, patch, and publish with `409 conflict` and `field_errors.limit`.
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

- Domain entities in `crates/domain/src/bridge/`: `BridgeFlow { id, tenant_id, workspace_id, name, description, owner_id, draft_steps: Vec<Step>, published_version: Option<i64>, version, audit fields, deleted_at }`, `Step { id: StepId, kind: StepKind, config: StepConfig, next: Option<StepId>, timeout_secs: u32 }`, `StepKind` enum, `StepConfig` enum (`Trigger(TriggerConfig)`, `ConnectorAction { action: ActionRef, connection_id, input: FieldMapping }`, `OpshubAction(WorkflowAction)`, `Transform { mapping: FieldMapping, for_each: Option<ForEach> }`, `Wait(WaitConfig)`, `Branch { conditions: Vec<(Condition, StepId)>, otherwise: StepId }`), `BridgeFlowVersion { id, flow_id, version, steps_snapshot, published_by, published_at }`, `BridgeRun { id, tenant_id, flow_id, flow_version, status: RunStatus, idempotency_key, input, current_step_id, correlation_id, started_at, finished_at, error_code }`, `BridgeRunStep { id, run_id, step_id, kind, status: StepStatus, attempts, input_snapshot, output_snapshot, error_code, started_at, finished_at }`.
- Use cases: `create_flow`, `update_flow`, `publish_flow` (calls `validate_graph` and `resolve_action_schemas`), `enqueue_run`, `list_runs`, `get_run`, `retry_step`, `cancel_run`, `redact(value) -> Value`; pure `validate_graph(steps) -> Result<(), GraphError>` covers single trigger, reachability, cycles, `for_each` bounds, step count.
- Worker in `services/worker/src/bridge/`: `BridgeExecutor` consumes the F019 JetStream subject `workflow-run.bridge` with the F019 quota and idempotency middleware; `StepRunner` dispatches by kind: connector actions call `opshub_connectors::ActionInvoker::invoke(connection_id, action, input)` from F030, OpsHub actions call the F018 action executor, waits schedule a resume via the F004 scheduler or subscribe to `approval.decided.v1`, transforms evaluate through the F035 expression evaluator in restricted mode.
- API endpoints (`services/api/src/bridge/`): `GET /api/v1/bridge/flows`, `POST /api/v1/bridge/flows`, `PATCH /api/v1/bridge/flows/{id}`, `POST /api/v1/bridge/flows/{id}/publish`, `POST /api/v1/bridge/flows/{id}/run`, `GET /api/v1/bridge/runs`, `GET /api/v1/bridge/runs/{id}`, `POST /api/v1/bridge/runs/{id}/retry-step`. DTOs: `CreateFlowRequest`, `UpdateFlowRequest`, `PublishResponse { version }`, `RunFlowRequest { input, idempotency_key }`, `RunAccepted { run_id, status }`, `RetryStepRequest { step_id }`, `FlowResponse`, `RunResponse { run, flow_version, steps }`, `Page<RunResponse>`. Cancel reuses the F019 route `POST /api/v1/workflow-runs/{id}/cancel` because Bridge runs share the F019 run identifier namespace; the Bridge executor observes the cancellation and marks pending steps `cancelled`.
- Events: `bridge-run.started.v1`, `bridge-run.step-completed.v1`, `bridge-run.completed.v1`, `bridge-run.failed.v1`; payload per contract conventions plus `flow_id`, `flow_version`, `step_id`.
- Authorization: `RequireModule(ModuleSlug::Bridge)` on the router; `workflow-editor` on the workspace for mutations; `workflow-viewer` for reads; connection access checked with F029 `integration_connections` ACL at publish and per step at run time; explicit deny wins; foreign tenant → `not_found`.
- Validation: name 1–120 chars; steps 1–50; `timeout_secs` 5–300; `for_each` ≤ 1,000 items; transform expressions ≤ 500 AST nodes; schedule interval ≥ 5 minutes; `input` ≤ 256 KB.
- Error mapping: `GraphError::* → 409 conflict` with `field_errors.steps`, `BridgeError::NotPublished → 409 conflict`, `BridgeError::StepNotFailed → 409 conflict`, `BridgeError::LimitExceeded → 409 conflict` with `field_errors.limit`, `BridgeError::QuotaExceeded → 429 rate_limited`, `ConnectionError::Denied → 403 denied`, `NotFound → 404`, `StaleVersion → 409`, validation → `400 invalid`.

### PostgreSQL/SQLx

- Migration `*_bridge_*.sql` creates `bridge_flows(id uuid pk, tenant_id uuid not null, workspace_id uuid not null, name text not null, description text, owner_id uuid not null, draft_steps jsonb not null, published_version bigint, version bigint not null default 1, created_by, created_at, updated_by, updated_at, deleted_at)`, `bridge_flow_versions(id uuid pk, tenant_id, flow_id uuid not null references bridge_flows(id), version bigint not null, steps_snapshot jsonb not null, published_by uuid, published_at timestamptz not null)`, `bridge_runs(id uuid pk, tenant_id, flow_id, flow_version bigint not null, status text not null check (status in ('queued','running','waiting','succeeded','failed','cancelled')), idempotency_key text not null, input jsonb, current_step_id text, correlation_id uuid not null, error_code text, started_at, finished_at, created_at)`, `bridge_run_steps(id uuid pk, tenant_id, run_id uuid not null references bridge_runs(id), step_id text not null, kind text not null, status text not null check (status in ('pending','running','waiting','succeeded','failed','skipped','cancelled')), attempts int not null default 0, input_snapshot jsonb, output_snapshot jsonb, error_code text, started_at, finished_at)`.
- Invariants: unique `bridge_flows(tenant_id, workspace_id, lower(name)) where deleted_at is null`; unique `bridge_flow_versions(flow_id, version)`; unique `bridge_runs(tenant_id, flow_id, idempotency_key)`; unique `bridge_run_steps(run_id, step_id, attempts)`; check `jsonb_array_length(draft_steps) between 1 and 50`; foreign keys `on delete restrict`.
- Indexes: `bridge_runs(tenant_id, flow_id, created_at desc)`, `bridge_runs(tenant_id, status, created_at desc)`, `bridge_run_steps(run_id, started_at)`, `bridge_runs(status) where status = 'waiting'`.
- Audit events: `bridge.flow.create`, `bridge.flow.update`, `bridge.flow.publish`, `bridge.run.enqueue`, `bridge.run.retry-step`, `bridge.run.cancel` with diffs.
- Retention/deletion: flows soft-delete; runs and steps follow the tenant workflow-run retention policy (F027 purge); rollback drops the four tables (no data before this feature).

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
- [ ] Database migration/constraint tests: uniqueness, status checks, step count check, indexes, rollback
- [ ] React component tests: `FlowBuilderPage`, `StepForm` variants, `RunConsolePage`, `StepTimeline` states
- [ ] Browser E2E tests: build, publish, run, fail, retry step, cancel, viewer read-only
- [ ] Accessibility tests: axe on builder and console, timeline keyboard navigation, live region
- [ ] Performance/load tests: enqueue p95 < 2 s, 10-step run < 30 s, run list p95 < 500 ms at 100k runs

### Fast fanout configuration

- Test harness path: `testing/features/F054/`
- Feature flag: `F054_FEATURE`
- Fixture/seed factory: `testing/fixtures/bridge.rs` builds tenant A (editor, viewer), tenant B, active `bridge` entitlement with `max_flows 10`, `max_steps_per_flow 50`, `max_runs_per_day 100`, mocked Jira/Slack/Salesforce connections, a seeded 5-step flow, and 200 historical runs
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
- [ ] Migration file name and owned paths claimed, including `services/worker/src/bridge/**`
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
- Migration adds `bridge_flows`, `bridge_flow_versions`, `bridge_runs`, and `bridge_run_steps`; rollback drops them. Feature is off by default behind `F054_FEATURE` and requires the `bridge` entitlement.
