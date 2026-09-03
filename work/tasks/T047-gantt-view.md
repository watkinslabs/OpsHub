---
id: T047
type: task
status: planned
parent_epic: E003
parent_feature: F012
parent_story: S024
depends_on: [T046]
owned_paths: [crates/domain/src/dependencies/**, services/api/src/dependencies/**, apps/web/src/features/dependencies/**, testing/features/F012/api/**, testing/features/F012/frontend/**]
feature_flag: F012_FEATURE
branch: t047-gantt-view
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 6
- Capability contract: `docs/capability-contracts.md` row F012

# T047 — Gantt view

## Identity

- Parent story: `S024` Schedule shifts
- Owner: platform
- Branch: `t047-gantt-view`
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 6; `docs/capability-contracts.md` row F012

## Objective

Implement the schedule shift service and route with preview and commit, and build the Gantt page with bars, arrows, milestones, summary bars, critical-path toggle, dependency dialog, and shift dialog wired to the real API.

## Specification

- Owned paths: `crates/domain/src/dependencies/{shift.rs, service_shift.rs}`, `services/api/src/dependencies/handlers_shift.rs`, `apps/web/src/features/dependencies/{GanttPage.tsx, GanttChart.tsx, GanttBar.tsx, MilestoneMarker.tsx, SummaryBar.tsx, DependencyArrow.tsx, DependencyDialog.tsx, CriticalPathToggle.tsx, ShiftDialog.tsx, ShiftPreviewTable.tsx, BaselineOverlaySlot.tsx, api.ts, hooks.ts, routes.ts}`
- Contract/input: `ShiftRequest { row_id?, anchor_date?, delta_days?, preview }` with exactly one of `row_id` or `anchor_date`, `delta_days` within ±3,650; header `If-Match: <schedule_version>`; generated `DependenciesApi` client; route `/w/:workspaceId/sheets/:sheetId?mode=gantt`.
- Output/behavior: `POST /api/v1/sheets/{sheet_id}/schedule/shift` computes `ShiftPlan` by moving the target(s) and pushing each successor by the minimum working-day amount that satisfies its constraints through `add_working_days`; `preview: true` returns `ShiftResponse { committed: false, affected }` without writes; `preview: false` requires `project-editor`, writes start/end cells in one transaction, audit event `schedule.shift`, `schedule.shifted.v1` once, returns new `schedule_version`; more than 10,000 affected rows or 2 s elapsed returns `503 unavailable` `details.reason = "shift_budget"`; metric `schedule_shift_duration_ms`. The Gantt renders rows from `['sheet-rows']`, arrows from `['dependencies']`, critical highlights from `['critical-path']`; bar drag or `Shift+Arrow` calls preview, shows `ShiftPreviewTable`, commits on confirm, rolls back on `conflict`; `BaselineOverlaySlot` accepts an optional baseline prop rendered by F015; states: loading, empty (no schedule settings), error, denied, stale, offline, not-found; telemetry `gantt_opened`, `dependency_created`, `dependency_cycle_rejected`, `critical_path_toggled`, `schedule_shift_previewed`, `schedule_shift_committed`.
- Dependencies: T046 graph and critical path; F011 calendar arithmetic; F006 sheet page mode switch for the `Gantt` entry point.
- Feature flag: `F012_FEATURE` read through the flag hook; the Gantt mode and shift route are absent when off.

## TDD

- Failing test first: `testing/features/F012/api/shift_tests.rs::shift_preview_writes_nothing`, `::shift_commit_moves_successors_across_holiday`, `::shift_anchor_reanchors_whole_sheet`, `::shift_over_budget_unavailable`, `::shift_stale_schedule_version_conflicts`, `::shift_viewer_commit_denied`; `testing/features/F012/frontend/GanttChart.test.tsx::renders_bars_arrows_and_milestones`, `::critical_toggle_highlights_zero_float`, `ShiftDialog.test.tsx::preview_table_then_commit`, `::rolls_back_on_conflict`, `DependencyDialog.test.tsx::shows_cycle_path_error`
- Targeted command: `cargo xtask test-feature F012`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: seeded 12-row schedule with holiday; MSW handlers from the fixture; 1,000-successor chain generator

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Shift p95 target from NFR-F012-01 met; component lane passes
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S024
- [ ] `finished_at` recorded
