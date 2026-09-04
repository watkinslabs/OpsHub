---
id: T080
type: task
status: planned
parent_epic: E004
parent_feature: F020
parent_story: S040
depends_on: [T079]
owned_paths: [apps/web/src/features/approvals/**, testing/features/F020/frontend/**, testing/features/F020/e2e/**, testing/features/F020/accessibility/**, testing/features/F020/performance/**]
feature_flag: F020_FEATURE
branch: t080-audit-tests
started_at: null
finished_at: null
---

# T080 — Audit tests

## Identity

- Parent story: `S040` Routing/escalation
- Owner: platform
- Branch: `t080-audit-tests`
- Decision references: `docs/architecture-decisions.md` sections 6, 9; `docs/capability-contracts.md` row F020

## Objective

Build the approvals inbox and detail UI and the end-to-end, accessibility, and performance lanes that prove every decision, reassignment, escalation, and expiry is visible in the UI and recorded in the audit trail.

## Specification

- Owned paths: `apps/web/src/features/approvals/{ApprovalInboxPage.tsx, ApprovalList.tsx, ApprovalCard.tsx, DueBadge.tsx, ApprovalDetailPage.tsx, TargetSummary.tsx, ApproverList.tsx, DecisionHistory.tsx, EscalationTrail.tsx, DecideDialog.tsx, ReassignDialog.tsx, CancelApprovalDialog.tsx, RequestApprovalDialog.tsx, PolicyEditor.tsx, api.ts, hooks.ts, routes.ts}`, `testing/features/F020/e2e/approvals.spec.ts`, `testing/features/F020/accessibility/approvals.a11y.spec.ts`, `testing/features/F020/performance/{inbox_bench.rs, sweep_bench.rs, decide_bench.rs}`
- Contract/input: generated `ApprovalsApi`; route params `workspaceId`, `approvalId`; query keys `['approvals', ...]`, `['approval', approvalId]`, `['approvals-pending-count', workspaceId]`; F037 in-app notification stream for count refresh.
- Output/behavior: inbox with `assigned_to_me` default filter, `DueBadge` with text and icon, cards under 768 px; detail with `TargetSummary`, `ApproverList` states, `DecisionHistory`, `EscalationTrail` rendered from the removed and escalation-sourced approver rows; `DecideDialog` requires a reason for reject and moves focus to the error; `ReassignDialog` with user picker; optimistic decide rolled back on `conflict`; `RequestApprovalDialog` embedded in the row panel; states loading, empty, error with correlation ID, denied read-only, not-found, stale, offline; keyboard `A`/`R`/`S`/`Enter`/`Escape`; telemetry `approval_requested`, `approval_opened`, `approval_decided`, `approval_reassigned`, `approval_escalation_viewed`. E2E asserts the audit trail through the F003 activity API after each step; benches assert inbox p95 < 500 ms over 100,000 approvals, 10,000-timer sweep < 60 s, decide p95 < 800 ms.
- Dependencies: T079 routes and sweeper; F003 activity read API for audit assertions; F006 row panel entry point; `testing/harness/` Playwright, axe, criterion runners.
- Feature flag: `F020_FEATURE` read through the flag hook; routes are not registered when off.

## TDD

- Failing test first: `testing/features/F020/frontend/DecideDialog.test.tsx::reject_dialog_requires_reason`, `ApprovalDetailPage.test.tsx::decide_rolls_back_on_conflict`, `::non_approver_sees_read_only`; `testing/features/F020/e2e/approvals.spec.ts::request_from_row_and_approve_from_inbox`, `::reject_with_reason_records_audit`, `::reassign_records_audit_and_notifies`, `::overdue_escalates_to_manager`, `::escalation_trail_shows_replaced_approver`; `testing/features/F020/accessibility/approvals.a11y.spec.ts::inbox_and_detail_have_no_serious_axe_violations`; `testing/features/F020/performance/inbox_bench.rs::inbox_100k_p95`, `sweep_bench.rs::sweep_10k_timers_under_60s`
- Targeted command: `cargo xtask test-feature F020`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: MSW handlers from the approval fixture; Playwright against seeded tenant with worker and clock control endpoint; 100,000-approval generator with seed `0x0F20`

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Component, E2E, accessibility, and performance lanes pass with evidence under `testing/evidence/F020/`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S040
- [ ] `finished_at` recorded
