---
id: T132
type: task
status: planned
parent_epic: E007
parent_feature: F033
parent_story: S066
depends_on: [T131]
owned_paths: [testing/features/F033/api/**, testing/features/F033/e2e/**, testing/features/F033/performance/**, testing/features/F033/requirements/**]
feature_flag: F033_FEATURE
branch: t132-capacity-tests
started_at: null
finished_at: null
---

# T132 — Capacity tests

## Identity

- Parent story: `S066` Allocations
- Owner: platform
- Branch: `t132-capacity-tests`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 4, 9; `docs/capability-contracts.md` row F033

## Objective

Prove capacity arithmetic, the normalized skill and cost-snapshot constraints, permission boundaries including cost visibility, and performance targets end to end through the browser and against generated large fixtures.

## Specification

- Owned paths: `testing/features/F033/api/permission_tests.rs`, `testing/features/F033/api/constraint_tests.rs`, `testing/features/F033/e2e/{resources.spec.ts, resource_permissions.spec.ts}`, `testing/features/F033/performance/capacity_bench.rs`, `testing/features/F033/requirements/cases.md`
- Contract/input: every fixture row is created through the `crates/persistence/src/resources/` repositories (`ResourceRepository`, `SkillRepository`, `AvailabilityRepository`, `CostRateRepository`, `AllocationRepository`) and every assertion reads back through them or through the API — no test opens a connection or issues SQL of its own (decision section 2.1); seeded tenant A with resource-admin, resource-viewer, a linked user who is also a resource, tenant B admin; Mon–Fri 8 h calendar with holiday `2026-10-12`; resources with FTE 1.0 and 0.5; generated fixtures: one resource with 200 allocations over 52 weeks and a tenant with 5,000 resources, both with fixed seeds.
- Output/behavior: `constraint_tests.rs` proves the normalized shape through the repositories — `resource_skills` rejects a second row for the same `(resource_id, skill_id)`, rejects a `level` outside 1–5, and disappears when its resource is purged, `skills` rejects a duplicate name within a tenant and cannot be deleted while a `resource_skills` row references it, the same skill name in two tenants stays two rows, and an allocation cannot be written with `cost_rate_id` set and `snapshot_hourly_rate` null or the reverse; API permission tests assert tenant B receives 404 on all ten routes, the viewer receives 403 on every mutation and never sees `cost_rates`, the `cost_rate_snapshot` object, or `planned_cost` on any read route or in list pages, and the linked user can read their own profile and capacity but not another resource's; E2E flows: administrator creates resource, adds leave, allocates 20 h to the leave week, sees `Over by 20 h`; edits FTE to 0.5 and sees the strip halve; viewer opens the planner without cost columns or edit controls; benchmarks: capacity 52 weeks with 200 allocations p95 < 500 ms over 200 requests; resource list `limit=200` over 5,000 resources p95 < 500 ms; allocation create p95 < 800 ms including recompute over 200 creates.
- Dependencies: T129 repositories and schema; T130 capacity service; T131 routes and pages; F003 fixture bindings; F011 calendar fixture.
- Feature flag: `F033_FEATURE`

## TDD

- Failing test first: `testing/features/F033/api/constraint_tests.rs::resource_skills_rejects_duplicate_skill_id`, `::resource_skills_level_out_of_range_rejected`, `::resource_skills_cascade_on_resource_purge`, `::skill_name_unique_per_tenant`, `::skill_delete_restricted_while_referenced`, `::allocation_snapshot_columns_pair_or_are_both_null`; `testing/features/F033/api/permission_tests.rs::cross_tenant_all_routes_not_found`, `::viewer_all_mutations_denied`, `::viewer_never_receives_cost_fields`, `::self_reads_own_profile_and_capacity_only`; `testing/features/F033/e2e/resources.spec.ts::create_resource_add_leave_allocate_see_over_allocation`, `::fte_change_updates_capacity_strip`; `testing/features/F033/e2e/resource_permissions.spec.ts::viewer_planner_has_no_costs_or_controls`; `testing/features/F033/performance/capacity_bench.rs::capacity_52_weeks_200_allocations_p95`, `::resource_list_5000_p95`, `::allocation_create_with_recompute_p95`
- Targeted command: `cargo xtask test-feature F033`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/resources.rs` plus 200-allocation and 5,000-resource generators, all writing through the resources repositories; Playwright against the real API; real authz engine

## Exit criteria

- [ ] Tests written before any fix and observed failing where behavior is missing
- [ ] Permission-negative, E2E, and performance lanes green in targeted and full modes
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S066
- [ ] `finished_at` recorded
