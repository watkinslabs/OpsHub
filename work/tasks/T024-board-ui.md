---
id: T024
type: task
status: planned
parent_epic: E002
parent_feature: F006
parent_story: S012
depends_on: [T023]
owned_paths: [apps/web/src/features/sheets/**, testing/features/F006/frontend/**, testing/features/F006/e2e/**, testing/features/F006/accessibility/**]
feature_flag: F006_FEATURE
branch: t024-board-ui
started_at: null
finished_at: null
---

# T024 — Board UI

## Identity

- Parent story: `S012` Create/update row
- Owner: platform
- Branch: `t024-board-ui`
- Decision references: `docs/architecture-decisions.md` section 6; `docs/capability-contracts.md` row F006

## Objective

Build the sheet page with grid and board modes, the new-sheet and restore dialogs, and keyboard-accessible card moves wired to the real row API.

## Specification

- Owned paths: `apps/web/src/features/sheets/{SheetPage.tsx, SheetHeader.tsx, GridView.tsx, GroupSection.tsx, RowLine.tsx, BoardView.tsx, BoardLane.tsx, RowCard.tsx, NewSheetDialog.tsx, RestoreSheetDialog.tsx, api.ts, hooks.ts, routes.ts}`
- Contract/input: generated `SheetsApi` client; route params `workspaceId`, `sheetId`, query `mode=grid|board`.
- Output/behavior: grid lists groups as sections and rows by position with the primary column frozen; board renders groups as lanes; drag or keyboard move calls `moveRow` optimistically and rolls back on `conflict` with the stale banner; states: loading skeleton, empty call to action, error banner with correlation ID, denied affordances for viewers, not-found page, offline badge; Lucide icons and design tokens per ticket section 3; telemetry events `sheet_opened`, `row_created`, `row_moved`, `sheet_mode_changed`.
- Dependencies: T023 routes; F005 workspace shell for navigation and the `New sheet` entry point.
- Feature flag: `F006_FEATURE` read through the flag hook; routes are not registered when off.

## TDD

- Failing test first: `testing/features/F006/frontend/GridView.test.tsx::renders_groups_and_rows`, `::shows_denied_state_for_viewer`, `BoardView.test.tsx::keyboard_move_calls_api`, `::rolls_back_on_conflict`; `testing/features/F006/e2e/sheet.spec.ts::create_sheet_add_row_move_card`, `::restore_deleted_sheet`; `testing/features/F006/accessibility/sheet.a11y.spec.ts::grid_and_board_have_no_serious_axe_violations`
- Targeted command: `cargo xtask test-feature F006`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: MSW handlers from the seeded sheet fixture; Playwright uses the real API against a seeded tenant

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Component, E2E, and accessibility lanes pass
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S012
- [ ] `finished_at` recorded
