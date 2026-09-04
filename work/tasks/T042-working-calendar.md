---
id: T042
type: task
status: planned
parent_epic: E003
parent_feature: F011
parent_story: S021
depends_on: [T041]
owned_paths: [crates/domain/src/schedules/**, crates/persistence/src/schedules/**, services/api/src/schedules/**, testing/features/F011/api/**, testing/features/F011/requirements/**, testing/features/F011/performance/**]
feature_flag: F011_FEATURE
branch: t042-working-calendar
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4
- Capability contract: `docs/capability-contracts.md` row F011

# T042 — Working calendar

## Identity

- Parent story: `S021` Dates/calendars
- Owner: platform
- Branch: `t042-working-calendar`
- Decision references: `docs/architecture-decisions.md` sections 2–4; `docs/capability-contracts.md` row F011

## Objective

Implement the working-calendar domain service, the pure working-day arithmetic, and the three calendar routes with authorization, idempotency, optimistic concurrency, audit, and outbox publication.

## Specification

- Owned paths: `crates/domain/src/schedules/{calendar.rs, calendar_math.rs, service_calendar.rs}` (no SQL), `crates/persistence/src/schedules/{mod.rs, working_calendar_repository.rs}`, `services/api/src/schedules/{mod.rs, routes.rs, handlers_calendar.rs, dto.rs}`
- Contract/input: `CreateCalendarRequest { name, timezone, week: { mon..sun: [{ start, end }] }, hours_per_day, is_default?, exceptions?: [{ date, kind, hours?, label }] }`, `UpdateCalendarRequest` with the same optional fields; headers `Idempotency-Key`, `If-Match`; list query `{ cursor?, limit? ≤ 100, include_deleted? }`.
- Output/behavior: routes `GET /api/v1/working-calendars`, `POST /api/v1/working-calendars`, `PATCH /api/v1/working-calendars/{id}` return `CalendarResponse { id, name, timezone, week, hours_per_day, is_default, exceptions, version, created_at, updated_at }`; `ensure_default_calendar` creates `Standard` on first list through `WorkingCalendarRepository::ensure_default`; `WorkingCalendarRepository` owns `working_calendars`, `working_calendar_intervals`, `calendar_exceptions`, `calendar_exception_intervals` and adds `list_for_tenant`, `find_default`, `ensure_default`, `replace_week_intervals`, `replace_exceptions`, `load_resolved_calendar(calendar_id)` on top of the shared `Repository` contract, assembling `week` and `exceptions[].hours` from the interval rows so `CalendarResponse` is unchanged; `calendar_math.rs` takes a loaded `ResolvedCalendar` and exposes `add_working_days(cal, date, days) -> NaiveDate`, `working_days_between(cal, a, b) -> Decimal`, `next_working_day`, `previous_working_day`, `snap_start`, `snap_end`, all evaluated on calendar dates in the calendar timezone; default swap, `replace_week_intervals`, and `replace_exceptions` happen in one `UnitOfWork` transaction; events `working-calendar.updated.v1`; errors map per ticket section 4.
- Dependencies: T041 types and tables; F003 `authz::require(actor, Permission::CalendarManage, tenant)`; F004 outbox writer.
- Feature flag: `F011_FEATURE` gates router mounting.

## TDD

- Failing test first: `testing/features/F011/api/calendar_tests.rs::calendar_create_validates_week`, `::calendar_default_swap_is_atomic`, `::calendar_exceptions_limit_400`, `::calendar_stale_version_conflicts`, `::calendar_cross_tenant_not_found`, `::calendar_viewer_create_denied`; `testing/features/F011/api/calendar_math_tests.rs::add_working_days_skips_weekend_and_holiday`, `::working_exception_adds_saturday`, `::dst_transition_does_not_shift_dates`; `testing/features/F011/performance/calendar_math_bench.rs::add_working_days_10y_under_5ms`
- Targeted command: `cargo xtask test-feature F011`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/schedules.rs` `Standard` and `Berlin` calendars; in-memory outbox recorder

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Router mounted in `services/api/src/router.rs` behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S021
- [ ] `finished_at` recorded
