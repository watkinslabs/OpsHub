---
id: T131
type: task
status: planned
parent_epic: E007
parent_feature: F033
parent_story: S066
depends_on: [T130]
owned_paths: [crates/domain/src/resources/**, services/api/src/resources/**, apps/web/src/features/resources/**, testing/features/F033/api/**, testing/features/F033/frontend/**, testing/features/F033/accessibility/**]
feature_flag: F033_FEATURE
branch: t131-allocation-ui
started_at: null
finished_at: null
---

# T131 — Allocation UI

## Identity

- Parent story: `S066` Allocations
- Owner: platform
- Branch: `t131-allocation-ui`
- Decision references: `docs/architecture-decisions.md` sections 2–3, 6; `docs/capability-contracts.md` row F033

## Objective

Implement the allocation service and its four routes, then build the resource directory, resource profile, and allocation planner pages wired to the real resources API with immediate over-allocation feedback.

## Specification

- Owned paths: `crates/domain/src/resources/{allocation.rs, service_allocations.rs}`, `services/api/src/resources/handlers_allocation.rs`, `apps/web/src/features/resources/{ResourceDirectoryPage.tsx, ResourceCard.tsx, ResourcePage.tsx, SkillsEditor.tsx, AvailabilityEditor.tsx, CostRatesEditor.tsx, CapacityStrip.tsx, AllocationPlannerPage.tsx, PlannerGrid.tsx, PlannerCell.tsx, AllocationDialog.tsx, NewResourceDialog.tsx, DeactivateResourceDialog.tsx, api.ts, hooks.ts, routes.ts}`
- Contract/input: `CreateAllocationRequest { resource_id, project_sheet_id, row_id?, start_date, end_date, planned_hours? | planned_percent?, role, confidence, note? }`, `UpdateAllocationRequest` (same fields optional), list query `{ cursor?, limit? ≤ 500, resource_id?, project_sheet_id?, row_id?, from?, to?, confidence? }`; generated `ResourcesApi` client; route params `workspaceId`, `resourceId`; query keys per ticket section 4.
- Output/behavior: routes `GET/POST /api/v1/allocations`, `PATCH/DELETE /api/v1/allocations/{id}` return `AllocationResponse { id, resource_id, project_sheet_id, row_id, start_date, end_date, planned_hours, planned_percent, role, confidence, cost_rate_snapshot?, planned_cost?, over_allocated_periods, version }` with cost fields filtered by `scope.rs`; create snapshots the effective cost rate at `start_date`, calls `recompute_span`, and publishes `allocation.created.v1` plus `capacity.computed.v1`; planner grid renders resources by ISO week with allocation bars, `PlannerCell` shows `available/allocated` text, red `Over by N h` with `AlertTriangle` when over-allocated; `AllocationDialog` enforces hours-or-percent, role, confidence, and shows `field_errors.planned`; directory shows skill badges and leave badges with filters; profile shows `SkillsEditor`, `AvailabilityEditor`, `CostRatesEditor` (admin only), `CapacityStrip` with `meter` semantics; optimistic create and move with rollback on `invalid`/`conflict` and stale banner; states: loading, empty, error with correlation ID, denied, conflict, over-allocated, offline; under 768 px single-resource planner; telemetry per ticket section 4.
- Dependencies: T130 capacity service; F005 shell for the `Resources` sidebar entry; F006 row menu `Allocate` entry point; F015 project sheet lookup.
- Feature flag: `F033_FEATURE` gates routes and the flag hook.

## TDD

- Failing test first: `testing/features/F033/api/allocation_tests.rs::allocation_hours_and_percent_mutually_exclusive`, `::allocation_row_must_belong_to_sheet`, `::allocation_snapshots_effective_cost_rate`, `::allocation_create_returns_over_allocated_periods`, `::allocation_list_filters_by_overlap`, `::allocation_delete_recomputes_capacity`, `::allocation_cross_tenant_not_found`; `testing/features/F033/frontend/PlannerGrid.test.tsx::planner_marks_over_allocated_cell`, `AllocationDialog.test.tsx::rejects_hours_and_percent_together`, `CapacityStrip.test.tsx::renders_periods_as_meters`, `ResourcePage.test.tsx::hides_cost_rates_for_viewer`; `testing/features/F033/accessibility/resources.a11y.spec.ts::planner_has_no_serious_axe_violations`
- Targeted command: `cargo xtask test-feature F033`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/resources.rs`; MSW handlers from the two-resource fixture with an over-allocated week; axe via Playwright against seeded tenant

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Allocation routes mounted behind the flag; component and accessibility lanes pass
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S066
- [ ] `finished_at` recorded
