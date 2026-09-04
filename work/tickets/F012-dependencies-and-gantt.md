---
id: F012
type: feature
status: planned
priority: P1
owner: platform
estimate: 8
target_milestone: M2
parent_epic: E003
depends_on: [F009, F011]
blocks: [F015, F034]
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/dependencies/**, services/api/src/dependencies/**, apps/web/src/features/dependencies/**, services/api/migrations/*_dependencies_*.sql, testing/features/F012/**]
feature_flag: F012_FEATURE
flag_default: off
branch: f012-dependencies-and-gantt
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 6
- Capability contract: `docs/capability-contracts.md` row F012

# F012 — Dependencies and Gantt

## 1. Identity and dates

- Branch: `f012-dependencies-and-gantt`
- Capability area: planning (spec 5.1 WORK-04, Gantt low-level bullet: dependency validation, working calendar, lag, parent roll-up, milestone marker, baseline overlay, critical-path calculation; section 4 `Dependency` entity: predecessor, successor, type, lag)
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 6; `docs/capability-contracts.md` row F012
- Aggregate: `dependency`
- Module slug: `dependencies`

## 2. Requirement specification

### Problem and user outcome

A project sheet has dated rows but no way to express that one task must wait for another. Planners re-enter dates by hand whenever a predecessor slips, and nobody can see which tasks decide the end date. This feature adds typed dependency links between rows of one sheet, validates them against cycles, computes the critical path with working-calendar arithmetic from F011, and propagates a date shift through successors in one operation, visible in a Gantt view.

As a project editor, I want to link tasks with FS/SS/FF/SF dependencies and lag, see the critical path, and shift a task or the whole schedule with successors following working days, so that my plan stays consistent without manual date edits.

### Functional requirements

- **FR-F012-01:** An actor with `project-editor` on the sheet can create a dependency with `predecessor_row_id`, `successor_row_id`, `kind` in `FS|SS|FF|SF`, `lag` (signed integer, default 0), and `lag_unit` in `days|hours` (default `days`); the response carries a UUIDv7 `id` and `version` 1, and `dependency.created.v1` is published.
- **FR-F012-02:** Both rows must belong to the same sheet, must not be soft-deleted, and must differ; a cross-sheet pair returns `400 invalid` with `field_errors.successor_row_id = "different_sheet"`, and a self-link returns `400 invalid` with `field_errors.successor_row_id = "self"`.
- **FR-F012-03:** Creating or updating a dependency that would close a cycle returns `400 invalid` with `field_errors.successor_row_id = "cycle"` and `details.cycle_path` listing the row IDs of the cycle in traversal order; no write occurs.
- **FR-F012-04:** A second dependency for the same `(predecessor_row_id, successor_row_id)` pair returns `409 conflict` with `field_errors.successor_row_id = "duplicate"` and the existing dependency `id` in `details.existing_id`.
- **FR-F012-05:** A sheet holds at most 20,000 dependencies; the 20,001st create returns `400 invalid` with `field_errors.sheet_id = "limit"`.
- **FR-F012-06:** `GET /api/v1/sheets/{sheet_id}/dependencies` pages by cursor in `(predecessor_row_id, successor_row_id)` order, `limit` up to 1,000, and filters by `row_id` (either side) and `kind`; `PATCH` changes `kind`, `lag`, `lag_unit` with `If-Match`; `DELETE` removes the link and both emit their `dependency.*.v1` events.
- **FR-F012-07:** Lag is a working-time offset: positive lag delays the successor, negative lag (lead) advances it, `days` lag counts working days of the sheet calendar, and `hours` lag counts working hours from the calendar's daily working window; lag is bounded to ±3,650 days or ±87,600 hours.
- **FR-F012-08:** `GET /api/v1/sheets/{sheet_id}/critical-path` returns, for every scheduled row, `early_start`, `early_finish`, `late_start`, `late_finish`, `total_float_days`, `is_critical` (total float 0), and `schedule_version`; the result is computed by a forward and backward pass over the dependency graph using `add_working_days` and `working_days_between` from F011 with the sheet calendar and timezone.
- **FR-F012-09:** Parent rows (F009 hierarchy) roll up `early_start` as the minimum and `early_finish` as the maximum of their descendants and cannot be a predecessor or successor themselves; a link to a parent row returns `400 invalid` with `field_errors.predecessor_row_id = "parent_row"` or the successor equivalent.
- **FR-F012-10:** A row whose duration column is 0 is a milestone: it occupies no working time, is drawn as a diamond in the Gantt, and participates in float and critical-path calculation like any other node.
- **FR-F012-11:** `POST /api/v1/sheets/{sheet_id}/schedule/shift` with `{ row_id?, anchor_date?, delta_days?, preview: bool }` either moves one row by `delta_days` working days or re-anchors the whole sheet so its earliest start lands on `anchor_date`; successors move by the minimum amount needed to satisfy every constraint, dates written to the start and end columns respect the working calendar and exceptions, and `preview: true` returns the affected rows with old and new dates without writing.
- **FR-F012-12:** A committed shift writes all affected cells in one transaction with a single `If-Match` on the sheet schedule version, records one audit event with the list of `row_id` and before/after dates, publishes `schedule.shifted.v1` once with `changed_fields` naming the affected rows, and returns the new `schedule_version`.
- **FR-F012-13:** A shift affecting more than 10,000 rows or exceeding a 2 s evaluation budget returns `503 unavailable` with `details.reason = "shift_budget"` and writes nothing.
- **FR-F012-14:** The web app renders `/w/{workspace_id}/sheets/{sheet_id}?mode=gantt` with bars per row, arrows per dependency, milestone diamonds, parent summary bars, a critical-path toggle, drag-to-reschedule that calls the shift endpoint, a keyboard shift dialog, and a baseline overlay slot that F015 fills; viewers see the chart read-only and users without sheet access get the not-found state.
- **FR-F012-15:** Cross-tenant access to any dependency, critical-path, or shift route by ID returns `404 not_found`; an actor with `sheet-viewer` but not `project-editor` receives `403 denied` on every mutation.

### Non-functional requirements

- **NFR-F012-01 Performance:** critical-path computation for a sheet with 10,000 scheduled rows and 20,000 dependencies completes in under 500 ms p95; a shift touching 1,000 successors commits in under 800 ms p95; dependency list of 1,000 rows responds in under 500 ms p95 (spec section 6).
- **NFR-F012-02 Security/privacy:** every query carries a `tenant_id` predicate; row IDs from another tenant or another sheet are rejected before any graph work; shift previews never write; cross-tenant, role, and cross-sheet negatives run in the harness.
- **NFR-F012-03 Accessibility:** the Gantt chart exposes each bar and arrow as a labelled focusable element, keyboard shift and link creation exist for every mouse gesture, live region announces shifts and link results, and axe reports zero serious violations.
- **NFR-F012-04 Reliability/observability:** each request has a span with `tenant_id`, `sheet_id`, `correlation_id`, `affected_rows`; shift failures roll back completely; metrics `dependencies_cycle_rejections_total`, `schedule_shift_duration_ms`, and `critical_path_duration_ms` are exported.

### Scope

Included: dependency CRUD with four link types and signed lag, cycle detection, duplicate and limit rules, forward/backward pass critical path with persisted results, parent roll-up, milestones, single-row and whole-sheet shift with preview, working-calendar arithmetic through F011, Gantt view with drag and keyboard rescheduling, critical-path toggle, baseline overlay slot.

Excluded: working calendars and schedule settings themselves (F011), row hierarchy operations (F009), baselines and variance data (F015 fills the overlay slot), resource levelling and workload (F033, F034), cross-sheet dependencies, automatic re-anchoring on cell edits (row edits trigger a recompute of `schedule_results` only, not a shift).

## 3. UX specification

- Entry points: sheet mode switch `Gantt` next to grid and board; row context menu `Add dependency`; Gantt toolbar `Shift schedule`; route `/w/{workspace_id}/sheets/{sheet_id}?mode=gantt`.
- Primary flow: open Gantt, select task "Design", choose `Add dependency`, pick successor "Build", type `FS`, lag `2 days`, save; an arrow appears and "Build" moves to two working days after "Design" ends. Toggle `Critical path`; critical bars turn to the critical token colour. Drag "Design" three days right; a preview panel lists affected rows with old and new dates; confirm; bars move and the toast reports the number of rows shifted.
- Loading: skeleton bars per row; Empty: chart with an `Add dates` prompt when no schedule settings exist (link to F011 settings); Error: banner with `correlation_id` and retry; Success: toast `Shifted 14 rows`; Stale/conflict: banner `Schedule changed` with `Reload`; Offline: drag disabled with badge; Denied: link and shift controls hidden for viewers.
- Cycle and validation feedback: the dependency dialog shows `Would create a cycle: Design → Build → Test → Design` inline and keeps focus on the successor field.
- Shift preview: `ShiftDialog` lists affected rows, old dates, new dates, and shows `Too many rows to shift (10,000 limit)` when the API returns `unavailable`.
- Responsive: under 1,024 px the row label column collapses to 160 px and the timeline scrolls horizontally; under 640 px the chart lists rows with date text and hides arrows.
- Keyboard: arrow keys move focus between bars, `Shift+ArrowRight/Left` opens the shift dialog pre-filled with ±1 day, `L` opens the add-dependency dialog for the focused row, `Enter` opens row details, `Escape` cancels a drag; focus ring uses the shared token; motion respects `prefers-reduced-motion`.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062); Lucide icons `GanttChart`, `Link2`, `Diamond`, `MoveHorizontal`, `Route`, `AlertTriangle`; colours from `apps/web/src/design/tokens.css` including `--color-critical`.

## 4. Technical specification

### Rust backend

- Domain entities: `Dependency { id, tenant_id, sheet_id, predecessor_row_id, successor_row_id, kind: DependencyKind, lag: i32, lag_unit: LagUnit, version, created/updated actor+time }`, `DependencyKind { FS, SS, FF, SF }`, `LagUnit { Days, Hours }`, `ScheduleNode { row_id, start, finish, duration_days, is_milestone, is_parent }`, `ScheduleResult { row_id, early_start, early_finish, late_start, late_finish, total_float_days, is_critical, schedule_version }`, `ShiftPlan { affected: Vec<RowShift { row_id, old_start, old_finish, new_start, new_finish }>, schedule_version }`.
- Use cases in `crates/domain/src/dependencies/`: `create_dependency`, `update_dependency`, `delete_dependency`, `list_dependencies`, `detect_cycle` (Kahn topological sort over the sheet graph plus the candidate edge, returns the cycle path via DFS on failure), `compute_critical_path` (forward pass earliest dates from constraints `FS: succ.start ≥ pred.finish + lag`, `SS: succ.start ≥ pred.start + lag`, `FF: succ.finish ≥ pred.finish + lag`, `SF: succ.finish ≥ pred.start + lag`; backward pass latest dates; float = late_start − early_start in working days), `rollup_parents`, `plan_shift`, `commit_shift`.
- Working-time arithmetic is imported from F011 `crates/domain/src/schedules/working_time.rs` (`add_working_days`, `add_working_hours`, `working_days_between`) with the calendar and exceptions loaded once per request; F012 never redefines calendars.
- API endpoints (`services/api/src/dependencies/`): `GET /api/v1/sheets/{sheet_id}/dependencies`, `POST /api/v1/dependencies`, `PATCH /api/v1/dependencies/{id}`, `DELETE /api/v1/dependencies/{id}`, `GET /api/v1/sheets/{sheet_id}/critical-path`, `POST /api/v1/sheets/{sheet_id}/schedule/shift`. DTOs `CreateDependencyRequest { predecessor_row_id, successor_row_id, kind, lag?, lag_unit? }`, `UpdateDependencyRequest { kind?, lag?, lag_unit? }`, `ShiftRequest { row_id?, anchor_date?, delta_days?, preview }`, responses `DependencyResponse`, `Page<DependencyResponse>`, `CriticalPathResponse { schedule_version, computed_at, rows: Vec<ScheduleResult> }`, `ShiftResponse { schedule_version, affected: Vec<RowShift>, committed: bool }`.
- Events: `dependency.created.v1`, `dependency.updated.v1`, `dependency.deleted.v1`, `schedule.shifted.v1`; payload per contract conventions; the `changed_fields` payload of `schedule.shifted.v1` lists `rows[].row_id` and the two date column IDs.
- Recompute trigger: the service subscribes to `row.updated.v1`, `cell.updated.v1`, and `row.reparented.v1` for sheets with schedule settings and rewrites `schedule_results` for the sheet, bumping `schedule_version`.
- Authorization: `project-editor` on the sheet for create, update, delete, and committed shift; `sheet-viewer` for list, critical path, and preview shift; explicit deny wins; missing sheet access maps to `not_found`.
- Validation: `lag` within ±3,650 days or ±87,600 hours; `delta_days` within ±3,650; exactly one of `row_id` or `anchor_date`; `limit` 1–1,000; dependency count per sheet ≤ 20,000 checked inside the insert transaction with a `SELECT count(*) ... FOR UPDATE` on the sheet schedule settings row.
- Error mapping: `DependencyError::Cycle { path } → 400 invalid`, `DependencyError::Duplicate { existing_id } → 409 conflict`, `DependencyError::SelfLink | DifferentSheet | ParentRow | LagOutOfRange | SheetLimit → 400 invalid`, `ScheduleError::NoScheduleSettings → 400 invalid (field_errors.sheet_id = "unscheduled")`, `ScheduleError::Budget → 503 unavailable`, `StaleVersion → 409 conflict`, `NotFound → 404`, `AuthzError::Denied → 403 denied`.

### PostgreSQL/SQLx

- Migration `*_dependencies_*.sql` creates `row_dependencies(id uuid pk, tenant_id uuid not null, sheet_id uuid not null references sheets(id) on delete restrict, predecessor_row_id uuid not null references rows(id) on delete restrict, successor_row_id uuid not null references rows(id) on delete restrict, kind text not null check (kind in ('FS','SS','FF','SF')), lag integer not null default 0, lag_unit text not null default 'days' check (lag_unit in ('days','hours')), version bigint not null default 1, created_by, created_at, updated_by, updated_at, check (predecessor_row_id <> successor_row_id))` and `schedule_results(tenant_id uuid not null, sheet_id uuid not null, row_id uuid not null references rows(id) on delete cascade, early_start date, early_finish date, late_start date, late_finish date, total_float_days integer, is_critical boolean not null default false, computed_at timestamptz not null, schedule_version bigint not null, primary key (sheet_id, row_id))`.
- Invariants: unique index `row_dependencies_pair_idx on (tenant_id, predecessor_row_id, successor_row_id)`; check constraint on lag range; trigger-free cycle safety is guaranteed by the service under a `SELECT ... FOR UPDATE` on the sheet's `sheet_schedule_settings` row so concurrent inserts serialize per sheet.
- Indexes: `row_dependencies(sheet_id, predecessor_row_id)`, `row_dependencies(sheet_id, successor_row_id)`, `row_dependencies(tenant_id, id)`, `schedule_results(sheet_id, is_critical) where is_critical`.
- Audit events: `dependency.create`, `dependency.update`, `dependency.delete`, `schedule.shift` (with the affected row list and before/after dates), `schedule.recompute`.
- Retention/deletion: dependencies are hard-deleted on `DELETE` because they carry no user content beyond the link; deleting a row (F006 soft delete) leaves its dependencies in place and excludes them from the graph until restore; rollback drops both tables.

### React/TypeScript

- Routes: `mode=gantt` on `/w/:workspaceId/sheets/:sheetId` in `apps/web/src/features/dependencies/`; components `GanttPage`, `GanttChart`, `GanttBar`, `MilestoneMarker`, `SummaryBar`, `DependencyArrow`, `DependencyDialog`, `CriticalPathToggle`, `ShiftDialog`, `ShiftPreviewTable`, `BaselineOverlaySlot`.
- State: TanStack Query keys `['dependencies', sheetId, cursor]`, `['critical-path', sheetId]`, `['schedule-shift-preview', sheetId, request]`; mutations invalidate `['dependencies', sheetId]`, `['critical-path', sheetId]`, and `['sheet-rows', sheetId]`.
- API client: generated `DependenciesApi` with `listDependencies`, `createDependency`, `updateDependency`, `deleteDependency`, `getCriticalPath`, `shiftSchedule`.
- Optimistic updates: bar drag renders the preview locally, calls `shiftSchedule` with `preview: true`, shows the table, and commits on confirm; a `conflict` rolls back and shows the stale banner.
- Telemetry: `gantt_opened`, `dependency_created`, `dependency_cycle_rejected`, `critical_path_toggled`, `schedule_shift_previewed`, `schedule_shift_committed` with `sheet_id`, `kind`, `affected_rows`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F012-01 through FR-F012-15 in `testing/features/F012/requirements/cases.md`
- [ ] Failure/edge-case tests: three-node cycle, duplicate pair, self link, cross-sheet pair, parent row link, lag out of range, 20,000 limit, shift over 10,000 rows, shift over 2 s budget, sheet without schedule settings
- [ ] Permission-negative and tenant-isolation tests: cross-tenant routes return `not_found`, viewer mutation returns `denied`, preview allowed for viewer, commit denied
- [ ] Rust unit tests: `crates/domain/src/dependencies/` forward/backward pass, float, each link type, negative lag, hours lag, milestone, parent roll-up, calendar exceptions
- [ ] API contract/integration tests: every route above with success and each error code
- [ ] Database migration/constraint tests: pair unique index, kind and lag checks, foreign keys, cascade on `schedule_results`, rollback
- [ ] React component tests: `GanttChart`, `DependencyDialog`, `ShiftDialog` states
- [ ] Browser E2E tests: link two tasks, toggle critical path, drag shift with preview, keyboard shift, cycle rejection
- [ ] Accessibility tests: axe on Gantt, keyboard link and shift, live region announcements
- [ ] Performance/load tests: 10,000-row/20,000-dependency critical path under 500 ms, 1,000-successor shift under 800 ms

### Fast fanout configuration

- Test harness path: `testing/features/F012/`
- Feature flag: `F012_FEATURE`
- Fixture/seed factory: `testing/fixtures/dependencies.rs` builds tenant, sheet with F011 schedule settings (Mon–Fri calendar, one holiday exception), project editor, viewer, foreign tenant, 12 rows including one parent and one milestone, and 9 dependencies covering all four kinds
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, calendar timezone `UTC`
- Mock/stub contracts: outbox publisher recorded in memory; F011 calendar service used directly from its crate with fixture calendars; authz uses the real F003 engine
- Parallel isolation: one schema per test worker, tenant ID per test
- Targeted command: `cargo xtask test-feature F012`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F012/`

## 6. Acceptance criteria

```gherkin
Feature: Dependencies, critical path, and schedule shift

Scenario: Finish-to-start link with lag moves the successor
  Given rows "Design" (Mon–Wed) and "Build" (Mon–Tue) on a Mon–Fri calendar
  When a project editor creates an FS dependency Design → Build with lag 2 days
  Then Build starts the following Monday and dependency.created.v1 is in the outbox

Scenario: Cycle is rejected
  Given dependencies Design → Build and Build → Test
  When the editor creates Test → Design
  Then the response is 400 invalid with field_errors.successor_row_id "cycle" and cycle_path [Design, Build, Test, Design]

Scenario: Critical path identifies zero-float rows
  Given the seeded 12-row schedule
  When the editor requests the critical path
  Then rows on the longest chain have total_float_days 0 and is_critical true

Scenario: Shift with preview then commit
  Given "Design" has 14 transitive successors
  When the editor previews a +3 working day shift and then commits it
  Then the preview writes nothing, the commit updates 15 rows across a holiday, and schedule.shifted.v1 is published once

Scenario: Viewer cannot commit a shift
  Given a user with sheet-viewer only
  When they POST a shift with preview false
  Then the response is 403 denied and no cell changes
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F009 (row hierarchy for parent roll-up and `row.reparented.v1`), F011 (schedule settings, working calendars, working-time arithmetic); decisions sections 2–4, 6; contracts row F012
- Blocks: F015 (baselines overlay and template dependencies), F034 (workload uses schedule results)
- Conflicts with: none (disjoint owned paths)
- External dependencies: none
- Risks and mitigations: graph work on every cell edit could be expensive, so recompute is debounced per sheet by 500 ms in the consumer and bounded by the 2 s budget; concurrent dependency inserts could bypass cycle detection, so inserts lock the sheet's schedule settings row; hour-based lag across calendar exceptions is easy to get wrong, so working-hour arithmetic stays in F011 and F012 only calls it.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F009 and F011 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F012/`
- [ ] Migration file name and owned paths claimed
- [ ] Fixture factory with a calendar and hierarchy available in `testing/fixtures/dependencies.rs`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for every mutation and every committed shift
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F012_FEATURE`, run down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Project editors can link tasks with FS, SS, FF, and SF dependencies and lag, see the critical path, and shift schedules with successors following the working calendar in a Gantt view.
- Migration adds `row_dependencies` and `schedule_results`; rollback drops them. Feature is off by default behind `F012_FEATURE`.
