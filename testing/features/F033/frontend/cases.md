# F033 frontend cases

File: `testing/features/F033/frontend/{ResourceDirectoryPage.test.tsx,ResourcePage.test.tsx,CapacityStrip.test.tsx,AvailabilityEditor.test.tsx,PlannerGrid.test.tsx,AllocationDialog.test.tsx}`. Vitest with MSW. Flag `F033_FEATURE`.

- `directory_renders_skill_and_leave_badges` — FR-F033-13: two resources render with `Rust 4` badge and `On leave 5–9 Oct` badge.
- `directory_filters_by_skill_level` — FR-F033-02: skill filter `Rust ≥ 3` calls `listResources` with `skill` and `min_level`.
- `renders_periods_as_meters` — FR-F033-13, NFR-F033-03: capacity strip renders one `meter` per week with `available/allocated` text.
- `capacity_strip_marks_over_allocated_week` — FR-F033-06: week with `over_allocated: true` shows `Over by 4 h` and the warning icon.
- `hides_cost_rates_for_viewer` — FR-F033-12: viewer role hides `CostRatesEditor` and cost columns; admin sees them.
- `availability_editor_blocks_overlap` — FR-F033-04: overlapping entries show inline error before submit; server `availability[1]` error mapped to the row.
- `planner_marks_over_allocated_cell` — FR-F033-13: fixture week renders red `Over by 4 h` cell with text and icon.
- `planner_keyboard_grid_navigation` — NFR-F033-03: arrow keys move focus between cells; `Enter` opens `AllocationDialog` for the focused resource and week.
- `rejects_hours_and_percent_together` — FR-F033-08: dialog blocks submit; server `field_errors.planned` shown inline.
- `allocation_dialog_requires_role_and_confidence` — FR-F033-08: empty role or confidence blocks submit.
- `optimistic_allocation_rolls_back_on_conflict` — FR-F033-09: 409 restores the previous bar and shows the stale banner.
- `shows_loading_empty_error_states` — FR-F033-13: skeleton, `No resources yet`, and error banner with `correlation_id`.
- `offline_disables_planner_edits` — FR-F033-13: `navigator.onLine=false` shows offline badge and disables cell actions.
- `single_resource_planner_under_768px` — FR-F033-13: narrow viewport renders one resource with a week picker.

Evidence: Vitest JUnit under `testing/evidence/F033/frontend/`.
