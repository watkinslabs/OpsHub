---
id: T158
type: task
status: planned
parent_epic: E008
parent_feature: F040
parent_story: S079
depends_on: [S079]
owned_paths: [crates/domain/src/ai-insights/**, crates/persistence/src/ai-insights/**, services/api/src/ai-insights/**, services/worker/src/ai-insights/**, testing/features/F040/api/**, testing/features/F040/e2e/**]
feature_flag: F040_FEATURE
branch: t158-approval-gate
started_at: null
finished_at: null
---

# T158 — Approval gate

## Identity

- Parent story: `S079` Risks and trends
- Owner: platform
- Branch: `t158-approval-gate`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 7; `docs/capability-contracts.md` row F040

## Objective

Implement the `ai_actions` state machine and the confirm and reject routes so that no AI-proposed change can execute without a human confirmation that matches the preview they saw, with high-risk proposals escalated to an F020 approval.

## Specification

- Owned paths: `crates/domain/src/ai-insights/{action.rs, gate.rs, risk.rs, preview.rs}`; `crates/persistence/src/ai-insights/action_repository.rs`; `services/api/src/ai-insights/handlers_action.rs` and the confirm/reject DTOs in `services/api/src/ai-insights/dto.rs`; `services/worker/src/ai-insights/approval_listener.rs`
- Contract/input: `ConfirmRequest { preview_hash: String }` with `Idempotency-Key` and `If-Match: <version>`; `RejectRequest { reason: String }`; the consumed event `approval.decided.v1` carrying `{ approval_id, decision, decided_by, decided_at }`.
- Output/behavior: routes `POST /api/v1/ai/actions/{id}/confirm` and `POST /api/v1/ai/actions/{id}/reject`. `gate.rs` owns the only transition into `confirmed`: it requires role `workflow-editor`, `PrincipalKind::User` (a service or API token yields `403 denied` with `reason: human_confirmation_required`), a matching `If-Match` version, and `preview_hash` equal to the stored `sha256` of the canonical preview; a mismatch returns `409 conflict` with the re-rendered diff, and a proposal past `expires_at` returns `409 conflict` with `reason: proposal_expired` and sets `status: expired`. `risk.rs` classifies `create_workflow_draft`, `request_approval`, and `target_count > 5` as `high`; confirming a high proposal calls F020 `POST /api/v1/approvals` with the preview attached, stores `approval_id`, and leaves `status: awaiting_approval`. `approval_listener.rs` moves the action to `confirmed` on an approved decision and to `rejected` on a denied decision, publishing `ai-action.confirmed.v1` or `ai-action.rejected.v1`. Reject sets `rejected_by`, `rejected_at`, `reject_reason`, publishes `ai-action.rejected.v1`, and returns `409 conflict` when the action is already `applied`. The `AiAction::confirm` constructor is private to `gate.rs` so no other module can construct a confirmed action; audit events `ai-action.confirmed` and `ai-action.rejected` are written on every transition.
- Data access: `gate.rs`, `risk.rs`, `preview.rs`, `handlers_action.rs`, and `approval_listener.rs` hold no SQL — every state read and transition goes through `AiActionRepository` in `crates/persistence/src/ai-insights/action_repository.rs`, which owns `ai_actions` and `ai_action_targets` and exposes `get_for_confirm`, `list_action_targets`, `mark_awaiting_approval`, `mark_confirmed`, `mark_rejected`, `expire_proposals`, and `find_by_approval_id`; the version check, the status transition, the audit row, and the outbox enqueue for one confirmation are a single `UnitOfWork` write, and the F020 approval row is created through the F020 repository in that same unit (decision section 2.1).
- Dependencies: T157 for `ai_actions`/`ai_action_targets`/`ai_action_runs` DDL and the insight aggregate; F020 approvals and `approval.decided.v1`; F003 authz for `workflow-editor` and principal kind; F028 idempotency and concurrency conventions.
- Feature flag: `F040_FEATURE` gates both routes and the listener.

## TDD

- Failing test first: `testing/features/F040/api/gate_tests.rs::confirm_requires_human_principal`, `::confirm_requires_workflow_editor_role`, `::confirm_rejects_stale_preview_hash_with_rerendered_diff`, `::confirm_rejects_expired_proposal_and_marks_expired`, `::confirm_rejects_stale_if_match_version`, `::confirm_publishes_ai_action_confirmed_v1`, `::confirm_is_idempotent_for_repeated_key`; `testing/features/F040/api/risk_tests.rs::create_workflow_draft_is_high_risk`, `::six_targets_is_high_risk`, `::high_risk_confirm_requests_approval_before_running`, `::approval_denied_marks_action_rejected`; `testing/features/F040/api/reject_tests.rs::reject_records_reason_and_publishes_event`, `::reject_applied_action_returns_conflict`, `::foreign_tenant_action_returns_not_found`; `testing/features/F040/e2e/approval_gate.spec.ts::confirm_dialog_restates_target_count_and_risk`
- Targeted command: `cargo xtask test-feature F040`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/ai_insights.rs` seeded pending proposals at `low` and `high` risk, an expired proposal, and a proposal whose targets changed after preview; an in-process F020 approval service; a service-token principal; fixed clock `2026-09-03T00:00:00Z`

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] `grep` proves no construction of a confirmed `AiAction` outside `gate.rs`; the negative test for service-token confirmation passes
- [ ] Routes and the approval listener registered behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check, file limit, lint, and audit-event gates pass
- [ ] Handoff evidence recorded in S079
- [ ] `finished_at` recorded
