---
id: S045
type: story
status: planned
parent_epic: E005
parent_feature: F023
depends_on: [F021, F036]
owned_paths: [crates/domain/src/dashboards/**, crates/persistence/src/dashboards/**, services/api/src/dashboards/**, services/worker/src/dashboards/**, services/api/migrations/*_dashboards_*.sql, testing/features/F023/**]
feature_flag: F023_FEATURE
branch: s045-widget-layout
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 7
- Capability contract: `docs/capability-contracts.md` row F023

# S045 — Widget layout

## Identity

- Parent feature: `F023` Dashboard builder
- Owner: platform
- Branch: `s045-widget-layout`
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 7; `docs/capability-contracts.md` row F023

## Vertical slice

As a dashboard editor, I want to create a dashboard, place typed widgets on a validated 12-column grid, and have each widget's data resolved into a per-viewer cache with refresh state, so that a live page exists before sharing and chart widgets are layered on.

## Requirements

- **SR-S045-01:** `POST /api/v1/dashboards` creates the dashboard through `DashboardRepository::insert` with `layout` stored as `grid_columns`/`row_height_px`, `refresh_policy` stored as `refresh_mode`/`refresh_interval_minutes`, and empty widgets, returning `version` 1; duplicate names in a folder return `409 conflict` (FR-F023-01).
- **SR-S045-02:** `PUT /api/v1/dashboards/{id}/widgets` validates the twelve kinds and per-kind config through the registry, rejects overlaps, out-of-range positions, and more than 40 widgets with `400 invalid`, then runs `DashboardWidgetRepository::replace_widgets` in one `UnitOfWork` that diffs against existing widgets, keeps cache for retained IDs, and rewrites `dashboard_widget_sources` and `dashboard_widget_columns`, and publishes `dashboard.updated.v1` (FR-F023-02, FR-F023-03).
- **SR-S045-03:** The registry resolves `table`, `report_embed`, `text`, and `image` and returns `unavailable` with `reason: "resolver_not_registered"` for kinds without a resolver (FR-F023-04).
- **SR-S045-04:** `GET /api/v1/widgets/{id}/data` serves `WidgetCacheRepository::get_cache(widget_id, scope_key)`, enqueues a `dashboards.refresh-widget` job on a miss, computes `stale` by comparing `widget_cache_sources` rows against current source versions, and returns `denied` without payload when the viewer lacks access to any `dashboard_widget_sources` row of the widget; the `source_versions` response field is unchanged (FR-F023-05).
- **SR-S045-05:** `POST /api/v1/dashboards/{id}/refresh` returns `202 { run_id, status, widget_count }` under 2 seconds, `409 conflict` when `find_active_refresh(dashboard_id, scope_key)` returns a run, and the worker resolves widgets 8 at a time with a 20 s timeout, isolates failures, writes cache entries and source versions with `put_cache` in one `UnitOfWork`, and publishes `dashboard.refreshed.v1` (FR-F023-06, NFR-F023-04).
- **SR-S045-06:** `GET /api/v1/dashboards` (`page_dashboards`), `GET /api/v1/dashboards/{id}` with `cache_summary` (`load_with_widgets`), `PATCH`, and `DELETE` (`delete_cache_for_dashboard`) behave per FR-F023-08 and FR-F023-10, including cascade soft delete, cascade of widget source and column rows, and foreign-tenant `404`.
- **SR-S045-07:** Every mutation requires `Idempotency-Key`, writes an audit row with the widget diff, and publishes the matching `dashboard.*.v1` event (FR-F023-11).

## Surfaces

- Infrastructure/container: JetStream subjects `dashboards.refresh` and `dashboards.refresh-widget` declared in `services/worker/src/dashboards/mod.rs`
- Rust service/API: `crates/domain/src/dashboards/{mod.rs, dashboard.rs, widget.rs, grid.rs, registry.rs, resolvers/{table.rs, report_embed.rs, text.rs, image.rs}, cache.rs, errors.rs, service.rs}` (repository traits only, no SQL); `services/api/src/dashboards/{mod.rs, routes.rs, handlers_dashboard.rs, handlers_widgets.rs, handlers_data.rs, dto.rs}`; `services/worker/src/dashboards/{mod.rs, refresh_job.rs, scheduler.rs}` calling named repository queries and holding no SQL or connection
- Persistence: `crates/persistence/src/dashboards/{mod.rs, dashboard_repository.rs, dashboard_widget_repository.rs, widget_cache_repository.rs}` — `DashboardRepository` owns `dashboards`, `DashboardWidgetRepository` owns `dashboard_widgets`, `dashboard_widget_sources`, `dashboard_widget_columns`, `WidgetCacheRepository` owns `widget_cache`, `widget_cache_sources`; all SQL for this feature lives here
- Data/migration: `services/api/migrations/<ts>_dashboards_create_tables.sql` creating `dashboards`, `dashboard_widgets`, `dashboard_widget_sources`, `dashboard_widget_columns`, `widget_cache`, `widget_cache_sources` with the checks and indexes from ticket section 4
- React/UI: none in this story (S046 covers builder, viewer, and sharing)
- Mocks/fixtures: `testing/fixtures/dashboards.rs`; in-memory outbox recorder; JetStream stub; F017 signed URL stub

## TDD harness

- Test path: `testing/features/F023/api/` and `testing/features/F023/database/`
- Feature flag: `F023_FEATURE`
- Targeted command: `cargo xtask test-feature F023`
- Full command: `cargo xtask test-all`
- First failing tests: `dashboard_create_returns_version_one`, `widgets_overlap_rejected`, `widget_unknown_kind_rejected`, `widget_data_unavailable_without_resolver`, `widget_data_denied_for_restricted_source`, `dashboard_refresh_isolates_widget_failure`

## Exit criteria

- [ ] Requirement tests SR-S045-01 through SR-S045-07 written first and failing
- [ ] Tasks T089 and T090 complete and wired through `services/api` router and the worker consumer registry
- [ ] Unit, API, database, permission, and worker tests pass in targeted and full modes, with `cargo xtask check-persistence` confirming no SQL outside `crates/persistence/src/dashboards/`
- [ ] Production call path named: `services/api/src/dashboards/routes.rs` mounted in `services/api/src/router.rs`; `services/worker/src/dashboards/refresh_job.rs` registered in `services/worker/src/consumers.rs`
- [ ] Handoff evidence recorded in the F023 ticket
