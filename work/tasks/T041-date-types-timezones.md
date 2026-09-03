---
id: T041
type: task
status: planned
parent_epic: E003
parent_feature: F011
parent_story: S021
depends_on: [S021]
owned_paths: [crates/domain/src/schedules/**, services/api/migrations/*_schedules_*.sql, testing/features/F011/database/**, testing/features/F011/api/**]
feature_flag: F011_FEATURE
branch: t041-date-types-timezones
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 9
- Capability contract: `docs/capability-contracts.md` row F011

# T041 — Date types/timezones

## Identity

- Parent story: `S021` Dates/calendars
- Owner: platform
- Branch: `t041-date-types-timezones`
- Decision references: `docs/architecture-decisions.md` sections 2, 9; `docs/capability-contracts.md` row F011

## Objective

Define the `WorkDate`, `WorkDateTime`, `WorkDuration`, and timezone types with parsing, serialization, and validation, and create the three schedule tables with constraints and rollback.

## Specification

- Owned paths: `crates/domain/src/schedules/{mod.rs, types.rs, timezone.rs, errors.rs, schema.rs}`, `services/api/migrations/<ts>_schedules_create_tables.sql`, `services/api/migrations/<ts>_schedules_create_tables.down.sql`
- Contract/input: cell JSON shapes `"2026-09-14"` for date, `"2026-09-14T07:00:00.000000Z"` for datetime, `{ "value": "3", "unit": "days" }` for duration; timezone strings validated with `chrono_tz::Tz::from_str`; `resolve_timezone(sheet: Option<Tz>, user: Option<Tz>, tenant: Option<Tz>) -> Tz` defaulting to UTC.
- Output/behavior: types implement `FromStr`, `Display`, `Serialize`, `Deserialize`, `sqlx::Type`; invalid input maps to `ScheduleError::InvalidValue { column_id, reason }`; DDL per F011 ticket section 4 PostgreSQL: `working_calendars`, `calendar_exceptions`, `sheet_schedule_settings`, unique name index, single-default partial index, `(calendar_id, date)` uniqueness, `hours_per_day` check, restrict on referenced calendar; `sqlx migrate run` applies on a database with F006/F007 tables and `sqlx migrate revert` drops them.
- Dependencies: F007 `columns.type` enum values `date`, `datetime`, `duration`, `boolean`, `number`; F006 `sheets` table for the settings foreign key.
- Feature flag: `F011_FEATURE` (migration runs regardless; routes are gated)
- Large-table note: no existing data; later columns must be additive and nullable.

## TDD

- Failing test first: `testing/features/F011/api/type_tests.rs::date_types_parse_and_reject`, `::datetime_round_trips_microseconds`, `::duration_rejects_negative_and_unknown_unit`, `::resolve_timezone_prefers_sheet_then_user_then_tenant`; `testing/features/F011/database/migration_tests.rs::schedule_tables_exist_with_constraints`, `::second_default_calendar_rejected`, `::rollback_drops_tables`
- Targeted command: `cargo xtask test-feature F011`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: schema-per-worker database from `testing/harness/db.rs`; no external mocks

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; `cargo xtask check-migrations` passes
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S021
- [ ] `finished_at` recorded
