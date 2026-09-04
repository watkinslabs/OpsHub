---
id: S021
type: story
status: planned
parent_epic: E003
parent_feature: F011
depends_on: [F007]
owned_paths: [crates/domain/src/schedules/**, crates/persistence/src/schedules/**, services/api/src/schedules/**, services/api/migrations/*_schedules_*.sql, testing/features/F011/**]
feature_flag: F011_FEATURE
branch: s021-dates-calendars
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 9
- Capability contract: `docs/capability-contracts.md` row F011

# S021 — Dates/calendars

## Identity

- Parent feature: `F011` Dates and schedules
- Owner: platform
- Branch: `s021-dates-calendars`
- Decision references: `docs/architecture-decisions.md` sections 2–4, 9; `docs/capability-contracts.md` row F011

## Vertical slice

As a tenant admin, I want typed date, datetime, and duration values with one working calendar per tenant (plus holidays and extra calendars), so that every sheet, view, and engine computes working time the same way before any schedule settings exist.

## Requirements

- **SR-S021-01:** `WorkDate`, `WorkDateTime`, and `WorkDuration` parse and serialize per FR-F011-01; malformed cell values return `400 invalid` with `field_errors.<column_id>` (FR-F011-01).
- **SR-S021-02:** `POST /api/v1/working-calendars` creates a calendar with validated timezone, `hours_per_day`, and week intervals written as `working_calendar_intervals` rows through `WorkingCalendarRepository::replace_week_intervals`, where `position` caps a weekday at four intervals; the first `GET /api/v1/working-calendars` for a tenant materializes the `Standard` default via `ensure_default` (FR-F011-02).
- **SR-S021-03:** `PATCH /api/v1/working-calendars/{id}` requires `If-Match` and runs the default swap, `replace_week_intervals`, and `replace_exceptions` in one `UnitOfWork`, storing at most 400 unique dates with their `calendar_exception_intervals` rows and returning `week` and `exceptions[].hours` in the unchanged wire shape (FR-F011-03, FR-F011-04).
- **SR-S021-04:** `add_working_days`, `working_days_between`, `snap_start`, and `snap_end` operate on a `ResolvedCalendar` loaded by `WorkingCalendarRepository::load_resolved_calendar` and skip weekends and holiday exceptions and honour `working` exceptions; results are identical across DST transitions and leap days (FR-F011-07).
- **SR-S021-05:** Calendar mutations write an audit event and `working-calendar.updated.v1` in the same transaction with `Idempotency-Key` replay returning the original response (FR-F011-11).
- **SR-S021-06:** Foreign-tenant access to a calendar returns `404 not_found`; a `sheet-viewer` creating a calendar receives `403 denied` (FR-F011-13, NFR-F011-02).
- **SR-S021-07:** Arithmetic over a 10-year span with 400 exceptions runs under 5 ms per call (NFR-F011-01).

## Surfaces

- Infrastructure/container: none beyond F004 baseline
- Rust service/API: `crates/domain/src/schedules/{mod.rs, types.rs, calendar.rs, calendar_math.rs, errors.rs, service_calendar.rs}` (types and use cases only, no SQL); `crates/persistence/src/schedules/{mod.rs, working_calendar_repository.rs, sheet_schedule_settings_repository.rs}` holding every SQL statement; `services/api/src/schedules/{mod.rs, routes.rs, handlers_calendar.rs, dto.rs}`
- Data/migration: `services/api/migrations/<ts>_schedules_create_tables.sql` creating `working_calendars`, `working_calendar_intervals`, `calendar_exceptions`, `calendar_exception_intervals`, `sheet_schedule_settings` with the constraints and indexes from ticket section 4
- React/UI: none in this story (S022 and T044 cover UI)
- Mocks/fixtures: `testing/fixtures/schedules.rs` tenants A and B, admin, editor, viewer, `Standard` and `Berlin` calendars; in-memory outbox recorder

## TDD harness

- Test path: `testing/features/F011/api/` and `testing/features/F011/database/`
- Feature flag: `F011_FEATURE`
- Targeted command: `cargo xtask test-feature F011`
- Full command: `cargo xtask test-all`
- First failing tests: `date_types_parse_and_reject`, `calendar_create_validates_week`, `calendar_default_swap_is_atomic`, `add_working_days_skips_weekend_and_holiday`, `calendar_cross_tenant_not_found`

## Exit criteria

- [ ] Requirement tests SR-S021-01 through SR-S021-07 written first and failing
- [ ] Tasks T041 and T042 complete and wired through `services/api` router
- [ ] Unit, API, database, permission tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/schedules/routes.rs` mounted in `services/api/src/router.rs`
- [ ] Handoff evidence recorded in the F011 ticket
