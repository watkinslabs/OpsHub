---
id: S068
type: story
status: planned
parent_epic: E007
parent_feature: F034
depends_on: [F034]
owned_paths: [apps/web/src/features/workload/**, services/worker/src/workload/**, testing/features/F034/frontend/**, testing/features/F034/e2e/**, testing/features/F034/accessibility/**, testing/features/F034/performance/**]
feature_flag: F034_FEATURE
branch: s068-time-entries-and-planned-vs-actual
started_at: null
finished_at: null
---

# S068 — Time entries and planned versus actual

## Identity

- Parent feature: `F034` Workload/actuals
- Owner: platform
- Branch: `s068-time-entries-and-planned-vs-actual`
- Child tasks: `T135` balancing UI, `T136` performance tests
- Decision references: `docs/architecture-decisions.md` sections 3, 4, 9; `docs/capability-contracts.md` row F034

## Vertical slice

As a resource manager and as an engineer, I want the workload heatmap, conflicts panel, time sheet, reconciliation queue, and a planned versus actual panel on every task row, backed by summaries that stay fresh and fast, so that over-allocation is visible and variance against plan is answered in one place.

The slice is the `summary_builder` worker plus the five web surfaces and the latency and reliability gates that keep them usable at 1,000 resources. The routes, tables, conflict detector, and reconciliation semantics they consume are S067 (T133, T134).

## Requirements

- **SR-S068-01:** `services/worker/src/workload/summary_builder.rs` maintains `effort_summaries` for scopes `row`, `project`, and `resource_period` within 60 seconds of `time-entry.recorded.v1`, `time-entry.reconciled.v1`, `allocation.*.v1`, and `capacity.computed.v1`, recording `computed_at` and `source_versions`; reads serve from summaries and report `stale: true` when a newer source event is queued (covers FR-F034-10).
- **SR-S068-02:** `GET /api/v1/rows/{id}/effort` renders in the task-row `Effort` tab as `planned_hours`, `actual_hours`, `pending_external_hours`, `remaining_hours`, `variance_hours`, `variance_pct`, and `by_resource[]`, with the F009 descendant rollup when `include_children=true` and cost figures only for `resource-admin` (FR-F034-09, NFR-F034-02).
- **SR-S068-03:** The web surfaces at `/w/:workspaceId/workload`, `/workload/conflicts`, `/time`, and `/workload/reconcile` provide the resource-by-period heatmap, the conflicts panel whose `Shift` and `Reassign` actions call the F033 allocation API, the current user's time sheet, the reconciliation queue, and the effort panel, with loading, empty, error, stale, conflict, locked, denied, and offline states (FR-F034-13).
- **SR-S068-04:** Client permission behavior: `resource-viewer` sees workload, conflicts, and effort without cost columns and without import or reconcile entry points; a non-viewer sees only their own row and entries; a cross-tenant id lands on the not-found view (FR-F034-12).
- **SR-S068-05:** Accessibility: heatmap cells expose utilization as text with `meter` semantics, status is carried by text and icon, the grid is arrow-key navigable, the time sheet is keyboard editable, dialogs trap and restore focus, `prefers-reduced-motion` disables cell transitions, and axe reports no serious violations on the four routes (NFR-F034-03).
- **SR-S068-06:** Performance budgets are executable gates: workload for 1,000 resources over 12 weeks under 500 ms p95 from summaries, conflict detection within 30 seconds of `capacity.computed.v1`, native entry create under 800 ms p95, and a 2,000-entry import under 5 seconds (NFR-F034-01).
- **SR-S068-07:** Reliability: the summary and conflict jobs are idempotent by `(scope_id, source_version)`, retried three times, and dead-lettered with `last_error`; import is atomic per request; spans carry `tenant_id`, `resource_id`, `row_id`, `time_entry_id`, and `correlation_id`; `workload_summary_lag_seconds` and `conflict_detection_ms` are exported (NFR-F034-04).

## Surfaces

- Worker: `services/worker/src/workload/summary_builder.rs` registered in `services/worker/src/registry.rs` behind `F034_FEATURE`, with `rebuild_summaries` as the repair path
- React/UI: `apps/web/src/features/workload/{routes.ts, api.ts, hooks.ts, WorkloadPage.tsx, WorkloadHeatmap.tsx, HeatmapCell.tsx, ConflictsPanel.tsx, ConflictItem.tsx, SuggestionActions.tsx, TimeSheetPage.tsx, TimeEntryRow.tsx, TimeEntryDialog.tsx, ImportDialog.tsx, ReconcileQueuePage.tsx, ReconcileDecisionDialog.tsx, EffortPanel.tsx}`
- State: TanStack Query keys `['workload', filters]`, `['workload-conflicts', filters, cursor]`, `['time-entries', resourceId, from, to]`, `['row-effort', rowId, includeChildren]`; a `stale` response refetches every 5 seconds until fresh
- Telemetry: `workload_viewed`, `conflict_suggestion_applied`, `time_entry_recorded`, `time_entries_imported`, `time_entries_reconciled`, `effort_panel_opened`
- Mocks/fixtures: `testing/fixtures/workload.rs` served through the mock API layer for component tests, and `testing/fixtures/workload.rs::large_tenant` (1,000 resources, 12 weeks, 40,000 entries, 120 conflicts) for the performance lane

## TDD harness

- Test path: `testing/features/F034/{frontend,e2e,accessibility,performance}/`
- Feature flag: `F034_FEATURE`
- Targeted command: `cargo xtask test-feature F034`
- Full command: `cargo xtask test-all`
- First failing tests: `heatmap_cell_shows_utilization_text_and_meter`, `shift_suggestion_opens_allocation_dialog_with_float_window`, `daily_cap_error_rolls_back_optimistic_entry`, `effort_panel_hides_cost_for_non_admin`, `stale_effort_shows_updating_badge_and_refetches`, `manager_shifts_allocation_and_conflict_resolves`, `workload_1000_resources_12_weeks_under_500ms_p95`, `summaries_refresh_within_60s_of_recorded_event`, `workload_pages_have_no_serious_axe_violations`

## Exit criteria

- [ ] SR-S068-01 through SR-S068-07 written as failing tests before implementation
- [ ] Tasks T135 and T136 complete; the four routes are mounted behind `F034_FEATURE` and `summary_builder.rs` is registered in `services/worker/src/registry.rs`
- [ ] Component, E2E, accessibility, and performance lanes pass in targeted and full modes
- [ ] All five latency budgets met on CI hardware for three consecutive runs, archived under `testing/evidence/F034/performance/`
- [ ] axe serious violations = 0 on `/workload`, `/workload/conflicts`, `/time`, and `/workload/reconcile`
- [ ] Handoff evidence recorded in the F034 ticket
