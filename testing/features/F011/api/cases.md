# F011 api cases

File: `testing/features/F011/api/{type_tests.rs,calendar_tests.rs,calendar_math_tests.rs,settings_tests.rs,schedule_tests.rs}`. Flag `F011_FEATURE`.

- `date_types_parse_and_reject` — FR-F011-01: `"2026-09-14"` accepted; `"14/09/2026"` and `"2026-02-30"` → 400 with `field_errors.<column_id>`.
- `datetime_round_trips_microseconds` — FR-F011-01: `2026-09-14T07:00:00.123456Z` stored and returned unchanged; `display` rendered in `Europe/Berlin`.
- `duration_rejects_negative_and_unknown_unit` — FR-F011-01: `{ value: -1 }` and `{ unit: "weeks" }` → 400.
- `calendar_create_validates_week` — FR-F011-02: overlapping intervals `09:00–13:00` and `12:00–17:00` → 400 `field_errors.week`; valid body → 201 version 1.
- `calendar_default_materialized_on_first_list` — FR-F011-02: empty tenant GET → one `Standard` calendar, Mon–Fri 09:00–17:00, 8 h.
- `calendar_default_swap_is_atomic` — FR-F011-03: PATCH `is_default: true` on `Berlin` → `Standard.is_default` false in the same response version.
- `calendar_stale_version_conflicts` — FR-F011-03: `If-Match: 1` against version 2 → 409 with `current_version: 2`.
- `calendar_exceptions_limit_400` — FR-F011-04: 400 exceptions accepted; 401 → 400 `field_errors.exceptions`; duplicate date → 409.
- `calendar_cross_tenant_not_found` — FR-F011-13: tenant B GET/PATCH `Berlin` → 404.
- `calendar_viewer_create_denied` — FR-F011-13: viewer POST → 403 `denied`.
- `add_working_days_skips_weekend_and_holiday` — FR-F011-07: Fri 2026-09-11 + 3 → 2026-09-16; with holiday on 09-14 → 2026-09-17.
- `working_exception_adds_saturday` — FR-F011-04: `working` exception on 2026-09-12 makes Fri + 1 → Sat.
- `dst_transition_does_not_shift_dates` — FR-F011-07: 2026-03-27 + 2 across the EU DST change → 2026-03-31 with no hour drift.
- `settings_rejects_type_mismatch` — FR-F011-05: number column as `start_column_id` → 400 `type_mismatch`.
- `settings_requires_same_type_for_start_and_end` — FR-F011-05: date start with datetime end → 400.
- `schedule_read_marks_unscheduled` — FR-F011-06: rows without start return `start: null`, `status: unscheduled`; 500-row page in position order.
- `schedule_read_uses_sheet_timezone` — FR-F011-12: sheet `Asia/Tokyo` overrides user `Europe/Berlin`; `display_timezone: "Asia/Tokyo"`.
- `reschedule_computes_end_from_duration` — FR-F011-08: start 2026-09-11, duration 3d → end 2026-09-16, `row.rescheduled.v1` with old/new values.
- `reschedule_snaps_start_off_holiday` — FR-F011-07: start 2026-12-25 → stored 2026-12-28, `snap_applied: true`.
- `reschedule_rejects_end_before_start` — FR-F011-08: end < start → 400 `field_errors.end = "before_start"`.
- `reschedule_milestone_forces_zero_duration` — FR-F011-09: milestone with duration 2 → 400; without duration → end = start.
- `reschedule_parent_with_rollup_rejected` — FR-F011-10: parent row with roll-up rule → 400 `parent_rollup`.
- `reschedule_idempotent_replay_returns_original` — FR-F011-11: same key twice → one cell write; different body → 409.
- `reschedule_viewer_denied` — FR-F011-13: viewer POST → 403 and cells unchanged.
- `request_span_carries_schedule_ids` — NFR-F011-04: span has `tenant_id`, `sheet_id`, `calendar_id`, `correlation_id`; metric `schedule_reschedule_duration_ms` observed.

Evidence: JUnit output and request logs under `testing/evidence/F011/api/`.
