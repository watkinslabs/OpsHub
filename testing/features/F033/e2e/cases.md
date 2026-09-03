# F033 e2e cases

File: `testing/features/F033/e2e/{resources.spec.ts,resource_permissions.spec.ts}`. Playwright against seeded tenant. Flag `F033_FEATURE`.

- `create_resource_add_leave_allocate_see_over_allocation` — FR-F033-01, FR-F033-04, FR-F033-08, FR-F033-10, FR-F033-13: admin creates "Cleo" FTE 0.8, adds leave for one week, allocates 20 h to "Rollout" in that week, planner shows `Over by 20 h`.
- `fte_change_updates_capacity_strip` — FR-F033-02, FR-F033-06: editing FTE from 1.0 to 0.5 halves `available_hours` in the strip after save.
- `percent_allocation_follows_available_hours` — FR-F033-07: 50 percent allocation shows 16 h in a normal week and 8 h in a reduced week.
- `deactivate_resource_ends_allocations` — FR-F033-14: deactivate dialog lists future allocations; confirming with `End allocations` sets their end date to today.
- `viewer_planner_has_no_costs_or_controls` — FR-F033-12: viewer sees planner and profiles without cost columns, `New allocation`, or editors.
- `self_user_sees_own_profile` — FR-F033-12: linked user opens their profile and capacity; opening Ben's profile shows not-found.
- `non_member_sees_not_found` — FR-F033-12: user outside the workspace opens the resources URL → not-found page.

Evidence: Playwright traces and videos under `testing/evidence/F033/e2e/`.
