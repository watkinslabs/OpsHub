---
id: F020
type: feature
status: planned
priority: P1
owner: platform
estimate: 5
target_milestone: M3
parent_epic: E004
depends_on: [F019, F037]
blocks: [F032, F057, F040]
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/approvals/**, services/api/src/approvals/**, services/worker/src/approvals/**, apps/web/src/features/approvals/**, services/api/migrations/*_approvals_*.sql, testing/features/F020/**]
feature_flag: F020_FEATURE
flag_default: off
branch: f020-approvals-and-escalation
started_at: null
finished_at: null
---

# F020 — Approvals and escalation

## 1. Identity and dates

- Branch: `f020-approvals-and-escalation`
- Capability area: review and sign-off (spec 5.4b COLLAB-04 and the approval-instance low-level rule; 5.5 AUTO-02 approvals and routing; section 8 MVP scenario "routes it for approval")
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 7; `docs/capability-contracts.md` row F020
- Module slug: `approvals`

## 2. Requirement specification

### Problem and user outcome

A request that enters through a form or a status change often needs a decision from one or more people before work proceeds. Teams need an approval record with a defined approver set, a quorum rule, a due date, and an escalation path, so that decisions are captured with reasons, reassignable when someone is away, and visible in the audit trail. Workflows (F018/F019) request approvals and react to decisions; notifications (F037) tell approvers what to do.

As an approver, I want to receive approval requests with context, decide with a reason, reassign when needed, and know that overdue requests escalate, so that work never stalls silently on a missing sign-off.

### Functional requirements

- **FR-F020-01:** An actor with `workflow-editor` on the workspace, or the F019 service actor executing a `request_approval` action, can `POST /api/v1/approvals` with `target { type: row|document|file, id }`, `approvers` (1–20 user or group references, groups expanded at creation to at most 50 users), `quorum` (`any`, `all`, or `count: n` with `1 ≤ n ≤ approver count`), `due_at` (optional, at least 15 minutes ahead), `policy_id` (optional), and `context` (title ≤ 200 chars, message ≤ 2,000 chars); the response returns a UUIDv7 `id`, `status: pending`, and `version` 1.
- **FR-F020-02:** Creating an approval emits `approval.requested.v1` and creates one F037 notification per resolved approver in category `approval` with the approval deep link; the requester never receives an approver notification for their own request unless they are in the approver set.
- **FR-F020-03:** `POST /api/v1/approvals/{id}/decide` with `{ decision: approved|rejected, reason }` (reason required for `rejected`, ≤ 2,000 chars) by a current approver writes one `approval_decisions` row; a second decision by the same approver returns `conflict`, and a decision by a non-approver returns `denied`.
- **FR-F020-04:** The quorum rule resolves the approval: `any` completes on the first `approved`; `all` completes when every approver has approved; `count: n` completes on the n-th `approved`; any single `rejected` moves the approval to `rejected` immediately under all rules; completion sets `status`, `decided_at`, emits `approval.decided.v1` with `outcome`, and publishes it so `approval_decided` workflow triggers (F018/F019) fire.
- **FR-F020-05:** `POST /api/v1/approvals/{id}/reassign` with `{ from_user_id, to_user_id, reason }` by the requester, a `workflow-editor`, or the `from_user_id` approver replaces the approver in the set, preserves decisions already made by others, notifies the new approver, and writes an audit row; reassigning to a user without read access to the target returns `invalid` with `field_errors.to_user_id`.
- **FR-F020-06:** `POST /api/v1/approvals/{id}/cancel` with `{ reason }` by the requester or a `workflow-editor` sets `status: cancelled`, emits `approval.cancelled.v1`, and cancels pending escalation timers; decide and reassign on a non-pending approval return `conflict`.
- **FR-F020-07:** An `approval_policies` row (`PUT /api/v1/approval-policies/{id}` by `workflow-editor`) defines `default_due_minutes`, `reminder_before_minutes` (list, each ≥ 5), `escalate_after_minutes` (≥ 5), `escalate_to` (user, group, or `manager` resolved from F002 profile), `max_escalations` (1–3), and `on_expiry: none|auto_reject|auto_approve`; a policy applies to approvals created with its `policy_id`.
- **FR-F020-08:** When an approval is created with a policy or `due_at`, `escalation_timers` rows are scheduled for each reminder and for the escalation; the worker fires due timers within 60 seconds, sends F037 reminders, and on escalation adds `escalate_to` to the approver set, records `escalation_level`, emits `approval.escalated.v1`, and reschedules up to `max_escalations`.
- **FR-F020-09:** When `due_at` passes with the approval still `pending` and the policy's `on_expiry` is `auto_reject` or `auto_approve`, the worker records a system decision with reason `expired` and resolves the approval accordingly; with `none` it stays `pending` and is flagged `overdue: true` in reads.
- **FR-F020-10:** `GET /api/v1/approvals` pages by cursor with `filter` on `status`, `target_type`, `target_id`, `assigned_to_me`, `requested_by_me`, `overdue` and `sort` by `due_at` or `created_at`; `GET /api/v1/approvals/{id}` returns the approver set with per-approver state, decisions, escalation history, timers, and `overdue`.
- **FR-F020-11:** Reads of an approval require read access to its target through the target's ACL or membership in the approver set; a foreign tenant or a user with neither returns `not_found`.
- **FR-F020-12:** Every decision, reassignment, escalation, expiry, and cancellation writes an append-only `audit_events` row with actor, before/after status, reason, and correlation ID linking back to the originating workflow run when present.
- **FR-F020-13:** The approvals inbox lists approvals assigned to the actor with due and overdue indicators, opens a detail view with the target summary, decision history, and escalation state, and offers `Approve`, `Reject` (reason required), and `Reassign` to current approvers; non-approvers see the detail read-only, and cancelled or decided approvals show their outcome.
- **FR-F020-14:** Every mutation requires `Idempotency-Key` and `If-Match` version; a stale version returns `conflict` with the current version, and replaying the same key with the same body returns the original response.

### Non-functional requirements

- **NFR-F020-01 Performance:** create and decide respond in under 800 ms p95 including notification enqueue; inbox list p95 under 500 ms with 100,000 approvals in a tenant; timer sweep processes 10,000 due timers in under 60 seconds.
- **NFR-F020-02 Security/privacy:** decisions are attributable only to the authenticated approver or the system expiry actor; group expansion is snapshotted at creation so later group edits cannot add approvers silently; guests can approve only when explicitly listed and scoped by F036; cross-tenant IDs return `not_found`.
- **NFR-F020-03 Accessibility:** inbox and detail pass axe with no serious violations; due/overdue state uses text and icon; the reject dialog labels the required reason and moves focus to the first error.
- **NFR-F020-04 Reliability/observability:** timers are persisted rows swept by a single-writer worker task with `FOR UPDATE SKIP LOCKED`, so a worker restart never loses or duplicates an escalation; metrics `approval_created_total`, `approval_decided_total{outcome}`, `approval_escalated_total`, `approval_timer_lag_seconds` are exported; spans carry `tenant_id`, `approval_id`, `correlation_id`.

### Scope

Included: approval creation with approver sets and quorum rules, decisions with reasons, reassignment, cancellation, policies, reminders, escalation timers, expiry behaviour, inbox and detail UI, events, audit, notification requests through F037.

Excluded: notification channel delivery and preferences (F037); workflow authoring of the `request_approval` action (F018) and its execution (F019); stage-gate governance built on approvals (F032); asset approval flows (F057); assisted decisions (F040).

## 3. UX specification

- Entry points: global nav `Approvals` badge with pending count; route `/w/{workspace_id}/approvals` (inbox) and `/approvals/{approval_id}` (detail); row detail panel `Request approval` button; notification deep links.
- Primary flow: approver opens the inbox from the notification, sees the request "Approve vendor contract" due in 2 days, opens it, reads the row summary and message, clicks `Approve`, confirms, sees status `Approved` and the requester is notified; a rejecting approver must enter a reason before `Reject` enables.
- Loading: skeleton list; Empty: `Nothing waiting for you`; Error: banner with `correlation_id` and retry; Success: toast `Approved` / `Rejected` / `Reassigned`; Stale/conflict: banner `This approval was already decided` with reload; Offline: decision buttons disabled with offline badge.
- Permission-denied: non-approvers see read-only detail with an explanation; no target access renders not-found.
- Responsive: inbox becomes cards under 768 px; detail stacks target summary above decisions.
- Keyboard: arrow keys move between inbox items, `Enter` opens, `A` approve, `R` reject, `S` reassign on a focused approval, `Escape` closes dialogs; focus ring from shared token; `prefers-reduced-motion` disables badge pulse.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062); Lucide icons `CheckCircle2`, `XCircle`, `UserRoundCog`, `Clock`, `AlertTriangle`, `Ban`; tokens from `apps/web/src/design/tokens.css`.

## 4. Technical specification

### Rust backend

- Domain entities in `crates/domain/src/approvals/`: `Approval { id, tenant_id, workspace_id, target: ApprovalTarget, requested_by, approvers: Vec<Approver>, quorum: QuorumRule, policy_id, due_at, status: ApprovalStatus, outcome, decided_at, escalation_level, context, correlation_id, run_id, version, audit fields }`, `Approver { user_id, source: Direct|Group(group_id)|Escalation(level)|Reassigned(from), state: Pending|Approved|Rejected|Replaced }`, `ApprovalDecision { id, approval_id, approver_id, decision, reason, decided_at, system: bool }`, `ApprovalPolicy { id, tenant_id, name, default_due_minutes, reminder_before_minutes, escalate_after_minutes, escalate_to, max_escalations, on_expiry }`, `EscalationTimer { id, tenant_id, approval_id, kind: Reminder|Escalate|Expire, fire_at, fired_at, level }`, `QuorumRule::{Any, All, Count(u8)}`, `ApprovalStatus::{Pending, Approved, Rejected, Cancelled}`.
- Use cases: `create_approval`, `decide`, `resolve_quorum`, `reassign`, `cancel`, `upsert_policy`, `schedule_timers`, `fire_timer`, `escalate`, `expire`, `get_approval`, `list_approvals`.
- Worker (`services/worker/src/approvals/`): `timer_sweeper.rs` polls `escalation_timers` every 30 seconds with `FOR UPDATE SKIP LOCKED`, calls `fire_timer`, and enqueues F037 notifications through the outbox.
- API endpoints (`services/api/src/approvals/`): `GET /api/v1/approvals`, `POST /api/v1/approvals`, `GET /api/v1/approvals/{id}`, `POST /api/v1/approvals/{id}/decide`, `POST /api/v1/approvals/{id}/reassign`, `POST /api/v1/approvals/{id}/cancel`, `PUT /api/v1/approval-policies/{id}`. DTOs: `CreateApprovalRequest`, `DecideRequest`, `ReassignRequest`, `CancelRequest`, `UpsertPolicyRequest`, `ApprovalResponse`, `ApprovalDetailResponse`, `PolicyResponse`, `Page<ApprovalResponse>`.
- Events: `approval.requested.v1`, `approval.decided.v1` (with `outcome`, `decisions`, `run_id`), `approval.escalated.v1` (with `level`, `escalated_to`), `approval.cancelled.v1`.
- Authorization: create by `workflow-editor` or the F019 service actor; decide by a current approver in `Pending` state; reassign by requester, `workflow-editor`, or the replaced approver; cancel by requester or `workflow-editor`; policies by `workflow-editor`; reads by target ACL or approver membership; explicit deny wins.
- Validation: approvers 1–20 references, expanded set ≤ 50; `count` within range; `due_at` ≥ now + 15 minutes; reason required on reject; `escalate_after_minutes` ≥ 5; `max_escalations` 1–3. Idempotency in `idempotency_keys` for 24 hours; `If-Match` checked inside the transaction.
- Error mapping: `ApprovalError::NotApprover → 403 denied`, `ApprovalError::AlreadyDecided → 409 conflict`, `ApprovalError::NotPending → 409 conflict`, `ApprovalError::StaleVersion → 409 conflict`, `ApprovalError::NotFound → 404 not_found`, validation → `400 invalid` with `field_errors`, `AuthzError::Denied → 403 denied`.

### PostgreSQL/SQLx

- Migration `*_approvals_*.sql` creates `approvals(id uuid pk, tenant_id uuid not null, workspace_id uuid not null, target_type text not null check (target_type in ('row','document','file')), target_id uuid not null, requested_by uuid not null, approvers jsonb not null, quorum jsonb not null, policy_id uuid null, due_at timestamptz null, status text not null check (status in ('pending','approved','rejected','cancelled')), outcome text null, decided_at timestamptz null, escalation_level int not null default 0, context jsonb not null, correlation_id uuid not null, run_id uuid null, version bigint not null default 1, created_by, created_at, updated_by, updated_at)`, `approval_decisions(id uuid pk, tenant_id, approval_id not null, approver_id uuid not null, decision text not null check (decision in ('approved','rejected')), reason text, system bool not null default false, decided_at timestamptz not null)`, `approval_policies(id uuid pk, tenant_id, name text not null, default_due_minutes int, reminder_before_minutes int[] not null default '{}', escalate_after_minutes int not null, escalate_to jsonb not null, max_escalations int not null check (max_escalations between 1 and 3), on_expiry text not null check (on_expiry in ('none','auto_reject','auto_approve')), version bigint not null default 1, audit fields)`, `escalation_timers(id uuid pk, tenant_id, approval_id not null, kind text not null check (kind in ('reminder','escalate','expire')), level int not null default 0, fire_at timestamptz not null, fired_at timestamptz null, created_at)`.
- Invariants: unique `approval_decisions(approval_id, approver_id)`; `approval_decisions` has no `updated_at` and a trigger `approval_decisions_immutable` raises on `UPDATE`/`DELETE`; unique `escalation_timers(approval_id, kind, level)`; `policy_id` references `approval_policies(id)`; unique `approval_policies(tenant_id, lower(name))`.
- Indexes: `approvals(tenant_id, status, due_at)`, `approvals(tenant_id, target_type, target_id)`, GIN `approvals using gin ((approvers) jsonb_path_ops)` for `assigned_to_me`, `approvals(tenant_id, requested_by, created_at desc)`, `escalation_timers(fire_at) where fired_at is null`.
- Audit events: `approval.create`, `approval.decide`, `approval.reassign`, `approval.escalate`, `approval.expire`, `approval.cancel`, `approval-policy.upsert` with before/after status and reason.
- Retention/deletion: approvals are retained with their target and purged by the F027 job on target purge; decisions are never edited; fired timers older than 30 days are deleted by the sweeper; rollback drops the four tables and the trigger.

### React/TypeScript

- Routes in `apps/web/src/features/approvals/`: `/w/:workspaceId/approvals`, `/approvals/:approvalId`; components `ApprovalInboxPage`, `ApprovalList`, `ApprovalCard`, `DueBadge`, `ApprovalDetailPage`, `TargetSummary`, `ApproverList`, `DecisionHistory`, `EscalationTrail`, `DecideDialog`, `ReassignDialog`, `CancelApprovalDialog`, `RequestApprovalDialog` (embedded in the row panel), `PolicyEditor`.
- State: TanStack Query keys `['approvals', workspaceId, filters, cursor]`, `['approval', approvalId]`, `['approval-policy', policyId]`, `['approvals-pending-count', workspaceId]` refreshed on `approval.*` notifications from F037.
- API client: generated `ApprovalsApi` with `listApprovals`, `createApproval`, `getApproval`, `decideApproval`, `reassignApproval`, `cancelApproval`, `upsertPolicy`.
- Optimistic updates: decide marks the approver state locally and rolls back on `conflict` with the already-decided banner.
- Telemetry: `approval_requested`, `approval_opened`, `approval_decided`, `approval_reassigned`, `approval_escalation_viewed` with `approval_id`, `quorum`, `outcome`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F020-01 through FR-F020-14 in `testing/features/F020/requirements/cases.md`
- [ ] Failure/edge-case tests: 21 approvers, group expansion over 50, `count` above approver count, due in 5 minutes, reject without reason, double decision, decide after cancel, reassign to user without access, fourth escalation
- [ ] Permission-negative and tenant-isolation tests: non-approver decide returns `denied`, foreign tenant returns `not_found`, guest not in set cannot read
- [ ] Rust unit tests: `crates/domain/src/approvals/` quorum resolution table, timer schedule derivation, escalation target resolution
- [ ] API contract/integration tests: every route above with success and each error code
- [ ] Database migration/constraint tests: decision uniqueness and immutability, timer uniqueness, policy constraints, rollback
- [ ] React component tests: `ApprovalInboxPage`, `ApprovalDetailPage`, `DecideDialog`, `ReassignDialog` states
- [ ] Browser E2E tests: request from a row, approve from the inbox, reject with reason, reassign, escalation after due
- [ ] Accessibility tests: axe on inbox and detail, due state not color-only, reject reason focus
- [ ] Performance/load tests: 100,000-approval inbox, 10,000 due timers per sweep, decide p95

### Fast fanout configuration

- Test harness path: `testing/features/F020/`
- Feature flag: `F020_FEATURE`
- Fixture/seed factory: `testing/fixtures/approvals.rs` builds tenant, workspace, sheet row target, requester, three approvers, one group of four users, a manager relation, foreign tenant, and two policies (`fast-track`, `standard`)
- Deterministic test data: fixed UUIDv7 seeds, controllable clock `2026-09-03T00:00:00Z` with `advance()`, timezone `UTC`
- Mock/stub contracts: F037 notification outbox recorded in memory; F019 event publisher recorded; F002 manager lookup stubbed from fixture
- Parallel isolation: one schema per test worker, tenant ID per test
- Targeted command: `cargo xtask test-feature F020`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F020/`

## 6. Acceptance criteria

```gherkin
Feature: Approvals and escalation

Scenario: Count quorum resolves on the second approval
  Given an approval on row "Vendor contract" with approvers Ana, Ben, Cai and quorum count 2
  When Ana approves and Ben approves
  Then the approval is approved with decided_at set
  And approval.decided.v1 with outcome approved is in the outbox and Cai's pending notification is withdrawn

Scenario: Rejection requires a reason
  Given a pending approval assigned to Ben
  When Ben decides rejected without a reason
  Then the response is 400 invalid with field_errors.reason

Scenario: Non-approver cannot decide
  Given a pending approval assigned to Ana and Ben
  When Dee, who can read the row but is not an approver, decides approved
  Then the response is 403 denied and no decision row exists

Scenario: Overdue approval escalates to the manager
  Given policy "standard" escalating to manager after 60 minutes with max 2 escalations
  And an approval created with that policy and no decision
  When the clock advances 61 minutes and the sweeper runs
  Then the manager is added to the approver set at level 1
  And approval.escalated.v1 is in the outbox and a reminder notification is queued

Scenario: Cross-tenant read does not leak
  Given an approval in tenant A
  When an approver from tenant B requests it by id
  Then the response is 404 not_found
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F019 (`request_approval` executor, `approval.decided.v1` consumption, correlation with runs), F037 (notification creation and withdrawal); decisions sections 2–4, 7; contracts row F020
- Blocks: F032, F057, F040
- Conflicts with: none (disjoint owned paths)
- External dependencies: none; manager resolution uses F002 profile fields
- Risks and mitigations: two approvers deciding at the same instant could both appear to complete a `count` quorum, so `decide` locks the approval row `FOR UPDATE` and resolves the quorum inside the transaction; timers could fire twice across workers, so the sweeper uses `SKIP LOCKED` and sets `fired_at` in the same transaction; group membership drift is avoided by snapshotting the expanded set.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F019 and F037 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F020/`
- [ ] Migration file name and owned paths claimed
- [ ] Fixture factory `testing/fixtures/approvals.rs` and controllable clock available in `testing/harness/`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for every mutation and timer action
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F020_FEATURE` (sweeper stops, pending approvals preserved), run down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Users can request approvals on rows, documents, and files with quorum rules, due dates, reminders, escalation, reassignment, and a full decision history; workflows react to decisions.
- Migration adds `approvals`, `approval_decisions`, `approval_policies`, and `escalation_timers`; rollback drops them. Feature is off by default behind `F020_FEATURE`.
