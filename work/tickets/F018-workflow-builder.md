---
id: F018
type: feature
status: planned
priority: P1
owner: platform
estimate: 8
target_milestone: M3
parent_epic: E004
depends_on: [F007, F035]
blocks: [F019, F040]
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/workflows/**, crates/persistence/src/workflows/**, services/api/src/workflows/**, apps/web/src/features/workflows/**, services/api/migrations/*_workflows_*.sql, testing/features/F018/**]
feature_flag: F018_FEATURE
flag_default: off
branch: f018-workflow-builder
started_at: null
finished_at: null
---

# F018 — Workflow builder

## 1. Identity and dates

- Branch: `f018-workflow-builder`
- Capability area: automation authoring (spec 5.5 AUTO-01, AUTO-02, low-level trigger/condition/action lists and version rules; section 4 `Workflow` entity)
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 6; `docs/capability-contracts.md` row F018
- Aggregate: `workflow`
- Module slug: `workflows`

## 2. Requirement specification

### Problem and user outcome

Teams repeat the same manual steps on every row: set a status, assign an owner, notify a manager, ask for sign-off. They need to express those steps as a trigger, an optional condition tree, and an ordered list of actions without writing code, test the definition against a sample row, and publish it so the runtime (F019) can execute it safely. Every run must be pinned to an immutable version so that editing a workflow never changes the behavior of runs already in flight.

As a workflow editor, I want to define, test, publish, and disable trigger-condition-action workflows on a sheet, so that routine work moves without manual effort and the definition that executed is always auditable.

### Functional requirements

- **FR-F018-01:** An actor with the `workflow-editor` role on the sheet's workspace can `POST /api/v1/workflows` with `name`, `sheet_id`, `trigger`, optional `condition`, and 1 to 25 `actions`; the response returns a UUIDv7 `id`, `state: draft`, `version` 1, and `published_version: null`.
- **FR-F018-02:** `trigger.kind` must be one of `row_created`, `row_updated`, `field_changed` (with `column_id`), `form_submitted` (with `form_id`), `schedule` (with a 5-field cron expression and IANA timezone, minimum interval 5 minutes), `date_reached` (with `column_id` and `offset_minutes` between -43,200 and 43,200), `webhook_received`, or `approval_decided` (with `outcome: approved|rejected|any`); any other kind returns `invalid` with `field_errors.trigger.kind`.
- **FR-F018-03:** `condition` is a tree of `all` / `any` groups nested at most 4 deep containing leaf tests `compare` (typed operators `eq, ne, lt, lte, gt, gte, contains, starts_with, in, between` checked against the column type from F007), `changed` (column changed in this event), `actor_in` (user or group set), `exists` (column has a value), and `formula` (F035 expression returning boolean); a leaf whose operator does not match the column type returns `invalid` with `field_errors.condition[<path>]`.
- **FR-F018-04:** Each action has `kind` in `update_fields`, `create_row`, `move_row`, `copy_row`, `assign`, `comment`, `request_approval`, `send_email`, `send_in_app`, `send_push`, `call_webhook`, `invoke_integration`, a typed `params` object validated per kind, and an optional `continue_on_error: bool` (default false); `call_webhook` params require an `https` URL and a secret reference, never an inline secret.
- **FR-F018-05:** Action params and email/comment bodies may reference row values with `{{row.<column_id>}}`, `{{event.<field>}}`, and `{{actor.<field>}}` placeholders; unknown column IDs return `invalid` with the failing placeholder in `field_errors.actions[<index>].params`.
- **FR-F018-06:** `PATCH /api/v1/workflows/{id}` with `If-Match` edits the draft definition in place while `state` is `draft` or `published`; editing a published workflow creates a new unpublished draft version and never modifies the immutable `workflow_versions` row that `published_version` points to.
- **FR-F018-07:** `POST /api/v1/workflows/{id}/publish` validates the full definition, writes an immutable `workflow_versions` row with a monotonically increasing `version_no`, projects its ordered actions into `workflow_steps` and every F007 column it references into `workflow_step_column_refs`, sets `state: published`, `published_version` to that row, emits `workflow.published.v1`, and returns the new version; publishing a definition with validation errors returns `invalid` with every error listed. Deleting a column still referenced by a published version is refused by the `on delete restrict` foreign key, so F007's delete route reports the conflict without scanning definitions.
- **FR-F018-08:** `POST /api/v1/workflows/{id}/disable` sets `state: disabled`, emits `workflow.disabled.v1`, and stops new runs while preserving run history; publishing again re-enables the workflow with a new version.
- **FR-F018-09:** `POST /api/v1/workflows/{id}/test` accepts `{ row_id }` or `{ sample_event }`, evaluates the trigger match and condition tree against that input without executing actions, and returns `{ trigger_matched, condition_result, action_plan: [ { index, kind, resolved_params } ] }` within 2 seconds.
- **FR-F018-10:** `GET /api/v1/workflows` pages by cursor with `filter` on `sheet_id`, `state`, and `trigger_kind`, and `sort` by `name` or `updated_at`; `GET /api/v1/workflows/{id}` returns the draft definition, the published version summary, and `last_run_at` supplied by F019 when present.
- **FR-F018-11:** `DELETE /api/v1/workflows/{id}` soft deletes a workflow and its draft; the immutable published versions remain readable by ID for run history, and a deleted workflow returns `not_found` on every route except history reads from F019.
- **FR-F018-12:** A sheet can own at most 100 published workflows and a tenant at most 5,000; exceeding either returns `conflict` with `field_errors.limit`.
- **FR-F018-13:** Every mutation requires `Idempotency-Key`, writes an `audit_events` row with a definition diff, and publishes the matching `workflow.updated.v1`, `workflow.published.v1`, or `workflow.disabled.v1` event through the outbox.
- **FR-F018-14:** The builder UI renders trigger, condition, and action steps as an ordered stepper, validates on each change using the same rules as the API, shows the test panel with a picked row, and disables `Publish` until validation passes; a viewer without `workflow-editor` sees the definition read-only and a foreign-tenant ID renders not-found.

### Non-functional requirements

- **NFR-F018-01 Performance:** definition validation completes in under 200 ms p95 for a 25-action workflow with a 4-level condition tree; `test` responds in under 2 seconds p95 including the F035 formula budget; workflow list p95 under 500 ms with 5,000 workflows in a tenant.
- **NFR-F018-02 Security/privacy:** webhook secrets and integration credentials are stored only as references to the F029 vault; definitions never contain raw secrets; cross-tenant workflow IDs return `not_found`; formula conditions evaluate with the editor's permissions and cannot read other sheets the editor cannot read.
- **NFR-F018-03 Accessibility:** the stepper, condition tree, and action forms pass axe with no serious violations, every step is keyboard reachable, tree nesting is announced with `aria-level`, and validation errors are associated to fields with `aria-describedby`.
- **NFR-F018-04 Reliability/observability:** every request carries a span with `tenant_id`, `workflow_id`, and `correlation_id`; publish writes the version and the outbox event in one transaction; metrics `workflow_publish_total`, `workflow_validation_error_total{kind}` are emitted.

### Scope

Included: workflow CRUD, typed trigger/condition/action schema, placeholder resolution, expression evaluation of conditions, draft/publish/disable lifecycle, immutable versions, dry-run test, list/filter, limits, audit, outbox events, builder UI.

Excluded: queueing and executing runs, retries, dead letters, inbound webhook tokens, run history (F019); approval routing and escalation (F020); notification delivery channels (F037); integration adapters (F029, F030); assisted workflow authoring (F040).

## 3. UX specification

- Entry points: sheet toolbar `Automations` button; route `/w/{workspace_id}/sheets/{sheet_id}/workflows`; `New workflow` opens `/workflows/new`; a workflow opens at `/workflows/{workflow_id}`.
- Primary flow: open a sheet, click `Automations`, click `New workflow`, name it, pick trigger `Field changed` and column `Status`, add condition `Status eq Approved`, add actions `Assign` and `Send in-app`, pick a sample row in the test panel, see `trigger_matched: true` and the action plan, click `Publish`, land on the list with state `Published v1`.
- Loading: skeleton stepper; Empty: `No automations yet` with `New workflow`; Error: banner with `correlation_id` and retry; Success: toast `Published v2`; Stale/conflict: banner `This workflow changed` with reload; Offline: editing disabled with offline badge.
- Permission-denied: non-editors see the definition read-only with `Publish`, `Disable`, and `Delete` hidden and an explanation; no-access renders not-found.
- Responsive: stepper stacks vertically under 768 px; condition tree indents with 16 px per level and scrolls horizontally inside its container.
- Keyboard: `Tab` between steps, `Enter` expands a step, `Alt+ArrowUp/Down` reorders actions, `Delete` removes a focused action after confirmation, `Escape` closes pickers; focus ring from shared token; `prefers-reduced-motion` disables step transitions.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062); Lucide icons `Zap`, `GitBranch`, `Play`, `Send`, `Pause`, `Trash2`; tokens from `apps/web/src/design/tokens.css`.

- Design: `design/artboards/Workflow.dc.html` on the canvas indexed by `design/canvas.json`. The ticket is the contract and the artboard is the picture; when they disagree the ticket wins.

## 4. Technical specification

### Rust backend

- Domain entities in `crates/domain/src/workflows/`: `Workflow { id, tenant_id, workspace_id, sheet_id, name, state: WorkflowState, draft: WorkflowDefinition, published_version_id: Option<Uuid>, version, audit fields, deleted_at }`, `WorkflowVersion { id, tenant_id, workflow_id, version_no, definition: WorkflowDefinition, definition_hash, published_by, published_at }`, `WorkflowStep { id, version_id, index, kind: ActionKind, params: serde_json::Value, continue_on_error }`, `WorkflowStepColumnRef { version_id, tenant_id, step_id: Option<Uuid>, column_id, usage: ColumnRefUsage }`, `WorkflowDefinition { trigger: Trigger, condition: Option<ConditionNode>, actions: Vec<ActionSpec> }`, `Trigger` enum, `ConditionNode::{All(Vec), Any(Vec), Compare, Changed, ActorIn, Exists, Formula}`, `ActionSpec`, `WorkflowState::{Draft, Published, Disabled}`.
- Use cases: `create_workflow`, `update_workflow`, `publish_workflow`, `disable_workflow`, `test_workflow`, `delete_workflow`, `get_workflow`, `list_workflows`, `validate_definition`, `evaluate_condition`, `resolve_placeholders`; `evaluate_condition` and `resolve_placeholders` are exported for F019.
- Persistence (`crates/persistence/src/workflows/`): `WorkflowRepository` owns `workflows`; `WorkflowVersionRepository` owns `workflow_versions`, `workflow_steps`, and `workflow_step_column_refs`. Each implements the shared `Repository` contract (`get`, `list` with cursor pagination, `insert`, `update` under an expected version, `soft_delete`, `restore`, `purge`) and adds named queries `list_for_sheet(sheet_id, state, cursor)`, `next_version_no(workflow_id)`, `publish(workflow_id, definition)`, `load_published(workflow_id)`, `load_version(version_id)`, `list_workflows_using_column(column_id)`, `find_by_definition_hash(workflow_id, hash)`; the tenant predicate, soft-delete filter, version check, audit row, and outbox enqueue come from the base contract. Publishing — freezing the draft, inserting the `workflow_versions` row, its `workflow_steps`, its `workflow_step_column_refs`, and repointing `workflows.published_version_id` — runs in one `UnitOfWork` that owns the transaction. `validate_definition`, `evaluate_condition`, and `resolve_placeholders` run over values already loaded and hold no SQL; `POST /api/v1/workflows/{id}/test` evaluates against a loaded fixture row and writes nothing. Per decision 2.1 the use cases above depend on these repository traits and contain no SQL: no SQL string, `sqlx::query*` call, or connection exists in `crates/domain/src/workflows` or `services/api/src/workflows`.
- Filter operators: `docs/filter-vocabulary.md`, subset `eq`, `ne`, `lt`, `lte`, `gt`, `gte`, `contains`, `starts_with`, `in`, `between` — a condition tests a value it already holds; emptiness is the separate `exists` leaf and actor membership the separate `actor_in` leaf.
- API endpoints (`services/api/src/workflows/`): `GET /api/v1/workflows`, `POST /api/v1/workflows`, `GET /api/v1/workflows/{id}`, `PATCH /api/v1/workflows/{id}`, `POST /api/v1/workflows/{id}/publish`, `POST /api/v1/workflows/{id}/disable`, `POST /api/v1/workflows/{id}/test`, `DELETE /api/v1/workflows/{id}`. DTOs: `CreateWorkflowRequest`, `UpdateWorkflowRequest`, `TestWorkflowRequest`, `WorkflowResponse`, `WorkflowVersionSummary`, `TestWorkflowResponse`, `Page<WorkflowResponse>`.
- Events: `workflow.published.v1`, `workflow.disabled.v1`, `workflow.updated.v1` with `changed_fields` and `version_no` for publish.
- Authorization: `workflow-editor` on the workspace for every mutation and `test`; reads follow the sheet ACL; explicit deny wins; foreign tenant or missing access maps to `not_found`.
- Validation: name 1–120 chars; actions 1–25; condition depth ≤ 4 and ≤ 200 leaves; cron minimum interval 5 minutes; placeholders resolved against F007 column metadata; formula leaves parsed by F035 with the 10,000 AST node limit. Idempotency stored in `idempotency_keys` for 24 hours.
- Error mapping: `WorkflowError::Invalid(field_errors) → 400 invalid`, `WorkflowError::StaleVersion → 409 conflict`, `WorkflowError::LimitExceeded → 409 conflict`, `WorkflowError::NotFound → 404 not_found`, `AuthzError::Denied → 403 denied`, `WorkflowError::FormulaTimeout → 400 invalid` with `field_errors.condition`.

### Interface

Exact shapes. Every field gives its JSON name, its type, whether it is required, and the constraint
that makes it invalid. `T?` is nullable; an absent optional field and an explicit `null` mean the
same thing. Ids are UUIDv7 strings, timestamps are RFC 3339 UTC, `version` increments by one per
write. Unlisted fields are rejected with `400 invalid`. `Page<T>`, the opaque cursor and `ListQuery`
are F028's; the error body `{ code, message, field_errors, correlation_id }` and the six codes are
the shared ones; `CellValue` and `columns.type` are F007's; `ActorContext` is F038's.

**`WorkflowDefinition`** — the shape F018 owns, F019 executes verbatim from the immutable
`workflow_versions.definition`, F054 extends with connector actions and F040 proposes edits to. It is
the `draft` on create and update, and the frozen body of a published version.

| Field | Type | Required | Constraint |
|---|---|---|---|
| 2026-09-04 | F054 action-name alignment | F054's `opshub_action` steps now name four of this ticket's twelve `ActionKind` members verbatim; adding a fifth is an amendment to both tickets | F054 carried its own spelling of two of these actions |
| `trigger` | Trigger | yes | exactly one, per the trigger table below |
| `condition` | ConditionNode? | no | absent or `null` means "always"; an empty group is `400 invalid` |
| `actions` | ActionSpec[] | yes | 1–25 entries, executed in array order (FR-F018-01); 0 or 26 → `400 invalid` with `field_errors.actions` |

**`Trigger`** — discriminated by `kind` (FR-F018-02). Any other `kind` is `400 invalid` with
`field_errors.trigger.kind`. A parameter listed for one kind and sent on another is `400 invalid`.

| `kind` | Parameters | Constraint |
|---|---|---|
| `row_created` | none | fires on `row.created.v1` for the workflow's `sheet_id` |
| `row_updated` | none | fires on `row.updated.v1` for that sheet |
| `field_changed` | `column_id` (uuid, required) | a live column of the sheet; recorded in `workflow_step_column_refs` with `usage = 'trigger'` at publish |
| `form_submitted` | `form_id` (uuid, required) | an F014 form bound to the same sheet |
| `schedule` | `cron` (string, required), `timezone` (string, required) | 5-field cron; two consecutive fire times at least 5 minutes apart, else `field_errors.trigger.cron`; `timezone` an IANA name |
| `date_reached` | `column_id` (uuid, required), `offset_minutes` (integer, required) | column type `date` or `datetime`; `offset_minutes` −43,200..43,200; recorded as a `trigger` column ref |
| `webhook_received` | none | the token and secret are F019's `inbound_webhooks` row, never part of the definition |
| `approval_decided` | `outcome` (`"approved" \| "rejected" \| "any"`, required) | matches F020's `approval.decided.v1` outcome |

**`ConditionNode`** — F018's own condition tree, not F013's `FilterNode`: its leaves are five typed
tests rather than one column predicate, and F019 evaluates it through this feature's exported
`evaluate_condition`. Discriminated by `kind`; every failure is `400 invalid` with
`field_errors.condition[<path>]` where `<path>` is the node's position, e.g. `all[0].any[2]`.

| `kind` | Fields | Constraint |
|---|---|---|
| `all`, `any` | `children` (ConditionNode[], required) | 1–20 children; an empty array is invalid; nesting depth ≤ 4 counting the root, whole tree ≤ 200 leaves |
| `compare` | `column_id` (uuid), `op` (ConditionOp), `value` (conditional) | `op` must be legal for that column's `columns.type` (F007); `value` required for every `op` except none — all ten operators take one; `in` takes an array of 1–100 scalars, `between` takes `{ from, to }` with `from <= to`, every other operator one scalar of the column's type |
| `changed` | `column_id` (uuid) | true only when the triggering event's `changed_fields` names that column; on a `schedule` or `webhook_received` trigger it is always false, not an error |
| `actor_in` | `user_ids` (uuid[]), `group_ids` (uuid[]) | at least one array non-empty, ≤ 100 entries each; matched against the triggering `ActorContext.actor_id` and its group memberships |
| `exists` | `column_id` (uuid) | true when the cell's `CellValue.raw` is non-null; `""` counts as present |
| `formula` | `expression` (string) | an F035 expression whose result type is boolean, parsed at save under F035's 10,000 AST node limit; a non-boolean result or a parse failure is `400 invalid`, and exceeding the 2-second budget is `field_errors.condition` per the error map |

`ConditionOp` is exactly `eq`, `ne`, `lt`, `lte`, `gt`, `gte`, `contains`, `starts_with`, `in`,
`between` (FR-F018-03). It is this feature's set and deliberately not F013's `FilterOp`: F013 owns
the view filter vocabulary and carries members F018 has no trigger for (`is_me`, `before`, `after`).
Every `column_id` in the tree is projected into `workflow_step_column_refs` with `usage = 'condition'`
at publish.

**`ActionSpec`**

| Field | Type | Required | Constraint |
|---|---|---|---|
| `kind` | ActionKind | yes | one of the twelve below; any other value → `400 invalid` with `field_errors.actions[<index>].kind` |
| `params` | object | yes | validated per `kind` by the table below; an unlisted key → `400 invalid` with `field_errors.actions[<index>].params` |
| `continue_on_error` | bool | no | default `false`; `true` makes F019 record the step `skipped_error` and continue (FR-F019-05) |

**Action `params` per `kind`** (FR-F018-04). Where a parameter set belongs to another feature this
names the owner rather than restating it. Every string value may carry the placeholders of
FR-F018-05 — `{{row.<column_id>}}`, `{{event.<field>}}`, `{{actor.<field>}}` — and an unknown column
id in any placeholder is `400 invalid` with `field_errors.actions[<index>].params`.

| `kind` | `params` | Constraint |
|---|---|---|
| `update_fields` | `{ cells: map<uuid, RawValue> }` | keys are live columns of the workflow's sheet; each value is F007's `RawValue` for that column type, the same unwrapped form F006 accepts on write; an unknown or foreign column → `invalid` |
| `create_row` | `{ sheet_id?, group_id?, after_row_id?, cells }` | F006's `CreateRowRequest` fields; `sheet_id` defaults to the workflow's sheet and must be readable by the publishing editor |
| `move_row` | `{ group_id?, after_row_id? }` | F006's `MoveRowRequest`; at least one present |
| `copy_row` | `{ target_sheet_id, group_id? }` | `target_sheet_id` a live sheet in the same workspace; the copy carries the cells of columns present on both sheets |
| `assign` | `{ column_id, user_ids }` | `column_id` must be a `person` column (F007), else `invalid`; 1–20 user ids of the tenant |
| `comment` | `{ body }` | F016's `CreateCommentRequest.body` rules — Markdown 1–10,000 chars, ≤ 50 mention tokens; the target is the triggering row |
| `request_approval` | `{ approvers, quorum, due_at?, policy_id?, context }` | F020's `CreateApprovalRequest` fields with the same limits; `target` is not carried here because F019 supplies the triggering row |
| `send_email`, `send_in_app`, `send_push` | `{ recipients, title, body, link? }` | F037's `NotificationRequest` fields (`title` 1–200, `body` 1–2,000, `link` a relative path starting `/`); the action `kind` selects the channel and `recipients` is 1–50 user or group references fanned out one notification per member |
| `call_webhook` | `{ url, method, headers?, body?, secret_ref }` | `url` must be `https` and resolve outside private address space, else `field_errors.actions[<index>].params.url`; `method` one of `POST`, `PUT`, `PATCH`; `headers` ≤ 20 entries; `secret_ref` an F029 vault reference — an inline secret in any field is `400 invalid` (NFR-F018-02) |
| `invoke_integration` | `{ connection_id, operation, payload? }` | `connection_id` an F029 `integration_connections` id and `operation` a name that connection's provider declares; until F029 ships only the reference format is validated, per section 7 |

**`CreateWorkflowRequest`** — `POST /api/v1/workflows`

| Field | Type | Required | Constraint |
|---|---|---|---|
| `name` | string | yes | 1–120 chars after trim, unique per `(tenant_id, sheet_id)` among live workflows, else `409 conflict` with `field_errors.name` |
| `sheet_id` | uuid | yes | a live sheet the caller holds `workflow-editor` on through its workspace, else `403 denied`; invisible → `404 not_found` |
| `trigger` | Trigger | yes | as above |
| `condition` | ConditionNode? | no | as above |
| `actions` | ActionSpec[] | yes | 1–25 |

**`UpdateWorkflowRequest`** — `PATCH /api/v1/workflows/{id}`, `If-Match` required, every field
optional and at least one present. `name` as above; `trigger`, `condition` and `actions` each replace
their part of the draft whole, never merged. Patching while `state` is `published` writes only the
draft and leaves `published_version_id` untouched (FR-F018-06); patching a `disabled` workflow is
`409 conflict`.

**`TestWorkflowRequest`** — `POST /api/v1/workflows/{id}/test`: exactly one of `row_id` (uuid, a live
row of the workflow's sheet the caller may read) or `sample_event` (object, the trigger payload shape
of the definition's `trigger.kind`, ≤ 64 KB). Both present or neither is `400 invalid`.

**`TestWorkflowResponse`**

| Field | Type | Notes |
|---|---|---|
| `trigger_matched` | bool | whether the input satisfies the trigger, evaluated without side effects |
| `condition_result` | bool | `true` when `condition` is absent; only meaningful when `trigger_matched` |
| `action_plan` | array of `{ index, kind, resolved_params }` | present only when `trigger_matched` and `condition_result` are both true; `resolved_params` is `params` with every placeholder substituted and every secret reference left unresolved |
| `evaluated_at` | timestamp | |

**`WorkflowResponse`**

| Field | Type | Notes |
|---|---|---|
| `id`, `workspace_id`, `sheet_id` | uuid | |
| `name` | string | |
| `state` | `"draft" \| "published" \| "disabled"` | |
| `draft` | WorkflowDefinition | the editable definition; always present |
| `published_version` | WorkflowVersionSummary? | `null` until the first publish; the pinned version F019 runs |
| `has_unpublished_changes` | bool | `true` when `draft` differs from `published_version.definition_hash` |
| `last_run_at` | timestamp? | supplied by F019 when that feature is enabled, otherwise absent (FR-F018-10) |
| `version` | integer | pass as `If-Match` on the next write |
| `created_at` / `updated_at` | timestamp | |
| `created_by` / `updated_by` | uuid | |
| `deleted_at` | timestamp? | present only when reading a soft-deleted workflow |

**`WorkflowVersionSummary`** `{ id, version_no, definition_hash (hex string), published_by, published_at }`.
`POST /publish` returns the full `WorkflowResponse` with the new summary; `POST /disable` returns it
with `state: "disabled"`; `DELETE` returns `204`.

**List route.** `GET /api/v1/workflows` returns `Page<WorkflowResponse>` in F028's envelope
`{ items, next_cursor, has_more, total? }`, sorted by `sort` = `name` or `updated_at` (default
`-updated_at`), `limit` 1–200 (F028's cap; this route documents none higher), and filters
`sheet_id` (uuid), `state` (the three members), `trigger_kind` (the eight members) and `deleted`
(bool, default `false`). A filter value outside its set is `400 invalid` with `field_errors.filter`.

**Status codes**

| Status | `code` | Produced by |
|---|---|---|
| `400` | `invalid` | any constraint above, an unlisted field, a formula leaf that fails to parse or exceeds its budget, an inline secret |
| `403` | `denied` | a caller who may read the sheet but lacks `workflow-editor` on its workspace, on every mutation and on `test` |
| `404` | `not_found` | unknown, foreign-tenant, or invisible workflow or sheet id, and every route on a soft-deleted workflow except F019's history reads (FR-F018-11) |
| `409` | `conflict` | stale `If-Match`, duplicate `name` in the sheet, `Idempotency-Key` replayed with a different body, `PATCH` on a `disabled` workflow, 101st published workflow on a sheet or 5,001st in a tenant with `field_errors.limit` (FR-F018-12) |
| `429` | `rate_limited` | the calling application's F028 token bucket is exhausted |
| `503` | `unavailable` | the outbox or F035 evaluator is unreachable; safe to retry |

### Use case signatures

In `crates/domain/src/workflows/`. Every one takes `ctx: &ActorContext` carrying tenant, actor and
correlation id, takes a `UnitOfWork` for writes or a repository trait for reads — never a pool or a
connection — and returns the shared `DomainError` whose HTTP mapping is the table above.

```rust
fn create_workflow(ctx: &ActorContext, uow: &mut UnitOfWork, req: CreateWorkflow) -> Result<Workflow, DomainError>;
fn update_workflow(ctx: &ActorContext, uow: &mut UnitOfWork, id: WorkflowId, expected: Version, req: UpdateWorkflow) -> Result<Workflow, DomainError>;
fn publish_workflow(ctx: &ActorContext, uow: &mut UnitOfWork, id: WorkflowId, expected: Version) -> Result<WorkflowVersion, DomainError>;
fn disable_workflow(ctx: &ActorContext, uow: &mut UnitOfWork, id: WorkflowId, expected: Version) -> Result<Workflow, DomainError>;
fn delete_workflow(ctx: &ActorContext, uow: &mut UnitOfWork, id: WorkflowId, expected: Version) -> Result<(), DomainError>;
fn get_workflow(ctx: &ActorContext, repo: &dyn WorkflowRepository, id: WorkflowId) -> Result<Workflow, DomainError>;
fn list_workflows(ctx: &ActorContext, repo: &dyn WorkflowRepository, filter: WorkflowFilter, page: Cursor) -> Result<Page<Workflow>, DomainError>;
fn test_workflow(ctx: &ActorContext, repo: &dyn WorkflowRepository, rows: &dyn RowRepository, id: WorkflowId, req: TestWorkflow) -> Result<TestOutcome, DomainError>;
fn validate_definition(ctx: &ActorContext, columns: &ColumnMetadata, def: &WorkflowDefinition) -> Result<ValidatedDefinition, FieldErrors>;
fn evaluate_condition(ctx: &ActorContext, node: &ConditionNode, scope: &RowScope) -> Result<bool, DomainError>;
fn resolve_placeholders(ctx: &ActorContext, params: &Json, scope: &RowScope) -> Result<Json, DomainError>;
```

**Transaction boundaries.** `publish_workflow` is one `UnitOfWork` covering the draft freeze, the
`workflow_versions` insert, its ordered `workflow_steps`, its `workflow_step_column_refs`, the
repoint of `workflows.published_version_id`, the audit row and the `workflow.published.v1` outbox
entry. That boundary is what makes a published version immutable *and* complete: F019 pins
`workflow_version_id` and replays the steps, so a version whose steps or column refs committed
separately could be executed with half its actions, and the `on delete restrict` guard F007 relies on
would be missing for a column the definition already names. `create_workflow`, `update_workflow`,
`disable_workflow` and `delete_workflow` each take one `UnitOfWork` covering the row write under the
expected version, the audit row and the outbox entry. `validate_definition`, `evaluate_condition`,
`resolve_placeholders` and `test_workflow` write nothing and open no transaction.

### PostgreSQL/SQLx

- Migration `*_workflows_*.sql` creates `workflows(id uuid pk, tenant_id uuid not null, workspace_id uuid not null, sheet_id uuid not null, name text not null, state text not null check (state in ('draft','published','disabled')), draft jsonb not null, published_version_id uuid null, version bigint not null default 1, created_by, created_at, updated_by, updated_at, deleted_at)`, `workflow_versions(id uuid pk, tenant_id, workflow_id not null, version_no int not null, definition jsonb not null, definition_hash bytea not null, published_by uuid, published_at timestamptz)`, `workflow_steps(id uuid pk, tenant_id, version_id not null, index int not null, kind text not null, params jsonb not null, continue_on_error bool not null default false)`.
- `jsonb` audit against decision section 2 — three payload columns are kept and every queried reference inside them is projected out: `workflow_versions.definition` is the immutable published definition, a user-authored graph of trigger, condition and actions that is hashed by `definition_hash` and replayed verbatim by F019, read and written whole and never filtered by key in SQL, because the queried projection is `workflow_steps` plus `workflow_step_column_refs` written in the same publish transaction; `workflows.draft` is the editor's working document, loaded and stored whole by `PATCH` and never queried by key; `workflow_steps.params` holds per-`kind` action parameters whose shape the action adapter defines and the in-memory registry validates, never read by key in SQL. There are no array columns.
- Migration also creates `workflow_step_column_refs(version_id uuid not null references workflow_versions(id) on delete cascade, tenant_id uuid not null, step_id uuid null references workflow_steps(id) on delete cascade, column_id uuid not null references columns(id) on delete restrict, usage text not null check (usage in ('trigger','condition','action')), created_at timestamptz not null default now(), primary key (version_id, column_id, usage))`: the F007 column IDs a published version names — `field_changed`/`date_reached` trigger columns (FR-F018-02), `compare`/`changed`/`exists` condition leaves (FR-F018-03), and `{{row.<column_id>}}` placeholders in action params (FR-F018-05) — with `step_id` set for action refs and null for trigger and condition refs. This preserves both behaviours the ticket already promised without a JSON scan: "which workflows use this column" is a b-tree lookup on `(column_id)` joined back to `workflow_versions`, and F007's column-delete guard becomes declarative through `on delete restrict`, which still surfaces to the caller as the same `conflict` on the F007 delete route rather than a new error.
- Invariants: unique `workflow_versions(workflow_id, version_no)`; unique `workflow_steps(version_id, index)`; `workflow_versions` rows have no `updated_at` and a trigger `workflow_versions_immutable` raises on `UPDATE` or `DELETE`; unique `workflows(tenant_id, sheet_id, lower(name)) where deleted_at is null`; `published_version_id` references `workflow_versions(id)`; `workflow_step_column_refs` is unique on `(version_id, column_id, usage)` by its primary key, is written only inside the publish transaction, and is covered by the same immutability rule because its parent version cannot be updated.
- Indexes: `workflows(tenant_id, sheet_id, state) where deleted_at is null`, `workflows(tenant_id, updated_at desc)`, `workflow_versions(workflow_id, version_no desc)`, `workflow_steps(version_id, index)`, `workflow_step_column_refs(column_id)`.
- Audit events: `workflow.create`, `workflow.update`, `workflow.publish`, `workflow.disable`, `workflow.delete`, `workflow.test` with definition diffs and `version_no`.
- Retention/deletion: soft delete sets `deleted_at` on `workflows`; versions are retained while any `workflow_runs` row (F019) references them and purged by the F027 job otherwise; purging a version cascades its `workflow_steps` and `workflow_step_column_refs` rows; rollback drops `workflow_step_column_refs`, `workflow_steps`, `workflow_versions`, and `workflows`.

### React/TypeScript

- Routes in `apps/web/src/features/workflows/`: `/w/:workspaceId/sheets/:sheetId/workflows`, `/workflows/new`, `/workflows/:workflowId`; components `WorkflowListPage`, `WorkflowBuilderPage`, `TriggerStep`, `ConditionTree`, `ConditionLeafEditor`, `ActionList`, `ActionEditor`, `PlaceholderPicker`, `TestPanel`, `PublishDialog`, `DisableDialog`.
- State: TanStack Query keys `['workflows', sheetId, cursor]`, `['workflow', workflowId]`, `['workflow-test', workflowId, rowId]`; mutations invalidate by key and update cached `version`.
- API client: generated `WorkflowsApi` with `listWorkflows`, `createWorkflow`, `getWorkflow`, `updateWorkflow`, `publishWorkflow`, `disableWorkflow`, `testWorkflow`, `deleteWorkflow`.
- Client validation mirrors `validate_definition` through a shared JSON schema exported from `crates/contracts`; server errors are mapped onto the same field paths.
- Telemetry: `workflow_created`, `workflow_tested`, `workflow_published`, `workflow_disabled`, `workflow_action_added` with `workflow_id`, `trigger_kind`, and `action_kind`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F018-01 through FR-F018-14 in `testing/features/F018/requirements/cases.md`
- [ ] Failure/edge-case tests: operator/type mismatch, cron under 5 minutes, condition depth 5, 26 actions, inline webhook secret, unknown placeholder, publish with errors, edit after publish, limit 101 per sheet
- [ ] Permission-negative and tenant-isolation tests: viewer publish returns `denied`, foreign tenant returns `not_found`, formula leaf cannot read a hidden sheet
- [ ] Rust unit tests: `crates/domain/src/workflows/` trigger parsing, condition evaluation table, placeholder resolution, definition hash stability
- [ ] Persistence tests: `crates/persistence/src/workflows/` publish `UnitOfWork` writes version, steps and column refs atomically; `list_workflows_using_column` returns the referencing workflows; `check-persistence` finds no SQL in domain or API
- [ ] API contract/integration tests: every route above with success and each error code
- [ ] Database migration/constraint tests: immutable version trigger, unique version number, unique name, column-ref primary key and `on delete restrict` guard, rollback
- [ ] React component tests: `TriggerStep`, `ConditionTree`, `ActionEditor`, `TestPanel`, `WorkflowBuilderPage` states
- [ ] Browser E2E tests: create, test, publish, edit after publish, disable, viewer read-only
- [ ] Accessibility tests: axe on list and builder, keyboard reorder, tree levels announced
- [ ] Performance/load tests: validation p95 under 200 ms, test p95 under 2 s, list with 5,000 workflows

### Fast fanout configuration

- Test harness path: `testing/features/F018/`
- Feature flag: `F018_FEATURE`
- Fixture/seed factory: `testing/fixtures/workflows.rs` builds tenant, workspace, sheet with typed columns `Status` (select), `Owner` (person), `Due` (date), `Amount` (number), editor, viewer, foreign tenant, and 6 sample workflows (one per common trigger)
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, timezone `UTC`
- Mock/stub contracts: outbox recorded in memory; F035 evaluator real; F029 vault stubbed with fixed secret references; no run execution
- Parallel isolation: one schema per test worker, tenant ID per test
- Targeted command: `cargo xtask test-feature F018`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F018/`

## 6. Acceptance criteria

```gherkin
Feature: Workflow builder

Scenario: Publish a field-changed workflow
  Given a workflow editor on sheet "Requests" with a select column "Status"
  When they create a workflow triggered by "Status" changing with condition Status eq "Approved" and actions Assign and Send in-app
  And they publish it
  Then the workflow is published at version_no 1 with an immutable definition
  And the "Status" column is recorded in workflow_step_column_refs with usage trigger and condition
  And workflow.published.v1 is in the outbox

Scenario: Editing a published workflow does not change the published version
  Given workflow "Route approvals" published at version_no 1
  When the editor patches the draft to add a third action
  Then version_no 1 is unchanged and the workflow shows an unpublished draft

Scenario: Type mismatch is rejected
  Given a number column "Amount"
  When the editor adds condition Amount starts_with "1"
  Then the response is 400 invalid with field_errors.condition pointing at the leaf

Scenario: Viewer cannot publish
  Given a viewer on sheet "Requests"
  When they call publish on a draft workflow
  Then the response is 403 denied and the state stays draft

Scenario: Dry run does not execute actions
  Given a published workflow with a Send email action
  When the editor tests it against row "Kickoff"
  Then the response lists the resolved action plan and no email is queued
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F007 (typed columns for operator validation, and `columns(id)` as the parent of `workflow_step_column_refs`), F035 (formula leaves); decisions sections 2–4, 6; contracts row F018
- Blocks: F019, F040
- Conflicts with: none (disjoint owned paths)
- External dependencies: none; F029 vault references are optional until F029 ships (validation accepts the reference format only)
- Risks and mitigations: condition semantics could drift between builder and runtime, so `evaluate_condition` lives in `crates/domain/src/workflows/` and is the only implementation used by F019; formula leaves could be slow, so the 2-second budget is enforced per evaluation and surfaced as `invalid` at publish time.
- Open questions: none

## 7.1 Amendments

Every change made to this ticket after it was first accepted, newest first.

| Date | Caused by | What changed | Why |
|---|---|---|---|
| 2026-09-04 | Filter vocabulary unification (F013) | Subset of `docs/filter-vocabulary.md` declared in section 4 and the operator names aligned to it | `ConditionOp` is now a declared subset; `exists` and `actor_in` stay separate leaf kinds rather than becoming operators |

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F007 and F035 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F018/`
- [ ] Migration file name and owned paths claimed
- [ ] Fixture factory `testing/fixtures/workflows.rs` and schema-per-worker isolation available

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for every mutation
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F018_FEATURE`, run down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Users can build, test, publish, and disable trigger-condition-action workflows on a sheet; every published version is immutable.
- Migration adds `workflows`, `workflow_versions`, `workflow_steps`, and `workflow_step_column_refs`; rollback drops them. Feature is off by default behind `F018_FEATURE`.
