---
id: T051
type: task
status: planned
parent_epic: E003
parent_feature: F013
parent_story: S026
depends_on: [T050]
owned_paths: [crates/domain/src/views/**, services/api/src/views/**, apps/web/src/features/views/**, testing/features/F013/api/**, testing/features/F013/frontend/**, testing/features/F013/e2e/**, testing/features/F013/accessibility/**]
feature_flag: F013_FEATURE
branch: t051-calendar-timeline
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 3, 6
- Capability contract: `docs/capability-contracts.md` row F013

# T051 — Calendar/timeline

## Identity

- Parent story: `S026` Timeline
- Owner: platform
- Branch: `t051-calendar-timeline`
- Decision references: `docs/architecture-decisions.md` sections 3, 6; `docs/capability-contracts.md` row F013

## Objective

Build the calendar and timeline views with timezone-aware rendering, range-bounded row queries, read-only recurrence display, zoom levels, color-by, and drag or keyboard rescheduling through the F011 reschedule route.

## Specification

- Owned paths: `crates/domain/src/views/range.rs`, `services/api/src/views/handlers_rows.rs` (range parameters), `apps/web/src/features/views/{CalendarView.tsx, CalendarEvent.tsx, CalendarHeader.tsx, TimelineView.tsx, TimelineBar.tsx, TimelineHeader.tsx, useViewRows.ts, timezone.ts}`
- Contract/input: `GET /api/v1/views/{id}/rows?range_start=<date>&range_end=<date>` for `calendar` and `timeline` kinds; the wire members `CalendarSettings { date_column_id | start_column_id + end_column_id, mode: month|week|day }` and `TimelineSettings { start_column_id, end_column_id, zoom: day|week|month|quarter, color_by_column_id? }`, composed by `ViewRepository` from `views.date_column_id`, `views.start_column_id`, `views.end_column_id`, `views.calendar_mode`, `views.timeline_zoom`, and `views.color_by_column_id` whose presence per kind is enforced by check constraint; `SchedulesApi.rescheduleRow` from F011; timezone from `sheet_schedule_settings.timezone` with F049 user locale fallback.
- Output/behavior: `range.rs` rejects ranges over 366 days with `invalid` and contributes a range predicate to the specification F008's row repository executes, restricting the rows to those whose date or date pair intersects the range, expanding recurrence rules into read-only occurrences; `CalendarView` renders month, week, and day grids with events placed in the resolved timezone and an agenda list under 640 px; `TimelineView` renders a header scaled by zoom, a pinned label column, and a bar per row colored by the `color_by_column_id` select option; pointer drag or Space/Arrow/Enter moves call `rescheduleRow` with `If-Match` optimistically and roll back on `conflict`; recurrence occurrences show a lock icon and refuse drag; telemetry `calendar_event_rescheduled`, `timeline_bar_moved`, `view_kind_changed`.
- Dependencies: T050 view page shell and row hooks; F011 reschedule handler and schedule settings; F049 locale formatter.
- Feature flag: `F013_FEATURE`.

## TDD

- Failing test first: `testing/features/F013/api/view_rows_tests.rs::calendar_rows_bounded_by_range`, `::range_over_366_days_invalid`, `::timeline_view_requires_start_and_end`; `testing/features/F013/frontend/CalendarView.test.tsx::renders_events_in_sheet_timezone`, `::recurrence_is_read_only`, `::drag_calls_reschedule`; `TimelineView.test.tsx::zoom_changes_header_scale`, `::timeline_bar_move_calls_reschedule`; `testing/features/F013/e2e/views.spec.ts::calendar_drag_reschedules_row`, `::timeline_zoom_and_drag`; `testing/features/F013/accessibility/views.a11y.spec.ts::calendar_and_timeline_no_serious_axe_violations`
- Targeted command: `cargo xtask test-feature F013`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: seeded rows with `Due`, `Start`, `End` across 90 days including one weekly recurrence; sheet timezone `America/New_York`; MSW handlers for reschedule; Playwright against the real API on a seeded tenant

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Timezone and recurrence rendering verified against the fixed clock
- [ ] Component, E2E, and accessibility lanes pass for calendar and timeline
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S026
- [ ] `finished_at` recorded
