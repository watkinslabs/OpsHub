# F012 frontend cases

File: `testing/features/F012/frontend/{GanttChart.test.tsx,ShiftDialog.test.tsx,DependencyDialog.test.tsx}`. Vitest with MSW. Flag `F012_FEATURE`.

- `renders_bars_arrows_and_milestones` — FR-F012-14: seeded schedule renders 12 bars, 9 arrows, one diamond, one summary bar.
- `critical_toggle_highlights_zero_float` — FR-F012-14: toggling applies the critical token class to `is_critical` rows only and emits `critical_path_toggled`.
- `shows_loading_skeleton_then_chart` — FR-F012-14: pending queries show skeleton bars; resolves to chart.
- `shows_empty_state_without_schedule_settings` — FR-F012-14: 400 `unscheduled` renders the `Add dates` prompt linking to F011 settings.
- `shows_error_banner_with_correlation_id` — NFR-F012-04: 500 shows banner with `correlation_id` and retry.
- `viewer_hides_link_and_shift_controls` — FR-F012-15: viewer role renders bars without drag handles or `Add dependency`.
- `preview_table_then_commit` — FR-F012-11: drag +3 days calls `shiftSchedule` with `preview: true`, renders affected rows, confirm calls with `preview: false`.
- `rolls_back_on_conflict` — FR-F012-12: commit 409 restores bar positions and shows the stale banner.
- `shows_budget_error` — FR-F012-13: 503 `shift_budget` renders `Too many rows to shift (10,000 limit)`.
- `keyboard_shift_opens_dialog` — FR-F012-14: `Shift+ArrowRight` on a focused bar opens `ShiftDialog` with `delta_days: 1`.
- `shows_cycle_path_error` — FR-F012-03: 400 `cycle` renders `Would create a cycle: Design → Build → Test → Design` and keeps focus on successor.
- `offline_disables_drag` — FR-F012-14: `navigator.onLine=false` shows offline badge and disables drag handles.

Evidence: Vitest JUnit under `testing/evidence/F012/frontend/`.
