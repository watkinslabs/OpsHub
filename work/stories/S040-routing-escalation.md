---
id: S040
type: story
status: planned
parent_epic: E004
parent_feature: F020
depends_on: [S039]
owned_paths: [crates/domain/src/approvals/**, services/api/src/approvals/**, services/worker/src/approvals/**, apps/web/src/features/approvals/**, testing/features/F020/**]
feature_flag: F020_FEATURE
branch: s040-routing-escalation
started_at: null
finished_at: null
---

# S040 — Routing/escalation

## Identity

- Parent feature: `F020` Approvals and escalation
- Owner: platform
- Branch: `s040-routing-escalation`
- Decision references: `docs/architecture-decisions.md` sections 3, 6, 7; `docs/capability-contracts.md` row F020

## Vertical slice

As a workflow editor, I want approval policies with due dates, reminders, escalation to a manager or group, and expiry behaviour, and as an approver I want to reassign a request and act from an inbox, so that no approval stalls silently and every routing step is auditable.

## Requirements

- **SR-S040-01:** `PUT /api/v1/approval-policies/{id}` upserts `default_due_minutes`, `reminder_before_minutes`, `escalate_after_minutes` (≥ 5), `escalate_to`, `max_escalations` (1–3), `on_expiry`; invalid values return `400 invalid` with the field path (FR-F020-07).
- **SR-S040-02:** Creating an approval with a policy or `due_at` writes `escalation_timers` rows for each reminder, the escalation, and the expiry; cancel and completion void unfired timers (FR-F020-08, FR-F020-06).
- **SR-S040-03:** The sweeper fires due timers within 60 seconds using `FOR UPDATE SKIP LOCKED`, sends F037 reminders, adds `escalate_to` (user, group, or manager) at `escalation_level + 1`, emits `approval.escalated.v1`, and stops after `max_escalations` (FR-F020-08, NFR-F020-04).
- **SR-S040-04:** On expiry with `auto_reject` or `auto_approve` the sweeper writes a system decision with reason `expired` and resolves the approval; with `none` reads return `overdue: true` (FR-F020-09).
- **SR-S040-05:** `POST /api/v1/approvals/{id}/reassign` by requester, editor, or the replaced approver swaps the approver, keeps other decisions, notifies the new approver, and rejects targets without read access (FR-F020-05).
- **SR-S040-06:** `ApprovalInboxPage` and `ApprovalDetailPage` list assigned approvals with due badges, show target summary, decisions, and escalation trail, offer approve, reject with required reason, and reassign to current approvers, and render loading, empty, error, denied, stale, and offline states (FR-F020-13, NFR-F020-03).
- **SR-S040-07:** Inbox over 100,000 approvals and a 10,000-timer sweep meet NFR-F020-01.

## Surfaces

- Infrastructure/container: none beyond F004 worker baseline
- Rust service/API: `crates/domain/src/approvals/{policy.rs, timers.rs, escalation.rs, service_routing.rs}`; `services/worker/src/approvals/{mod.rs, timer_sweeper.rs}`; `services/api/src/approvals/{handlers_policy.rs, handlers_reassign.rs}`
- Data/migration: none new; uses tables from S039
- React/UI: `apps/web/src/features/approvals/{ApprovalInboxPage.tsx, ApprovalList.tsx, ApprovalCard.tsx, DueBadge.tsx, ApprovalDetailPage.tsx, TargetSummary.tsx, ApproverList.tsx, DecisionHistory.tsx, EscalationTrail.tsx, DecideDialog.tsx, ReassignDialog.tsx, CancelApprovalDialog.tsx, RequestApprovalDialog.tsx, PolicyEditor.tsx, api.ts, hooks.ts, routes.ts}`
- Mocks/fixtures: policies `fast-track` and `standard`; manager relation stub; controllable clock; 100,000-approval generator; MSW handlers for component tests

## TDD harness

- Test path: `testing/features/F020/{api,frontend,e2e,accessibility,performance}/`
- Feature flag: `F020_FEATURE`
- Targeted command: `cargo xtask test-feature F020`
- Full command: `cargo xtask test-all`
- First failing tests: `policy_escalate_after_under_five_invalid`, `timers_scheduled_from_policy`, `sweeper_escalates_to_manager_once_per_level`, `expiry_auto_reject_writes_system_decision`, `reassign_keeps_other_decisions`, `reject_dialog_requires_reason`, `inbox_100k_p95`

## Exit criteria

- [ ] Requirement tests SR-S040-01 through SR-S040-07 written first and failing
- [ ] Tasks T079 and T080 complete; UI wired to real API through generated client; sweeper registered in the worker
- [ ] Unit, API, React, E2E, accessibility, permission, and performance tests pass
- [ ] Production call path named: `apps/web/src/features/approvals/ApprovalInboxPage.tsx` mounted at `/w/:workspaceId/approvals`; `services/worker/src/approvals/timer_sweeper.rs` registered in `services/worker/src/main.rs`
- [ ] Handoff evidence recorded in the F020 ticket
