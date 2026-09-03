# F011 e2e cases

File: `testing/features/F011/e2e/schedule.spec.ts`. Playwright against seeded tenant. Flag `F011_FEATURE`.

- `configure_schedule_and_reschedule_over_holiday` — FR-F011-05, FR-F011-07, FR-F011-08: editor configures start/end/duration, sets duration `3d` on "Kickoff" starting Fri 2026-12-18 on `Berlin`, end shows 2026-12-28 after skipping the weekend and 12-25; reload persists.
- `admin_edits_calendar_and_default` — FR-F011-02, FR-F011-03: admin adds a Saturday working exception, makes `Berlin` the default, `Standard` loses the default badge.
- `viewer_sees_read_only_settings` — FR-F011-13: viewer opens settings route; form disabled; date cells open read-only.
- `milestone_row_keeps_zero_duration` — FR-F011-09: toggling milestone on a row collapses the end date to the start and disables duration.
- `concurrent_settings_edit_shows_stale` — FR-F011-11: second session changes the calendar; first session save shows the stale banner and reloads.
- `datetime_renders_in_sheet_timezone` — FR-F011-12: user in `America/New_York` sees a `datetime` cell rendered in the sheet's `Asia/Tokyo` with the timezone label.

Evidence: Playwright traces and videos under `testing/evidence/F011/e2e/`.
