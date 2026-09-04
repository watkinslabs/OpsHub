---
id: T050
type: task
status: planned
parent_epic: E003
parent_feature: F013
parent_story: S025
depends_on: [T049]
owned_paths: [crates/domain/src/views/**, crates/persistence/src/views/**, services/api/src/views/**, apps/web/src/features/views/**, testing/features/F013/api/**, testing/features/F013/frontend/**, testing/features/F013/accessibility/**]
feature_flag: F013_FEATURE
branch: t050-card-view
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 3, 4, 6
- Capability contract: `docs/capability-contracts.md` row F013

# T050 — Card view

## Identity

- Parent story: `S025` Card/calendar
- Owner: platform
- Branch: `t050-card-view`
- Decision references: `docs/architecture-decisions.md` sections 3, 4, 6; `docs/capability-contracts.md` row F013

## Objective

Implement the permission-filtered view row list and the view page shell with switcher, settings panel, filter builder, and a keyboard-accessible card view whose lane moves patch the lane cell through the F008 route.

## Specification

- Owned paths: `crates/domain/src/views/service_rows.rs` (repository traits only, no SQL), `crates/persistence/src/views/view_repository.rs` (row-specification composition from `views`, `view_sorts`, `view_columns`), `services/api/src/views/handlers_rows.rs`, `apps/web/src/features/views/{ViewPage.tsx, ViewSwitcher.tsx, ViewSettingsPanel.tsx, FilterBuilder.tsx, SortEditor.tsx, CardView.tsx, CardLane.tsx, ViewCard.tsx, api.ts, hooks.ts, routes.ts}`
- Contract/input: `GET /api/v1/views/{id}/rows` query `{ cursor?, limit? ≤ 500, range_start?, range_end? }`; generated `ViewsApi` client plus `GridApi.patchCells` from F008; route params `workspaceId`, `sheetId`, `viewId`.
- Output/behavior: `list_view_rows` loads the view through `ViewRepository`, ANDs the compiled `views.filter` specification into the F008 permission-filtered row query executed by F008's row repository, orders by `group_by_column_id` then the `view_sorts` rows then position, projects the `view_columns` visible columns plus the primary column, and returns `Page<ViewRowResponse { row_id, group_key, version, cells }>`; `CardView` renders a `CardLane` per option of the `lane_column_id` select column with the `view_card_fields` columns on each `ViewCard`, optional swimlanes from `swimlane_column_id`; drag or Space/Arrow/Enter move calls `patchCells` with `If-Match` optimistically and rolls back on `conflict` with the stale banner; `FilterBuilder` edits the AST with operators limited to the chosen column type and a 50-leaf cap; states: loading skeleton, empty with `Clear filters`, error banner with correlation ID, viewer without drag handles, not-found page, offline badge; telemetry `view_opened`, `view_created`, `card_lane_moved`.
- Dependencies: T049 view routes, repositories, and filter compiler; F008 cell patch handler and row query; F007 column types for operator lists.
- Feature flag: `F013_FEATURE` read through the flag hook; routes not registered when off.

## TDD

- Failing test first: `testing/features/F013/api/view_rows_tests.rs::view_rows_apply_filter_sort_group`, `::view_rows_exclude_hidden_rows`, `::view_rows_page_limit_500`, `::card_view_requires_select_lane_column`; `testing/features/F013/frontend/CardView.test.tsx::renders_lane_per_select_option`, `::keyboard_lane_move_patches_cell`, `::rolls_back_on_conflict`; `FilterBuilder.test.tsx::limits_operators_to_column_type`; `testing/features/F013/accessibility/views.a11y.spec.ts::card_view_no_serious_axe_violations`
- Targeted command: `cargo xtask test-feature F013`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: seeded sheet with `Status` select and 200 rows including a restricted group; MSW handlers from the seeded view fixture

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Hidden-row exclusion proven by the permission test
- [ ] Component and accessibility lanes pass for the card view
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S025
- [ ] `finished_at` recorded
