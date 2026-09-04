---
id: F032
type: feature
status: planned
priority: P1
owner: platform
estimate: 13
target_milestone: M6
parent_epic: E007
depends_on: [F031, F020]
blocks: []
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/governance/**, crates/persistence/src/governance/**, services/api/src/governance/**, services/worker/src/governance/**, apps/web/src/features/governance/**, services/api/migrations/*_governance_*.sql, testing/features/F032/**]
feature_flag: F032_FEATURE
flag_default: off
branch: f032-project-health-governance
started_at: null
finished_at: null
---

# F032 — Project health/governance

## 1. Identity and dates

- Branch: `f032-project-health-governance`
- Capability area: project governance (spec 5.7 PPM-01 governance checkpoints, PPM-04; low-level bullets "Health is configurable from weighted indicators (schedule, budget, scope, risk, resource) with manual override and reason" and "Stage gates require defined evidence, decision, approver, date, and audit event"; 5.11 Control Center intake and stage gates absorbed here)
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 7, 9; `docs/capability-contracts.md` row F032
- Aggregate: `project-governance`
- Module slug: `governance`

## 2. Requirement specification

### Problem and user outcome

A PMO cannot trust a health colour that a project manager picks by hand, and cannot prove that a phase was approved with evidence. They need health computed from weighted schedule, budget, scope, risk, and resource indicators against a model they control, an override that always records who and why, stage gates that cannot advance without defined evidence and an approver's dated decision, and a governed intake path that provisions projects only after approval.

As a portfolio administrator, I want computed project health with auditable overrides, evidence-backed stage gates, and approved intake, so that portfolio reviews rest on consistent, explainable, and enforceable governance.

### Functional requirements

- **FR-F032-01:** `PUT /api/v1/health-models/{id}` upserts a health model with `name`, `scope` (`tenant_default` or `template_version:{id}`), integer `weights` for `schedule`, `budget`, `scope`, `risk`, and `resource` that sum to exactly 100, `thresholds { green_min, amber_min }` with `100 ≥ green_min > amber_min ≥ 0`, and per-indicator `rules`; the request and response keep the `weights`, `thresholds`, and `rules` objects and the `scope` string, while the server stores one `health_model_weights` row per indicator, one `health_model_thresholds` row per colour band, one `health_model_rules` row per `(indicator, parameter)`, one `health_model_risk_points` row per risk severity, and `scope` as `scope_kind` plus `template_version_id`; a weight sum other than 100 returns `invalid` with `field_errors.weights`, and updates require `If-Match`.
- **FR-F032-02:** Indicator scores are 0–100 computed by rule from `health_model_rules` rows: `schedule` from baseline `variance_days` (0 days → 100, `late_days_for_zero` default 30 → 0, linear), `budget` from `variance_pct` (0 → 100, `over_pct_for_zero` default 25 → 0), `scope` from percent of rows added since the named baseline (`creep_pct_for_zero` default 20), `risk` from open risk rows weighted by the `health_model_risk_points` rows (`high` 3, `medium` 2, `low` 1 by default) against `risk_points_for_zero` default 12, and `resource` from open F034 workload conflicts on the project's allocations (`conflicts_for_zero` default 5). A model missing a rule row falls back to the default for that parameter and the API still renders the full `rules` object.
- **FR-F032-03:** Project health `score` is the weighted mean of available indicators, using the `health_model_weights` rows renormalized over indicators whose state is `ok`; `colour` is `green` when `score ≥` the `green` threshold row, `amber` when `≥` the `amber` row, else `red`; `confidence` equals the sum of the weight rows of available indicators; when no indicator is available the colour is `unknown`.
- **FR-F032-04:** The worker recomputes a project's health within 60 seconds of `row.updated.v1`, `baseline.captured.v1`, `allocation.*.v1`, or `workload-conflict.detected.v1` for that project (debounced per project) and nightly at 02:00 tenant time, replaces the `project_health` row together with its five `project_health_indicators` rows and their `project_health_indicator_inputs` rows in one transaction, and publishes `project-health.computed.v1` with `changed_fields` naming indicators whose score moved.
- **FR-F032-05:** `GET /api/v1/projects/{id}/health` returns `computed { score, colour, confidence, indicators[{ name, score, state, inputs }] , computed_at, model_id }`, `override { colour, reason, set_by, set_at, expires_at } | null`, and `effective_colour`; the `indicators` array is assembled from `project_health_indicators` in `display_order` with `inputs` assembled from `project_health_indicator_inputs`, and `override` from the `project_health_overrides` row, so the response shape is unchanged; an actor without read access to the project sheet receives `not_found`.
- **FR-F032-06:** `PUT /api/v1/projects/{id}/health-override` by a `portfolio-admin` writes a `project_health_overrides` row with `colour` in {`green`, `amber`, `red`}, `reason` of 10–1,000 characters, and optional `expires_at` in the future, or clears the override with `colour: null` and a reason, which deletes the row after the audit write; a missing or short reason returns `invalid` with `field_errors.reason`; every change writes an audit event and publishes `health-override.set.v1`; an override row past `expires_at` is ignored by `effective_colour` and reported as `expired: true`.
- **FR-F032-07:** Stage gates are created for a project when the worker consumes `project.provisioned.v1` and reads `governance.gates` from the F015 template version: each gate is a `stage_gates` row with `name`, `sequence`, and exactly one of `approver_group_id` or `approver_user_id`, plus one `stage_gate_requirements` row per required item carrying `position`, `kind` in {`file`, `approval`, `checklist`, `field`}, `label`, and `column_id` for `field`, and one `stage_gate_requirement_items` row per checklist item in its authored order; `GET /api/v1/projects/{id}/stage-gates` lists gates in sequence with `required_evidence[]` rebuilt from those rows in `position` order, `status` in {`pending`, `submitted`, `approved`, `rejected`, `deferred`}, `attempt`, and the latest decision.
- **FR-F032-08:** `POST /api/v1/stage-gates/{id}/submit` by a `sheet-editor` on the project accepts `evidence[]` indexed by the requirement `position` (a `file_id` from F017, an `approval_id` from F020, a checklist of completed items, or a field value read from the project sheet) and `note`, and writes one `stage_gate_evidence` row per requirement for the new `attempt` plus one `stage_gate_evidence_checklist` row per ticked checklist item; any requirement with no matching evidence row returns `invalid` with `field_errors.evidence[i]` where `i` is that requirement's `position`; submitting gate N while gate N-1 is not `approved` returns `conflict` with `code_detail: gate_sequence`; success sets `submitted`, increments `attempt`, creates an F020 approval for the approver set, and publishes `stage-gate.submitted.v1`.
- **FR-F032-09:** `POST /api/v1/stage-gates/{id}/decide` by a member of the approver set or a `portfolio-admin` records `decision` in {`approved`, `rejected`, `deferred`}, `reason` (required, ≥ 10 chars, for `rejected` and `deferred`), the server `decided_at`, and the approver ID in `stage_gate_decisions`, and copies the attempt's evidence into insert-only `stage_gate_decision_evidence` rows (kind, label, file ID and SHA-256, approval ID, column ID and value, checklist completed and required counts) that form the immutable evidence snapshot and are still returned as the `evidence_snapshot` array; deciding a gate not in `submitted` returns `conflict`; `rejected` returns the gate to `pending` for resubmission, `deferred` sets `deferred_until`; every decision writes an audit event and publishes `stage-gate.decided.v1`.
- **FR-F032-10:** When the F020 approval linked to a submitted gate is decided, the worker consumes `approval.decided.v1` and applies the same decision through the decide use case with the approval's approver as the actor, so a gate never has two divergent outcomes.
- **FR-F032-11:** `POST /api/v1/project-intake` by a `sheet-editor` in the target workspace accepts `template_id`, `name` (1–200), `workspace_id`, `sponsor_user_id`, `justification` (≤ 4,000), `requested_start`, optional `requested_finish`, `budget_planned` with `currency`, `value_estimate`, and optional `portfolio_id`; it stores a `project_intake_requests` row with status `submitted` in which every intake field is a typed column with its own foreign key (`template_id`, `workspace_id`, `sponsor_user_id`, `portfolio_id`) rather than a form payload, opens an F020 approval using approval policy key `project_intake`, and publishes `project-intake.submitted.v1`.
- **FR-F032-12:** When the intake approval is approved the worker provisions the project through the F015 provision use case, records `provisioning_run_id` and `project_sheet_id`, moves status through `provisioning` to `provisioned`, and adds the project to `portfolio_id` when given; a rejected approval sets `rejected` with the reason; a provisioning failure sets `failed` with `error`; `GET /api/v1/project-intake/{id}` returns the request, status, `approval_id`, `decision`, `reason`, and the provisioning references.
- **FR-F032-13:** Every mutation requires `Idempotency-Key` and writes an `audit_events` row with actor, action, and before/after diff; cross-tenant access to any health model, gate, or intake request by ID returns `not_found`; a `sheet-viewer` receives `denied` on submit, decide, override, and model routes.
- **FR-F032-14:** The web governance page shows the health card (effective colour, score, confidence, indicator breakdown, override banner with reason and author), the stage gate timeline with evidence checklist, submit and decide dialogs, and the intake form and status page; every colour is paired with a text label.

### Non-functional requirements

- **NFR-F032-01 Performance:** `GET /health` and `GET /stage-gates` respond in under 500 ms p95; submit, decide, override, and intake writes respond in under 800 ms p95; health recompute for one project completes in under 5 seconds and for 1,000 projects in the nightly run in under 20 minutes (spec section 6).
- **NFR-F032-02 Security/privacy:** health inputs are read as the tenant system actor but responses are gated by the caller's project read access; `stage_gate_decision_evidence` rows store IDs and hashes, never file bodies; override reasons and decision reasons are redacted from logs; cross-tenant, viewer, and non-approver negatives are in the harness.
- **NFR-F032-03 Accessibility:** health colours carry text labels and icons; the gate timeline is an ordered list with status announced; dialogs trap focus; axe reports no serious violations; all actions keyboard reachable.
- **NFR-F032-04 Reliability/observability:** recompute jobs are idempotent by `(project_sheet_id, source_version)`, retried 3 times, dead-lettered with `project_health.last_error`; approval-decision consumers are idempotent by `approval_id`; spans carry `tenant_id`, `project_sheet_id`, `gate_id`, `intake_id`, `correlation_id`; metrics `project_health_recompute_ms` and `stage_gate_decision_latency_ms` are exported.

### Scope

Included: health models, indicator scoring, weighted health with confidence, manual override with reason and expiry, health recompute worker, stage gate creation from templates, evidence submission, decision recording with audit, approval synchronization, governed intake with provisioning, governance web pages.

Excluded: portfolio rollup storage (F031 consumes `project_health`), approval routing and escalation (F020), template authoring and provisioning internals (F015), allocation conflict detection (F034 publishes it), notifications (F037 consumes events), Control Center entitlement packaging (F048).

## 3. UX specification

- Entry points: project sheet header tab `Governance` → route `/w/{workspace_id}/projects/{project_sheet_id}/governance` with `?tab=health|gates`; workspace sidebar `Intake` → `/w/{workspace_id}/intake/new` and `/w/{workspace_id}/intake/{intake_id}`; settings `Health models` → `/w/{workspace_id}/settings/health-models/{model_id}`.
- Primary flow: administrator opens `Governance`, sees health card `Amber 58 (confidence 80)` with indicator bars, clicks `Override`, picks `Red`, types reason, saves; banner shows `Overridden to Red by {name}: {reason}`; switches to `Gates`, opens `Gate 2 Design review`, completes the evidence checklist (attach file, tick items), clicks `Submit`; approver receives the approval, opens the gate, clicks `Approve`, sees the timeline mark approved with date and approver. A requester fills the intake form, submits, and watches the status page move from `Submitted` to `Provisioned` with a link to the new project.
- Loading: skeleton card and timeline; Empty: `No gates defined by this template`; Error: banner with `correlation_id`; Success: toasts for override, submit, decide, intake; Stale: `Health computed {time} ago` with `Recompute pending` when a job is queued; Conflict: `Gate 1 must be approved first` inline; Denied: submit/decide/override hidden; Expired override: grey banner `Override expired`.
- Permission-denied: viewers see read-only health and gates; non-approvers see the decision as pending without `Approve`/`Reject`; non-members get not-found.
- Responsive: health indicators stack vertically under 640 px; gate timeline becomes a vertical list.
- Keyboard: tab through indicator rows, `Enter` opens override dialog, gate timeline items are buttons, dialogs trap focus and `Escape` cancels; `prefers-reduced-motion` disables the score animation.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062), Lucide icons `HeartPulse`, `ShieldCheck`, `Flag`, `FileCheck`, `Inbox`, `AlertOctagon`; tokens from `apps/web/src/design/tokens.css`.

- Design: `design/artboards/Intake.dc.html` on the canvas indexed by `design/canvas.json`. The ticket is the contract and the artboard is the picture; when they disagree the ticket wins.

## 4. Technical specification

### Rust backend

- Data access (decision section 2.1): `crates/persistence/src/governance/{mod.rs, health_model_repository.rs, project_health_repository.rs, stage_gate_repository.rs, decision_repository.rs, intake_repository.rs}` holds every SQL statement in this module. `HealthModelRepository` owns `health_models`, `health_model_weights`, `health_model_thresholds`, `health_model_rules`, `health_model_risk_points`; `ProjectHealthRepository` owns `project_health`, `project_health_indicators`, `project_health_indicator_inputs`, `project_health_overrides`; `StageGateRepository` owns `stage_gates`, `stage_gate_requirements`, `stage_gate_requirement_items`, `stage_gate_evidence`, `stage_gate_evidence_checklist`; `StageGateDecisionRepository` owns `stage_gate_decisions`, `stage_gate_decision_evidence`; `IntakeRequestRepository` owns `project_intake_requests`. No table is written by two classes. Named queries beyond the shared `Repository` contract: `find_effective_model_for_project`, `load_model_definition`, `replace_weights`, `replace_thresholds`, `replace_rules`, `replace_risk_points`, `get_health_with_indicators`, `upsert_computed_health`, `replace_indicator_results`, `set_override`, `clear_override`, `list_projects_due_for_recompute`, `record_recompute_error`, `list_gates_for_project`, `find_gate_with_requirements`, `previous_gate_status`, `create_gates_from_template`, `insert_attempt_evidence`, `mark_submitted`, `find_gate_by_approval_id`, `append_decision_with_evidence`, `latest_decision_per_gate`, `find_decision_by_gate_attempt`, `insert_intake_request`, `get_intake_request`, `advance_intake_status`, `find_intake_by_approval_id`, `list_intakes_awaiting_provisioning`; no generic query escape hatch is exposed. The use cases below, the `services/api/src/governance/` handlers, all four worker consumers including `health_recompute.rs`, and the harness fixtures depend on these traits and contain no `sqlx::query*` call. `compute_project_health` writes the health row, its indicator and input rows, and the outbox record in one `UnitOfWork`; `submit_stage_gate` (gate row, evidence and checklist rows, F020 approval), `decide_stage_gate` (gate row, decision row, snapshot rows), `create_gates_from_template` (gate, requirement, and item rows), and `advance_intake` (intake row, F015 provisioning run, F031 `replace_projects`) each run in one `UnitOfWork` shared with the dependent features' repositories.
- Domain entities in `crates/domain/src/governance/`: `HealthModel { id, tenant_id, name, scope: ModelScope, weights: Weights, thresholds: Thresholds, rules: IndicatorRules, risk_points: RiskPoints, version, audit fields }`, `ProjectHealth { project_sheet_id, tenant_id, model_id, score: Option<u8>, colour: HealthColour, confidence: u8, indicators: Vec<IndicatorResult>, computed_at, source_version, override_: Option<HealthOverride>, last_error, version }`, `HealthOverride { colour, reason, set_by, set_at, expires_at }`, `StageGate { id, tenant_id, project_sheet_id, name, sequence, required_evidence: Vec<EvidenceRequirement>, approver: ApproverRef, status: GateStatus, attempt, approval_id, deferred_until, version }`, `StageGateDecision { id, gate_id, attempt, decision, approver_id, reason, decided_at, evidence_snapshot: Vec<EvidenceSnapshotEntry> }`, `IntakeRequest { id, tenant_id, workspace_id, template_id, name, sponsor_user_id, justification, requested_start, requested_finish, budget_planned, currency, value_estimate, portfolio_id, status: IntakeStatus, approval_id, provisioning_run_id, project_sheet_id, decision, reason, error, version }`.
- Use cases: `upsert_health_model`, `score_indicators`, `compute_project_health`, `get_project_health`, `set_health_override`, `list_stage_gates`, `create_gates_from_template`, `submit_stage_gate`, `decide_stage_gate`, `apply_approval_decision`, `submit_intake`, `get_intake`, `advance_intake`.
- API endpoints (`services/api/src/governance/`): `GET /api/v1/projects/{id}/health`, `PUT /api/v1/projects/{id}/health-override`, `PUT /api/v1/health-models/{id}`, `GET /api/v1/projects/{id}/stage-gates`, `POST /api/v1/stage-gates/{id}/submit`, `POST /api/v1/stage-gates/{id}/decide`, `POST /api/v1/project-intake`, `GET /api/v1/project-intake/{id}`. DTOs: `UpsertHealthModelRequest`, `HealthOverrideRequest`, `ProjectHealthResponse`, `StageGateResponse`, `SubmitGateRequest { evidence, note }`, `DecideGateRequest { decision, reason }`, `IntakeRequestBody`, `IntakeResponse`.
- Worker (`services/worker/src/governance/`): `health_recompute.rs` (debounced consumer and nightly schedule), `gate_provisioning.rs` (consumes `project.provisioned.v1`), `approval_sync.rs` (consumes `approval.decided.v1` for gates and intake), `intake_provisioning.rs` (calls F015 provision and F031 `replace_projects`).
- Events: `project-health.computed.v1`, `health-override.set.v1`, `stage-gate.submitted.v1`, `stage-gate.decided.v1`, `project-intake.submitted.v1`; payload per contract conventions with `changed_fields`.
- Authorization: `portfolio-admin` for health models, overrides, and decisions; approver-set membership also permits decide; `sheet-editor` on the project for submit and in the workspace for intake; `sheet-viewer` on the project for reads; explicit deny wins; missing access maps to `not_found`.
- Validation: weights sum 100, thresholds ordered, reason 10–1,000 chars, justification ≤ 4,000, evidence count equals required count, `expires_at` in the future, `decision` enum. Idempotency via `idempotency_keys` for 24 hours. Concurrency: `If-Match` on model and override.
- Error mapping: `GovernanceError::WeightsNotHundred → 400 invalid`, `GovernanceError::MissingEvidence(i) → 400 invalid`, `GovernanceError::GateSequence → 409 conflict`, `GovernanceError::GateNotSubmitted → 409 conflict`, `GovernanceError::StaleVersion → 409 conflict`, `GovernanceError::NotFound → 404 not_found`, `AuthzError::Denied → 403 denied`.

### Interface

Ids are UUIDv7 strings, timestamps RFC 3339 UTC, dates `YYYY-MM-DD`, `version` an integer incrementing
by one per write. `T?` is nullable and an absent optional field equals an explicit `null`. Unlisted
fields are rejected with `400 invalid`. The error body is F028's. Mutations require `Idempotency-Key`;
`PUT /api/v1/health-models/{id}` and `PUT /api/v1/projects/{id}/health-override` require
`If-Match: <version>`. Projects are addressed by their sheet id throughout, so `{id}` on the project
routes is a `sheet_id`.

**`Indicator`** is the closed set `schedule | budget | scope | risk | resource`; **`HealthColour`** is
`green | amber | red | unknown`, and `unknown` is computed-only — a client may never send it.

**`UpsertHealthModelRequest`** — `PUT /api/v1/health-models/{id}`, a whole replacement

| Field | Type | Required | Constraint |
|---|---|---|---|
| `name` | string | yes | 1–200 chars after trim |
| `scope` | string | yes | `"tenant_default"` or `"template_version:{uuid}"`; stored as `scope_kind` plus `template_version_id`. A second `tenant_default` model in a tenant, or a second model for one template version, is `409 conflict` with `field_errors.scope = "taken"` |
| `weights` | map<Indicator, integer> | yes | all five keys, each `0..=100`, summing to exactly 100, else `400 invalid` with `field_errors.weights = "sum"` |
| `thresholds` | `{ green_min: integer, amber_min: integer }` | yes | `100 >= green_min > amber_min >= 0`, else `field_errors.thresholds = "order"` |
| `rules` | map<Indicator, map<string, decimal>> | no | inner keys are the parameters that indicator takes; each value `> 0`. An unknown indicator or parameter is `400 invalid` naming `field_errors["rules.<indicator>.<parameter>"]`. An omitted parameter falls back to its default and is still returned |
| `risk_points` | `{ high: integer, medium: integer, low: integer }` | no | each `> 0`; defaults `3`, `2`, `1` |

The parameter each indicator takes, with its default: `schedule` → `late_days_for_zero` (30);
`budget` → `over_pct_for_zero` (25); `scope` → `creep_pct_for_zero` (20); `risk` →
`risk_points_for_zero` (12); `resource` → `conflicts_for_zero` (5). Each scores 100 at zero and 0 at
the parameter's value, linearly, clamped to `0..=100`.

**`HealthModelResponse`** is the request plus `{ id, version, created_at, created_by, updated_at, updated_by, deleted_at? }`, with `rules` and `risk_points` fully materialised from the stored rows and the defaults.

**`ProjectHealthResponse`** — `GET /api/v1/projects/{id}/health`

| Field | Type | Notes |
|---|---|---|
| `computed` | ComputedHealth? | null before the first recompute |
| `override` | HealthOverride? | null when no `project_health_overrides` row exists |
| `effective_colour` | HealthColour | the override's colour when an override exists and is not expired, else `computed.colour`, else `unknown` |

**`ComputedHealth`**: `{ score: integer?, colour: HealthColour, confidence: integer, indicators: IndicatorResult[], computed_at: timestamp, model_id: uuid, source_version: integer, last_error: string? }`. `score` is null exactly when `colour` is `unknown`; `confidence` is the summed weight of indicators whose `state` is `ok`, `0..=100`.

**`IndicatorResult`**: `{ name: Indicator, score: integer?, state: "ok"|"missing", weight_applied: integer, inputs: map<string, decimal> }`, ordered by the stored `display_order` (1–5) so the card's bars never reorder between reads. `inputs` keys are the indicator's own input names — `variance_days`, `variance_pct`, `creep_pct`, `risk_points`, `open_conflicts` — and are absent when `state` is `missing`.

**`HealthOverride`**: `{ colour: "green"|"amber"|"red", reason: string, set_by: uuid, set_at: timestamp, expires_at: timestamp?, expired: bool }`. `expired` is computed on read; an expired override is returned and ignored by `effective_colour`, because hiding it would leave the reader unable to explain a colour change.

**`HealthOverrideRequest`** — `PUT /api/v1/projects/{id}/health-override`

| Field | Type | Required | Constraint |
|---|---|---|---|
| `colour` | `"green"\|"amber"\|"red"`? | yes | explicit `null` clears the override, deleting the row after the audit write |
| `reason` | string | yes | 10–1,000 chars, **also required when clearing**, else `400 invalid` with `field_errors.reason = "required"` |
| `expires_at` | timestamp? | no | strictly in the future, rejected when `colour` is null |

**`StageGateResponse`** — the item of `GET /api/v1/projects/{id}/stage-gates`, a plain array in
`sequence` order rather than a `Page<T>`: a project's gates are a short authored list, not a feed.

| Field | Type | Notes |
|---|---|---|
| `id`, `project_sheet_id`, `name`, `sequence` | | `sequence` starts at 1 |
| `approver` | `{ kind: "group"\|"user", id: uuid }` | exactly one of the two stored columns |
| `required_evidence` | EvidenceRequirement[] | in `position` order |
| `status` | `pending\|submitted\|approved\|rejected\|deferred` | |
| `attempt` | integer | 0 before the first submission |
| `approval_id` | uuid? | the F020 approval opened by the current submission |
| `deferred_until` | timestamp? | set only by a `deferred` decision |
| `latest_decision` | DecisionSummary? | null until a decision exists |
| `version` | integer | |

**`EvidenceRequirement`**: `{ position: integer, kind: "file"|"approval"|"checklist"|"field", label: string, column_id: uuid? (present exactly when kind is field), items: [{ position, label }]? (present exactly when kind is checklist) }`.

**`SubmitGateRequest`** — `POST /api/v1/stage-gates/{id}/submit`

| Field | Type | Required | Constraint |
|---|---|---|---|
| `evidence` | EvidenceEntry[] | yes | exactly one entry per `required_evidence` entry, matched by `position`; a missing one is `400 invalid` with `field_errors.evidence[i]` where `i` is that requirement's `position`, and an entry for an unknown position is `"unknown_position"` |
| `note` | string? | no | ≤ 2,000 chars |

**`EvidenceEntry`**: `{ position: integer }` plus exactly the payload its requirement's `kind` demands
— `file_id: uuid` (an F017 file the caller may read), `approval_id: uuid` (a decided F020 approval),
`completed_item_positions: integer[]` (a distinct subset of that requirement's item positions), or
`field_value: string` (read from the project sheet's `column_id`). A payload that does not match the
requirement's kind is `400 invalid` with `field_errors.evidence[i] = "kind_mismatch"`.

Submitting gate N while gate N−1 is not `approved` is `409 conflict` with
`details.code_detail = "gate_sequence"`. Submitting a gate already in `submitted` is `409 conflict`
with `"already_submitted"`.

**`DecideGateRequest`** — `POST /api/v1/stage-gates/{id}/decide`

| Field | Type | Required | Constraint |
|---|---|---|---|
| `decision` | `approved\|rejected\|deferred` | yes | |
| `reason` | string? | conditional | required and ≥ 10 chars for `rejected` and `deferred`, ≤ 1,000; optional for `approved` |
| `deferred_until` | timestamp? | conditional | required for `deferred`, strictly in the future, rejected otherwise |

Deciding a gate not in `submitted` is `409 conflict` with `details.code_detail = "gate_not_submitted"`.

**`DecisionSummary`**: `{ id, attempt, decision, approver_id, reason?, decided_at, evidence_snapshot: EvidenceSnapshotEntry[] }` where **`EvidenceSnapshotEntry`** is `{ position, kind, label, file_id?, file_sha256? (lowercase hex), approval_ref_id?, field_column_id?, field_value?, checklist_completed?, checklist_required? }`. The snapshot is insert-only and is what a later attempt cannot change.

**`IntakeRequestBody`** — `POST /api/v1/project-intake`

| Field | Type | Required | Constraint |
|---|---|---|---|
| `template_id` | uuid | yes | a **published** F015 template version; a draft is `400 invalid` with `field_errors.template_id = "not_published"` |
| `workspace_id` | uuid | yes | caller holds `sheet-editor` in it, else `403 denied`; unreadable → `404 not_found` |
| `name` | string | yes | 1–200 chars after trim |
| `sponsor_user_id` | uuid | yes | an active user of this tenant |
| `justification` | string? | no | ≤ 4,000 chars |
| `requested_start` | date | yes | |
| `requested_finish` | date? | no | on or after `requested_start`, else `field_errors.requested_finish = "before_start"` |
| `budget_planned` | decimal | yes | `>= 0`, two decimal places |
| `currency` | string | yes | ISO 4217 alpha-3, uppercase |
| `value_estimate` | decimal? | no | `>= 0` |
| `portfolio_id` | uuid? | no | a live portfolio of this tenant; the provisioned project is added to it on success |

**`IntakeResponse`** — the create body and `GET /api/v1/project-intake/{id}`: the request fields plus `{ id, status: "submitted"|"approved"|"rejected"|"provisioning"|"provisioned"|"failed", approval_id: uuid?, decision: "approved"|"rejected"?, reason: string?, provisioning_run_id: uuid?, project_sheet_id: uuid?, error: string?, version, created_at, created_by, updated_at, updated_by }`. `project_sheet_id` appears only in `provisioned`; `error` only in `failed`.

Status codes:

| Code | Produced by |
|---|---|
| `200` | health read, gate list, `PUT` model, `PUT` override, decide, intake read |
| `201` | `POST /api/v1/project-intake` |
| `202` | `POST /api/v1/stage-gates/{id}/submit` — the F020 approval is opened asynchronously |
| `400 invalid` | weight sum, threshold order, unknown rule key, `reason` length, evidence missing or `kind_mismatch` or `unknown_position`, `not_published`, `before_start`, `expires_at` in the past |
| `403 denied` | a `sheet-viewer` on any mutation; a non-approver, non-`portfolio-admin` deciding; a non-`portfolio-admin` on model or override routes |
| `404 not_found` | project, gate, model or intake in another tenant, or a project sheet the caller cannot read |
| `409 conflict` | `gate_sequence`, `already_submitted`, `gate_not_submitted`, duplicate model `scope`, stale `If-Match`, `Idempotency-Key` replayed with a different body |
| `429 rate_limited` | recompute or intake quota exceeded |
| `503 unavailable` | the recompute or provisioning work stream refuses the message; the request row is left in its prior status |

### Use case signatures

In `crates/domain/src/governance/`; the four consumers are in `services/worker/src/governance/`.
`Ctx` is F038's `ActorContext`.

```rust
fn upsert_health_model(ctx: &Ctx, uow: &mut UnitOfWork, id: ModelId, expected: Option<Version>, req: UpsertHealthModel) -> Result<HealthModel, DomainError>;
fn score_indicators(model: &HealthModel, inputs: &IndicatorInputs) -> Vec<IndicatorResult>;
fn compute_project_health(ctx: &Ctx, uow: &mut UnitOfWork, project: SheetId, source: Version) -> Result<ProjectHealth, DomainError>;
fn get_project_health(ctx: &Ctx, repo: &dyn ProjectHealthRepository, project: SheetId) -> Result<ProjectHealth, DomainError>;
fn set_health_override(ctx: &Ctx, uow: &mut UnitOfWork, project: SheetId, expected: Version, req: HealthOverrideRequest) -> Result<ProjectHealth, DomainError>;
fn list_stage_gates(ctx: &Ctx, repo: &dyn StageGateRepository, project: SheetId) -> Result<Vec<StageGate>, DomainError>;
fn create_gates_from_template(ctx: &Ctx, uow: &mut UnitOfWork, project: SheetId, version: VersionId) -> Result<Vec<StageGate>, DomainError>;
fn submit_stage_gate(ctx: &Ctx, uow: &mut UnitOfWork, gate: GateId, expected: Version, req: SubmitGate) -> Result<StageGate, DomainError>;
fn decide_stage_gate(ctx: &Ctx, uow: &mut UnitOfWork, gate: GateId, expected: Version, req: DecideGate) -> Result<StageGateDecision, DomainError>;
fn apply_approval_decision(ctx: &Ctx, uow: &mut UnitOfWork, approval: ApprovalId, decision: ApprovalOutcome) -> Result<(), DomainError>;
fn submit_intake(ctx: &Ctx, uow: &mut UnitOfWork, req: IntakeRequestBody) -> Result<IntakeRequest, DomainError>;
fn get_intake(ctx: &Ctx, repo: &dyn IntakeRequestRepository, id: IntakeId) -> Result<IntakeRequest, DomainError>;
fn advance_intake(ctx: &Ctx, uow: &mut UnitOfWork, id: IntakeId, to: IntakeStatus) -> Result<IntakeRequest, DomainError>;
```

`score_indicators` is pure — no `ctx`, no repository, no clock — so every scoring rule is testable as a
table of inputs to expected scores, which is the only way five weighted formulas stay verifiable.

Transaction boundaries:

- `upsert_health_model` writes the `health_models` row and the complete replacement of its
  `health_model_weights`, `health_model_thresholds`, `health_model_rules` and
  `health_model_risk_points` rows, plus the audit row, in one `UnitOfWork`. The "sum to 100" rule is
  an invariant over five rows, so it can only be true or false at a transaction boundary.
- `compute_project_health` writes the `project_health` row, all five `project_health_indicators` rows,
  their `project_health_indicator_inputs` rows and the `project-health.computed.v1` outbox row in one
  boundary. A score written without the indicators it was derived from cannot be explained or audited.
- `set_health_override` writes the override row (or deletes it), the audit row carrying the reason and
  the `health-override.set.v1` outbox row in one boundary — the reason is the record, so it must never
  outlive or predate the colour change.
- `submit_stage_gate` writes the gate's `status` and incremented `attempt`, one `stage_gate_evidence`
  row per requirement, every `stage_gate_evidence_checklist` row, the F020 approval through its
  repository, and the outbox event in one `UnitOfWork`. A gate marked `submitted` with no approval is
  a gate no one is asked to decide.
- `decide_stage_gate` writes the `stage_gate_decisions` row, the copy of that attempt's evidence into
  `stage_gate_decision_evidence`, the gate's new `status` and the outbox event in one boundary. The
  snapshot is copied inside the same transaction as the decision precisely so it records what the
  approver saw and not what a later attempt replaced.
- `advance_intake` writes the intake row's status, the F015 provisioning-run reference and the F031
  `replace_projects` membership addition in one `UnitOfWork` shared with those features' repositories,
  so an intake that reads `provisioned` always points at a project that exists and, when a portfolio
  was named, is in it.
- `apply_approval_decision` is idempotent by `approval_id` and shares the `decide_stage_gate`
  boundary, which is what stops an approval consumer and a direct decide call producing two divergent
  outcomes for one gate.

### PostgreSQL/SQLx

- Migration `*_governance_*.sql` creates the five catalog tables: `health_models(id uuid pk, tenant_id uuid not null references tenants(id) on delete restrict, name text not null, scope_kind text not null check (scope_kind in ('tenant_default','template_version')), template_version_id uuid null references template_versions(id) on delete cascade, check ((scope_kind = 'tenant_default') = (template_version_id is null)), version bigint not null default 1, created_by, created_at, updated_by, updated_at, deleted_at)` — the encoded `scope` string is rendered from the two columns rather than stored as a delimited value; `project_health(project_sheet_id uuid pk references sheets(id) on delete cascade, tenant_id uuid not null references tenants(id) on delete restrict, model_id uuid not null references health_models(id) on delete restrict, score smallint check (score between 0 and 100), colour text not null check (colour in ('green','amber','red','unknown')), confidence smallint not null check (confidence between 0 and 100), computed_at timestamptz not null, source_version bigint not null, last_error text, version bigint not null default 1, audit fields)`; `stage_gates(id uuid pk, tenant_id uuid not null references tenants(id) on delete restrict, project_sheet_id uuid not null references sheets(id) on delete cascade, name text not null, sequence int not null check (sequence > 0), approver_group_id uuid null references groups(id) on delete restrict, approver_user_id uuid null references users(id) on delete restrict, check (num_nonnulls(approver_group_id, approver_user_id) = 1), status text not null default 'pending' check (status in ('pending','submitted','approved','rejected','deferred')), attempt int not null default 0, approval_id uuid null references approvals(id) on delete restrict, deferred_until timestamptz, version bigint not null default 1, audit fields)`; `stage_gate_decisions(id uuid pk, tenant_id uuid not null references tenants(id) on delete restrict, gate_id uuid not null references stage_gates(id) on delete cascade, attempt int not null, decision text not null check (decision in ('approved','rejected','deferred')), approver_id uuid not null references users(id) on delete restrict, reason text, decided_at timestamptz not null, approval_id uuid null references approvals(id) on delete restrict)`; `project_intake_requests(id uuid pk, tenant_id uuid not null references tenants(id) on delete restrict, workspace_id uuid not null references workspaces(id) on delete restrict, template_id uuid not null references template_versions(id) on delete restrict, name text not null, sponsor_user_id uuid not null references users(id) on delete restrict, justification text, requested_start date not null, requested_finish date, budget_planned numeric(18,2) not null, currency char(3) not null, value_estimate numeric(18,2), portfolio_id uuid null references portfolios(id) on delete restrict, status text not null check (status in ('submitted','approved','rejected','provisioning','provisioned','failed')), approval_id uuid null references approvals(id) on delete restrict, provisioning_run_id uuid null references provisioning_runs(id) on delete restrict, project_sheet_id uuid null references sheets(id) on delete restrict, decision text check (decision in ('approved','rejected')), reason text, error text, version bigint not null default 1, audit fields)`.
- Normalized sets (decision section 2, no array or `jsonb` set columns): `health_model_weights(model_id uuid references health_models(id) on delete cascade, tenant_id, indicator text check (indicator in ('schedule','budget','scope','risk','resource')), weight smallint not null check (weight between 0 and 100), primary key (model_id, indicator))` replaces `weights jsonb`; `health_model_thresholds(model_id references health_models(id) on delete cascade, tenant_id, colour text check (colour in ('green','amber')), min_score smallint not null check (min_score between 0 and 100), primary key (model_id, colour))` replaces `thresholds jsonb`; `health_model_rules(model_id references health_models(id) on delete cascade, tenant_id, indicator text check (indicator in ('schedule','budget','scope','risk','resource')), parameter text check (parameter in ('late_days_for_zero','over_pct_for_zero','creep_pct_for_zero','risk_points_for_zero','conflicts_for_zero')), numeric_value numeric(12,4) not null check (numeric_value > 0), primary key (model_id, indicator, parameter))` and `health_model_risk_points(model_id references health_models(id) on delete cascade, tenant_id, severity text check (severity in ('high','medium','low')), points smallint not null check (points > 0), primary key (model_id, severity))` together replace `rules jsonb`, which the scorer read by key.
- Normalized sets, continued: `project_health_indicators(project_sheet_id references project_health(project_sheet_id) on delete cascade, tenant_id, indicator text check (indicator in ('schedule','budget','scope','risk','resource')), display_order smallint not null check (display_order between 1 and 5), score smallint check (score between 0 and 100), state text not null check (state in ('ok','missing')), weight_applied smallint not null check (weight_applied between 0 and 100), primary key (project_sheet_id, indicator), unique (project_sheet_id, display_order))` replaces `indicators jsonb` and fixes the card's bar order; `project_health_indicator_inputs(project_sheet_id, indicator, input_key text check (input_key in ('variance_days','variance_pct','creep_pct','risk_points','open_conflicts')), numeric_value numeric(12,4) not null, primary key (project_sheet_id, indicator, input_key), foreign key (project_sheet_id, indicator) references project_health_indicators(project_sheet_id, indicator) on delete cascade)` replaces the nested `inputs` object; `project_health_overrides(project_sheet_id uuid pk references project_health(project_sheet_id) on delete cascade, tenant_id, colour text not null check (colour in ('green','amber','red')), reason text not null check (char_length(reason) between 10 and 1000), set_by uuid not null references users(id) on delete restrict, set_at timestamptz not null, expires_at timestamptz)` replaces `override jsonb`, which `effective_colour` filtered by key and expiry; clearing an override deletes the row after the audit write.
- Normalized sets, continued: `stage_gate_requirements(id uuid pk, tenant_id, gate_id uuid not null references stage_gates(id) on delete cascade, position smallint not null check (position >= 0), kind text not null check (kind in ('file','approval','checklist','field')), label text not null, column_id uuid null references columns(id) on delete restrict, check ((kind = 'field') = (column_id is not null)), unique (gate_id, position))` replaces `required_evidence jsonb`, and `position` is the index reported in `field_errors.evidence[i]`; `stage_gate_requirement_items(requirement_id uuid references stage_gate_requirements(id) on delete cascade, tenant_id, position smallint not null, label text not null, primary key (requirement_id, position), unique (requirement_id, position))` holds checklist items in authored order; `stage_gate_evidence(id uuid pk, tenant_id, gate_id uuid not null references stage_gates(id) on delete cascade, attempt int not null, requirement_id uuid not null references stage_gate_requirements(id) on delete restrict, file_id uuid null references files(id) on delete restrict, file_sha256 bytea, evidence_approval_id uuid null references approvals(id) on delete restrict, field_value text, note text, submitted_by uuid not null references users(id) on delete restrict, submitted_at timestamptz not null, unique (gate_id, attempt, requirement_id))` stores one submitted item per requirement per attempt; `stage_gate_evidence_checklist(evidence_id uuid references stage_gate_evidence(id) on delete cascade, tenant_id, requirement_id uuid not null, item_position smallint not null, completed_at timestamptz not null, primary key (evidence_id, item_position), foreign key (requirement_id, item_position) references stage_gate_requirement_items(requirement_id, position) on delete restrict)` records which checklist items were ticked.
- Normalized sets, continued: `stage_gate_decision_evidence(decision_id uuid references stage_gate_decisions(id) on delete cascade, tenant_id, position smallint not null, kind text not null check (kind in ('file','approval','checklist','field')), label text not null, file_id uuid null references files(id) on delete restrict, file_sha256 bytea, approval_ref_id uuid null references approvals(id) on delete restrict, field_column_id uuid null references columns(id) on delete restrict, field_value text, checklist_completed smallint, checklist_required smallint, primary key (decision_id, position))` replaces `stage_gate_decisions.evidence_snapshot jsonb`. `StageGateDecisionRepository::append_decision_with_evidence` copies the attempt's `stage_gate_evidence` rows into it inside the decide transaction and never updates them afterwards, so the snapshot stays immutable and independent of any later attempt, and the API still returns it as the `evidence_snapshot` array. `SubmitGateRequest.evidence`, `StageGateResponse.required_evidence`, `ProjectHealthResponse.indicators`/`override`, and `UpsertHealthModelRequest.weights`/`thresholds`/`rules` keep their array and object shapes on the wire; the repositories fan them out to rows on write and reassemble them on read, so no externally visible behaviour changes.
- `jsonb` audit (decision section 2): no `jsonb` column remains in this module. `health_models.weights`, `.thresholds`, and `.rules` were read by key by the scorer and constrained (sum 100, ordered thresholds) and became `health_model_weights`, `health_model_thresholds`, `health_model_rules`, and `health_model_risk_points`. `project_health.indicators` was filtered and aggregated per indicator by the card and by F031 rollups and became `project_health_indicators` plus `project_health_indicator_inputs`. `project_health.override` was read by key and filtered on expiry by `effective_colour` and became `project_health_overrides`. `stage_gates.required_evidence` and `.approver` drove validation and authorization and became `stage_gate_requirements`, `stage_gate_requirement_items`, and the `approver_group_id`/`approver_user_id` columns. `stage_gate_decisions.evidence_snapshot` is queried by evidence kind and file ID for compliance export and became `stage_gate_decision_evidence`. The intake form fields are already typed columns with their own foreign keys on `project_intake_requests`, so they need no payload column.
- Invariants: unique partial index `health_models_tenant_default_idx on health_models(tenant_id) where scope_kind = 'tenant_default' and deleted_at is null` and `health_models_template_idx on health_models(template_version_id) where deleted_at is null` replace the index over the encoded `scope` string; `HealthModelRepository::replace_weights` requires exactly five `health_model_weights` rows summing to 100 and `replace_thresholds` requires both colour rows with `green.min_score > amber.min_score`, both checked inside the upsert transaction; `project_health_indicators` requires five rows per project, one per indicator, with distinct `display_order`; `project_health_overrides` allows at most one row per project by its primary key; unique `(project_sheet_id, sequence)` on `stage_gates`; unique `(gate_id, position)` on `stage_gate_requirements`; unique `(gate_id, attempt, requirement_id)` on `stage_gate_evidence` blocks duplicate evidence for one attempt; unique `(gate_id, attempt)` on `stage_gate_decisions`; `stage_gate_decisions` and `stage_gate_decision_evidence` rows are insert-only (no update trigger permitted); intake `status` and `decision` checks as above.
- Indexes: `project_health(tenant_id, colour)`, `project_health(computed_at)` for the recompute backlog query, `project_health_indicators(tenant_id, indicator, score)` for portfolio indicator breakdowns, `project_health_indicator_inputs(project_sheet_id)`, `project_health_overrides(tenant_id, expires_at)` for the expiry sweep, `health_model_weights(model_id)`, `health_model_rules(model_id, indicator)`, `health_model_risk_points(model_id)`, `health_model_thresholds(model_id)`, `stage_gates(project_sheet_id, sequence)`, `stage_gates(approval_id)`, `stage_gate_requirements(gate_id, position)`, `stage_gate_requirement_items(requirement_id, position)`, `stage_gate_evidence(gate_id, attempt)`, `stage_gate_evidence(file_id)`, `stage_gate_evidence_checklist(requirement_id, item_position)`, `stage_gate_decisions(gate_id, attempt)`, `stage_gate_decision_evidence(decision_id, position)`, `stage_gate_decision_evidence(file_id)`, `project_intake_requests(tenant_id, status, created_at desc)`, `project_intake_requests(approval_id)`.
- Audit events: `health-model.upsert`, `health.override.set`, `health.override.clear`, `stage-gate.submit`, `stage-gate.decide`, `project-intake.submit`, `project-intake.advance` with field-level diffs.
- Retention/deletion: models soft-delete; decisions and intake requests are retained per tenant retention policy (F027); migration rollback drops the seventeen tables, children before parents (`stage_gate_decision_evidence`, `stage_gate_decisions`, `stage_gate_evidence_checklist`, `stage_gate_evidence`, `stage_gate_requirement_items`, `stage_gate_requirements`, `stage_gates`, `project_health_indicator_inputs`, `project_health_indicators`, `project_health_overrides`, `project_health`, `health_model_risk_points`, `health_model_rules`, `health_model_thresholds`, `health_model_weights`, `health_models`, `project_intake_requests`).

### React/TypeScript

- Routes: `/w/:workspaceId/projects/:projectSheetId/governance`, `/w/:workspaceId/intake/new`, `/w/:workspaceId/intake/:intakeId`, `/w/:workspaceId/settings/health-models/:modelId` in `apps/web/src/features/governance/`; components `GovernancePage`, `HealthCard`, `IndicatorBar`, `OverrideDialog`, `GateTimeline`, `GateItem`, `SubmitGateDialog`, `EvidenceChecklist`, `DecideGateDialog`, `IntakeForm`, `IntakeStatusPage`, `HealthModelEditor`.
- State: TanStack Query keys `['project-health', projectSheetId]`, `['stage-gates', projectSheetId]`, `['intake', intakeId]`, `['health-model', modelId]`; intake status page polls every 5 seconds while status is `submitted` or `provisioning`.
- API client: generated `GovernanceApi` with `getProjectHealth`, `setHealthOverride`, `upsertHealthModel`, `listStageGates`, `submitStageGate`, `decideStageGate`, `submitIntake`, `getIntake`.
- Optimistic updates: none for decisions (server truth); override applies optimistically and rolls back on `invalid`.
- Telemetry: `health_viewed`, `health_override_set`, `stage_gate_submitted`, `stage_gate_decided`, `intake_submitted`, `health_model_saved` with `project_sheet_id` or `intake_id`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F032-01 through FR-F032-14 in `testing/features/F032/requirements/cases.md`
- [ ] Failure/edge-case tests: weights 99, short reason, expired override, missing evidence, out-of-sequence submit, decide on pending gate, duplicate approval event, provisioning failure
- [ ] Permission-negative and tenant-isolation tests: cross-tenant `not_found`, viewer `denied`, non-approver decide `denied`
- [ ] Rust unit tests: `crates/domain/src/governance/` indicator scoring, renormalized weights, colour thresholds, gate state transitions, intake state transitions
- [ ] API contract/integration tests: every route above with success and each error code
- [ ] Database migration/constraint tests: one tenant-default model per tenant, weight rows sum to 100, threshold ordering, five indicator rows per project, at most one override row, requirement `position` uniqueness, duplicate evidence for one attempt rejected, checklist item foreign key, decision and snapshot rows insert-only, gate sequence uniqueness, approver exactly-one check, rollback ordering
- [ ] React component tests: `HealthCard`, `OverrideDialog`, `GateTimeline`, `SubmitGateDialog`, `IntakeForm` states
- [ ] Browser E2E tests: override with reason, submit and approve a gate, out-of-sequence rejection, intake to provisioned
- [ ] Accessibility tests: axe on governance and intake pages, colour labels, dialog focus
- [ ] Performance/load tests: health read p95, nightly recompute for 1,000 projects, decision write p95

### Fast fanout configuration

- Test harness path: `testing/features/F032/`
- Feature flag: `F032_FEATURE`
- Fixture/seed factory: `testing/fixtures/governance.rs` builds tenant, workspace, portfolio-admin, approver, sheet-editor, sheet-viewer, foreign tenant, a provisioned project with baseline and risk rows, a template version with three gates, a tenant-default health model, and an `project_intake` approval policy
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, UTC, tenant time zone UTC
- Mock/stub contracts: outbox publisher recorded in memory; F020 approval engine real with fixture policy; F015 provision use case real against fixture template; F034 conflict counts stubbed through a trait
- Parallel isolation: one schema per test worker, tenant ID per test
- Targeted command: `cargo xtask test-feature F032`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F032/`

## 6. Acceptance criteria

```gherkin
Feature: Project health and governance

Scenario: Health is computed from weighted indicators
  Given a health model with weights schedule 40, budget 30, scope 10, risk 10, resource 10
  And project "Rollout" is 15 days late, 10 percent over budget, with no risk rows
  When the worker recomputes health
  Then schedule scores 50, budget scores 60, risk scores 100, scope and resource are ok
  And the score is 61, the colour is amber, and project-health.computed.v1 is published

Scenario: Override requires a reason and is audited
  Given project "Rollout" computed amber
  When an administrator overrides to red with reason "Vendor contract at risk"
  Then effective_colour is red, the override records the administrator and time
  And an audit event and health-override.set.v1 exist

Scenario: Gate cannot advance without evidence
  Given gate 2 "Design review" requires a file and a checklist
  When an editor submits with the file only
  Then the response is 400 invalid with field_errors.evidence[1]

Scenario: Approver decides a submitted gate
  Given gate 2 is submitted with complete evidence
  When the approver approves it
  Then the gate is approved with approver, decided_at, and evidence_snapshot
  And stage-gate.decided.v1 is published

Scenario: Viewer cannot override or decide
  Given a sheet-viewer on project "Rollout"
  When they PUT a health override or POST a decision
  Then the response is 403 denied and no audit mutation is written

Scenario: Cross-tenant intake read does not leak
  Given an intake request in tenant A
  When an administrator from tenant B requests it by id
  Then the response is 404 not_found
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F031 (portfolio membership and rollup consumer of `project_health`), F020 (approvals, policies, `approval.decided.v1`); decisions sections 2–4, 7; contracts row F032
- Blocks: none
- Conflicts with: none (disjoint owned paths)
- External dependencies: none
- Risks and mitigations: indicator inputs depend on template column conventions, so rules reference stable column IDs from the template version and missing columns reduce confidence rather than fail; approval and gate decisions can race, so `decide` is idempotent by `(gate_id, attempt)` and the second writer receives `conflict`; nightly recompute of many projects can saturate the worker, so it runs in batches of 50 with per-tenant quotas from F004.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F031 and F020 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F032/`
- [ ] Migration file name and owned paths claimed
- [ ] Fixture factory with template gates and approval policy available in `testing/fixtures/governance.rs`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, worker, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for every mutation and decision
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F032_FEATURE`, stop governance consumers, run down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Projects get computed health from weighted schedule, budget, scope, risk, and resource indicators with auditable overrides; stage gates require evidence and an approver's dated decision; new projects can be requested through governed intake that provisions after approval.
- Migration adds `health_models`, `project_health`, `stage_gates`, `stage_gate_decisions`, and `project_intake_requests` with their normalized child tables `health_model_weights`, `health_model_thresholds`, `health_model_rules`, `health_model_risk_points`, `project_health_indicators`, `project_health_indicator_inputs`, `project_health_overrides`, `stage_gate_requirements`, `stage_gate_requirement_items`, `stage_gate_evidence`, `stage_gate_evidence_checklist`, and `stage_gate_decision_evidence`; rollback drops them children first. Feature is off by default behind `F032_FEATURE`.
