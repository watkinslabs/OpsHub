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

- **FR-F032-01:** `PUT /api/v1/health-models/{id}` upserts a health model with `name`, `scope` (`tenant_default` or `template_version:{id}`), integer `weights` for `schedule`, `budget`, `scope`, `risk`, and `resource` that sum to exactly 100, `thresholds { green_min, amber_min }` with `100 ≥ green_min > amber_min ≥ 0`, and per-indicator `rules`; a weight sum other than 100 returns `invalid` with `field_errors.weights`, and updates require `If-Match`.
- **FR-F032-02:** Indicator scores are 0–100 computed by rule: `schedule` from baseline `variance_days` (0 days → 100, `late_days_for_zero` default 30 → 0, linear), `budget` from `variance_pct` (0 → 100, `over_pct_for_zero` default 25 → 0), `scope` from percent of rows added since the named baseline (`creep_pct_for_zero` default 20), `risk` from open risk rows weighted `high=3, medium=2, low=1` against `risk_points_for_zero` default 12, and `resource` from open F034 workload conflicts on the project's allocations (`conflicts_for_zero` default 5).
- **FR-F032-03:** Project health `score` is the weighted mean of available indicators with weights renormalized over indicators whose state is `ok`; `colour` is `green` when `score ≥ green_min`, `amber` when `≥ amber_min`, else `red`; `confidence` equals the sum of weights of available indicators; when no indicator is available the colour is `unknown`.
- **FR-F032-04:** The worker recomputes a project's health within 60 seconds of `row.updated.v1`, `baseline.captured.v1`, `allocation.*.v1`, or `workload-conflict.detected.v1` for that project (debounced per project) and nightly at 02:00 tenant time, writes `project_health`, and publishes `project-health.computed.v1` with `changed_fields` naming indicators whose score moved.
- **FR-F032-05:** `GET /api/v1/projects/{id}/health` returns `computed { score, colour, confidence, indicators[{ name, score, state, inputs }] , computed_at, model_id }`, `override { colour, reason, set_by, set_at, expires_at } | null`, and `effective_colour`; an actor without read access to the project sheet receives `not_found`.
- **FR-F032-06:** `PUT /api/v1/projects/{id}/health-override` by a `portfolio-admin` sets `colour` in {`green`, `amber`, `red`} with `reason` of 10–1,000 characters and optional `expires_at` in the future, or clears the override with `colour: null` and a reason; a missing or short reason returns `invalid` with `field_errors.reason`; every change writes an audit event and publishes `health-override.set.v1`; an expired override is ignored by `effective_colour` and reported as `expired: true`.
- **FR-F032-07:** Stage gates are created for a project when the worker consumes `project.provisioned.v1` and reads `governance.gates` from the F015 template version: each gate has `name`, `sequence`, `required_evidence[]` of kinds `file`, `approval`, `checklist`, or `field` (with `column_id`), and an `approver_group_id` or `approver_user_id`; `GET /api/v1/projects/{id}/stage-gates` lists them in sequence with `status` in {`pending`, `submitted`, `approved`, `rejected`, `deferred`}, `attempt`, and the latest decision.
- **FR-F032-08:** `POST /api/v1/stage-gates/{id}/submit` by a `sheet-editor` on the project accepts `evidence[]` indexed to `required_evidence` (a `file_id` from F017, an `approval_id` from F020, a checklist of completed items, or a field value read from the project sheet) and `note`; any missing required item returns `invalid` with `field_errors.evidence[i]`; submitting gate N while gate N-1 is not `approved` returns `conflict` with `code_detail: gate_sequence`; success sets `submitted`, increments `attempt`, creates an F020 approval for the approver set, and publishes `stage-gate.submitted.v1`.
- **FR-F032-09:** `POST /api/v1/stage-gates/{id}/decide` by a member of the approver set or a `portfolio-admin` records `decision` in {`approved`, `rejected`, `deferred`}, `reason` (required, ≥ 10 chars, for `rejected` and `deferred`), the server `decided_at`, the approver ID, and an immutable `evidence_snapshot` in `stage_gate_decisions`; deciding a gate not in `submitted` returns `conflict`; `rejected` returns the gate to `pending` for resubmission, `deferred` sets `deferred_until`; every decision writes an audit event and publishes `stage-gate.decided.v1`.
- **FR-F032-10:** When the F020 approval linked to a submitted gate is decided, the worker consumes `approval.decided.v1` and applies the same decision through the decide use case with the approval's approver as the actor, so a gate never has two divergent outcomes.
- **FR-F032-11:** `POST /api/v1/project-intake` by a `sheet-editor` in the target workspace accepts `template_id`, `name` (1–200), `workspace_id`, `sponsor_user_id`, `justification` (≤ 4,000), `requested_start`, optional `requested_finish`, `budget_planned` with `currency`, `value_estimate`, and optional `portfolio_id`; it stores a `project_intake_requests` row with status `submitted`, opens an F020 approval using approval policy key `project_intake`, and publishes `project-intake.submitted.v1`.
- **FR-F032-12:** When the intake approval is approved the worker provisions the project through the F015 provision use case, records `provisioning_run_id` and `project_sheet_id`, moves status through `provisioning` to `provisioned`, and adds the project to `portfolio_id` when given; a rejected approval sets `rejected` with the reason; a provisioning failure sets `failed` with `error`; `GET /api/v1/project-intake/{id}` returns the request, status, `approval_id`, `decision`, `reason`, and the provisioning references.
- **FR-F032-13:** Every mutation requires `Idempotency-Key` and writes an `audit_events` row with actor, action, and before/after diff; cross-tenant access to any health model, gate, or intake request by ID returns `not_found`; a `sheet-viewer` receives `denied` on submit, decide, override, and model routes.
- **FR-F032-14:** The web governance page shows the health card (effective colour, score, confidence, indicator breakdown, override banner with reason and author), the stage gate timeline with evidence checklist, submit and decide dialogs, and the intake form and status page; every colour is paired with a text label.

