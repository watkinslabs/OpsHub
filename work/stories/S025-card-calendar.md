---
id: S025
type: story
status: planned
parent_epic: E003
parent_feature: F013
depends_on: [F008, F011]
owned_paths: [crates/domain/src/views/**, crates/persistence/src/views/**, services/api/src/views/**, apps/web/src/features/views/**, services/api/migrations/*_views_*.sql, testing/features/F013/**]
feature_flag: F013_FEATURE
branch: s025-card-calendar
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 6
- Capability contract: `docs/capability-contracts.md` row F013

# S025 — Card/calendar

## Identity

- Parent feature: `F013` Views
- Owner: platform
- Branch: `s025-card-calendar`
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 6; `docs/capability-contracts.md` row F013

## Vertical slice

As a sheet member, I want to save a card view keyed on a select column and a calendar view keyed on a date column, with filters, sorts, and grouping applied by the server, and drag cards between lanes or events between days, so that my team plans from the canonical rows without a separate board or calendar copy.

## Requirements

- **SR-S025-01:** `POST /api/v1/views` with `{ sheet_id, name, kind, visibility, settings }` validates settings per kind, and `ViewRepository` decomposes the one wire `settings` object into `views` typed columns (`group_by_column_id`, `lane_column_id`, `swimlane_column_id`, `date_column_id`, `start_column_id`, `end_column_id`, `color_by_column_id`, `calendar_mode`, `timeline_zoom`, `gantt_settings`), the `filter` AST column, and `view_sorts`, `view_columns`, `view_card_fields`, `view_filter_columns` rows in one `UnitOfWork`, then composes the same object back into `ViewResponse` with version 1 and `owner_id`; the 101st view on a sheet returns `400 invalid` with `field_errors.sheet_id = "view_limit"` (covers FR-F013-01, FR-F013-04).
- **SR-S025-02:** `compile_filter` accepts `and`/`or` groups with up to 50 leaves and operators matched to column type, and rejects unknown columns, mismatched operators, or a 51st leaf with `field_errors.settings.filter`; the accepted AST is stored in `views.filter` and its column references are projected into `view_filter_columns`, so `list_views_using_column` answers the F007 column-delete lookup by foreign key (FR-F013-02, FR-F013-03).
- **SR-S025-03:** `GET /api/v1/views/{id}/rows` returns cursor pages of at most 500 rows in group then sort order, includes the `view_columns` visible columns plus the primary column ordered by `group_by_column_id` then the `view_sorts` rows, and excludes rows and cells the actor cannot read; the row query is executed by F008's row repository under the specification this feature contributes (FR-F013-05).
- **SR-S025-04:** A card view requires `views.lane_column_id` by check constraint and a `select` column type by service validation against `columns.type`; `CardView` renders one `CardLane` per option, and a keyboard or pointer lane move calls `PATCH /api/v1/sheets/{sheet_id}/cells` with `If-Match` and rolls back on `conflict` (FR-F013-04, FR-F013-07).
- **SR-S025-05:** A calendar view resolves its timezone from `sheet_schedule_settings.timezone` or the user locale, accepts `range_start`/`range_end` up to 366 days, renders recurrences read-only, and a drag calls `POST /api/v1/rows/{id}/reschedule` (FR-F013-06, FR-F013-07).
- **SR-S025-06:** `PATCH` and `DELETE` honour `If-Match`, owner or `sheet-editor` rules, replace the projection rows through `replace_projection` and clear the previous default through `clear_default` in one `UnitOfWork` when `is_default` is set, and refuse deleting the default view (FR-F013-08, FR-F013-09).
- **SR-S025-07:** Every mutation checks `Idempotency-Key`, writes an audit event, and enqueues `view.created.v1`, `view.updated.v1`, or `view.deleted.v1` (FR-F013-12); foreign-tenant IDs return `404 not_found` (NFR-F013-02).

## Surfaces

- Infrastructure/container: none beyond F004 baseline
- Rust service/API: `crates/domain/src/views/{view.rs, settings.rs, filter.rs, errors.rs, service.rs, service_rows.rs}` (repository traits only, no SQL); `crates/persistence/src/views/{mod.rs, view_repository.rs, view_share_repository.rs}`; `services/api/src/views/{routes.rs, handlers_view.rs, handlers_rows.rs, dto.rs}`
- Data/migration: `services/api/migrations/<ts>_views_create_tables.sql` creating `views`, `view_shares`, `view_sorts`, `view_columns`, `view_card_fields`, and `view_filter_columns` with the indexes and checks from ticket section 4
- React/UI: `apps/web/src/features/views/{ViewPage.tsx, ViewSwitcher.tsx, ViewSettingsPanel.tsx, FilterBuilder.tsx, SortEditor.tsx, CardView.tsx, CardLane.tsx, ViewCard.tsx, CalendarView.tsx, CalendarEvent.tsx, api.ts, hooks.ts, routes.ts}`
- Mocks/fixtures: `testing/fixtures/views.rs` sheet with `Status` select, `Due` date, 200 rows, owner/editor/viewer/foreign tenant; in-memory outbox recorder; MSW handlers for component tests

## TDD harness

- Test path: `testing/features/F013/{api,database,frontend,accessibility}/`
- Feature flag: `F013_FEATURE`
- Targeted command: `cargo xtask test-feature F013`
- Full command: `cargo xtask test-all`
- First failing tests: `view_create_returns_version_one`, `view_filter_rejects_type_mismatch`, `view_rows_exclude_hidden_rows`, `card_view_requires_select_lane_column`, `view_settings_roundtrip_through_projection_tables`, `card_lane_move_patches_cell`, `calendar_drag_calls_reschedule`, `view_default_delete_invalid`

## Exit criteria

- [ ] Requirement tests SR-S025-01 through SR-S025-07 written first and failing
- [ ] Tasks T049 and T050 complete and wired through `services/api` router and the web route
- [ ] Unit, API, database, React, accessibility, and permission tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/views/routes.rs` mounted in `services/api/src/router.rs`; `apps/web/src/features/views/ViewPage.tsx` mounted at `/w/:workspaceId/sheets/:sheetId/views/:viewId`
- [ ] Handoff evidence recorded in the F013 ticket
