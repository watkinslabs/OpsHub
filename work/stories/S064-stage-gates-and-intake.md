---
id: S064
type: story
status: planned
parent_epic: E007
parent_feature: F032
depends_on: [S063]
owned_paths: [crates/domain/src/governance/**, services/api/src/governance/**, services/worker/src/governance/**, apps/web/src/features/governance/**, testing/features/F032/**]
feature_flag: F032_FEATURE
branch: s064-stage-gates-and-intake
started_at: null
finished_at: null
---

# S064 — Stage gates and intake

## Identity

- Parent feature: `F032` Project health/governance
- Owner: platform
- Branch: `s064-stage-gates-and-intake`
- Decision references: `docs/architecture-decisions.md` sections 2–4, 6, 7; `docs/capability-contracts.md` row F032

## Vertical slice

As a project editor, approver, and requester, I want to see project health, submit gate evidence, decide gates, and request a new project through intake in the web app, with approvals synchronized and provisioning triggered automatically, so that governance runs end to end without manual reconciliation.

## Requirements

- **SR-S064-01:** `GovernancePage` renders `HealthCard` with effective colour label, score, confidence, indicator bars, and the override banner with reason, author, time, and expired state; `OverrideDialog` validates the 10-character reason and rolls back on `invalid` (FR-F032-05, FR-F032-06, FR-F032-14).
- **SR-S064-02:** `GateTimeline` lists gates in sequence with status, attempt, and latest decision; `SubmitGateDialog` renders `EvidenceChecklist` from `required_evidence`, blocks submit until every required item is provided, and shows `Gate N must be approved first` on `gate_sequence` conflict (FR-F032-07, FR-F032-08, FR-F032-14).
- **SR-S064-03:** `DecideGateDialog` is shown only to approver-set members and administrators, requires a reason for `rejected` and `deferred`, and the timeline shows approver, `decided_at`, and decision after success (FR-F032-09, FR-F032-13).
- **SR-S064-04:** Gates are created from the template version when the worker consumes `project.provisioned.v1`, and `approval.decided.v1` for a gate approval applies the same decision idempotently by `approval_id` (FR-F032-07, FR-F032-10, NFR-F032-04).
- **SR-S064-05:** `IntakeForm` submits the intake request and `IntakeStatusPage` polls every 5 seconds through `submitted`, `approved`, `provisioning`, `provisioned` (with the project link) or `rejected`/`failed` with reason or error; the worker provisions through F015 on approval and adds the project to the chosen portfolio (FR-F032-11, FR-F032-12).
- **SR-S064-06:** All governance pages show loading, empty, error, denied, stale, conflict, and expired states, pair every colour with text, and pass axe with keyboard-only operation (FR-F032-14, NFR-F032-03).
- **SR-S064-07:** Health and gate reads and governance writes meet NFR-F032-01 in the performance lane.

## Surfaces

- Infrastructure/container: none beyond S063 consumers
- Rust service/API: `services/worker/src/governance/{gate_provisioning.rs, approval_sync.rs, intake_provisioning.rs}` completion; `crates/domain/src/governance/service_intake.rs` provisioning hooks
- Data/migration: none new; uses tables from S063
- React/UI: `apps/web/src/features/governance/{GovernancePage.tsx, HealthCard.tsx, IndicatorBar.tsx, OverrideDialog.tsx, GateTimeline.tsx, GateItem.tsx, SubmitGateDialog.tsx, EvidenceChecklist.tsx, DecideGateDialog.tsx, IntakeForm.tsx, IntakeStatusPage.tsx, HealthModelEditor.tsx, api.ts, hooks.ts, routes.ts}`
- Mocks/fixtures: MSW handlers for health, gates, and intake in every status; Playwright seeded tenant with approver session; 1,000-project generator for the nightly recompute benchmark

## TDD harness

- Test path: `testing/features/F032/{api,frontend,e2e,accessibility,performance}/`
- Feature flag: `F032_FEATURE`
- Targeted command: `cargo xtask test-feature F032`
- Full command: `cargo xtask test-all`
- First failing tests: `gates_created_from_template_on_provision`, `approval_decision_applied_once_per_approval_id`, `intake_approval_provisions_project_and_joins_portfolio`, `health_card_shows_override_banner`, `submit_dialog_blocks_until_evidence_complete`, `intake_status_polls_to_provisioned`, `nightly_recompute_1000_projects_under_20m`

## Exit criteria

- [ ] Requirement tests SR-S064-01 through SR-S064-07 written first and failing
- [ ] Tasks T127 and T128 complete; UI wired to the real API through the generated client
- [ ] Unit, API, worker, React, E2E, accessibility, permission, and performance tests pass
- [ ] Production call path named: `apps/web/src/features/governance/GovernancePage.tsx` mounted at `/w/:workspaceId/projects/:projectSheetId/governance` and `IntakeStatusPage.tsx` at `/w/:workspaceId/intake/:intakeId`
- [ ] Handoff evidence recorded in the F032 ticket
