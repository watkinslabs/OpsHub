# F012 api cases

File: `testing/features/F012/api/{dependency_tests.rs,critical_path_tests.rs,shift_tests.rs}`. Flag `F012_FEATURE`.

- `dependency_create_returns_version_one` — FR-F012-01: POST `/api/v1/dependencies` FS lag 2 as project editor → 201, `version: 1`, `dependency.created.v1` in outbox.
- `dependency_self_link_invalid` — FR-F012-02: same row on both sides → 400 `field_errors.successor_row_id = "self"`.
- `dependency_cross_sheet_invalid` — FR-F012-02: successor from another sheet → 400 `different_sheet`.
- `dependency_parent_row_invalid` — FR-F012-09: parent row as predecessor → 400 `field_errors.predecessor_row_id = "parent_row"`.
- `dependency_cycle_rejected_with_path` — FR-F012-03: closing Design→Build→Test→Design → 400 `cycle`, `details.cycle_path` has four ids, count unchanged.
- `dependency_cycle_check_serialized_per_sheet` — FR-F012-03: two concurrent inserts that only cycle together → exactly one succeeds.
- `dependency_duplicate_pair_conflicts` — FR-F012-04: repeat pair → 409 with `details.existing_id`.
- `dependency_sheet_limit_invalid` — FR-F012-05: 20,000 seeded links, one more → 400 `field_errors.sheet_id = "limit"`.
- `dependency_list_filters_by_row_and_kind` — FR-F012-06: 2,500 links, `limit=1000` three pages; `row_id` matches either side; `kind=SF` filter.
- `dependency_update_and_delete_emit_events` — FR-F012-06: PATCH lag with `If-Match` → `dependency.updated.v1`; DELETE → `dependency.deleted.v1`; stale version → 409.
- `dependency_lag_out_of_range_invalid` — FR-F012-07: lag 3,651 days or 87,601 hours → 400 `field_errors.lag = "range"`.
- `critical_path_marks_zero_float_rows` — FR-F012-08: seeded sheet → longest chain has `total_float_days: 0`, `is_critical: true`, others positive float.
- `critical_path_respects_each_link_kind` — FR-F012-08: SS, FF, SF constraints move successors as specified.
- `critical_path_negative_lag_leads_successor` — FR-F012-07: FS lag −2 → successor starts two working days before predecessor finish.
- `critical_path_hours_lag_uses_working_window` — FR-F012-07: 12 hours lag on an 8-hour day → 1.5 working days.
- `critical_path_skips_calendar_exceptions` — FR-F012-08: chain across the holiday exception → dates skip it.
- `critical_path_rolls_up_parent_rows` — FR-F012-09: parent `early_start` = min child, `early_finish` = max child.
- `critical_path_milestone_zero_duration` — FR-F012-10: duration 0 row → `early_start == early_finish`, included in float.
- `critical_path_unscheduled_sheet_invalid` — FR-F012-08: sheet without F011 settings → 400 `field_errors.sheet_id = "unscheduled"`.
- `shift_preview_writes_nothing` — FR-F012-11: `preview: true` → `committed: false`, 15 affected rows, cell versions unchanged.
- `shift_commit_moves_successors_across_holiday` — FR-F012-11, FR-F012-12: +3 days → successors land after the holiday; one audit event; one `schedule.shifted.v1`.
- `shift_anchor_reanchors_whole_sheet` — FR-F012-11: `anchor_date` → earliest start equals anchor, relative offsets in working days preserved.
- `shift_over_budget_unavailable` — FR-F012-13: 10,001-row chain → 503 `details.reason = "shift_budget"`, no writes.
- `shift_stale_schedule_version_conflicts` — FR-F012-12: `If-Match` behind → 409 with `current_version`.
- `shift_viewer_commit_denied` — FR-F012-15: viewer `preview: false` → 403; `preview: true` → 200.
- `dependency_cross_tenant_not_found` — FR-F012-15: tenant B on all six routes → 404.
- `request_span_carries_ids_and_metrics` — NFR-F012-04: span has `tenant_id`, `sheet_id`, `correlation_id`, `affected_rows`; `dependencies_cycle_rejections_total` increments.

Evidence: JUnit output and request logs under `testing/evidence/F012/api/`.
