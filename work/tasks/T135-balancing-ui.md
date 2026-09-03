---
id: T135
type: task
status: planned
parent_epic: E007
parent_feature: F034
parent_story: S068
depends_on: [S068]
owned_paths: [apps/web/src/features/workload/**, testing/features/F034/frontend/**, testing/features/F034/e2e/**, testing/features/F034/accessibility/**]
feature_flag: F034_FEATURE
branch: t135-balancing-ui
started_at: null
finished_at: null
---

# T135 — Workload balancing UI

## Identity

- Parent story: `S068` Time entries and planned versus actual
- Owner: platform
- Branch: `t135-balancing-ui`
- Decision references: `docs/architecture-decisions.md` sections 3, 4; `docs/capability-contracts.md` row F034

## Objective

Build the four workload surfaces and the task-row effort panel — heatmap, conflicts panel with `Shift` and `Reassign` actions that call the F033 allocation API, time entry sheet, reconciliation queue, and planned versus actual panel — covering FR-F034-13, the client half of FR-F034-09 and FR-F034-12, and NFR-F034-03.

## Specification

- Owned files: `apps/web/src/features/workload/{routes.ts, api.ts, hooks.ts, WorkloadPage.tsx, WorkloadHeatmap.tsx, HeatmapCell.tsx, ConflictsPanel.tsx, ConflictItem.tsx, SuggestionActions.tsx, TimeSheetPage.tsx, TimeEntryRow.tsx, TimeEntryDialog.tsx, ImportDialog.tsx, ReconcileQueuePage.tsx, ReconcileDecisionDialog.tsx, EffortPanel.tsx}`.
- Routes: `/w/:workspaceId/workload` (accepts `?from&to&granularity`), `/w/:workspaceId/workload/conflicts`, `/w/:workspaceId/time`, `/w/:workspaceId/workload/reconcile`; `EffortPanel` mounts as the `Effort` tab of the task row side panel.
- Data: generated `WorkloadApi` with `getWorkload`, `listConflicts`, `createTimeEntry`, `updateTimeEntry`, `deleteTimeEntry`, `getRowEffort`, `importTimeEntries`, `reconcileTimeEntries`; `ResourcesApi.updateAllocation` (F033) for `Shift` and `Reassign`. TanStack Query keys `['workload', filters]`, `['workload-conflicts', filters, cursor]`, `['time-entries', resourceId, from, to]`, `['row-effort', rowId, includeChildren]`; when a response carries `stale: true` the query refetches every 5 s until fresh and shows an `Updating` badge.
- Behavior: `HeatmapCell` renders `utilization_pct` as text plus a `meter` with `aria-valuenow`/`aria-valuemin`/`aria-valuemax` and a status word (`Under`, `OK`, `Over 125%`, `No capacity`) alongside a Lucide icon — never colour alone. `ConflictItem` shows `Ana, week of 12 Oct, over by 6 h` with `Shift "Design API" (float 4 d)` and `Reassign to Ben (12 h remaining)`; `Shift` opens the F033 allocation dialog prefilled with the float window, `Reassign` posts the allocation change, and both invalidate `['workload-conflicts']`. `TimeSheetPage` saves optimistically and rolls back on 400 `invalid` (daily cap, with `field_errors.hours` shown inline) or 409 `conflict`; rows older than `time_entry_lock_days` render a `Lock` icon and `Contact your resource administrator` and are not editable. `ReconcileQueuePage` lists pending external entries and requires a 10–1,000 character reason per decision; reconciliation is server-truth only, never optimistic.
- States: skeleton heatmap and lists while loading; `No conflicts` with a check icon and `No time recorded this week` when empty; error banner carrying `correlation_id`; toasts for entry saved, import summary, reconciliation done; `This entry changed` with a reload action on 409; import and reconcile entry points hidden for `resource-viewer` and non-viewers; cost columns hidden unless the effort response carries `planned_cost`; offline queues and disables entry edits.
- Accessibility: heatmap is an ARIA grid with arrow-key navigation and `Enter` opening the resource's conflicts; the time sheet supports `Tab` between day cells and `Enter` to save; all dialogs trap focus and restore it on close; `prefers-reduced-motion` disables cell transitions; axe reports zero serious violations on all four routes.
- Responsive: below 768 px the heatmap shows one period at a time and the time sheet becomes a day list.
- Telemetry: `workload_viewed`, `conflict_suggestion_applied`, `time_entry_recorded`, `time_entries_imported`, `time_entries_reconciled`, `effort_panel_opened` with `resource_id`, `row_id`, `resolution`.
- Dependencies: T133 and T134 routes and DTOs; F033 `ResourcesApi.updateAllocation`; design tokens from `apps/web/src/design/tokens.css` and Lucide icons `Activity`, `AlertTriangle`, `Clock`, `Upload`, `GitMerge`, `Lock`, `CheckCircle2`.
- Rollback: hide the sidebar `Workload` entry and unmount the four routes by disabling `F034_FEATURE`; no client persistence to unwind.

## TDD

- Failing test first: `testing/features/F034/frontend/heatmap_test.tsx::heatmap_cell_shows_utilization_text_and_meter`, `::heatmap_arrow_keys_move_between_cells`, `::no_capacity_cell_renders_without_percentage`; `testing/features/F034/frontend/conflicts_panel_test.tsx::shift_suggestion_opens_allocation_dialog_with_float_window`, `::reassign_suggestion_calls_update_allocation_and_invalidates`; `testing/features/F034/frontend/time_sheet_test.tsx::daily_cap_error_rolls_back_optimistic_entry`, `::locked_entry_row_is_read_only_with_lock_hint`; `testing/features/F034/frontend/reconcile_queue_test.tsx::decision_requires_reason_of_at_least_ten_characters`, `::viewer_does_not_see_import_or_reconcile_actions`; `testing/features/F034/frontend/effort_panel_test.tsx::effort_panel_hides_cost_for_non_admin`, `::stale_effort_shows_updating_badge_and_refetches`; `testing/features/F034/e2e/balancing_spec.ts::manager_shifts_allocation_and_conflict_resolves`, `::engineer_records_six_hours_on_a_task`, `::admin_imports_then_reconciles_pending_entry`; `testing/features/F034/accessibility/axe_spec.ts::workload_pages_have_no_serious_axe_violations`, `::dialogs_trap_and_restore_focus`
- Fixtures/mocks: `testing/fixtures/workload.rs` seed served through the mock API layer (over-allocated week of 2026-10-12, `Design API` float, Ben as reassign candidate, one pending external entry); fixed clock `2026-09-03T00:00:00Z`
- Targeted command: `cargo xtask test-feature F034`
- Full command: `cargo xtask test-all`

## Exit criteria

- [ ] Tests above written before implementation and observed failing
- [ ] Routes registered in the workspace router behind `F034_FEATURE` and reachable from the sidebar `Workload` entry
- [ ] Loading, empty, error, stale, conflict, locked, denied, and offline states covered by component tests
- [ ] axe serious violations = 0 on all four routes; keyboard grid and dialog focus verified
- [ ] Owned-path, 500-line, lint, and type-check gates pass
- [ ] Handoff evidence recorded in S068
- [ ] `finished_at` recorded
