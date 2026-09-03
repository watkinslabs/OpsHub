---
id: T127
type: task
status: planned
parent_epic: E007
parent_feature: F032
parent_story: S064
depends_on: [T126]
owned_paths: [apps/web/src/features/governance/**, testing/features/F032/frontend/**, testing/features/F032/accessibility/**]
feature_flag: F032_FEATURE
branch: t127-health-dashboard
started_at: null
finished_at: null
---

# T127 — Health dashboard

## Identity

- Parent story: `S064` Stage gates and intake
- Owner: platform
- Branch: `t127-health-dashboard`
- Decision references: `docs/architecture-decisions.md` section 6; `docs/capability-contracts.md` row F032

## Objective

Build the governance page with the health card, override dialog, gate timeline with submit and decide dialogs, the intake form and status page, and the health model editor wired to the real governance API.

## Specification

- Owned paths: `apps/web/src/features/governance/{GovernancePage.tsx, HealthCard.tsx, IndicatorBar.tsx, OverrideDialog.tsx, GateTimeline.tsx, GateItem.tsx, SubmitGateDialog.tsx, EvidenceChecklist.tsx, DecideGateDialog.tsx, IntakeForm.tsx, IntakeStatusPage.tsx, HealthModelEditor.tsx, api.ts, hooks.ts, routes.ts}`
- Contract/input: generated `GovernanceApi` client; route params `workspaceId`, `projectSheetId`, `intakeId`, `modelId`; query `tab=health|gates`; query keys `['project-health', id]`, `['stage-gates', id]`, `['intake', id]`, `['health-model', id]`.
- Output/behavior: `HealthCard` shows effective colour with text label and icon, score, confidence, five `IndicatorBar` rows with state (`ok`, `missing`) and inputs tooltip, `Health computed {time} ago`, and the override banner (author, reason, time, `Override expired` when past `expires_at`); `OverrideDialog` validates reason length 10–1,000 and applies optimistically with rollback on `invalid`; `GateTimeline` renders an ordered list with status, attempt, latest decision, approver, and date; `SubmitGateDialog` builds `EvidenceChecklist` from `required_evidence` (file picker via F017, approval reference, checklist items, field value) and disables submit until complete, showing `Gate N must be approved first` on `gate_sequence`; `DecideGateDialog` appears only for approver-set members and administrators and requires a reason for reject and defer; `IntakeForm` validates required fields and currency; `IntakeStatusPage` polls every 5 seconds while `submitted` or `provisioning` and links to the provisioned project; `HealthModelEditor` enforces weights summing to 100 with a live total; states: loading, empty (`No gates defined by this template`), error with correlation ID, denied affordances hidden, not-found; icons and tokens per ticket section 3; telemetry `health_viewed`, `health_override_set`, `stage_gate_submitted`, `stage_gate_decided`, `intake_submitted`, `health_model_saved`.
- Dependencies: T126 routes; F006 sheet page header for the `Governance` tab; F017 file picker component; F005 shell for the `Intake` sidebar entry.
- Feature flag: `F032_FEATURE` read through the flag hook; routes are not registered when off.

## TDD

- Failing test first: `testing/features/F032/frontend/HealthCard.test.tsx::health_card_shows_override_banner`, `::colour_has_text_label`, `OverrideDialog.test.tsx::rejects_short_reason`, `GateTimeline.test.tsx::renders_gates_in_sequence_with_decision`, `SubmitGateDialog.test.tsx::submit_dialog_blocks_until_evidence_complete`, `::shows_sequence_conflict_message`, `DecideGateDialog.test.tsx::hidden_for_non_approver`, `IntakeStatusPage.test.tsx::intake_status_polls_to_provisioned`, `HealthModelEditor.test.tsx::blocks_save_when_weights_not_hundred`; `testing/features/F032/accessibility/governance.a11y.spec.ts::governance_pages_have_no_serious_axe_violations`
- Targeted command: `cargo xtask test-feature F032`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: MSW handlers for health (computed, overridden, expired), gates in every status, intake in every status; axe via Playwright against seeded tenant

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Component and accessibility lanes pass
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S064
- [ ] `finished_at` recorded
