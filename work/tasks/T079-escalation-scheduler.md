---
id: T079
type: task
status: planned
parent_epic: E004
parent_feature: F020
parent_story: S040
depends_on: [S040]
owned_paths: [crates/domain/src/approvals/**, crates/persistence/src/approvals/**, services/api/src/approvals/**, services/worker/src/approvals/**, testing/features/F020/api/**]
feature_flag: F020_FEATURE
branch: t079-escalation-scheduler
started_at: null
finished_at: null
---

# T079 — Escalation scheduler

## Identity

- Parent story: `S040` Routing/escalation
- Owner: platform
- Branch: `t079-escalation-scheduler`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 7; `docs/capability-contracts.md` row F020

## Objective

Implement approval policies, timer scheduling, the worker sweeper that sends reminders, escalates, and expires approvals, and the reassign and policy routes.

## Specification

- Owned paths: `crates/domain/src/approvals/{policy.rs, timers.rs, escalation.rs, service_routing.rs}` (no SQL), `crates/persistence/src/approvals/{approval_policy_repository.rs, escalation_timer_repository.rs}`, `services/worker/src/approvals/{mod.rs, timer_sweeper.rs}`, `services/api/src/approvals/{handlers_policy.rs, handlers_reassign.rs}`
- Contract/input: `UpsertPolicyRequest { name, default_due_minutes?, reminder_before_minutes: [int ≥ 5], escalate_after_minutes ≥ 5, escalate_to: { user_id } | { group_id } | { manager: true }, max_escalations 1–3, on_expiry }` (the request shape is unchanged; `ApprovalPolicyRepository` decomposes it into `approval_policy_reminders` and `approval_policy_escalation_targets` rows and recomposes it on read) via `PUT /api/v1/approval-policies/{id}`; `ReassignRequest { from_user_id, to_user_id, reason }` via `POST /api/v1/approvals/{id}/reassign`; sweeper runs every 30 seconds calling `EscalationTimerRepository::claim_due_timers(now, 500)`, whose `where fired_at is null and fire_at <= now() ... for update skip locked limit 500` claim lives in `crates/persistence`; the worker itself holds no SQL, and the same claim still hands each timer to exactly one sweeper.
- Output/behavior: `schedule_timers(approval, policy)` derives reminder rows at `due_at - reminder_before`, an `escalate` row at `created_at + escalate_after_minutes` per level, and an `expire` row at `due_at`; `fire_timer` sends the F037 reminder, or escalates by resolving the `approval_policy_escalation_targets` rows (manager from the F002 profile of the current pending approvers) and calling `add_escalation_approvers` to insert `approval_approvers` rows with `source = 'escalation'` at `level + 1` with `approval.escalated.v1`, or expires per `on_expiry` writing a system decision with reason `expired`; completion and cancel void unfired timers through `cancel_pending_timers`, and the 30-day cleanup runs `delete_fired_timers_older_than`; reassign calls `replace_approver`, which sets `removed_at` and `replaced_by_approver_id` on the outgoing row and inserts the replacement, keeps other decisions, notifies, audits, and rejects a target without read access with `invalid`; metrics `approval_escalated_total`, `approval_timer_lag_seconds` exported.
- Dependencies: T078 service and notifications; F004 worker baseline and metrics; F002 manager lookup.
- Feature flag: `F020_FEATURE` gates sweeper registration in `services/worker/src/main.rs` and the routes.

## TDD

- Failing test first: `testing/features/F020/api/escalation_tests.rs::policy_escalate_after_under_five_invalid`, `::timers_scheduled_from_policy`, `::sweeper_escalates_to_manager_once_per_level`, `::sweeper_stops_after_max_escalations`, `::reminder_sent_before_due`, `::expiry_auto_reject_writes_system_decision`, `::expiry_none_flags_overdue`, `::completion_voids_unfired_timers`, `::concurrent_sweepers_fire_timer_once`, `::policy_reminder_under_five_minutes_rejected_by_check`; `testing/features/F020/api/reassign_tests.rs::reassign_keeps_other_decisions`, `::reassign_to_user_without_access_invalid`, `::reassign_by_unrelated_user_denied`
- Targeted command: `cargo xtask test-feature F020`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: controllable clock with `advance()`; manager relation stub; two sweeper instances in one test for the lock case

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Sweeper registered behind the flag; policy and reassign routes mounted; OpenAPI without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S040
- [ ] `finished_at` recorded
