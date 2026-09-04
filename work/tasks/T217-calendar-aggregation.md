---
id: T217
type: task
status: planned
parent_epic: E008
parent_feature: F055
parent_story: S109
depends_on: [S109]
owned_paths: [services/api/migrations/*_calendar-app_*.sql, crates/domain/src/calendar-app/**, crates/persistence/src/calendar-app/**, services/api/src/calendar-app/**, testing/features/F055/database/**, testing/features/F055/api/**]
feature_flag: F055_FEATURE
branch: t217-calendar-aggregation
started_at: null
finished_at: null
---

# T217 — Calendar aggregation

## Identity

- Parent story: `S109` Multi-source calendar
- Owner: platform
- Branch: `t217-calendar-aggregation`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 10; `docs/capability-contracts.md` row F055

## Objective

Create the calendar schema and the calendar, source, and event-aggregation services with timezone-correct normalization so a window of events can be read across up to 20 sources.

## Specification

- Owned paths: `services/api/migrations/<ts>_calendar-app_create_tables.sql`, `services/api/migrations/<ts>_calendar-app_create_tables.down.sql`, `crates/domain/src/calendar-app/{mod.rs, calendar.rs, source.rs, normalize.rs, aggregate.rs, errors.rs, service.rs, schema.rs}`, `crates/persistence/src/calendar-app/{mod.rs, calendar_repository.rs, source_repository.rs}`, `services/api/src/calendar-app/{mod.rs, routes.rs, handlers_calendar.rs, handlers_sources.rs, handlers_events.rs, dto.rs}`
- Contract/input: DDL per F055 ticket section 4 (`calendars`, `calendar_sources`, `calendar_source_column_maps`, `calendar_publications`; declared foreign keys to `tenants`, `workspaces`, `users`, `sheets`, `views`, and `columns`; `check` constraints on `week_start`, `kind`, `all_day_rule`, `timezone_source_kind` and its payload columns, and the map `role`; unique name per workspace, 30-day publication check, single active publication partial index, 20-source trigger, indexes); `CreateCalendarRequest { name, workspace_id, default_timezone?, week_start?, description? }`, `UpdateCalendarRequest`, `ReplaceSourcesRequest { sources[1..20] }`, `EventsQuery { from, to, tz? }` with window ≤ 366 days; headers `Idempotency-Key`, `If-Match`.
- Output/behavior: routes `GET /api/v1/calendars`, `POST /api/v1/calendars`, `PATCH /api/v1/calendars/{id}`, `PUT /api/v1/calendars/{id}/sources`, `GET /api/v1/calendars/{id}/events` return `CalendarResponse`, `Page<CalendarResponse>`, `EventsResponse { events, hidden_sources, tz }`; `normalize_event` maps date columns to all-day events, datetime columns through `timezone_source` to `tz` with `chrono-tz` ambiguous/nonexistent handling, `duration_column_id` hours to `end`; `aggregate` loads sources and their `calendar_source_column_maps` rows through `CalendarSourceRepository::load_sources_with_column_map`, then reads each source through the F013 `ViewRepository` or F006 `RowRepository` named window query with F003 row ACL, caps 10,000 rows per source with `truncated_sources`, counts unreadable sources into `hidden_sources`; `max_calendars` and `max_sources_per_calendar` enforced from entitlement limits with `409 conflict`; audit rows `calendar.create|update|sources.replace` and `calendar.updated.v1` in the same transaction; errors per ticket section 4.
- Data access: `calendar.rs`, `source.rs`, `aggregate.rs`, `service.rs`, and the handlers hold no SQL. `CalendarRepository` (owns `calendars`; `list_calendars_for_viewer`, `find_calendar_by_id`, `count_active_calendars`) and `CalendarSourceRepository` (owns `calendar_sources` and `calendar_source_column_maps`; `load_sources_with_column_map`, `replace_sources`, `count_sources`, `list_sources_referencing_sheet`) live in `crates/persistence/src/calendar-app/`; a source replacement deletes and reinserts source and column-map rows and writes the audit and outbox rows inside one `UnitOfWork` (decision section 2.1).
- Dependencies: F007 typed date columns and index; F011 date rules and tenant zone; F013 view row query; F003 ACL; F048 limits; F049 tenant locale zone default.
- Feature flag: `F055_FEATURE` gates router mounting; migration runs regardless.
- Large-table note: no existing data; event reads touch F007 `cells` through the typed date index, never a full scan.

## TDD

- Failing test first: `testing/features/F055/database/migration_tests.rs::calendar_tables_exist_with_constraints`, `::source_kind_requires_matching_id`, `::column_map_rejects_duplicate_role`, `::source_requires_start_and_title_roles`, `::timezone_source_kind_requires_matching_payload`, `::twenty_first_source_rejected_by_trigger`, `::publication_expiry_capped_at_30_days`, `::rollback_drops_tables`; `testing/features/F055/api/calendar_tests.rs::calendar_create_defaults_tenant_timezone`, `::calendar_limit_exceeded_conflicts`, `sources_tests.rs::sources_reject_21st_source`, `::sources_reject_non_date_column`, `::sources_reject_unreadable_sheet`, `events_tests.rs::events_convert_dst_spring_forward`, `::events_no_duplicate_on_fall_back`, `::events_all_day_for_date_columns`, `::events_hide_unreadable_source_as_count`, `::events_window_over_366_days_invalid`
- Targeted command: `cargo xtask test-feature F055`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: schema-per-worker database from `testing/harness/db.rs`; `testing/fixtures/calendar_app.rs` DST fixture sheets and restricted sheet; in-memory outbox

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; router mounted in `services/api/src/router.rs`; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S109
- [ ] `finished_at` recorded
