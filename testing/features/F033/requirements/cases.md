# F033 requirements cases

Feature: Resources/capacity. Flag `F033_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F033-REQ-001` | FR-F033-01 | api, database | admin creates "Ana" FTE 0.5 → 201 version 1; second active resource for same `user_id` → 409 `field_errors.user_id` |
| `F033-REQ-002` | FR-F033-02 | api | 300 resources → cursor pages of 200; filter `skill=Rust&min_level=3`, `available_between` with `min_hours`; PATCH with stale `If-Match` → 409 |
| `F033-REQ-003` | FR-F033-03 | api | PUT 3 skills → replaced; duplicate `Rust` twice → 400 `skills[1]`; 51 skills → 400 |
| `F033-REQ-004` | FR-F033-04 | api, database | PUT leave and overlapping holiday → 400 `availability[1]`; reduced without `hours_per_day` → 400 |
| `F033-REQ-005` | FR-F033-05 | api | rates 50 USD until Sep, 60 USD from Oct; allocation starting Oct snapshots 60; `planned_cost` = hours × 60 |
| `F033-REQ-006` | FR-F033-06 | api | Ana 2026-10-05..18 weekly → week 1 fte 20 leave 20 available 0; week 2 calendar 32 fte 16 holiday 4 available 16 |
| `F033-REQ-007` | FR-F033-07 | api | 40 h over two weeks with 5 and 3 working days → 25 h and 15 h; 50 percent → half of available; weekend-only allocation → `no_working_days` |
| `F033-REQ-008` | FR-F033-08 | api | POST with hours and percent → 400 `field_errors.planned`; inactive resource → 400; 367-day span → 400 |
| `F033-REQ-009` | FR-F033-09 | api | list by `from/to` overlap and `confidence`; PATCH requires `If-Match`; DELETE soft-deletes with version |
| `F033-REQ-010` | FR-F033-10 | api | allocation 20 h into a 16 h week → response `over_allocated_periods` has that week; `capacity.computed.v1` with `{ resource_id, from, to }` |
| `F033-REQ-011` | FR-F033-11 | api, database | each mutation → one audit row and matching `resource.updated.v1` or `allocation.*.v1` |
| `F033-REQ-012` | FR-F033-12 | api, frontend | tenant B → 404; viewer → 403 on mutations and no cost fields; self reads own profile |
| `F033-REQ-013` | FR-F033-13 | frontend, e2e | directory badges, profile editors, capacity strip, planner with over-allocation markers |
| `F033-REQ-014` | FR-F033-14 | api | deactivate with future allocation → 409 listing IDs; `end_allocations: true` → ended today |
| `F033-NFR-001` | NFR-F033-01 | performance | capacity 52 weeks 200 allocations p95 < 500 ms; 5,000-resource list p95 < 500 ms; allocation create p95 < 800 ms |
| `F033-NFR-002` | NFR-F033-02 | api | cost fields absent from viewer responses and logs; invalid `user_id` → 400; cross-tenant suite green |
| `F033-NFR-003` | NFR-F033-03 | accessibility | axe serious = 0; meters expose values; over-allocation has text and icon; planner keyboard grid |
| `F033-NFR-004` | NFR-F033-04 | api, database | recompute inside the write transaction; failing outbox rolls back the allocation; spans carry IDs |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F033/`.
