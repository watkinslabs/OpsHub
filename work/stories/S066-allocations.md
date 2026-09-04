---
id: S066
type: story
status: planned
parent_epic: E007
parent_feature: F033
depends_on: [S065]
owned_paths: [crates/domain/src/resources/**, crates/persistence/src/resources/**, services/api/src/resources/**, apps/web/src/features/resources/**, testing/features/F033/**]
feature_flag: F033_FEATURE
branch: s066-allocations
started_at: null
finished_at: null
---

# S066 — Allocations

## Identity

- Parent feature: `F033` Resources/capacity
- Owner: platform
- Branch: `s066-allocations`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 6; `docs/capability-contracts.md` row F033

## Vertical slice

As a resource administrator, I want to allocate resources to projects and tasks by period with planned hours or percent, role, confidence, and a cost snapshot, and see allocations against capacity in a planner that flags over-allocation immediately, so that plans are feasible and costed.

## Requirements

- **SR-S066-01:** `POST /api/v1/allocations` validates `resource_id` active, `project_sheet_id` and optional `row_id` in the same sheet, `end_date ≥ start_date`, span ≤ 366 days, exactly one of `planned_hours` (0.25–10,000) or `planned_percent` (1–100), `role`, `confidence`, snapshots the rate found by `CostRateRepository::find_rate_effective_on` into the allocation's `cost_rate_id`, `snapshot_hourly_rate`, `snapshot_currency`, and `snapshot_effective_from` columns, and returns `AllocationResponse` with the `cost_rate_snapshot` object and `planned_cost` for administrators and `over_allocated_periods` (FR-F033-05, FR-F033-08, FR-F033-10).
- **SR-S066-02:** `GET /api/v1/allocations` pages with `limit` ≤ 500 and filters `resource_id`, `project_sheet_id`, `row_id`, `from`/`to` overlap, and `confidence` through `AllocationRepository::list_allocations_filtered`; `PATCH` requires `If-Match`; `DELETE` soft-deletes and recomputes capacity, both inside the allocation `UnitOfWork` (FR-F033-09).
- **SR-S066-03:** Capacity reads the resource, its availability, and its overlapping allocations through the `crates/persistence/src/resources/` repositories and the F011 `WorkingCalendarRepository` trait, distributes hours evenly over working days inside each period, applies `planned_percent × available_hours`, reports `warning: no_working_days` for allocations without working days, and marks `over_allocated` when `allocated_hours > available_hours` (FR-F033-06, FR-F033-07).
- **SR-S066-04:** Allocation writes publish `allocation.created.v1`, `allocation.updated.v1`, or `allocation.deleted.v1` and `capacity.computed.v1` with `changed_fields { resource_id, from, to }` in the same transaction (FR-F033-10, FR-F033-11, NFR-F033-04).
- **SR-S066-05:** `ResourceDirectoryPage`, `ResourcePage` with `CapacityStrip`, and `AllocationPlannerPage` with `PlannerGrid` and `AllocationDialog` render from the API with loading, empty, error, denied, conflict, over-allocated, and offline states, keyboard grid navigation, and text plus icon over-allocation markers (FR-F033-13, NFR-F033-03).
- **SR-S066-06:** Viewer sessions never receive the `cost_rate_snapshot` object built from the allocation snapshot columns or `planned_cost` and see no edit controls; foreign-tenant allocation routes return `404 not_found` (FR-F033-12, NFR-F033-02).
- **SR-S066-07:** Capacity with 200 allocations over 52 weeks, a 5,000-resource list, and allocation create meet NFR-F033-01.

## Surfaces

- Infrastructure/container: none
- Data access: `crates/persistence/src/resources/{allocation_repository.rs, cost_rate_repository.rs, availability_repository.rs}` hold every SQL statement this slice needs; `allocation.rs`, `distribution.rs`, `service_allocations.rs`, and `handlers_allocation.rs` contain no SQL, and an allocation write plus its capacity recompute, audit row, and outbox rows run in one `UnitOfWork` (decision section 2.1)
- Rust service/API: `crates/domain/src/resources/{allocation.rs, distribution.rs, service_allocations.rs}`; `services/api/src/resources/handlers_allocation.rs`
- Data/migration: none new; uses `allocations` and the `skills`/`resource_skills` pair created in S065
- React/UI: `apps/web/src/features/resources/{ResourceDirectoryPage.tsx, ResourceCard.tsx, ResourcePage.tsx, SkillsEditor.tsx, AvailabilityEditor.tsx, CostRatesEditor.tsx, CapacityStrip.tsx, AllocationPlannerPage.tsx, PlannerGrid.tsx, PlannerCell.tsx, AllocationDialog.tsx, NewResourceDialog.tsx, DeactivateResourceDialog.tsx, api.ts, hooks.ts, routes.ts}`
- Mocks/fixtures: two resources with leave and holiday; 200-allocation and 5,000-resource generators for the performance lane; MSW handlers for component tests

## TDD harness

- Test path: `testing/features/F033/{api,frontend,e2e,accessibility,performance}/`
- Feature flag: `F033_FEATURE`
- Targeted command: `cargo xtask test-feature F033`
- Full command: `cargo xtask test-all`
- First failing tests: `allocation_hours_and_percent_mutually_exclusive`, `allocation_snapshots_effective_cost_rate_into_typed_columns`, `allocation_create_returns_over_allocated_periods`, `allocation_percent_uses_available_hours`, `allocation_snapshot_columns_pair_or_are_both_null`, `planner_marks_over_allocated_cell`, `capacity_52_weeks_200_allocations_p95`

## Exit criteria

- [ ] Requirement tests SR-S066-01 through SR-S066-07 written first and failing
- [ ] Tasks T131 and T132 complete; UI wired to real API through the generated client
- [ ] Unit, API, React, E2E, accessibility, permission, and performance tests pass
- [ ] Production call path named: `apps/web/src/features/resources/AllocationPlannerPage.tsx` mounted at `/w/:workspaceId/allocations`, backed by `services/api/src/resources/handlers_allocation.rs`
- [ ] Handoff evidence recorded in the F033 ticket
