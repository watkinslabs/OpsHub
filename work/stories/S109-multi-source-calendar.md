---
id: S109
type: story
status: planned
parent_epic: E008
parent_feature: F055
depends_on: [F013, F011, F048]
owned_paths: [crates/domain/src/calendar-app/**, services/api/src/calendar-app/**, services/api/migrations/*_calendar-app_*.sql, testing/features/F055/**]
feature_flag: F055_FEATURE
branch: s109-multi-source-calendar
started_at: null
finished_at: null
---

# S109 — Multi-source calendar

## Identity

- Parent feature: `F055` Calendar App
- Owner: platform
- Branch: `s109-multi-source-calendar`
- Decision references: `docs/architecture-decisions.md` sections 2–4, 10; `docs/capability-contracts.md` row F055

## Vertical slice

As a calendar editor, I want to create a calendar, attach up to 20 sheet or view sources with date, title, and color mappings, and read a permission-filtered, timezone-correct event list for a window, so that one API returns everything a viewer may see across sheets before any UI exists.

## Requirements

- **SR-S109-01:** `POST /api/v1/calendars`, `PATCH /api/v1/calendars/{id}`, and `GET /api/v1/calendars` create, update, and list calendars with `default_timezone`, `week_start`, cursor paging, `If-Match`, and the `max_calendars` limit (covers FR-F055-01, FR-F055-10).
- **SR-S109-02:** `PUT /api/v1/calendars/{id}/sources` replaces 1–20 sources with validated column types and `timezone_source`; a 21st source, non-date column, or unreadable sheet → `400 invalid` with `field_errors.sources[i].<field>`; beyond `max_sources_per_calendar` → `409 conflict` (FR-F055-02).
- **SR-S109-03:** `GET /api/v1/calendars/{id}/events?from&to&tz` returns normalized events with RFC 3339 offsets for windows up to 366 days, all-day events for date columns, and DST-correct conversion for datetime columns (FR-F055-03, FR-F055-05).
- **SR-S109-04:** Events are filtered per source by the viewer's row-level permission; unreadable sources are omitted and counted in `hidden_sources` without exposing IDs; `can_edit` reflects `sheet-editor` on the source (FR-F055-04, FR-F055-06).
- **SR-S109-05:** The router is mounted behind `RequireModule(ModuleSlug::CalendarApp)`; a non-entitled tenant → `403 denied` with `field_errors.module` (FR-F055-12).
- **SR-S109-06:** Every mutation requires `Idempotency-Key`, writes an audit row, publishes `calendar.updated.v1`, and foreign-tenant access → `404 not_found` (FR-F055-11).
- **SR-S109-07:** Events for a 31-day window over 20 sources totalling 100,000 rows respond under 500 ms p95 (NFR-F055-01).

## Surfaces

- Infrastructure/container: none beyond F004 baseline
- Rust service/API: `crates/domain/src/calendar-app/{mod.rs, calendar.rs, source.rs, normalize.rs, aggregate.rs, errors.rs, service.rs}`; `services/api/src/calendar-app/{mod.rs, routes.rs, handlers_calendar.rs, handlers_sources.rs, handlers_events.rs, dto.rs}`
- Data/migration: `services/api/migrations/<ts>_calendar-app_create_tables.sql` creating `calendars`, `calendar_sources`, `calendar_publications` with constraints and indexes from ticket section 4
- React/UI: none in this story (S110 covers UI and publishing)
- Mocks/fixtures: `testing/fixtures/calendar_app.rs` tenants A/B, editor, viewer, partial viewer, entitlement with limits, DST fixture sheets `Launches`, `Maintenance`, `Leave`, restricted sheet; in-memory outbox; real F003 engine with fixture bindings

## TDD harness

- Test path: `testing/features/F055/api/`, `testing/features/F055/database/`, `testing/features/F055/performance/`
- Feature flag: `F055_FEATURE`
- Targeted command: `cargo xtask test-feature F055`
- Full command: `cargo xtask test-all`
- First failing tests: `sources_reject_21st_source`, `sources_reject_non_date_column`, `events_convert_dst_spring_forward`, `events_hide_unreadable_source_as_count`, `events_window_over_366_days_invalid`, `calendar_route_denied_without_entitlement`, `events_31_days_20_sources_p95`

## Exit criteria

- [ ] Requirement tests SR-S109-01 through SR-S109-07 written first and failing
- [ ] Tasks T217 and T218 complete and wired through `services/api` router
- [ ] Unit, API, database, permission, and performance tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/calendar-app/routes.rs` mounted in `services/api/src/router.rs` behind `RequireModule(ModuleSlug::CalendarApp)`
- [ ] Handoff evidence recorded in the F055 ticket
