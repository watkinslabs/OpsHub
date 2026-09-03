---
id: T044
type: task
status: planned
parent_epic: E003
parent_feature: F011
parent_story: S022
depends_on: [T043]
owned_paths: [apps/web/src/features/schedules/**, testing/features/F011/frontend/**, testing/features/F011/e2e/**, testing/features/F011/accessibility/**]
feature_flag: F011_FEATURE
branch: t044-date-ui-tests
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` section 6
- Capability contract: `docs/capability-contracts.md` row F011

# T044 — Date UI tests

## Identity

- Parent story: `S022` Working time
- Owner: platform
- Branch: `t044-date-ui-tests`
- Decision references: `docs/architecture-decisions.md` section 6; `docs/capability-contracts.md` row F011

## Objective

Build the schedule settings panel, working-calendar admin page, and date/duration cell editor with snap preview, and prove them with component, E2E, and accessibility tests against the real schedule API.

## Specification

- Owned paths: `apps/web/src/features/schedules/{ScheduleSettingsPanel.tsx, ColumnRolePicker.tsx, CalendarPicker.tsx, TimezoneSelect.tsx, WorkingCalendarPage.tsx, WeekEditor.tsx, ExceptionTable.tsx, DateCellEditor.tsx, DurationInput.tsx, SnapHint.tsx, api.ts, hooks.ts, routes.ts}`
- Contract/input: generated `SchedulesApi` client; route params `workspaceId`, `sheetId`; `DateCellEditor` props `{ value, columnType, settings, calendar, onCommit }`; `DurationInput` parses `3d`, `1.5d`, `12h`.
- Output/behavior: settings panel saves with `If-Match` and shows stale banner on `conflict`; calendar page edits week intervals and exceptions with inline validation; date editor shows the resolved working day before commit, calls `rescheduleRow` when the column is the start, end, or duration role, otherwise the F008 cell patch; `SnapHint` renders `Moved from 2026-12-25 (Christmas)` and announces via a live region; states: loading, empty (`Configure schedule`), error with correlation ID, denied read-only, stale, offline; telemetry `schedule_settings_saved`, `calendar_created`, `row_rescheduled`, `date_editor_opened`.
- Dependencies: T043 routes; F008 grid cell editor slot for `date`, `datetime`, `duration` columns; F005 admin shell for `/admin/working-calendars`.
- Feature flag: `F011_FEATURE` read through the flag hook; routes and editor slot are not registered when off.

## TDD

- Failing test first: `testing/features/F011/frontend/ScheduleSettingsPanel.test.tsx::saves_roles_and_shows_version`, `::shows_type_mismatch_field_error`, `::shows_stale_banner_on_conflict`; `DateCellEditor.test.tsx::date_editor_announces_snap`, `::duration_input_parses_days_and_hours`; `WeekEditor.test.tsx::rejects_overlapping_intervals`; `testing/features/F011/e2e/schedule.spec.ts::configure_schedule_and_reschedule_over_holiday`, `::admin_edits_calendar_and_default`, `::viewer_sees_read_only_settings`; `testing/features/F011/accessibility/schedule.a11y.spec.ts::settings_and_calendar_pages_have_no_serious_axe_violations`, `::date_picker_keyboard_only`
- Targeted command: `cargo xtask test-feature F011`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: MSW handlers from the seeded schedule fixture; Playwright uses the real API against a seeded tenant with the `Berlin` calendar

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Component, E2E, and accessibility lanes pass
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S022
- [ ] `finished_at` recorded
