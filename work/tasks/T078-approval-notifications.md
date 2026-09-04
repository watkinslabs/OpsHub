---
id: T078
type: task
status: planned
parent_epic: E004
parent_feature: F020
parent_story: S039
depends_on: [T077]
owned_paths: [crates/domain/src/approvals/**, crates/persistence/src/approvals/**, services/api/src/approvals/**, testing/features/F020/api/**, testing/features/F020/requirements/**]
feature_flag: F020_FEATURE
branch: t078-approval-notifications
started_at: null
finished_at: null
---

# T078 — Approval notifications

## Identity

- Parent story: `S039` Approvals
- Owner: platform
- Branch: `t078-approval-notifications`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4; `docs/capability-contracts.md` row F020

## Objective

Implement the approval service and the create, get, list, decide, and cancel routes with authorization, idempotency, audit, outbox events, and F037 notification requests and withdrawals.

## Specification

- Owned paths: `crates/domain/src/approvals/{service.rs, notify.rs, access.rs}` (use cases over repository traits, no SQL), `crates/persistence/src/approvals/approval_repository.rs`, `services/api/src/approvals/{mod.rs, routes.rs, handlers_approval.rs, handlers_decide.rs, dto.rs}`
- Contract/input: `CreateApprovalRequest { target: { type, id }, approvers: [ { user_id } | { group_id } ], quorum: { any } | { all } | { count: n }, due_at?, policy_id?, context: { title, message } }`, `DecideRequest { decision, reason? }`, `CancelRequest { reason }`, list query `{ cursor?, limit? ≤ 200, filter[status]?, filter[target_type]?, filter[target_id]?, filter[assigned_to_me]?, filter[requested_by_me]?, filter[overdue]?, sort? }`; headers `Idempotency-Key`, `If-Match`.
- Output/behavior: routes `GET/POST /api/v1/approvals`, `GET /api/v1/approvals/{id}`, `POST /api/v1/approvals/{id}/decide`, `POST /api/v1/approvals/{id}/cancel` return `ApprovalResponse { id, target, requested_by, approvers: [ { user_id, source, state } ], quorum, due_at, status, outcome, decided_at, escalation_level, overdue, context, correlation_id, run_id, version, created_at, updated_at }` and `ApprovalDetailResponse` adding `decisions`, `escalations`, `timers`; `notify.rs` writes one F037 notification per approver (category `approval`, deep link `/approvals/{id}`) on create, reassign, and escalate, and withdraws pending ones on completion or cancel; `decide` takes the approval row lock through `ApprovalRepository::transition_status`, checks membership with `is_current_approver`, writes the decision with `record_decision`, applies the state machine, and emits `approval.decided.v1` on completion, all inside one `UnitOfWork`; the create path writes the approval, its `approval_approvers` rows, the audit row and the outbox event in the same `UnitOfWork`, and `list` serves `assigned_to_me` through `page_for_approver`; `access.rs` grants reads by target ACL or approver membership; events `approval.requested.v1`, `approval.decided.v1`, `approval.cancelled.v1` and audit rows in the same transaction; errors map per ticket section 4.
- Dependencies: T077 migration, repositories, and state machine; F003 authz; F004 outbox; F037 notification writer; F019 service actor identity for workflow-created approvals.
- Feature flag: `F020_FEATURE` gates router mounting.

## TDD

- Failing test first: `testing/features/F020/api/approval_tests.rs::approval_create_expands_group_and_notifies`, `::approval_create_excludes_requester_notification`, `::decide_by_non_approver_denied`, `::reject_without_reason_invalid`, `::second_decision_same_approver_conflicts`, `::completion_withdraws_pending_notifications`, `::cancel_emits_event_and_blocks_decide`, `::list_assigned_to_me_filters_by_membership`, `::removed_approver_no_longer_in_assigned_to_me`, `::approval_cross_tenant_not_found`, `::idempotent_replay_returns_original`, `::stale_version_conflicts`
- Targeted command: `cargo xtask test-feature F020`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/approvals.rs` tenants A and B, requester, approvers, group; in-memory notification and outbox recorders

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Router mounted in `services/api/src/router.rs` behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S039
- [ ] `finished_at` recorded
