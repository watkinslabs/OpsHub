# F011 frontend cases

File: `testing/features/F011/frontend/{ScheduleSettingsPanel.test.tsx,DateCellEditor.test.tsx,WeekEditor.test.tsx,WorkingCalendarPage.test.tsx}`. Vitest with MSW. Flag `F011_FEATURE`.

- `saves_roles_and_shows_version` — FR-F011-05: choosing start/end/duration columns and saving calls `putScheduleSettings` with `If-Match` and shows the toast.
- `shows_type_mismatch_field_error` — FR-F011-05: 400 `type_mismatch` renders inline under the offending picker.
- `shows_stale_banner_on_conflict` — FR-F011-11: 409 renders `Settings changed by someone else` with reload.
- `shows_empty_state_when_unconfigured` — FR-F011-14: 404 settings renders `Configure schedule` call to action.
- `shows_denied_read_only_for_viewer` — FR-F011-13: viewer role renders the panel disabled with explanation.
- `date_editor_announces_snap` — FR-F011-14, NFR-F011-03: picking 2026-12-25 on `Berlin` shows and announces `Moved from 2026-12-25 (Christmas)`.
- `date_editor_shows_display_timezone` — FR-F011-12: datetime editor label reads `Europe/Berlin` from the schedule response.
- `duration_input_parses_days_and_hours` — FR-F011-01: `3d`, `1.5d`, `12h` map to `{ value, unit }`; `3w` shows an error.
- `rejects_overlapping_intervals` — FR-F011-02: `WeekEditor` blocks save when Monday intervals overlap.
- `exception_table_limits_400` — FR-F011-04: adding the 401st exception shows the limit message and disables add.
- `offline_disables_schedule_edits` — FR-F011-14: `navigator.onLine=false` disables the panel and shows the badge.
- `reschedule_emits_telemetry` — FR-F011-14: committing the editor emits `row_rescheduled` with `snap_applied`.

Evidence: Vitest JUnit under `testing/evidence/F011/frontend/`.
