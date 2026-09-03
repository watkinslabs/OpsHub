---
id: T126
type: task
status: planned
parent_epic: E007
parent_feature: F032
parent_story: S063
depends_on: [T125]
owned_paths: [crates/domain/src/governance/**, services/api/src/governance/**, services/worker/src/governance/**, testing/features/F032/api/**, testing/features/F032/requirements/**]
feature_flag: F032_FEATURE
branch: t126-gate-state-machine
started_at: null
finished_at: null
---

# T126 — Gate state machine

## Identity

- Parent story: `S063` Health indicators
- Owner: platform
- Branch: `t126-gate-state-machine`
- Decision references: `docs/architecture-decisions.md` sections 2–4, 7; `docs/capability-contracts.md` row F032

## Objective

Implement the stage gate and intake state machines with evidence validation, decision recording, approval synchronization, and the five gate and intake HTTP routes.

## Specification

- Owned paths: `crates/domain/src/governance/{gates.rs, intake.rs, service_gates.rs, service_intake.rs}`, `services/api/src/governance/{handlers_gates.rs, handlers_intake.rs}`, `services/worker/src/governance/{gate_provisioning.rs, approval_sync.rs, intake_provisioning.rs}`
- Contract/input: `SubmitGateRequest { evidence: [{ index, file_id? , approval_id?, checklist?: [string], value? }], note? }`, `DecideGateRequest { decision: approved|rejected|deferred, reason? }`, `IntakeRequestBody { template_id, name, workspace_id, sponsor_user_id, justification, requested_start, requested_finish?, budget_planned, currency, value_estimate, portfolio_id? }`; consumed events `project.provisioned.v1` (template `governance.gates`) and `approval.decided.v1`; headers `Idempotency-Key`.
- Output/behavior: routes `GET /api/v1/projects/{id}/stage-gates`, `POST /api/v1/stage-gates/{id}/submit`, `POST /api/v1/stage-gates/{id}/decide`, `POST /api/v1/project-intake`, `GET /api/v1/project-intake/{id}` return `StageGateResponse` and `IntakeResponse` per ticket section 4; `gates.rs` enforces `pending → submitted → approved | rejected → pending | deferred`, validates every `required_evidence` entry (file exists in F017 and is scanned clean, approval is approved, checklist complete, field value present), rejects out-of-sequence submission with `conflict` `gate_sequence`, increments `attempt`, opens an F020 approval for the approver set, and publishes `stage-gate.submitted.v1`; `decide_stage_gate` writes an insert-only `stage_gate_decisions` row with `evidence_snapshot` (IDs and checksums), server `decided_at`, approver ID, and reason, is idempotent by `(gate_id, attempt)`, and publishes `stage-gate.decided.v1`; `approval_sync.rs` applies `approval.decided.v1` once per `approval_id` to the gate or intake; `intake.rs` enforces `submitted → approved → provisioning → provisioned | failed` and `submitted → rejected`, opens the approval with policy key `project_intake`, publishes `project-intake.submitted.v1`; `intake_provisioning.rs` calls the F015 provision use case, records `provisioning_run_id` and `project_sheet_id`, and calls F031 `replace_projects` when `portfolio_id` is set; errors map per ticket section 4.
- Dependencies: T125 schema and router; F020 `approvals::request` and `approval.decided.v1`; F015 `template_versions.metadata.governance.gates` and provision use case; F017 file lookup; F031 `replace_projects`.
- Feature flag: `F032_FEATURE` gates routes and consumers.

## TDD

- Failing test first: `testing/features/F032/api/gate_tests.rs::gates_created_from_template_on_provision`, `::gate_submit_missing_evidence_invalid`, `::gate_submit_out_of_sequence_conflicts`, `::gate_decide_records_snapshot_and_event`, `::gate_decide_on_pending_conflicts`, `::gate_rejected_returns_to_pending_with_next_attempt`, `::approval_decision_applied_once_per_approval_id`, `::non_approver_decide_denied`; `testing/features/F032/api/intake_tests.rs::intake_submit_opens_approval`, `::intake_approval_provisions_project_and_joins_portfolio`, `::intake_provisioning_failure_sets_failed`, `::intake_cross_tenant_not_found`
- Targeted command: `cargo xtask test-feature F032`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/governance.rs` template version with three gates, approver group, `project_intake` approval policy, clean scanned file; real F020 engine; in-memory outbox recorder; in-process job runner

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Routes mounted in `services/api/src/governance/routes.rs` and consumers registered in `services/worker/src/main.rs` behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S063
- [ ] `finished_at` recorded
