# F033 api cases

File: `testing/features/F033/api/{resource_tests.rs,capacity_tests.rs,allocation_tests.rs,permission_tests.rs}`. Flag `F033_FEATURE`.

- `resource_create_returns_version_one` — FR-F033-01: POST `/api/v1/resources` as admin returns 201, `version: 1`, default calendar applied.
- `resource_duplicate_user_link_conflicts` — FR-F033-01: second active resource for the same `user_id` → 409 `field_errors.user_id`; allowed after the first is inactive.
- `resource_fte_out_of_range_invalid` — FR-F033-01: `fte: 1.2` and `fte: 0.01` → 400 `field_errors.fte`.
- `resource_list_filters_by_skill_and_availability` — FR-F033-02: `skill=Rust&min_level=3` returns Ana only; `available_between` with `min_hours=10` excludes the leave week.
- `resource_stale_version_conflicts` — FR-F033-02: `If-Match: 1` against version 2 → 409 with `current_version`.
- `skills_replace_rejects_duplicates` — FR-F033-03: duplicate skill names → 400 `field_errors.skills[1]`; 51 entries → 400.
- `availability_overlap_invalid` — FR-F033-04: overlapping leave and holiday → 400 `field_errors.availability[1]`.
- `availability_reduced_requires_hours_per_day` — FR-F033-04: `kind: reduced` without `hours_per_day` → 400.
- `cost_rate_overlap_invalid` — FR-F033-05: two rates covering October → 400 `field_errors.cost_rates[1]`.
- `capacity_subtracts_leave_holiday_and_fte` — FR-F033-06: Ana weekly 2026-10-05..18 → `[fte 20, leave 20, available 0]`, `[calendar 32, fte 16, holiday 4, available 16]`.
- `capacity_reduced_days_lower_available_hours` — FR-F033-06: Ben with two reduced days at 4 h → `reduced_hours: 8`, `available_hours: 32`.
- `capacity_week_periods_start_monday_in_resource_timezone` — FR-F033-06: resource in `America/New_York` gets Monday-aligned weeks.
- `capacity_distributes_hours_evenly_over_working_days` — FR-F033-07: 40 h across 5 + 3 working days → 25 h and 15 h.
- `capacity_percent_allocation_uses_available_hours` — FR-F033-07: 50 percent on a 16 h week → `allocated_hours: 8`.
- `capacity_flags_no_working_days_warning` — FR-F033-07: Saturday to Sunday allocation → 0 h and `warning: no_working_days`.
- `capacity_range_over_366_days_invalid` — FR-F033-06: 367-day range → 400 `field_errors.to`.
- `availability_write_publishes_capacity_computed` — FR-F033-10: PUT availability → `capacity.computed.v1` with `changed_fields { resource_id, from, to }`.
- `allocation_hours_and_percent_mutually_exclusive` — FR-F033-08: both or neither → 400 `field_errors.planned`.
- `allocation_row_must_belong_to_sheet` — FR-F033-08: `row_id` from another sheet → 400 `field_errors.row_id`.
- `allocation_span_over_366_days_invalid` — FR-F033-08: 367-day allocation → 400 `field_errors.end_date`.
- `allocation_snapshots_effective_cost_rate` — FR-F033-05: start in October → `cost_rate_snapshot.hourly_rate: 60`, `planned_cost: 1200` for 20 h.
- `allocation_create_returns_over_allocated_periods` — FR-F033-10: 20 h into a 16 h week → `over_allocated_periods` contains the week, `allocation.created.v1` published.
- `allocation_list_filters_by_overlap` — FR-F033-09: `from/to` returns allocations overlapping the range; `confidence=tentative` filter applied.
- `allocation_delete_recomputes_capacity` — FR-F033-09, FR-F033-10: DELETE → `allocation.deleted.v1`, capacity `allocated_hours` drops, second `capacity.computed.v1`.
- `deactivate_with_future_allocations_conflicts` — FR-F033-14: PATCH `status: inactive` → 409 listing allocation IDs; with `end_allocations: true` → allocations end today.
- `mutation_writes_audit_and_outbox` — FR-F033-11: each mutation → one audit row with diff and one outbox row.
- `viewer_response_omits_cost_rates` — FR-F033-12: viewer GET resource and allocation → no `cost_rates`, `cost_rate_snapshot`, `planned_cost`.
- `resource_cross_tenant_not_found` — FR-F033-12: tenant B on resource, capacity, and allocation routes → 404.
- `allocation_cross_tenant_not_found` — FR-F033-12: tenant B PATCH/DELETE allocation → 404.
- `cross_tenant_all_routes_not_found` — NFR-F033-02: tenant B admin on all ten routes → 404.
- `viewer_all_mutations_denied` — FR-F033-12: viewer on every mutation route → 403, no audit mutation.
- `viewer_never_receives_cost_fields` — NFR-F033-02: list, detail, capacity, and allocation pages for viewer contain no cost keys.
- `self_reads_own_profile_and_capacity_only` — FR-F033-12: linked user → 200 on own profile and capacity, 404 on Ben.
- `request_span_carries_ids` — NFR-F033-04: span has `tenant_id`, `resource_id`, `allocation_id`, `correlation_id`.

Evidence: JUnit output and request logs under `testing/evidence/F033/api/`.
