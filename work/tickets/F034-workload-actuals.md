---
id: F034
type: feature
status: planned
priority: P1
owner: platform
estimate: 8
target_milestone: M6
parent_epic: E007
depends_on: [F033, F012]
blocks: []
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/workload/**, services/api/src/workload/**, services/worker/src/workload/**, apps/web/src/features/workload/**, services/api/migrations/*_workload_*.sql, testing/features/F034/**]
feature_flag: F034_FEATURE
flag_default: off
branch: f034-workload-actuals
started_at: null
finished_at: null
---

# F034 — Workload/actuals

## 1. Identity and dates

- Branch: `f034-workload-actuals`
- Capability area: workload balancing and actuals (spec 5.7 PPM-03 workload balancing and planned versus actual effort; low-level bullets on allocation actuals and allocation conflicts; section 10 "Resource actuals are native OpsHub time entries; imported actuals are marked external and cannot overwrite native entries without an audited reconciliation"; 5.6 REPORT-04 workload widget data)
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 7, 9; `docs/capability-contracts.md` row F034
- Module slug: `workload`

## 2. Requirement specification

### Problem and user outcome

Resource managers can see allocations (F033) but not where people are over-committed across projects, and nobody records what was actually worked. Actuals that arrive from external timesheet systems silently overwrite what people entered. They need a workload view across resources and periods, persistent conflict records with rebalancing suggestions, native time entries as the source of truth for actuals, an import path that marks external actuals and never overwrites native entries without an audited reconciliation, and planned versus actual effort and cost per task and project.

As a resource manager, I want to find and resolve over-allocation and compare planned effort and budget with recorded actuals, so that plans stay feasible and variances are visible early.

### Functional requirements

- **FR-F034-01:** `GET /api/v1/workload?from&to&granularity=week|day&resource_ids[]&project_sheet_id&skill` returns, for up to 500 resources over at most 182 days, one row per resource and period with `available_hours`, `allocated_hours`, `actual_hours`, `utilization_pct = allocated ÷ available × 100` (null when available is 0), and `status` in {`under` (< 70), `ok` (70–100), `over` (> 100), `no_capacity`}, plus per-period totals; more than 500 resources or 182 days returns `invalid`.
- **FR-F034-02:** The worker consumes `capacity.computed.v1` from F033 and, for the affected resource and span, upserts one `workload_conflicts` row per period where `allocated_hours > available_hours` with `over_hours`, the contributing `allocation_ids`, and `status: open`, publishes `workload-conflict.detected.v1` for each newly opened conflict, and sets `status: resolved` with `resolved_at` for periods no longer over-allocated.
- **FR-F034-03:** `GET /api/v1/workload/conflicts?resource_id&project_sheet_id&status&from&to` pages open and resolved conflicts and includes `suggestions` per conflict: allocations whose task row has `total_float_days > 0` in F012 `schedule_results` (`shift_within_float`), and up to three alternative active resources sharing a required skill with `remaining_hours ≥ over_hours` in that period (`reassign_to`).
- **FR-F034-04:** `POST /api/v1/time-entries` records a native entry with `resource_id`, `row_id` (and its `project_sheet_id`), `entry_date` not later than today in the tenant time zone, `hours` in 0.25–24 with quarter-hour steps, and optional `note` (≤ 500); a user linked to the resource (`self`) or a `resource-admin` may create it; the daily total for the resource may not exceed 24 hours (`invalid` with `field_errors.hours`); the entry stores `source: native` and a `cost_snapshot` from the resource's effective cost rate.
- **FR-F034-05:** `PATCH /api/v1/time-entries/{id}` and `DELETE` are allowed for the entry's own user within the tenant lock window (`time_entry_lock_days`, default 30) and for `resource-admin` at any time; other users receive `denied`; edits require `If-Match`; external entries cannot be patched except through reconciliation and return `conflict` with `code_detail: external_entry`.
- **FR-F034-06:** `POST /api/v1/time-entries/import` by a `resource-admin` accepts `source_system` (1–50 chars) and up to 2,000 entries of `{ external_id, resource_id | user_email, row_id, entry_date, hours, note? }`, is idempotent per `(source_system, external_id)` (a repeat updates the external entry rather than duplicating it), creates entries with `source: external`, and returns `{ created, updated, pending_reconciliation: [ids], rejected: [{ index, code }] }`.
- **FR-F034-07:** An imported entry whose `(resource_id, row_id, entry_date)` matches a native entry is stored with `reconciliation_state: pending` and excluded from actuals until reconciled; imported entries with no native counterpart are `accepted`; an external entry never modifies or deletes a native entry.
- **FR-F034-08:** `POST /api/v1/time-entries/reconcile` by a `resource-admin` takes `decisions[]` of `{ time_entry_id (pending external), resolution in {keep_native, accept_external, sum} }` and a `reason` (10–1,000 chars); `keep_native` marks the external entry `rejected`, `accept_external` marks the native entry `superseded` (retained, not deleted) and the external `accepted`, `sum` accepts the external and keeps both counting; each decision writes an audit event with before/after states and publishes `time-entry.reconciled.v1`; a decision on a non-pending entry returns `conflict`.
- **FR-F034-09:** `GET /api/v1/rows/{id}/effort?include_children=true|false` returns `planned_hours` (allocation hours attributed to the row plus the row's mapped `estimate_hours` column when no allocation exists), `actual_hours` (native plus accepted external, excluding `superseded` and `rejected`), `pending_external_hours`, `remaining_hours = max(0, planned − actual)`, `variance_hours`, `variance_pct`, `by_resource[]`, and, when `include_children` is true, the F009 descendant rollup; `planned_cost` and `actual_cost` are included only for `resource-admin`.
- **FR-F034-10:** The worker maintains `effort_summaries` for scopes `row`, `project`, and `resource_period` within 60 seconds of `time-entry.recorded.v1`, `time-entry.reconciled.v1`, `allocation.*.v1`, and `capacity.computed.v1`, recording `computed_at` and `source_versions`; reads serve from summaries and report `stale: true` when a newer source event is queued.
- **FR-F034-11:** Every mutation requires `Idempotency-Key` and writes an `audit_events` row; `time-entry.recorded.v1` is published for native create, patch, delete, and every imported entry with `changed_fields.source`; `time-entry.reconciled.v1` for each reconciliation decision; `workload-conflict.detected.v1` for each new open conflict.
- **FR-F034-12:** Cross-tenant access to any time entry, conflict, or effort read returns `not_found`; a `resource-viewer` can read workload, conflicts, and effort but receives `denied` on import, reconcile, and other users' entries; a user without `resource-viewer` sees only their own workload row and their own entries.
- **FR-F034-13:** The web workload page shows a resource-by-period heatmap with utilization text, a conflicts panel with suggestions and `Shift` and `Reassign` actions that call the F033 allocation API, a time entry sheet for the current user by day, a reconciliation queue for administrators, and a planned versus actual panel on each task row.
- **FR-F034-14:** Reconciliation history is immutable: reconciled entries keep `reconciled_by`, `reconciled_at`, `resolution`, and `reason`, and a superseded native entry remains readable with `superseded_by` pointing at the external entry.

### Non-functional requirements

- **NFR-F034-01 Performance:** workload for 1,000 resources over 12 weeks responds in under 500 ms p95 from summaries; conflict detection for a resource span completes within 30 seconds of `capacity.computed.v1`; native time entry create responds in under 800 ms p95; import of 2,000 entries completes in under 5 seconds (spec section 6).
- **NFR-F034-02 Security/privacy:** cost fields are filtered by role in the DTO layer; time entry notes are excluded from logs; external import cannot target resources outside the tenant (`invalid` per entry); cross-tenant, viewer, self-only, and non-admin reconciliation negatives are in the harness.
- **NFR-F034-03 Accessibility:** heatmap cells expose utilization as text and `meter` semantics, status is conveyed by text and icon, the time entry sheet is keyboard editable, dialogs trap focus, and axe reports no serious violations.
- **NFR-F034-04 Reliability/observability:** summary and conflict jobs are idempotent by `(scope_id, source_version)`, retried 3 times, and dead-lettered with `last_error`; import is atomic per request; spans carry `tenant_id`, `resource_id`, `row_id`, `time_entry_id`, `correlation_id`; metrics `workload_summary_lag_seconds` and `conflict_detection_ms` are exported.

### Scope

Included: workload query, conflict detection and records with suggestions, native time entries with lock window, external import with idempotency and pending reconciliation, audited reconciliation, effort and cost summaries per row, project, and resource period, workload page, conflicts panel, time entry sheet, reconciliation queue, planned versus actual panel.

Excluded: allocation editing itself (F033 API, called from the UI), capacity arithmetic (F033), schedule float computation (F012), workload dashboard widgets (F024), notification delivery for conflicts (F037), timesheet approval workflows and forecasting (E008 Resource Management module).

## 3. UX specification

- Entry points: workspace sidebar `Workload` → `/w/{workspace_id}/workload` (heatmap with `?from&to&granularity`), `/w/{workspace_id}/workload/conflicts`, `/w/{workspace_id}/time` (my time entries), `/w/{workspace_id}/workload/reconcile` (administrators); task row side panel tab `Effort`.
- Primary flow: manager opens `Workload`, sees a resource-by-week heatmap with `Over 125%` cells, opens `Conflicts`, sees `Ana, week of 12 Oct, over by 6 h` with suggestions `Shift "Design API" (float 4 d)` and `Reassign to Ben (12 h remaining)`, clicks `Shift`, adjusts the allocation dates in the F033 dialog, and the conflict resolves after recompute. An engineer opens `My time`, enters 6 h on `Design API` for today, saves. An administrator imports a timesheet file, sees three entries pending reconciliation, opens the queue, chooses `Keep native` with a reason, and the queue clears.
- Loading: skeleton heatmap and lists; Empty: `No conflicts` with check icon, `No time recorded this week`; Error: banner with `correlation_id`; Success: toasts for entry saved, import summary, reconciliation done; Stale: `Updating` badge on summaries while `stale: true`; Conflict: `This entry changed` with reload; Locked: entry rows older than the lock window show a lock icon and `Contact your resource administrator`; Denied: import and reconcile hidden; Offline: entry edits queued and disabled.
- Permission-denied: viewers see workload, conflicts, and effort without cost columns; non-viewers see only their own row and their own entries; non-members see not-found.
- Responsive: under 768 px the heatmap shows one week at a time and the time sheet becomes a day list.
- Keyboard: heatmap is a grid with arrow navigation and `Enter` opening the resource's conflicts; the time sheet supports `Tab` between day cells and `Enter` to save; dialogs trap focus; `prefers-reduced-motion` disables cell transitions.
- Font/icon/design tokens: Inter variable, Lucide icons `Activity`, `AlertTriangle`, `Clock`, `Upload`, `GitMerge`, `Lock`, `CheckCircle2`; tokens from `apps/web/src/design/tokens.css`.

## 4. Technical specification

### Rust backend

- Domain entities in `crates/domain/src/workload/`: `TimeEntry { id, tenant_id, resource_id, row_id, project_sheet_id, entry_date, hours: Decimal, note, source: EntrySource, external_ref: Option<ExternalRef { source_system, external_id }>, reconciliation_state: ReconciliationState, reconciled_by, reconciled_at, resolution, reason, superseded_by, cost_snapshot, version, audit fields, deleted_at }`, `WorkloadRow { resource_id, period_start, period_end, available_hours, allocated_hours, actual_hours, utilization_pct, status }`, `WorkloadConflict { id, tenant_id, resource_id, period_start, period_end, available_hours, allocated_hours, over_hours, allocation_ids, status, detected_at, resolved_at, version }`, `ConflictSuggestion { kind: ShiftWithinFloat { allocation_id, float_days } | ReassignTo { resource_id, remaining_hours } }`, `EffortSummary { scope, scope_id, period_start, period_end, planned_hours, actual_hours, pending_external_hours, available_hours, planned_cost, actual_cost, computed_at, source_versions, stale }`.
- Use cases: `query_workload`, `detect_conflicts`, `list_conflicts_with_suggestions`, `record_time_entry`, `update_time_entry`, `delete_time_entry`, `import_time_entries`, `reconcile_time_entries`, `get_row_effort`, `rebuild_summaries`.
- API endpoints (`services/api/src/workload/`): `GET /api/v1/workload`, `GET /api/v1/workload/conflicts`, `POST /api/v1/time-entries`, `PATCH /api/v1/time-entries/{id}`, `DELETE /api/v1/time-entries/{id}`, `GET /api/v1/rows/{id}/effort`, `POST /api/v1/time-entries/import`, `POST /api/v1/time-entries/reconcile`. DTOs: `WorkloadResponse { granularity, rows, totals }`, `Page<ConflictResponse>`, `CreateTimeEntryRequest`, `UpdateTimeEntryRequest`, `TimeEntryResponse`, `ImportTimeEntriesRequest`, `ImportResult`, `ReconcileRequest { decisions, reason }`, `ReconcileResult`, `EffortResponse`.
- Worker (`services/worker/src/workload/`): `conflict_detector.rs` consumes `capacity.computed.v1`; `summary_builder.rs` consumes `time-entry.recorded.v1`, `time-entry.reconciled.v1`, `allocation.*.v1`, `capacity.computed.v1` and rebuilds `effort_summaries` for the affected row, project, and resource periods; both idempotent by `(scope_id, source_version)`.
- Events: `time-entry.recorded.v1`, `time-entry.reconciled.v1`, `workload-conflict.detected.v1`; payload per contract conventions with `changed_fields`.
- Authorization: `self` (user linked to the resource) for own native entries; `resource-viewer` for workload, conflicts, and effort reads; `resource-admin` (F033 role) for import, reconcile, and entries of other users; cost fields via `ResponseScope::with_costs(actor)`; explicit deny wins; missing access maps to `not_found`.
- Validation: limits from FR-F034-01 through FR-F034-09; `entry_date ≤ today` in tenant time zone; quarter-hour steps; daily cap 24 h; reason 10–1,000 chars. Idempotency via `idempotency_keys` for 24 hours plus `(source_system, external_id)` for imports. Concurrency: `If-Match` on time entries.
- Error mapping: `WorkloadError::RangeTooLarge → 400 invalid`, `TimeEntryError::DailyCapExceeded → 400 invalid`, `TimeEntryError::FutureDate → 400 invalid`, `TimeEntryError::Locked → 403 denied`, `TimeEntryError::ExternalEntry → 409 conflict`, `TimeEntryError::NotPending → 409 conflict`, `TimeEntryError::StaleVersion → 409 conflict`, `TimeEntryError::NotFound → 404 not_found`, `AuthzError::Denied → 403 denied`.

### PostgreSQL/SQLx

- Migration `*_workload_*.sql` creates `time_entries(id uuid pk, tenant_id, resource_id uuid not null, row_id uuid not null, project_sheet_id uuid not null, entry_date date not null, hours numeric(5,2) not null, note text, source text not null, source_system text, external_id text, reconciliation_state text not null default 'none', reconciled_by uuid, reconciled_at timestamptz, resolution text, reason text, superseded_by uuid, cost_snapshot jsonb, version bigint, audit fields, deleted_at)`, `effort_summaries(tenant_id, scope text not null, scope_id uuid not null, period_start date, period_end date, planned_hours numeric(12,2), actual_hours numeric(12,2), pending_external_hours numeric(12,2), available_hours numeric(12,2), planned_cost numeric(18,2), actual_cost numeric(18,2), computed_at timestamptz not null, source_versions jsonb not null, stale bool not null default false, primary key (tenant_id, scope, scope_id, period_start))`, `workload_conflicts(id uuid pk, tenant_id, resource_id, period_start date, period_end date, available_hours numeric(10,2), allocated_hours numeric(10,2), over_hours numeric(10,2), allocation_ids uuid[] not null, status text not null default 'open', detected_at timestamptz not null, resolved_at timestamptz, version bigint, audit fields)`.
- Invariants: check `hours between 0.25 and 24 and (hours * 4) = floor(hours * 4)`; check `source in ('native','external')`; check `reconciliation_state in ('none','pending','accepted','rejected','superseded')`; check `(source = 'external') = (source_system is not null and external_id is not null)`; unique partial index `time_entries_external_ref_idx on (tenant_id, source_system, external_id) where source = 'external' and deleted_at is null`; unique `(resource_id, period_start)` on `workload_conflicts`; check `status in ('open','resolved')`; foreign keys to `resources(id)`, `rows(id)`, `sheets(id)` with `on delete restrict`; a statement trigger rejects `UPDATE` of `reconciled_by`, `reconciled_at`, `resolution`, or `reason` once set.
- Indexes: `time_entries(resource_id, entry_date) where deleted_at is null`, `time_entries(row_id, entry_date) where deleted_at is null`, `time_entries(project_sheet_id, entry_date)`, `time_entries(tenant_id, reconciliation_state) where reconciliation_state = 'pending'`, `effort_summaries(scope, scope_id, period_start)`, `workload_conflicts(tenant_id, status, period_start)`, `workload_conflicts(resource_id, status)`.
- Audit events: `time-entry.create`, `time-entry.update`, `time-entry.delete`, `time-entry.import`, `time-entry.reconcile` (with `resolution`, `reason`, before/after states), `workload-conflict.open`, `workload-conflict.resolve`.
- Retention/deletion: time entries soft-delete and are retained per tenant retention (F027); summaries are rebuildable and truncated on rollback; migration rollback drops the three tables and the trigger.

### React/TypeScript

- Routes: `/w/:workspaceId/workload`, `/w/:workspaceId/workload/conflicts`, `/w/:workspaceId/time`, `/w/:workspaceId/workload/reconcile` in `apps/web/src/features/workload/`; components `WorkloadPage`, `WorkloadHeatmap`, `HeatmapCell`, `ConflictsPanel`, `ConflictItem`, `SuggestionActions`, `TimeSheetPage`, `TimeEntryRow`, `TimeEntryDialog`, `ImportDialog`, `ReconcileQueuePage`, `ReconcileDecisionDialog`, `EffortPanel`.
- State: TanStack Query keys `['workload', filters]`, `['workload-conflicts', filters, cursor]`, `['time-entries', resourceId, from, to]`, `['row-effort', rowId, includeChildren]`; conflicts and effort refetch when `stale` is true every 5 seconds until fresh.
- API client: generated `WorkloadApi` with `getWorkload`, `listConflicts`, `createTimeEntry`, `updateTimeEntry`, `deleteTimeEntry`, `getRowEffort`, `importTimeEntries`, `reconcileTimeEntries`; `ResourcesApi.updateAllocation` from F033 for `Shift` and `Reassign`.
- Optimistic updates: time entry save applies locally and rolls back on `invalid` (daily cap) or `conflict`; reconciliation is server-truth only.
- Telemetry: `workload_viewed`, `conflict_suggestion_applied`, `time_entry_recorded`, `time_entries_imported`, `time_entries_reconciled`, `effort_panel_opened` with `resource_id`, `row_id`, `resolution`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F034-01 through FR-F034-14 in `testing/features/F034/requirements/cases.md`
- [ ] Failure/edge-case tests: 501 resources, 183-day range, daily cap, future date, locked entry, patch external entry, repeat import, decision on accepted entry, summary rebuild after dead letter
- [ ] Permission-negative and tenant-isolation tests: cross-tenant `not_found`, viewer import `denied`, other user's entry `denied`, non-viewer sees own row only, costs hidden
- [ ] Rust unit tests: `crates/domain/src/workload/` utilization and status thresholds, conflict diffing, suggestion ranking, effort arithmetic, reconciliation transitions
- [ ] API contract/integration tests: every route above with success and each error code
- [ ] Database migration/constraint tests: hours check, external ref uniqueness, reconciliation immutability trigger, conflict uniqueness, rollback
- [ ] React component tests: `WorkloadHeatmap`, `ConflictsPanel`, `TimeSheetPage`, `ReconcileQueuePage`, `EffortPanel` states
- [ ] Browser E2E tests: find and shift a conflict, record time, import and reconcile, planned versus actual on a row
- [ ] Accessibility tests: axe on all four pages, heatmap grid keyboard, meters, dialog focus
- [ ] Performance/load tests: 1,000-resource workload, conflict detection latency, entry create p95, 2,000-entry import

### Fast fanout configuration

- Test harness path: `testing/features/F034/`
- Feature flag: `F034_FEATURE`
- Fixture/seed factory: `testing/fixtures/workload.rs` builds tenant, workspace, resource-admin, resource-viewer, two linked users, foreign tenant, F033 resources with capacity and an over-allocated week, F012 schedule results with float on one task, native entries, and an external timesheet payload with one colliding entry
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, tenant time zone UTC
- Mock/stub contracts: outbox publisher recorded in memory; F033 capacity and F012 schedule services real against fixtures; in-process job runner
- Parallel isolation: one schema per test worker, tenant ID per test
- Targeted command: `cargo xtask test-feature F034`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F034/`

## 6. Acceptance criteria

```gherkin
Feature: Workload and actuals

Scenario: Conflict is detected with suggestions
  Given Ana has 16 available hours and 22 allocated hours in the week of 2026-10-12
  And task "Design API" has 4 days of float and Ben has a matching skill with 12 hours remaining
  When capacity.computed.v1 is consumed
  Then an open conflict with over_hours 6 exists and workload-conflict.detected.v1 is published
  And the conflict suggests shifting "Design API" and reassigning to Ben

Scenario: External actual does not overwrite native entry
  Given Ana recorded 6 native hours on "Design API" for 2026-09-02
  When an import contains 8 external hours for the same resource, task, and date
  Then the external entry is pending reconciliation and actual_hours remains 6

Scenario: Reconciliation is audited
  Given a pending external entry
  When an administrator reconciles with accept_external and reason "Timesheet system is authoritative"
  Then the native entry is superseded, actual_hours is 8
  And an audit event and time-entry.reconciled.v1 record the resolution and reason

Scenario: Viewer cannot import or reconcile
  Given a resource-viewer
  When they POST an import or a reconciliation
  Then the response is 403 denied and no entries change

Scenario: Cross-tenant effort read does not leak
  Given a task row in tenant A
  When a user from tenant B requests its effort
  Then the response is 404 not_found
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F033 (resources, allocations, capacity, `capacity.computed.v1`, `resource-admin` role), F012 (`schedule_results` float for shift suggestions); decisions sections 2–4, 7; contracts row F034
- Blocks: none
- Conflicts with: none (disjoint owned paths)
- External dependencies: none
- Risks and mitigations: workload over many resources cannot compute capacity on demand, so `resource_period` summaries are materialized by the worker and reads report `stale`; import collisions could hide hours, so pending entries are surfaced in the queue and counted separately as `pending_external_hours`; reconciliation reversals would erode trust, so decisions are immutable and a new import creates a new pending entry rather than reopening an old one.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F033 and F012 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F034/`
- [ ] Migration file name and owned paths claimed
- [ ] Fixture factory with over-allocated week, float, and colliding import available in `testing/fixtures/workload.rs`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, worker, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for every mutation, import, and reconciliation
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F034_FEATURE`, stop workload consumers, run down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Managers can see workload and over-allocation conflicts with shift and reassign suggestions; people record native time entries; imported actuals are marked external and reconciled under audit; tasks and projects show planned versus actual effort and cost.
- Migration adds `time_entries`, `effort_summaries`, and `workload_conflicts`; rollback drops them. Feature is off by default behind `F034_FEATURE`.