### Non-functional requirements

- **NFR-F032-01 Performance:** `GET /health` and `GET /stage-gates` respond in under 500 ms p95; submit, decide, override, and intake writes respond in under 800 ms p95; health recompute for one project completes in under 5 seconds and for 1,000 projects in the nightly run in under 20 minutes (spec section 6).
- **NFR-F032-02 Security/privacy:** health inputs are read as the tenant system actor but responses are gated by the caller's project read access; evidence snapshots store IDs and hashes, never file bodies; override reasons and decision reasons are redacted from logs; cross-tenant, viewer, and non-approver negatives are in the harness.
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

## 4. Technical specification

### Rust backend

- Domain entities in `crates/domain/src/governance/`: `HealthModel { id, tenant_id, name, scope: ModelScope, weights: Weights, thresholds: Thresholds, rules: IndicatorRules, version, audit fields }`, `ProjectHealth { project_sheet_id, tenant_id, model_id, score: Option<u8>, colour: HealthColour, confidence: u8, indicators: Vec<IndicatorResult>, computed_at, source_version, override_: Option<HealthOverride>, last_error, version }`, `HealthOverride { colour, reason, set_by, set_at, expires_at }`, `StageGate { id, tenant_id, project_sheet_id, name, sequence, required_evidence: Vec<EvidenceRequirement>, approver: ApproverRef, status: GateStatus, attempt, approval_id, deferred_until, version }`, `StageGateDecision { id, gate_id, attempt, decision, approver_id, reason, decided_at, evidence_snapshot }`, `IntakeRequest { id, tenant_id, workspace_id, template_id, name, sponsor_user_id, justification, requested_start, requested_finish, budget_planned, currency, value_estimate, portfolio_id, status: IntakeStatus, approval_id, provisioning_run_id, project_sheet_id, decision, reason, error, version }`.
- Use cases: `upsert_health_model`, `score_indicators`, `compute_project_health`, `get_project_health`, `set_health_override`, `list_stage_gates`, `create_gates_from_template`, `submit_stage_gate`, `decide_stage_gate`, `apply_approval_decision`, `submit_intake`, `get_intake`, `advance_intake`.
- API endpoints (`services/api/src/governance/`): `GET /api/v1/projects/{id}/health`, `PUT /api/v1/projects/{id}/health-override`, `PUT /api/v1/health-models/{id}`, `GET /api/v1/projects/{id}/stage-gates`, `POST /api/v1/stage-gates/{id}/submit`, `POST /api/v1/stage-gates/{id}/decide`, `POST /api/v1/project-intake`, `GET /api/v1/project-intake/{id}`. DTOs: `UpsertHealthModelRequest`, `HealthOverrideRequest`, `ProjectHealthResponse`, `StageGateResponse`, `SubmitGateRequest { evidence, note }`, `DecideGateRequest { decision, reason }`, `IntakeRequestBody`, `IntakeResponse`.
- Worker (`services/worker/src/governance/`): `health_recompute.rs` (debounced consumer and nightly schedule), `gate_provisioning.rs` (consumes `project.provisioned.v1`), `approval_sync.rs` (consumes `approval.decided.v1` for gates and intake), `intake_provisioning.rs` (calls F015 provision and F031 `replace_projects`).
- Events: `project-health.computed.v1`, `health-override.set.v1`, `stage-gate.submitted.v1`, `stage-gate.decided.v1`, `project-intake.submitted.v1`; payload per contract conventions with `changed_fields`.
- Authorization: `portfolio-admin` for health models, overrides, and decisions; approver-set membership also permits decide; `sheet-editor` on the project for submit and in the workspace for intake; `sheet-viewer` on the project for reads; explicit deny wins; missing access maps to `not_found`.
- Validation: weights sum 100, thresholds ordered, reason 10–1,000 chars, justification ≤ 4,000, evidence count equals required count, `expires_at` in the future, `decision` enum. Idempotency via `idempotency_keys` for 24 hours. Concurrency: `If-Match` on model and override.
- Error mapping: `GovernanceError::WeightsNotHundred → 400 invalid`, `GovernanceError::MissingEvidence(i) → 400 invalid`, `GovernanceError::GateSequence → 409 conflict`, `GovernanceError::GateNotSubmitted → 409 conflict`, `GovernanceError::StaleVersion → 409 conflict`, `GovernanceError::NotFound → 404 not_found`, `AuthzError::Denied → 403 denied`.

