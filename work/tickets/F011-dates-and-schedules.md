---
id: F011
type: feature
status: planned
priority: P1
owner: platform
estimate: 5
target_milestone: M2
parent_epic: E003
depends_on: [F007]
blocks: [F012, F013, F033, F055]
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/schedules/**, crates/persistence/src/schedules/**, services/api/src/schedules/**, apps/web/src/features/schedules/**, services/api/migrations/*_schedules_*.sql, testing/features/F011/**]
feature_flag: F011_FEATURE
flag_default: off
branch: f011-dates-and-schedules
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 6, 9
- Capability contract: `docs/capability-contracts.md` row F011

# F011 — Dates and schedules

## 1. Identity and dates

- Branch: `f011-dates-and-schedules`
- Capability area: planning (spec 5.1 WORK-02, WORK-04 working calendar and Gantt bullets, 5.7 capacity calendar bullet, section 4 typed `date`, `datetime`, `duration` values, section 6 timezones and tenant working calendars)
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 6, 9; `docs/capability-contracts.md` row F011
- Aggregate: `schedule`
- Module slug: `schedules`

## 2. Requirement specification

### Problem and user outcome

F007 gives sheets typed `date`, `datetime`, and `duration` columns but no shared meaning: a task that "takes 3 days" starting on a Friday ends on a different day depending on who reads it, and every downstream feature (dependencies, calendar views, capacity, baselines) would invent its own arithmetic. Teams need one definition of working time per tenant, one schedule configuration per sheet, and one reschedule operation that every view and engine calls.

As a project editor, I want to declare which columns hold start, end, and duration, pick a working calendar and timezone for my sheet, and move a task while the end date follows working days, so that dates mean the same thing in the grid, the calendar, the Gantt, and reports.

### Functional requirements

- **FR-F011-01:** A `date` cell stores an ISO 8601 calendar date (`2026-09-14`) with no timezone; a `datetime` cell stores a UTC instant with microsecond precision and returns `display` rendered in the sheet timezone; a `duration` cell stores `{ value: decimal ≥ 0, unit: days|hours }` where 1 day equals the calendar `hours_per_day`; any other shape returns `400 invalid` with `field_errors.<column_id>`.
- **FR-F011-02:** A `tenant-admin` or `sheet-editor` can create a working calendar with `name` (1–120 chars, unique per tenant case-insensitive), `timezone` (valid IANA name), `week` (per weekday list of `{ start: "09:00", end: "17:00" }` intervals, non-overlapping, at most 4 per day), and `hours_per_day` (0.5–24); a tenant receives a default `Standard` calendar (Mon–Fri 09:00–17:00, 8 h, tenant timezone) on first read. Each interval is a `working_calendar_intervals` row keyed by `(calendar_id, weekday, position)`, so the at-most-4-per-day limit is declarative (`position smallint check (position between 1 and 4)` with `unique (calendar_id, weekday, position)`) and non-overlap stays a service check because PostgreSQL cannot express per-weekday interval exclusion declaratively; the request and response still carry `week` as a per-weekday list of intervals, assembled by the repository from those rows.
- **FR-F011-03:** `PATCH /api/v1/working-calendars/{id}` updates `name`, `timezone`, `week`, `hours_per_day`, `is_default`, and the `exceptions` list with `If-Match`; a `week` update replaces the calendar's `working_calendar_intervals` rows wholesale; exactly one calendar per tenant is default; setting a new default clears the old one in the same transaction; a stale version returns `409 conflict` with `current_version`.
- **FR-F011-04:** Calendar exceptions are dated overrides `{ date, kind: holiday|working, hours?: [{start,end}], label }` unique per `(calendar_id, date)`; a `holiday` exception removes the day from working time and has zero `calendar_exception_intervals` rows, a `working` exception adds or replaces intervals and has one to four rows keyed by `(exception_id, position)`; at most 400 exceptions per calendar. The response still returns `exceptions[].hours` as a list, assembled from those rows.
- **FR-F011-05:** `PUT /api/v1/sheets/{sheet_id}/schedule-settings` sets `start_column_id` (date or datetime), `end_column_id` (same type as start), `duration_column_id` (duration, optional), `milestone_column_id` (boolean, optional), `percent_complete_column_id` (number, optional), `calendar_id`, and `timezone`; column IDs must belong to the sheet and have the required type or the response is `400 invalid` with `field_errors.<field> = "type_mismatch"`.
- **FR-F011-06:** `GET /api/v1/sheets/{sheet_id}/schedule` returns the settings, the resolved calendar (with exceptions), and a cursor page (`limit` ≤ 500) of `RowSchedule { row_id, start, end, duration_days, is_milestone, percent_complete, version }` computed from current cells; rows missing a start are returned with `start: null` and `status: unscheduled`.
- **FR-F011-07:** Working-time arithmetic is deterministic and reads a `ResolvedCalendar` assembled from the calendar's weekday interval rows and exception interval rows: `add_working_days(2026-09-11 Fri, 3)` on the Standard calendar returns `2026-09-16 Wed`; `working_days_between(2026-09-11, 2026-09-16)` returns 3; holidays and weekends are skipped; a start that lands on a non-working day snaps forward to the next working day and an end snaps backward to the previous working day.
- **FR-F011-08:** `POST /api/v1/rows/{id}/reschedule` accepts exactly two of `{ start, end, duration }` (or one when the row already has the others) and computes the third with the sheet calendar; `end < start` returns `400 invalid` with `field_errors.end = "before_start"`; duration over 3,650 days returns `invalid`; the response is the updated `RowResponse` with a new `version` and emits `row.rescheduled.v1` with `{ old_start, old_end, new_start, new_end, duration_days }`.
- **FR-F011-09:** Rescheduling a row whose `is_milestone` cell is true forces `duration = 0` and `end = start`; giving a non-zero duration to a milestone returns `400 invalid` with `field_errors.duration = "milestone"`.
- **FR-F011-10:** Rescheduling a parent row (F009 hierarchy) is rejected with `400 invalid` and `field_errors.row_id = "parent_rollup"` when the sheet has roll-up rules on the start or end column, because parent dates derive from children.
- **FR-F011-11:** Every mutation requires `Idempotency-Key` and `If-Match`, writes an `audit_events` row with the before/after diff, and publishes `working-calendar.updated.v1`, `schedule-settings.updated.v1`, or `row.rescheduled.v1` through the outbox in the same transaction.
- **FR-F011-12:** `datetime` rendering honours the resolution order sheet timezone, then the actor's user timezone (F049 when present), then the tenant timezone, then UTC; the response includes `display_timezone` so the client never guesses.
- **FR-F011-13:** Cross-tenant access to any calendar, schedule, or row by ID returns `404 not_found`; a `sheet-viewer` calling any mutation route receives `403 denied`.
- **FR-F011-14:** The web app exposes a schedule settings panel and a date cell editor with timezone label, working-day snapping preview, and duration entry (`3d`, `12h`), and shows loading, empty (no schedule settings), error, denied, stale, and offline states.

### Non-functional requirements

- **NFR-F011-01 Performance:** `GET /schedule` for 500 rows of a 100,000-row sheet responds under 500 ms p95; reschedule responds under 800 ms p95; working-day arithmetic over a 10-year span with 400 exceptions completes under 5 ms per call (spec section 6).
- **NFR-F011-02 Security/privacy:** every query carries a `tenant_id` predicate; calendars are tenant-owned and never visible across tenants; cross-tenant and role-negative tests are part of the harness; IANA names are validated against the bundled tz database, never used to build paths.
- **NFR-F011-03 Accessibility:** date editor and settings panel meet WCAG 2.2 AA; the date picker is operable by keyboard with arrow-key navigation and announces the resolved working day; `prefers-reduced-motion` disables picker transitions.
- **NFR-F011-04 Reliability/observability:** every request span records `tenant_id`, `sheet_id`, `calendar_id`, and `correlation_id`; metric `schedule_reschedule_duration_ms` and counter `schedule_snap_applied_total` are exported; a tz database update is a deployment, not a data migration.

### Scope

Included: date/datetime/duration semantics, working calendars with exceptions, default calendar, sheet schedule settings, schedule read model, working-day arithmetic, single-row reschedule, timezone resolution, audit and outbox events, settings panel and date editor.

Excluded: dependencies, critical path, and multi-row shift propagation (F012), calendar and timeline views (F013), locale formatting and translations (F049), capacity and leave calendars (F033), calendar publishing (F055), recurring rows.

## 3. UX specification

- Entry points: sheet header menu `Schedule settings`; route `/w/{workspace_id}/sheets/{sheet_id}/settings/schedule`; tenant admin route `/admin/working-calendars`; any date cell in the grid opens the date editor.
- Primary flow: open `Schedule settings`, choose start, end, and duration columns, pick the `Standard` calendar and `Europe/Berlin`, save; return to the grid, edit a task's duration to `3d`, the end date moves to the next working day and a hint shows `Skipped Sat, Sun`; open a row on a holiday, the start snaps forward with the label `Moved from 2026-12-25 (Christmas)`.
- Loading: skeleton settings form and calendar table; Empty: `No schedule configured` with `Configure` action; Error: banner with `correlation_id` and retry; Success: toast `Schedule settings saved`; Stale: banner `Settings changed by someone else` with reload; Offline: form disabled with badge.
- Permission-denied: viewers see settings read-only with an explanation; users outside the workspace see not-found.
- Responsive: settings form stacks to one column under 640 px; the calendar week editor becomes a per-day accordion.
- Keyboard: date picker uses arrow keys for days, `PageUp`/`PageDown` for months, `T` for today, `Enter` to confirm, `Escape` to cancel; duration field accepts `3d` or `12h`; focus ring uses the shared token.
- Screen reader: the date editor exposes `role="dialog"` named by the column label, the resolved working day is announced through `aria-live="polite"`, and the timezone label is part of the field description.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062); Lucide icons `CalendarDays`, `Clock`, `Globe`, `Flag`, `Settings2`; tokens from `apps/web/src/design/tokens.css`.

- Design: `design/artboards/Schedules.dc.html` on the canvas indexed by `design/canvas.json`. The ticket is the contract and the artboard is the picture; when they disagree the ticket wins.

## 4. Technical specification

### Rust backend

- Domain entities in `crates/domain/src/schedules/`: `WorkingCalendar { id, tenant_id, name, timezone: Tz, week: WorkingWeek, hours_per_day: Decimal, is_default, version, audit fields, deleted_at }`, `WorkingWeek([Vec<Interval>; 7])`, `Interval { start: NaiveTime, end: NaiveTime }`, `CalendarException { id, calendar_id, date: NaiveDate, kind: ExceptionKind, hours: Option<Vec<Interval>>, label }`, `SheetScheduleSettings { sheet_id, tenant_id, start_column_id, end_column_id, duration_column_id, milestone_column_id, percent_complete_column_id, calendar_id, timezone, version }`, `WorkDate(NaiveDate)`, `WorkDateTime(DateTime<Utc>)`, `WorkDuration { value: Decimal, unit: DurationUnit }`, `ResolvedCalendar { calendar, week: WorkingWeek, exceptions: Vec<CalendarException> }`, `RowSchedule`; these are types only, with no SQL and no schema definitions.
- Use cases: `create_calendar`, `update_calendar`, `list_calendars`, `ensure_default_calendar`, `put_schedule_settings`, `read_schedule`, `reschedule_row`; pure functions `add_working_days`, `working_days_between`, `next_working_day`, `previous_working_day`, `snap_start`, `snap_end`, `resolve_timezone(sheet, user, tenant)` in `calendar_math.rs`; those functions take a loaded `ResolvedCalendar` value and touch no database.
- Persistence (`crates/persistence/src/schedules/`): `WorkingCalendarRepository` owns `working_calendars`, `working_calendar_intervals`, `calendar_exceptions`, `calendar_exception_intervals`; `SheetScheduleSettingsRepository` owns `sheet_schedule_settings`. Each implements the shared `Repository` contract (`get`, `list` with cursor pagination, `insert`, `update` under an expected version, `soft_delete`, `restore`, `purge`) and adds named queries `list_for_tenant`, `find_default`, `ensure_default`, `replace_week_intervals`, `replace_exceptions`, `load_resolved_calendar(calendar_id)`, `get_for_sheet(sheet_id)`, `page_row_schedules(sheet_id, cursor, limit)`; the tenant predicate, soft-delete filter, version check, audit row, and outbox enqueue come from the base contract. `load_resolved_calendar` assembles `week` from the interval rows and `exceptions[].hours` from the exception interval rows, so the wire contract is unchanged. Multi-table writes — the FR-F011-03 default swap with its week and exception replacement, and the settings write plus row reschedule — run in one `UnitOfWork` that owns the transaction. Row cells are read and written through F006/F007's `RowRepository`/`CellRepository`, never by this feature's SQL. Per decision 2.1 the use cases above depend on these repository traits and contain no SQL: no SQL string, `sqlx::query*` call, or connection exists in `crates/domain/src/schedules` or `services/api/src/schedules`.
- API endpoints (`services/api/src/schedules/`): `GET /api/v1/working-calendars`, `POST /api/v1/working-calendars`, `PATCH /api/v1/working-calendars/{id}`, `PUT /api/v1/sheets/{sheet_id}/schedule-settings`, `GET /api/v1/sheets/{sheet_id}/schedule`, `POST /api/v1/rows/{id}/reschedule`. DTOs: `CreateCalendarRequest`, `UpdateCalendarRequest`, `CalendarResponse`, `PutScheduleSettingsRequest`, `ScheduleSettingsResponse`, `ScheduleResponse { settings, calendar, rows: Page<RowSchedule> }`, `RescheduleRequest { start?, end?, duration? }`, reuse `RowResponse` from F006.
- Events: `working-calendar.updated.v1`, `schedule-settings.updated.v1`, `row.rescheduled.v1` with contract payload plus `changed_fields`.
- Authorization: `sheet-editor` on the sheet for settings and reschedule; `tenant-admin` or `sheet-editor` for calendars; `sheet-viewer` for reads; explicit deny wins; missing access maps to `not_found`.
- Validation: timezone parsed by `chrono_tz::Tz::from_str`; intervals sorted and non-overlapping; `hours_per_day` 0.5–24; exceptions ≤ 400; duration ≤ 3,650 days; `limit` 1–500. Idempotency via the shared `idempotency_keys` table for 24 hours.
- Error mapping: `ScheduleError::NameTaken → 409 conflict`, `StaleVersion → 409 conflict`, `TypeMismatch → 400 invalid`, `EndBeforeStart → 400 invalid`, `MilestoneDuration → 400 invalid`, `ParentRollup → 400 invalid`, `NotFound → 404 not_found`, `AuthzError::Denied → 403 denied`.

### PostgreSQL/SQLx

- Migration `*_schedules_*.sql` creates `working_calendars(id uuid pk, tenant_id uuid not null, name text not null, timezone text not null, hours_per_day numeric(4,2) not null, is_default bool not null default false, version bigint not null default 1, created_by, created_at, updated_by, updated_at, deleted_at)`, `working_calendar_intervals(id uuid pk, tenant_id uuid not null, calendar_id uuid not null references working_calendars(id) on delete cascade, weekday smallint not null check (weekday between 0 and 6), position smallint not null check (position between 1 and 4), start_time time not null, end_time time not null check (end_time > start_time), created_by, created_at)`, `calendar_exceptions(id uuid pk, tenant_id uuid not null, calendar_id uuid not null references working_calendars(id) on delete cascade, date date not null, kind text not null check (kind in ('holiday','working')), label text, created_by, created_at)`, `calendar_exception_intervals(id uuid pk, tenant_id uuid not null, exception_id uuid not null references calendar_exceptions(id) on delete cascade, position smallint not null check (position between 1 and 4), start_time time not null, end_time time not null check (end_time > start_time), created_at)`, `sheet_schedule_settings(sheet_id uuid pk references sheets(id) on delete restrict, tenant_id uuid not null, start_column_id uuid not null, end_column_id uuid not null, duration_column_id uuid, milestone_column_id uuid, percent_complete_column_id uuid, calendar_id uuid not null references working_calendars(id) on delete restrict, timezone text not null, version bigint not null default 1, audit fields)`.
- Invariants: unique index `working_calendars_tenant_name_idx on (tenant_id, lower(name)) where deleted_at is null`; partial unique index `working_calendars_tenant_default_idx on (tenant_id) where is_default and deleted_at is null`; unique `(calendar_id, date)` on exceptions; `unique (calendar_id, weekday, position)` and `unique (calendar_id, weekday, start_time)` on `working_calendar_intervals`, which make the ≤ 4 intervals per weekday limit declarative through `position` and forbid two intervals starting at the same minute; `unique (exception_id, position)` on `calendar_exception_intervals`, so a `holiday` exception carries zero rows and a `working` exception one to four; check `hours_per_day between 0.5 and 24`; interval non-overlap within a weekday and the ≤ 400 exceptions per calendar limit stay service checks because PostgreSQL cannot express either declaratively per weekday or per parent; column IDs validated in service against `columns.type`.
- Indexes: `working_calendar_intervals(calendar_id, weekday, start_time)`, `calendar_exception_intervals(exception_id, position)`, `calendar_exceptions(calendar_id, date)`, `sheet_schedule_settings(tenant_id, calendar_id)`, `working_calendars(tenant_id, updated_at desc)`.
- Audit events: `calendar.create`, `calendar.update`, `schedule-settings.put`, `row.reschedule` with field-level diffs.
- Retention/deletion: calendars soft-delete only when no `sheet_schedule_settings` references them (`409 conflict` otherwise); rollback drops `calendar_exception_intervals`, `working_calendar_intervals`, `calendar_exceptions`, `sheet_schedule_settings`, and `working_calendars`.

### React/TypeScript

- Routes: `/w/:workspaceId/sheets/:sheetId/settings/schedule`, `/admin/working-calendars` in `apps/web/src/features/schedules/`; components `ScheduleSettingsPanel`, `ColumnRolePicker`, `CalendarPicker`, `TimezoneSelect`, `WorkingCalendarPage`, `WeekEditor`, `ExceptionTable`, `DateCellEditor`, `DurationInput`, `SnapHint`.
- State: TanStack Query keys `['working-calendars']`, `['schedule-settings', sheetId]`, `['schedule', sheetId, cursor]`; reschedule mutation updates the cached row version and invalidates `['sheet-rows', sheetId]`.
- API client: generated `SchedulesApi` with `listCalendars`, `createCalendar`, `updateCalendar`, `putScheduleSettings`, `getSchedule`, `rescheduleRow`.
- Optimistic updates: reschedule applies locally with the client-side snap preview, rolls back on `conflict` or `invalid` and shows the field error.
- Telemetry: `schedule_settings_saved`, `calendar_created`, `calendar_exception_added`, `row_rescheduled` (with `snap_applied` boolean), `date_editor_opened`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F011-01 through FR-F011-14 in `testing/features/F011/requirements/cases.md`
- [ ] Failure/edge-case tests: end before start, milestone with duration, parent with roll-up, overlapping intervals, second default calendar, 401st exception, invalid timezone, DST boundary datetime
- [ ] Permission-negative and tenant-isolation tests: cross-tenant calendar and schedule return `not_found`; viewer reschedule returns `denied`
- [ ] Rust unit tests: `calendar_math.rs` add/between/snap over weekends, holidays, DST, and leap days
- [ ] API contract/integration tests: all six routes with success and each error code
- [ ] Database migration/constraint tests: default-calendar partial index, exception uniqueness, `working_calendar_intervals` position range and `(calendar_id, weekday, position)` uniqueness, `calendar_exception_intervals` position uniqueness, cascade from calendar to both interval tables, restrict on referenced calendar, rollback
- [ ] React component tests: `ScheduleSettingsPanel`, `DateCellEditor`, `WeekEditor` states
- [ ] Browser E2E tests: configure schedule, reschedule across a holiday, admin edits calendar, viewer read-only
- [ ] Accessibility tests: axe on settings and calendar pages; keyboard-only date picking
- [ ] Performance/load tests: schedule read p95, reschedule p95, arithmetic micro-benchmark

### Fast fanout configuration

- Test harness path: `testing/features/F011/`
- Feature flag: `F011_FEATURE`
- Fixture/seed factory: `testing/fixtures/schedules.rs` builds tenant, editor, viewer, foreign tenant, the `Standard` calendar, a `Berlin` calendar with 12 holidays, and a sheet with start/end/duration columns and 50 rows
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, UTC, tz database pinned to the workspace `chrono-tz` version
- Mock/stub contracts: outbox recorded in memory; F007 column type lookup uses real tables; F049 user timezone stubbed to `None` until F049 lands
- Parallel isolation: one schema per test worker, tenant ID per test
- Targeted command: `cargo xtask test-feature F011`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F011/`

## 6. Acceptance criteria

```gherkin
Feature: Dates, working calendars, and reschedule

Scenario: Duration follows working days
  Given sheet "Launch plan" uses the Standard calendar in Europe/Berlin
  When an editor reschedules row "Kickoff" with start 2026-09-11 and duration 3 days
  Then the end is 2026-09-16, the row version increments, and row.rescheduled.v1 is published

Scenario: Holiday snaps the start forward
  Given calendar "Berlin" has a holiday exception on 2026-12-25
  When an editor sets a row start to 2026-12-25
  Then the start is stored as 2026-12-28 and the response carries snap_applied true

Scenario: Viewer cannot reschedule
  Given a sheet-viewer on "Launch plan"
  When they call POST /api/v1/rows/{id}/reschedule
  Then the response is 403 denied and no cell changes

Scenario: Cross-tenant calendar is invisible
  Given calendar "Berlin" in tenant A
  When an admin from tenant B patches it by id
  Then the response is 404 not_found
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F007 (typed date/datetime/duration/boolean/number columns); decisions sections 2–4, 6, 9; contracts row F011
- Blocks: F012, F013, F033, F055
- Conflicts with: none (disjoint owned paths)
- External dependencies: `chrono`, `chrono-tz`, `rust_decimal` crates already in the workspace
- Risks and mitigations: DST transitions can make a `datetime` day shorter than `hours_per_day`, so arithmetic operates on calendar dates in the sheet timezone and only converts to instants at the boundaries; F009 roll-up rules may not exist yet when F011 ships, so `ParentRollup` is checked only when a rule row exists; users may expect duration in calendar days, so the editor always shows the resolved end date before commit.
- Rollout: enable `F011_FEATURE` per tenant after the `Standard` calendar is materialized; disabling the flag hides the routes and editor slot while existing cell values remain readable through F008.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F007 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F011/`
- [ ] Migration file name and owned paths claimed
- [ ] Fixture factory `testing/fixtures/schedules.rs` and schema-per-worker isolation available

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for every mutation
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F011_FEATURE`, run down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Tenants get working calendars with holidays; sheets can declare start, end, duration, and milestone columns; rescheduling a task respects working days and the sheet timezone.
- Migration adds `working_calendars`, `working_calendar_intervals`, `calendar_exceptions`, `calendar_exception_intervals`, and `sheet_schedule_settings`; rollback drops them. Feature is off by default behind `F011_FEATURE`.
