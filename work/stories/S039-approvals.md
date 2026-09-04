---
id: S039
type: story
status: planned
parent_epic: E004
parent_feature: F020
depends_on: [F019, F037]
owned_paths: [crates/domain/src/approvals/**, crates/persistence/src/approvals/**, services/api/src/approvals/**, services/api/migrations/*_approvals_*.sql, testing/features/F020/**]
feature_flag: F020_FEATURE
branch: s039-approvals
started_at: null
finished_at: null
---

# S039 — Approvals

## Identity

- Parent feature: `F020` Approvals and escalation
- Owner: platform
- Branch: `s039-approvals`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4; `docs/capability-contracts.md` row F020

## Vertical slice

As a requester and an approver, I want to create an approval on a row with an approver set and quorum rule, decide it with a reason, and see the decision history, so that sign-off is captured as an auditable record and workflows can react to the outcome.

## Requirements

- **SR-S039-01:** `POST /api/v1/approvals` with `{ target, approvers, quorum, due_at?, policy_id?, context }` expands groups to at most 50 users, writes the `approvals` row with `quorum_kind`/`quorum_count` and `context_title`/`context_message` plus one `approval_approvers` row per resolved user through `ApprovalRepository` in one `UnitOfWork`, and returns `ApprovalResponse` with version 1 and the same nested `approvers`/`quorum`/`context` shape (covers FR-F020-01).
- **SR-S039-02:** Creation emits `approval.requested.v1` and one F037 notification per approver in category `approval`, excluding the requester unless listed (FR-F020-02).
- **SR-S039-03:** `POST /api/v1/approvals/{id}/decide` checks `ApprovalRepository::is_current_approver` and writes an immutable `approval_decisions` row through `record_decision`; a repeated decision returns `409 conflict`; a non-approver returns `403 denied`; reject without reason returns `400 invalid` (FR-F020-03).
- **SR-S039-04:** `resolve_quorum(rule, decisions)` completes `any` on the first approval, `all` when every approver approved, `count: n` on the `quorum_count`-th approval over the rows from `list_active_approvers`, and rejects on any rejection; completion emits `approval.decided.v1` and withdraws pending notifications (FR-F020-04).
- **SR-S039-05:** `POST /api/v1/approvals/{id}/cancel` sets `cancelled`, emits `approval.cancelled.v1`; decide on a non-pending approval returns `409 conflict` (FR-F020-06).
- **SR-S039-06:** `GET /api/v1/approvals` and `GET /api/v1/approvals/{id}` page, filter by `status`, `target_id`, `assigned_to_me` (a join on `approval_approvers` where `removed_at is null`, served by `page_for_approver`), `requested_by_me`, and enforce read access through the target ACL or approver membership; foreign tenants receive `404 not_found` (FR-F020-10, FR-F020-11).
- **SR-S039-07:** Every mutation requires `Idempotency-Key` and `If-Match`, writes an audit row, and links `correlation_id` and `run_id` when created by F019 (FR-F020-12, FR-F020-14).

## Surfaces

- Infrastructure/container: none beyond F004 baseline
- Rust service/API: `crates/domain/src/approvals/{approval.rs, decision.rs, quorum.rs, errors.rs, service.rs}` (types and use cases only, no SQL); `crates/persistence/src/approvals/{mod.rs, approval_repository.rs, approval_policy_repository.rs, escalation_timer_repository.rs}` holding every SQL statement; `services/api/src/approvals/{routes.rs, handlers_approval.rs, handlers_decide.rs, dto.rs}`
- Data/migration: `services/api/migrations/<ts>_approvals_create_tables.sql` creating `approvals`, `approval_approvers`, `approval_decisions`, `approval_policies`, `approval_policy_reminders`, `approval_policy_escalation_targets`, `escalation_timers` with indexes and the decision immutability trigger from ticket section 4
- React/UI: none in this story (S040 and T078 cover UI)
- Mocks/fixtures: `testing/fixtures/approvals.rs` requester, three approvers, group of four, foreign tenant; in-memory notification and outbox recorders

## TDD harness

- Test path: `testing/features/F020/api/`, `testing/features/F020/database/`, `testing/features/F020/requirements/`
- Feature flag: `F020_FEATURE`
- Targeted command: `cargo xtask test-feature F020`
- Full command: `cargo xtask test-all`
- First failing tests: `approval_create_expands_group_and_notifies`, `decide_by_non_approver_denied`, `reject_without_reason_invalid`, `count_quorum_completes_on_nth_approval`, `single_rejection_rejects_under_all_rules`, `approval_cross_tenant_not_found`, `active_approver_unique_per_approval`

## Exit criteria

- [ ] Requirement tests SR-S039-01 through SR-S039-07 written first and failing
- [ ] Tasks T077 and T078 complete and wired through `services/api` router
- [ ] Unit, API, database, permission tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/approvals/routes.rs` mounted in `services/api/src/router.rs`
- [ ] Handoff evidence recorded in the F020 ticket