### PostgreSQL/SQLx

- Migration `*_governance_*.sql` creates `health_models(id uuid pk, tenant_id, name text, scope text not null, weights jsonb not null, thresholds jsonb not null, rules jsonb not null, version bigint, audit fields, deleted_at)`, `project_health(project_sheet_id uuid pk, tenant_id, model_id uuid, score smallint, colour text not null, confidence smallint not null, indicators jsonb not null, computed_at timestamptz, source_version bigint, override jsonb, last_error text, version bigint, audit fields)`, `stage_gates(id uuid pk, tenant_id, project_sheet_id, name text, sequence int not null, required_evidence jsonb not null, approver jsonb not null, status text not null default 'pending', attempt int not null default 0, approval_id uuid, deferred_until timestamptz, version bigint, audit fields)`, `stage_gate_decisions(id uuid pk, tenant_id, gate_id, attempt int, decision text not null, approver_id uuid not null, reason text, decided_at timestamptz not null, evidence_snapshot jsonb not null, approval_id uuid)`, `project_intake_requests(id uuid pk, tenant_id, workspace_id, template_id, name, sponsor_user_id, justification, requested_start date, requested_finish date, budget_planned numeric(18,2), currency char(3), value_estimate numeric(18,2), portfolio_id uuid, status text not null, approval_id uuid, provisioning_run_id uuid, project_sheet_id uuid, decision text, reason text, error text, version bigint, audit fields)`.
- Invariants: unique partial index `health_models_tenant_scope_idx on (tenant_id, scope) where deleted_at is null`; check `colour in ('green','amber','red','unknown')`; check `status in ('pending','submitted','approved','rejected','deferred')`; unique `(project_sheet_id, sequence)` on `stage_gates`; unique `(gate_id, attempt)` on `stage_gate_decisions`; `stage_gate_decisions` rows are insert-only (no update trigger permitted); check `intake status in ('submitted','approved','rejected','provisioning','provisioned','failed')`.
- Indexes: `project_health(tenant_id, colour)`, `stage_gates(project_sheet_id, sequence)`, `stage_gates(approval_id)`, `project_intake_requests(tenant_id, status, created_at desc)`, `project_intake_requests(approval_id)`.
- Audit events: `health-model.upsert`, `health.override.set`, `health.override.clear`, `stage-gate.submit`, `stage-gate.decide`, `project-intake.submit`, `project-intake.advance` with field-level diffs.
- Retention/deletion: models soft-delete; decisions and intake requests are retained per tenant retention policy (F027); migration rollback drops the five tables.

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
- [ ] Database migration/constraint tests: scope uniqueness, colour and status checks, decision insert-only, gate sequence uniqueness, rollback
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
- Migration adds `health_models`, `project_health`, `stage_gates`, `stage_gate_decisions`, and `project_intake_requests`; rollback drops them. Feature is off by default behind `F032_FEATURE`.
