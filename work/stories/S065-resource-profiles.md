---
id: S065
type: story
status: planned
parent_epic: E007
parent_feature: F033
depends_on: [F011, F002]
owned_paths: [crates/domain/src/resources/**, crates/persistence/src/resources/**, services/api/src/resources/**, services/api/migrations/*_resources_*.sql, testing/features/F033/**]
feature_flag: F033_FEATURE
branch: s065-resource-profiles
started_at: null
finished_at: null
---

# S065 — Resource profiles

## Identity

- Parent feature: `F033` Resources/capacity
- Owner: platform
- Branch: `s065-resource-profiles`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4; `docs/capability-contracts.md` row F033

## Vertical slice

As a resource administrator, I want to create resource profiles with skills, availability, cost rates, FTE, and a working calendar, and read each resource's capacity per period, so that true availability exists before any allocation is planned.

## Requirements

- **SR-S065-01:** `POST /api/v1/resources` creates a resource with `display_name`, `kind`, optional `user_id`, `role_title`, `working_calendar_id`, `fte`, `timezone`, and `status`, returning `ResourceResponse` with version 1; a second active resource for the same `user_id` returns `409 conflict` with `field_errors.user_id` (covers FR-F033-01).
- **SR-S065-02:** `GET /api/v1/resources` pages with `limit` ≤ 200, filters `status`, `kind`, `skill` with `min_level` (a join through `resource_skills` to the `skills` lookup, resolved by `ResourceRepository::list_filtered`), `role_title` prefix, and `available_between`, sorts by `display_name` or `updated_at`; `PATCH /api/v1/resources/{id}` requires `If-Match` and accepts profile fields and `cost_rates` (FR-F033-02, FR-F033-05).
- **SR-S065-03:** `PUT /api/v1/resources/{id}/skills` replaces up to 50 `{ skill, level 1–5 }` entries, resolving each name to one tenant `skills` row and storing one `resource_skills(resource_id, skill_id, level)` row per entry while the request and response keep the array shape, and rejects duplicates with `field_errors.skills[i]`; `PUT /api/v1/resources/{id}/availability` replaces up to 500 non-overlapping `{ kind, start_date, end_date, hours_per_day? }` entries and rejects overlaps with `field_errors.availability[i]` (FR-F033-03, FR-F033-04).
- **SR-S065-04:** `GET /api/v1/resources/{id}/capacity` for ≤ 366 days returns per period `calendar_hours`, `fte_hours`, `leave_hours`, `holiday_hours`, `reduced_hours`, `available_hours`, `allocated_hours`, `remaining_hours`, `over_allocated`, and totals, computed from the F011 calendar and exceptions, FTE, and availability entries read through `AvailabilityRepository::list_availability_overlapping` and `AllocationRepository::list_allocations_overlapping` (FR-F033-06).
- **SR-S065-05:** Deactivation with allocations ending after today returns `409 conflict` listing allocation IDs from `AllocationRepository::list_active_allocations_ending_after` unless `end_allocations: true` is given, which calls `end_allocations_today` in the same `UnitOfWork` transaction as the status change (FR-F033-14).
- **SR-S065-06:** Every mutation checks `Idempotency-Key`, writes an audit event, and enqueues `resource.updated.v1`; availability and profile writes publish `capacity.computed.v1` for the affected span (FR-F033-10, FR-F033-11).
- **SR-S065-07:** A `resource-viewer` reads resources and capacity without `cost_rates` and receives `403 denied` on mutations; a foreign-tenant actor receives `404 not_found`; a user reads their own profile (FR-F033-12).

## Surfaces

- Infrastructure/container: none beyond F004 baseline; `btree_gist` extension enabled by the migration
- Data access: `crates/persistence/src/resources/{mod.rs, resource_repository.rs, skill_repository.rs, availability_repository.rs, cost_rate_repository.rs, allocation_repository.rs}` hold every SQL statement for this slice; `ResourceRepository` owns `resources` and `resource_skills`, `SkillRepository` owns `skills`, `AvailabilityRepository` owns `resource_availability`, `CostRateRepository` owns `cost_rates`, `AllocationRepository` owns `allocations`, and the domain services and `services/api/src/resources` handlers depend on the traits with no `sqlx::query*` call (decision section 2.1)
- Rust service/API: `crates/domain/src/resources/{mod.rs, resource.rs, skills.rs, availability.rs, cost_rates.rs, capacity.rs, errors.rs, service_resources.rs}`; `services/api/src/resources/{mod.rs, routes.rs, handlers_resource.rs, handlers_capacity.rs, dto.rs, scope.rs}`
- Data/migration: `services/api/migrations/<ts>_resources_create_tables.sql` creating `resources`, `skills`, `resource_skills`, `resource_availability`, `cost_rates`, `allocations` with the foreign keys, enum checks, and indexes from ticket section 4
- React/UI: none in this story (S066 and T131 cover UI)
- Mocks/fixtures: `testing/fixtures/resources.rs` tenants A and B, resource-admin, resource-viewer, linked user, Mon–Fri 8 h calendar with a holiday, resources with FTE 1.0 and 0.5, leave week, cost rates, all seeded through the `crates/persistence/src/resources/` repositories; in-memory outbox recorder

## TDD harness

- Test path: `testing/features/F033/api/` and `testing/features/F033/database/`
- Feature flag: `F033_FEATURE`
- Targeted command: `cargo xtask test-feature F033`
- Full command: `cargo xtask test-all`
- First failing tests: `resource_create_returns_version_one`, `resource_duplicate_user_link_conflicts`, `availability_overlap_invalid`, `capacity_subtracts_leave_holiday_and_fte`, `capacity_range_over_366_days_invalid`, `skill_junction_rejects_duplicate_skill_id`, `viewer_response_omits_cost_rates`, `resource_cross_tenant_not_found`

## Exit criteria

- [ ] Requirement tests SR-S065-01 through SR-S065-07 written first and failing
- [ ] Tasks T129 and T130 complete and wired through `services/api` router
- [ ] Unit, API, database, permission tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/resources/routes.rs` mounted in `services/api/src/router.rs` behind `F033_FEATURE`
- [ ] Handoff evidence recorded in the F033 ticket
