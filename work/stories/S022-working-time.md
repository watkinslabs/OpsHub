---
id: S022
type: story
status: planned
parent_epic: E003
parent_feature: F011
depends_on: [S021]
owned_paths: [crates/domain/src/schedules/**, crates/persistence/src/schedules/**, services/api/src/schedules/**, apps/web/src/features/schedules/**, testing/features/F011/**]
feature_flag: F011_FEATURE
branch: s022-working-time
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 6, 9
- Capability contract: `docs/capability-contracts.md` row F011

# S022 — Working time

## Identity

- Parent feature: `F011` Dates and schedules
- Owner: platform
- Branch: `s022-working-time`
- Decision references: `docs/architecture-decisions.md` sections 2–4, 6, 9; `docs/capability-contracts.md` row F011

## Vertical slice

As a project editor, I want to declare which columns hold my schedule, read the computed schedule for every row, and reschedule a task so the end date follows working days in my sheet's timezone, so that the grid, calendar, and Gantt agree on when work happens.

## Requirements

- **SR-S022-01:** `PUT /api/v1/sheets/{sheet_id}/schedule-settings` validates column roles against F007 column types and returns `ScheduleSettingsResponse` with `version`; type mismatches return `field_errors.<field> = "type_mismatch"` (FR-F011-05).
- **SR-S022-02:** `GET /api/v1/sheets/{sheet_id}/schedule` returns settings from `SheetScheduleSettingsRepository::get_for_sheet`, the resolved calendar from `WorkingCalendarRepository::load_resolved_calendar` (its `week` and `exceptions[].hours` assembled from the interval rows), and a cursor page of `RowSchedule` from `page_row_schedules(sheet_id, cursor, limit)` with `status: unscheduled` for rows lacking a start (FR-F011-06).
- **SR-S022-03:** `POST /api/v1/rows/{id}/reschedule` computes the missing member of start/end/duration with pure `calendar_math` functions over the loaded `ResolvedCalendar`, writes cells through F006/F007's `RowRepository`/`CellRepository` inside one `UnitOfWork`, snaps to working days, rejects `end < start` and durations over 3,650 days, and emits `row.rescheduled.v1` (FR-F011-08).
- **SR-S022-04:** Milestone rows are forced to zero duration and parent rows with roll-up rules are rejected with `parent_rollup` (FR-F011-09, FR-F011-10).
- **SR-S022-05:** `datetime` display uses sheet, then user, then tenant timezone, then UTC and returns `display_timezone` (FR-F011-12).
- **SR-S022-06:** `ScheduleSettingsPanel`, `DateCellEditor`, and `WorkingCalendarPage` render loading, empty, error, denied, stale, and offline states and are keyboard operable with the snap announcement (FR-F011-14, NFR-F011-03).
- **SR-S022-07:** Schedule read on a 100,000-row sheet and reschedule meet NFR-F011-01 p95 targets; spans and metrics from NFR-F011-04 are emitted.

## Surfaces

- Infrastructure/container: none
- Rust service/API: `crates/domain/src/schedules/{settings.rs, schedule_read.rs, service_reschedule.rs, timezone.rs}` (use cases over repository traits, no SQL); `crates/persistence/src/schedules/{mod.rs, working_calendar_repository.rs, sheet_schedule_settings_repository.rs}` for `get_for_sheet` and `page_row_schedules`; `services/api/src/schedules/{handlers_settings.rs, handlers_schedule.rs, handlers_reschedule.rs}`
- Data/migration: none new; uses `sheet_schedule_settings`, `working_calendars`, and the interval tables from S021
- React/UI: `apps/web/src/features/schedules/{ScheduleSettingsPanel.tsx, ColumnRolePicker.tsx, CalendarPicker.tsx, TimezoneSelect.tsx, WorkingCalendarPage.tsx, WeekEditor.tsx, ExceptionTable.tsx, DateCellEditor.tsx, DurationInput.tsx, SnapHint.tsx, api.ts, hooks.ts, routes.ts}`
- Mocks/fixtures: seeded sheet with start/end/duration/milestone columns and 50 rows; 100,000-row generator for performance; MSW handlers for component tests

## TDD harness

- Test path: `testing/features/F011/{api,frontend,e2e,accessibility,performance}/`
- Feature flag: `F011_FEATURE`
- Targeted command: `cargo xtask test-feature F011`
- Full command: `cargo xtask test-all`
- First failing tests: `settings_rejects_type_mismatch`, `schedule_read_marks_unscheduled`, `reschedule_computes_end_from_duration`, `reschedule_milestone_forces_zero_duration`, `date_editor_announces_snap`, `schedule_read_100k_p95`

## Exit criteria

- [ ] Requirement tests SR-S022-01 through SR-S022-07 written first and failing
- [ ] Tasks T043 and T044 complete; UI wired to real API through generated client
- [ ] Unit, API, React, E2E, accessibility, permission, and performance tests pass
- [ ] Production call path named: `apps/web/src/features/schedules/ScheduleSettingsPanel.tsx` mounted at `/w/:workspaceId/sheets/:sheetId/settings/schedule`
- [ ] Handoff evidence recorded in the F011 ticket
