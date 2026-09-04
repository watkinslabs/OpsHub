---
id: T077
type: task
status: planned
parent_epic: E004
parent_feature: F020
parent_story: S039
depends_on: [S039]
owned_paths: [services/api/migrations/*_approvals_*.sql, crates/domain/src/approvals/**, crates/persistence/src/approvals/**, testing/features/F020/database/**, testing/features/F020/api/**]
feature_flag: F020_FEATURE
branch: t077-approval-state-machine
started_at: null
finished_at: null
---

# T077 — Approval state machine

## Identity

- Parent story: `S039` Approvals
- Owner: platform
- Branch: `t077-approval-state-machine`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1; `docs/capability-contracts.md` row F020

## Objective

Create the approval tables with constraints and rollback and implement the pure domain state machine (approver set, quorum resolution, transitions) that every route and the sweeper reuse.

## Specification

- Owned paths: `services/api/migrations/<ts>_approvals_create_tables.sql`, `services/api/migrations/<ts>_approvals_create_tables.down.sql`, `crates/domain/src/approvals/{mod.rs, approval.rs, decision.rs, quorum.rs, transitions.rs, errors.rs}` (types and state machine only, no SQL), `crates/persistence/src/approvals/{mod.rs, approval_repository.rs, approval_policy_repository.rs, escalation_timer_repository.rs}`
- Contract/input: DDL per F020 ticket section 4: `approvals` (with `quorum_kind`/`quorum_count` and `context_title`/`context_message` replacing the old `quorum` and `context` documents), `approval_approvers`, `approval_decisions`, `approval_policies`, `approval_policy_reminders`, `approval_policy_escalation_targets`, `escalation_timers` with tenant/UUIDv7/version/audit columns, status and kind check constraints, partial unique `(approval_id, approver_id) where removed_at is null` and unique `(approval_id, position)` on approvers, unique `(approval_id, approver_id)` on decisions, `approval_decisions_immutable` trigger, unique `(approval_id, kind, level)` on timers, `approval_approvers(tenant_id, approver_id) where removed_at is null` replacing the GIN index that served `assigned_to_me`, partial index on unfired timers. `ApprovalRepository`, `ApprovalPolicyRepository` and `EscalationTimerRepository` implement the shared `Repository` contract and own every SQL statement against these tables. Rust: `Approval::apply_decision(&mut self, approver, decision, reason, now) -> Result<Transition, ApprovalError>`, `QuorumRule::resolve(&self, approvers, decisions) -> Option<Outcome>`, `Approval::reassign`, `Approval::cancel`, `Approval::escalate(to, level)`.
- Output/behavior: `sqlx migrate run` applies on an empty database and with F006/F045/F017 target tables present; `sqlx migrate revert` drops everything; the state machine is deterministic: `Pending → Approved|Rejected|Cancelled` only, decisions on non-pending return `NotPending`, duplicate approver decision returns `AlreadyDecided`, non-member returns `NotApprover`, any rejection resolves `Rejected` under every rule, `Count(n)` clamps to the approver count at creation and fails validation when `n` exceeds it.
- Dependencies: F006 `rows`, F045 `documents`, F017 `files` tables for target validation; F002 users and groups.
- Feature flag: `F020_FEATURE` (migration runs regardless; API routes are gated)
- Large-table note: no existing data; a new approver source is an additive value in the `approval_approvers.source` check constraint, and a new escalation target kind an additive value in `approval_policy_escalation_targets.target_kind`.

## TDD

- Failing test first: `testing/features/F020/database/migration_tests.rs::approval_tables_exist_with_constraints`, `::duplicate_decision_same_approver_rejected`, `::decision_update_rejected`, `::duplicate_timer_level_rejected`, `::active_approver_unique_per_approval`, `::approver_position_bounded_to_fifty`, `::manager_escalation_target_requires_null_target_id`, `::rollback_drops_tables`; `testing/features/F020/api/quorum_tests.rs::any_quorum_completes_on_first_approval`, `::all_quorum_waits_for_every_approver`, `::count_quorum_completes_on_nth_approval`, `::single_rejection_rejects_under_all_rules`, `::decide_on_cancelled_not_pending`
- Targeted command: `cargo xtask test-feature F020`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: schema-per-worker database from `testing/harness/db.rs`; pure unit tests need no mocks

## Exit criteria

- [ ] Tests written before the migration and state machine and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S039
- [ ] `finished_at` recorded
