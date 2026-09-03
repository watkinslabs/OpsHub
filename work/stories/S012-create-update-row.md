---
id: S012
type: story
status: planned
parent_epic: E002
parent_feature: F006
depends_on: [S011]
owned_paths: [crates/domain/src/sheets/**, services/api/src/sheets/**, apps/web/src/features/sheets/**, testing/features/F006/**]
feature_flag: F006_FEATURE
branch: s012-create-update-row
started_at: null
finished_at: null
---

# S012 — Create/update row

## Identity

- Parent feature: `F006` Sheets/boards/items
- Owner: platform
- Branch: `s012-create-update-row`
- Decision references: `docs/architecture-decisions.md` sections 2–4, 6; `docs/capability-contracts.md` row F006

## Vertical slice

As a workspace editor, I want to add rows to a sheet, update their primary value, move them between groups, and see them in grid and board modes, so that work items exist as stable records the team can organize.

## Requirements

- **SR-S012-01:** `POST /api/v1/sheets/{id}/rows` creates a row with fractional `position`, default or given `group_id`, and cells keyed by column ID; returns `RowResponse` with version 1 (FR-F006-06).
- **SR-S012-02:** `GET /api/v1/sheets/{id}/rows` returns rows in `position` order with cursor paging and `limit` ≤ 500, including raw, display, and validation state per cell (FR-F006-07).
- **SR-S012-03:** `PATCH /api/v1/rows/{id}` updates cells and requires `If-Match`; `DELETE` and `POST /restore` soft-delete and restore the row (FR-F006-05, FR-F006-10).
- **SR-S012-04:** `POST /api/v1/rows/{id}/move` with `{ group_id?, after_row_id? }` rebalances positions when a key exceeds 64 chars and emits `row.moved.v1` (FR-F006-08).
- **SR-S012-05:** Deleting a non-default group moves its rows to the default group in the same transaction (FR-F006-09).
- **SR-S012-06:** `GridView` and `BoardView` render rows and groups from the API, support keyboard card moves, and show loading, empty, error, denied, stale, and offline states (FR-F006-13, FR-F006-14, NFR-F006-03).
- **SR-S012-07:** Row list on a 100,000-row fixture sheet meets NFR-F006-01.

## Surfaces

- Infrastructure/container: none
- Rust service/API: `crates/domain/src/sheets/{row.rs, position.rs, service_rows.rs}`; `services/api/src/sheets/{handlers_row.rs, handlers_group.rs}`
- Data/migration: none new; uses tables from S011
- React/UI: `apps/web/src/features/sheets/{SheetPage.tsx, GridView.tsx, GroupSection.tsx, RowLine.tsx, BoardView.tsx, BoardLane.tsx, RowCard.tsx, api.ts, hooks.ts}`
- Mocks/fixtures: seeded sheet with 3 groups and 50 rows; 100,000-row generator for performance lane; MSW handlers for component tests

## TDD harness

- Test path: `testing/features/F006/{api,frontend,e2e,accessibility,performance}/`
- Feature flag: `F006_FEATURE`
- Targeted command: `cargo xtask test-feature F006`
- Full command: `cargo xtask test-all`
- First failing tests: `row_create_assigns_position`, `row_move_between_groups_emits_event`, `row_list_pages_by_position`, `board_keyboard_move`, `row_list_100k_p95`

## Exit criteria

- [ ] Requirement tests SR-S012-01 through SR-S012-07 written first and failing
- [ ] Tasks T023 and T024 complete; UI wired to real API through generated client
- [ ] Unit, API, React, E2E, accessibility, permission, and performance tests pass
- [ ] Production call path named: `apps/web/src/features/sheets/SheetPage.tsx` mounted at `/w/:workspaceId/sheets/:sheetId`
- [ ] Handoff evidence recorded in the F006 ticket
