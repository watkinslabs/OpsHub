# F013 frontend cases

File: `testing/features/F013/frontend/{CardView.test.tsx,CalendarView.test.tsx,TimelineView.test.tsx,FilterBuilder.test.tsx,ShareViewDialog.test.tsx,ViewSwitcher.test.tsx}`. Vitest with MSW. Flag `F013_FEATURE`.

- `renders_lane_per_select_option` — FR-F013-13: card view on `Status` renders `Backlog`, `Doing`, `Done` lanes with cards showing `card_fields`.
- `keyboard_lane_move_patches_cell` — FR-F013-07: Space, ArrowRight, Enter on a card calls `patchCells` with the lane column and `If-Match`.
- `rolls_back_on_conflict` — FR-F013-07: `patchCells` 409 returns the card to its lane and shows the stale banner.
- `renders_events_in_sheet_timezone` — FR-F013-06: `Due` of `2026-09-10T03:30:00Z` renders on 9 September in `America/New_York`.
- `recurrence_is_read_only` — FR-F013-06: weekly occurrence shows the lock icon and ignores drag.
- `drag_calls_reschedule` — FR-F013-07: dropping an event on the next day calls `rescheduleRow` with the new date.
- `zoom_changes_header_scale` — FR-F013-04: switching `zoom` from `week` to `quarter` re-renders the timeline header with quarter columns.
- `timeline_bar_move_calls_reschedule` — FR-F013-07: ArrowRight on a focused bar with `zoom=day` calls `rescheduleRow` one day later.
- `limits_operators_to_column_type` — FR-F013-02: `FilterBuilder` offers `before`/`after` for dates and `contains` for text only; 51st condition is blocked with a message.
- `creates_link_share_and_copies_url` — FR-F013-10: dialog submits a link share with a 30-day expiry and copies `/public/views/{token}`.
- `hidden_for_non_owner` — FR-F013-10: share button absent when the viewer is not the owner.
- `switcher_lists_default_first` — FR-F013-13: `ViewSwitcher` shows the default view first with a star and grouped by kind.
- `shows_empty_state_with_clear_filters` — FR-F013-13: zero matching rows shows `No rows match this view` and `Clear filters` resets the AST.
- `shows_error_banner_with_correlation_id` — NFR-F013-04: 500 on view rows shows banner containing `correlation_id` and retry.
- `offline_disables_drag` — FR-F013-13: `navigator.onLine=false` shows the offline badge and removes drag handles.

Evidence: Vitest JUnit under `testing/evidence/F013/frontend/`.
