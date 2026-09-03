---
id: T130
type: task
status: planned
parent_epic: E007
parent_feature: F033
parent_story: S065
depends_on: [T129]
owned_paths: [crates/domain/src/resources/**, services/api/src/resources/**, testing/features/F033/api/**, testing/features/F033/requirements/**]
feature_flag: F033_FEATURE
branch: t130-capacity-calendar
started_at: null
finished_at: null
---

# T130 — Capacity calendar

## Identity

- Parent story: `S065` Resource profiles
- Owner: platform
- Branch: `t130-capacity-calendar`
- Decision references: `docs/architecture-decisions.md` sections 2–3; `docs/capability-contracts.md` row F033

## Objective

Implement the capacity calculator over the F011 working calendar, FTE, leave, holidays, and reduced availability, expose it through the capacity route, and publish `capacity.computed.v1` from every write that changes a resource's capacity.

## Specification

- Owned paths: `crates/domain/src/resources/{capacity.rs, working_days.rs, distribution.rs, service_capacity.rs}`, `services/api/src/resources/handlers_capacity.rs`
- Contract/input: query `{ from, to, granularity: day|week }` with `to − from ≤ 366` days; inputs from `working_calendars` and `calendar_exceptions` (F011), `resources.fte`, `resource_availability`, and non-deleted `allocations` overlapping the range.
- Output/behavior: `GET /api/v1/resources/{id}/capacity` returns `CapacityResponse { granularity, periods: [CapacityPeriod], totals }` where `calendar_hours` counts working days times hours per day excluding calendar exceptions, `fte_hours = calendar_hours × fte`, `leave_hours` and `holiday_hours` count whole working days of matching availability kinds at `hours_per_day × fte`, `reduced_hours = (calendar hours per day − hours_per_day) × fte` per reduced day, `available_hours = max(0, fte_hours − leave − holiday − reduced)`, `allocated_hours` distributes each hours allocation evenly over its working days and applies `planned_percent × available_hours` for percent allocations, `remaining_hours = available − allocated`, `over_allocated = allocated > available`, and allocations without working days produce `warning: no_working_days`; week periods start Monday in the resource time zone; `working_days.rs` precomputes working days per calendar per year in memory with a 24-hour cache keyed by `working-calendar.updated.v1`; `service_capacity.rs::recompute_span` is called by profile, availability, and allocation writes inside the transaction and enqueues `capacity.computed.v1` with `changed_fields { resource_id, from, to }`; a range over 366 days returns `400 invalid` with `field_errors.to`.
- Dependencies: T129 schema and routes; F011 calendar and exception queries; F004 outbox writer.
- Feature flag: `F033_FEATURE`

## TDD

- Failing test first: `testing/features/F033/api/capacity_tests.rs::capacity_subtracts_leave_holiday_and_fte`, `::capacity_reduced_days_lower_available_hours`, `::capacity_week_periods_start_monday_in_resource_timezone`, `::capacity_distributes_hours_evenly_over_working_days`, `::capacity_percent_allocation_uses_available_hours`, `::capacity_flags_no_working_days_warning`, `::capacity_range_over_366_days_invalid`, `::availability_write_publishes_capacity_computed`; unit tests in `crates/domain/src/resources/capacity.rs` for the arithmetic table in the F033 ticket acceptance scenario
- Targeted command: `cargo xtask test-feature F033`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: Mon–Fri 8 h calendar with holiday `2026-10-12`; resources with FTE 1.0 and 0.5; leave `2026-10-05` to `2026-10-09`; reduced days at 4 h; in-memory outbox recorder

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Capacity route mounted in `services/api/src/resources/routes.rs`; arithmetic matches the acceptance scenario exactly
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S065
- [ ] `finished_at` recorded
