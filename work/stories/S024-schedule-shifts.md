---
id: S024
type: story
status: planned
parent_epic: E003
parent_feature: F012
depends_on: [S023]
owned_paths: [crates/domain/src/dependencies/**, services/api/src/dependencies/**, apps/web/src/features/dependencies/**, testing/features/F012/**]
feature_flag: F012_FEATURE
branch: s024-schedule-shifts
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 6
- Capability contract: `docs/capability-contracts.md` row F012

# S024 — Schedule shifts

## Identity

- Parent feature: `F012` Dependencies and Gantt
- Owner: platform
- Branch: `s024-schedule-shifts`
- Decision references: `docs/architecture-decisions.md` sections 2–4, 6; `docs/capability-contracts.md` row F012

## Vertical slice

As a project editor, I want to preview and commit a shift of one task or the whole sheet so that successors move across working days automatically, and I want to do it from a Gantt view with bars, arrows, milestones, and a critical-path toggle, so that a slipped task updates the plan in one confirmed action.

## Requirements

- **SR-S024-01:** `POST /api/v1/sheets/{sheet_id}/schedule/shift` with `{ row_id, delta_days, preview: true }` returns `ShiftResponse { committed: false, affected }` listing every transitively affected row with old and new start/finish and writes nothing (FR-F012-11).
- **SR-S024-02:** `{ anchor_date, preview: false }` re-anchors the sheet so its earliest start equals `anchor_date`, moving every row by the same working-day distance and skipping calendar exceptions from F011 (FR-F012-11).
- **SR-S024-03:** A committed shift updates start and end cells of all affected rows in one transaction under the sheet `If-Match` schedule version, writes one audit event with before/after dates, publishes `schedule.shifted.v1` once, and returns the new `schedule_version` (FR-F012-12).
- **SR-S024-04:** Shifts affecting more than 10,000 rows or exceeding 2 s return `503 unavailable` with `details.reason = "shift_budget"` and change nothing (FR-F012-13).
- **SR-S024-05:** `GanttChart` renders bars, arrows, milestone diamonds, and parent summary bars from the dependency and critical-path APIs; `CriticalPathToggle` highlights zero-float rows; drag and `Shift+Arrow` open `ShiftDialog` with the preview table before commit (FR-F012-14, NFR-F012-03).
- **SR-S024-06:** Gantt shows loading, empty (no schedule settings), error, denied, stale, and offline states; viewers see read-only bars and non-members get not-found (FR-F012-14, FR-F012-15).
- **SR-S024-07:** Critical path on 10,000 rows/20,000 links and a 1,000-successor shift meet NFR-F012-01.

## Surfaces

- Infrastructure/container: none
- Rust service/API: `crates/domain/src/dependencies/{shift.rs, service_shift.rs}`; `services/api/src/dependencies/handlers_shift.rs`
- Data/migration: none new; uses tables from S023
- React/UI: `apps/web/src/features/dependencies/{GanttPage.tsx, GanttChart.tsx, GanttBar.tsx, MilestoneMarker.tsx, SummaryBar.tsx, DependencyArrow.tsx, DependencyDialog.tsx, CriticalPathToggle.tsx, ShiftDialog.tsx, ShiftPreviewTable.tsx, BaselineOverlaySlot.tsx, api.ts, hooks.ts}`
- Mocks/fixtures: seeded 12-row schedule with a holiday exception; 10,000-row/20,000-link generator for performance lane; MSW handlers for component tests

## TDD harness

- Test path: `testing/features/F012/{api,frontend,e2e,accessibility,performance}/`
- Feature flag: `F012_FEATURE`
- Targeted command: `cargo xtask test-feature F012`
- Full command: `cargo xtask test-all`
- First failing tests: `shift_preview_writes_nothing`, `shift_commit_moves_successors_across_holiday`, `shift_over_budget_unavailable`, `gantt_drag_opens_preview_then_commits`, `critical_path_10k_p95`

## Exit criteria

- [ ] Requirement tests SR-S024-01 through SR-S024-07 written first and failing
- [ ] Tasks T047 and T048 complete; UI wired to real API through generated client
- [ ] Unit, API, React, E2E, accessibility, permission, and performance tests pass
- [ ] Production call path named: `apps/web/src/features/dependencies/GanttPage.tsx` mounted at `/w/:workspaceId/sheets/:sheetId?mode=gantt`
- [ ] Handoff evidence recorded in the F012 ticket
