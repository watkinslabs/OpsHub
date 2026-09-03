# F034 frontend cases

File: `testing/features/F034/frontend/{heatmap_test.tsx,conflicts_panel_test.tsx,time_sheet_test.tsx,reconcile_queue_test.tsx,effort_panel_test.tsx}` against `apps/web/src/features/workload/`. Flag `F034_FEATURE`.

- `heatmap_cell_shows_utilization_text_and_meter` — FR-F034-13, NFR-F034-03: a 137.5% cell renders `Over 137.5%` as text with a `meter` carrying `aria-valuenow` and an `AlertTriangle` icon, never colour alone.
- `no_capacity_cell_renders_without_percentage` — FR-F034-01: `available_hours` 0 → `No capacity`, no percentage, cell not actionable.
- `heatmap_arrow_keys_move_between_cells` — NFR-F034-03: the grid moves focus with arrow keys and `Enter` opens that resource's conflicts route.
- `heatmap_collapses_to_one_period_under_768px` — FR-F034-13: at 640 px width one period column is shown with previous and next controls.
- `conflicts_panel_renders_over_hours_and_suggestions` — FR-F034-03: `Ana, week of 12 Oct, over by 6 h` with `Shift "Design API" (float 4 d)` and `Reassign to Ben (12 h remaining)`.
- `shift_suggestion_opens_allocation_dialog_with_float_window` — FR-F034-13: `Shift` opens the F033 allocation dialog prefilled with the 4-day float window.
- `reassign_suggestion_calls_update_allocation_and_invalidates` — FR-F034-13: `Reassign` calls `ResourcesApi.updateAllocation` and invalidates `['workload-conflicts']`.
- `empty_conflicts_shows_no_conflicts_state` — FR-F034-13: empty page → `No conflicts` with a check icon and no table chrome.
- `daily_cap_error_rolls_back_optimistic_entry` — FR-F034-04: 400 `invalid` with `field_errors.hours` → optimistic row reverted and the message shown inline.
- `entry_conflict_shows_reload_prompt` — FR-F034-05: 409 → `This entry changed` with a reload action; no silent overwrite.
- `locked_entry_row_is_read_only_with_lock_hint` — FR-F034-05: an entry older than 30 days shows a `Lock` icon and `Contact your resource administrator` and cannot be edited.
- `time_sheet_saves_with_keyboard_only` — NFR-F034-03: `Tab` between day cells and `Enter` saves without a pointer.
- `decision_requires_reason_of_at_least_ten_characters` — FR-F034-08: submit is blocked under 10 characters and the field is described by the error.
- `reconcile_queue_is_server_truth_only` — FR-F034-08: no optimistic mutation; the row leaves the queue only after the response.
- `viewer_does_not_see_import_or_reconcile_actions` — FR-F034-12: `resource-viewer` session hides both entry points.
- `effort_panel_hides_cost_for_non_admin` — FR-F034-09, NFR-F034-02: a response without `planned_cost` renders no cost column.
- `effort_panel_shows_pending_external_separately` — FR-F034-07: `pending_external_hours` 8 is shown apart from `actual_hours` 6.
- `stale_effort_shows_updating_badge_and_refetches` — FR-F034-10: `stale: true` renders `Updating` and refetches every 5 s until fresh.
- `error_banner_surfaces_correlation_id` — FR-F034-11: a 500 response renders the banner with the `correlation_id` from the response.

Evidence: component test report and DOM snapshots under `testing/evidence/F034/frontend/`.
