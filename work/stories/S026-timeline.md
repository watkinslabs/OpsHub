---
id: S026
type: story
status: planned
parent_epic: E003
parent_feature: F013
depends_on: [S025]
owned_paths: [crates/domain/src/views/**, crates/persistence/src/views/**, services/api/src/views/**, apps/web/src/features/views/**, testing/features/F013/**]
feature_flag: F013_FEATURE
branch: s026-timeline
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 6
- Capability contract: `docs/capability-contracts.md` row F013

# S026 — Timeline

## Identity

- Parent feature: `F013` Views
- Owner: platform
- Branch: `s026-timeline`
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 6; `docs/capability-contracts.md` row F013

## Vertical slice

As a sheet member, I want a timeline view with start and end columns, zoom levels, and color-by, and I want to share any saved view with users, groups, or an expiring link and export it, so that stakeholders outside the sheet see the same filtered rows without gaining edit rights or tenant discovery.

## Requirements

- **SR-S026-01:** A timeline view requires `views.start_column_id`, `views.end_column_id`, and `views.timeline_zoom` in `day|week|month|quarter` by check constraint, `date|datetime` column types by service validation against `columns.type`, and an optional `views.color_by_column_id`; `TimelineView` renders one `TimelineBar` per row in the requested range and pointer or keyboard bar moves call `POST /api/v1/rows/{id}/reschedule` (covers FR-F013-04, FR-F013-07).
- **SR-S026-02:** `POST /api/v1/views/{id}/share` by the owner stores a `view_shares` row through `ViewShareRepository` with `principal_kind`, `principal_id`, `role`, and for links a hashed token and `expires_at` at most 30 days out, publishes `view.shared.v1`, and returns the share ID and link URL; a non-owner receives `403 denied` and an `expires_at` past 30 days receives `400 invalid` (FR-F013-10, FR-F013-12).
- **SR-S026-03:** `GET /api/v1/sheets/{sheet_id}/views` runs `ViewRepository::list_visible_to` and returns the actor's private views, all `sheet` views, and views shared to the actor or their groups, each with its `settings` composed from the typed columns and projection tables, paged by cursor with `filter=kind` and `sort=name|updated_at`; unshared private views of other users are absent and return `404 not_found` by ID (FR-F013-11).
- **SR-S026-04:** A view shared to a user or group is listed for those principals and its rows are filtered by each reader's own permissions; a revoked or expired share removes it and returns `404 not_found`, and `revoke_shares_for_view` revokes every share when the view is soft-deleted; F013 mints no tokens and exposes no unauthenticated route, so an F036 scoped-token actor reaches the view through `GET /public/share/{token}` and is filtered by this same service path (FR-F013-10, FR-F013-05, NFR-F013-02).
- **SR-S026-05:** `ExportViewButton` calls `POST /api/v1/exports` with `view_id`, and the export reads the same `views.filter`, `view_sorts`, and `view_columns` rows and applies permission filtering identically to the row list (FR-F013-14).
- **SR-S026-06:** `ViewSwitcher` lists accessible views with the default first, `ShareViewDialog` manages user and group shares with revoke and links out to F036 for share links, and all three view kinds expose loading, empty, error, denied, stale, and offline states (FR-F013-13, NFR-F013-03).
- **SR-S026-07:** Filtered view rows over a 100,000-row sheet, a lane move, and a calendar month over 5,000 rows meet NFR-F013-01 in the performance lane.

## Surfaces

- Infrastructure/container: none
- Rust service/API: `crates/domain/src/views/{share.rs, service_share.rs, scoped_reader.rs}` (repository traits only, no SQL); `crates/persistence/src/views/{mod.rs, view_share_repository.rs}` owning `view_shares` with `list_active_shares` and `revoke_shares_for_view`; `services/api/src/views/{handlers_share.rs}`
- Data/migration: none new; uses `view_shares` and the `view_sorts`, `view_columns`, `view_card_fields`, `view_filter_columns` projection tables from S025
- React/UI: `apps/web/src/features/views/{TimelineView.tsx, TimelineBar.tsx, TimelineHeader.tsx, ShareViewDialog.tsx, ExportViewButton.tsx, useViewRows.ts}`
- Mocks/fixtures: seeded timeline rows with `Start`/`End` datetime columns spanning 90 days; group with two members; expired and active link tokens; 100,000-row generator for performance lane; MSW handlers for shares

## TDD harness

- Test path: `testing/features/F013/{api,frontend,e2e,accessibility,performance}/`
- Feature flag: `F013_FEATURE`
- Targeted command: `cargo xtask test-feature F013`
- Full command: `cargo xtask test-all`
- First failing tests: `timeline_view_requires_start_and_end`, `timeline_bar_move_calls_reschedule`, `view_share_requires_principal_and_is_unique`, `view_share_non_owner_denied`, `view_list_hides_unshared_private`, `scoped_reader_cannot_mutate`, `view_rows_filtered_100k_p95`

## Exit criteria

- [ ] Requirement tests SR-S026-01 through SR-S026-07 written first and failing
- [ ] Tasks T051 and T052 complete; UI wired to real API through generated client
- [ ] Unit, API, React, E2E, accessibility, permission, and performance tests pass
- [ ] Production call path named: `services/api/src/views/handlers_share.rs` mounted through `services/api/src/views/routes.rs` in `services/api/src/router.rs`; `apps/web/src/features/views/TimelineView.tsx` rendered by `ViewPage.tsx` at `/w/:workspaceId/sheets/:sheetId/views/:viewId`
- [ ] Handoff evidence recorded in the F013 ticket
