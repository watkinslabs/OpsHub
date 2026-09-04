---
id: F033
type: feature
status: planned
priority: P1
owner: platform
estimate: 8
target_milestone: M6
parent_epic: E007
depends_on: [F011, F002]
blocks: [F034]
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/resources/**, crates/persistence/src/resources/**, services/api/src/resources/**, apps/web/src/features/resources/**, services/api/migrations/*_resources_*.sql, testing/features/F033/**]
feature_flag: F033_FEATURE
flag_default: off
branch: f033-resources-capacity
started_at: null
finished_at: null
---

# F033 — Resources/capacity

## 1. Identity and dates

- Branch: `f033-resources-capacity`
- Capability area: resource planning (spec 5.7 PPM-03; low-level bullets "Resource allocations are period-based with planned hours/percent, actuals, role, cost rate, and confidence" and "Capacity calculation accounts for working calendar, leave, holidays, part-time availability, and allocation conflicts"; section 4 Resource / Allocation entity; 5.11 Resource Management profiles, capacity, allocations)
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 9; `docs/capability-contracts.md` row F033
- Aggregate: `resource-profile`
- Module slug: `resources`

## 2. Requirement specification

### Problem and user outcome

Resource managers plan people against projects in spreadsheets that ignore part-time schedules, leave, and holidays, so commitments look feasible until they collide. They need resource profiles that carry skills, availability, and cost rates, allocations expressed per period as hours or percent with a role and confidence, and a capacity calculation that starts from the tenant working calendar and subtracts leave, holidays, and reduced availability before comparing against allocations.

As a resource administrator, I want to maintain resource profiles and period-based allocations and see true available capacity per period, so that plans reflect who can actually do the work and what it will cost.

### Functional requirements

- **FR-F033-01:** An actor with the `resource-admin` role can create a resource with `display_name` (1–200), `kind` in {`person`, `placeholder`}, optional `user_id` (a tenant user, unique across active resources), `role_title` (≤ 100), `working_calendar_id` (an F011 calendar, default the tenant calendar), `fte` (0.05–1.00, two decimals), `timezone` (IANA), and `status` in {`active`, `inactive`}; a second active resource for the same `user_id` returns `conflict` with `field_errors.user_id`.
- **FR-F033-02:** `GET /api/v1/resources` pages by opaque cursor with `limit` 1–200, filters `status`, `kind`, `skill` (name with optional `min_level`, resolved by joining `resource_skills` to `skills` on the tenant-scoped skill name, never by scanning an array), `role_title` prefix, and `available_between` (`from`, `to`, `min_hours`), and sorts by `display_name` or `updated_at`; `PATCH /api/v1/resources/{id}` updates profile fields and `cost_rates` with `If-Match`.
- **FR-F033-03:** `PUT /api/v1/resources/{id}/skills` replaces the skill set with up to 50 entries of `{ skill (1–80 chars), level 1–5 }`; each distinct name resolves to one `skills` row per tenant and each entry is stored as one `resource_skills(resource_id, skill_id, level)` row, so a skill can be joined, counted, and indexed; duplicate skill names in one request return `invalid` with `field_errors.skills[i]`, and the request and response keep the `skills` array of `{ skill, level }` objects so the API shape is unchanged.
- **FR-F033-04:** `PUT /api/v1/resources/{id}/availability` replaces up to 500 availability entries of `{ kind in {leave, holiday, reduced}, start_date, end_date, hours_per_day? (required for reduced, 0–23.75), note? }` where entries must not overlap and `end_date ≥ start_date`; overlaps return `invalid` with `field_errors.availability[i]`.
- **FR-F033-05:** Cost rates are an ordered list of `{ hourly_rate (0–100,000, two decimals), currency (ISO 4217), effective_from, effective_to? }` per resource with no overlapping effective ranges; the rate effective on an allocation's `start_date` is snapshotted into the allocation's typed `cost_rate_id`, `snapshot_hourly_rate`, `snapshot_currency`, and `snapshot_effective_from` columns, and the allocation exposes `planned_cost = planned_hours × snapshot_hourly_rate`; the response keeps a `cost_rate_snapshot` object so the API shape is unchanged.
- **FR-F033-06:** `GET /api/v1/resources/{id}/capacity?from&to&granularity=day|week` for a range of at most 366 days returns, per period, `calendar_hours` (working days × hours per day from the F011 calendar, excluding calendar exceptions), `fte_hours = calendar_hours × fte`, `leave_hours`, `holiday_hours`, `reduced_hours`, `available_hours = fte_hours − leave − holiday − reduced` (never below 0), `allocated_hours`, `remaining_hours`, and `over_allocated` when `allocated_hours > available_hours`, plus range totals.
- **FR-F033-07:** Allocation hours are distributed evenly across the working days of the allocation period that fall inside each capacity period; `planned_percent` allocations contribute `percent × available_hours` of each period; an allocation whose period contains no working days contributes 0 and is reported with `warning: no_working_days`.
- **FR-F033-08:** `POST /api/v1/allocations` by a `resource-admin` creates an allocation with `resource_id` (active), `project_sheet_id` (an F015 provisioned project or any sheet flagged as a project), optional `row_id` belonging to that sheet, `start_date`, `end_date` (`end ≥ start`, span ≤ 366 days), exactly one of `planned_hours` (0.25–10,000) or `planned_percent` (1–100), `role` (≤ 100), `confidence` in {`committed`, `likely`, `tentative`}, and optional `note`; providing both or neither of hours and percent returns `invalid` with `field_errors.planned`.
- **FR-F033-09:** `GET /api/v1/allocations` pages with `limit` 1–500 and filters `resource_id`, `project_sheet_id`, `row_id`, `from`, `to` (overlap), and `confidence`; `PATCH /api/v1/allocations/{id}` updates any allocation field with `If-Match`; `DELETE` soft-deletes; each returns `version`.
- **FR-F033-10:** Every allocation, availability, and profile write recomputes capacity for the affected resource and date span inside the same request, publishes `capacity.computed.v1` with `changed_fields` = `{ resource_id, from, to }`, and returns `over_allocated_periods` in the mutation response so callers see conflicts immediately.
- **FR-F033-11:** Every mutation requires `Idempotency-Key`, writes an `audit_events` row with a field diff, and publishes `resource.updated.v1` (create, patch, skills, availability) or `allocation.created.v1`, `allocation.updated.v1`, `allocation.deleted.v1`.
- **FR-F033-12:** Cross-tenant access to any resource or allocation returns `not_found`; a `resource-viewer` can read resources, capacity, and allocations but receives `denied` on every mutation; `cost_rates`, the `cost_rate_snapshot` object built from the allocation's snapshot columns, and `planned_cost` are omitted from responses to actors without `resource-admin`; a user may read their own resource profile and capacity.
- **FR-F033-13:** The web resource directory lists resources with skills and availability badges; the resource page shows profile, skills, availability, a weekly capacity strip; the allocation planner shows resources by week with allocation bars, an allocation dialog, and inline over-allocation markers.
- **FR-F033-14:** Deactivating a resource (`status: inactive`) is rejected with `conflict` and `field_errors.status` listing allocation IDs while it has allocations ending after today, unless the request includes `end_allocations: true`, which sets `end_date` to today on those allocations in the same transaction.

### Non-functional requirements

- **NFR-F033-01 Performance:** capacity for one resource over 52 weeks with 200 allocations responds in under 500 ms p95; resource list of 5,000 resources pages in under 500 ms p95; allocation create responds in under 800 ms p95 including capacity recompute (spec section 6).
- **NFR-F033-02 Security/privacy:** cost data is field-level filtered by role in the service layer and never reaches viewer responses or logs; tenant isolation is enforced by `tenant_id` predicates and tested with cross-tenant and viewer negatives; `user_id` links are validated against F002 active users.
- **NFR-F033-03 Accessibility:** the capacity strip and planner expose per-period values as text and `meter` semantics, over-allocation is conveyed by text and icon, dialogs trap focus, and axe reports no serious violations.
- **NFR-F033-04 Reliability/observability:** capacity recompute runs in the write transaction so allocation and capacity are never inconsistent; spans carry `tenant_id`, `resource_id`, `allocation_id`, `correlation_id`; metrics `capacity_compute_ms` and `allocation_write_ms` are exported.

### Scope

Included: resource CRUD, skills, availability, cost rates, capacity calculation with working calendar, leave, holidays, reduced availability and FTE, allocation CRUD with hours or percent, role, confidence, cost snapshot, over-allocation flags, resource directory, resource page, allocation planner.

Excluded: workload aggregation across resources and persistent conflict records (F034), time entries and actuals (F034), working calendar authoring (F011), forecasting and resource requests (E008 Resource Management module), notifications on conflicts (F037 consumes events).

## 3. UX specification

- Entry points: workspace sidebar `Resources` → `/w/{workspace_id}/resources` (directory), `/w/{workspace_id}/resources/{resource_id}` (profile), `/w/{workspace_id}/allocations` (planner); `New resource` and `New allocation` buttons for administrators; project sheet row menu `Allocate`.
- Primary flow: administrator opens `Resources`, clicks `New resource`, enters name, role, FTE 0.8, calendar, submits; adds skills `Rust 4`, `PostgreSQL 3`; adds leave `2026-10-05` to `2026-10-09`; opens the planner, clicks a week cell, creates an allocation `Project Rollout, 20 h/week, role Engineer, committed` for four weeks; the leave week shows `Over-allocated` because available hours dropped.
- Loading: skeleton cards and planner rows; Empty: `No resources yet` with `New resource`; Error: banner with `correlation_id` and retry; Success: toast on create/update; Conflict: `This resource changed` banner with reload; Over-allocated: red text `Over by 6 h` with `AlertTriangle` icon in the period cell; Denied: administrators-only controls hidden; Offline: edits disabled with offline badge.
- Permission-denied: viewers see directory, profiles, capacity, and allocations without cost fields and without edit controls; non-members see not-found.
- Responsive: under 768 px the planner shows one resource at a time with a week picker; profile sections stack.
- Keyboard: planner cells are focusable in a grid pattern (arrow keys), `Enter` opens the allocation dialog, `Delete` prompts removal; dialogs trap focus, `Escape` cancels; `prefers-reduced-motion` disables bar transitions.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062), Lucide icons `Users`, `UserPlus`, `CalendarOff`, `Gauge`, `AlertTriangle`, `Coins`; tokens from `apps/web/src/design/tokens.css`.

- Design: `design/artboards/Resources.dc.html` on the canvas indexed by `design/canvas.json`. The ticket is the contract and the artboard is the picture; when they disagree the ticket wins.

## 4. Technical specification

### Rust backend

- Data access (decision section 2.1): `crates/persistence/src/resources/` holds `ResourceRepository` (owns `resources` and its junction `resource_skills`), `SkillRepository` (owns the tenant `skills` lookup), `AvailabilityRepository` (owns `resource_availability`), `CostRateRepository` (owns `cost_rates`), and `AllocationRepository` (owns `allocations`); no other class writes those tables, and the F011 `WorkingCalendarRepository` and F002 `UserRepository` are consumed as traits, never re-queried here. Named queries: `find_by_user_id`, `list_filtered` (status, kind, `role_title` prefix, skill with `min_level`, `available_between`), `replace_skills`, `list_skills_for_resources`, `set_status`; `find_or_create_by_name`, `resolve_names`; `replace_availability_entries`, `list_availability_overlapping`; `replace_cost_rates`, `find_rate_effective_on`, `list_rates_for_resource`; `list_allocations_overlapping`, `list_allocations_filtered`, `list_active_allocations_ending_after`, `end_allocations_today`. No generic query escape hatch exists on any of them.
- Every use case below depends on those repository traits and contains no SQL; `compute_capacity` reads the calendar through F011's repository trait and the resource, availability, and allocation rows through `ResourceRepository`, `AvailabilityRepository`, and `AllocationRepository`, so the capacity calculator never touches SQLx. `services/api/src/resources/` handlers and `crates/domain/src/resources/` services hold no `sqlx::query*` call. A resource save (profile row, `resource_skills` replacement, `skills` inserts, `cost_rates` replacement, audit row, outbox row), an availability replacement, an allocation write with its capacity recompute, and deactivation with `end_allocations: true` each run as one `UnitOfWork` transaction shared across those repositories.
- Domain entities in `crates/domain/src/resources/`: `Resource { id, tenant_id, user_id, display_name, kind: ResourceKind, role_title, working_calendar_id, fte: Decimal, timezone, status: ResourceStatus, version, audit fields, deleted_at }`, `Skill { id, tenant_id, name }`, `ResourceSkill { resource_id, skill_id, skill_name, level: u8 }`, `AvailabilityEntry { id, resource_id, kind: AvailabilityKind, start_date, end_date, hours_per_day: Option<Decimal>, note }`, `CostRate { id, resource_id, hourly_rate: Decimal, currency, effective_from, effective_to }`, `Allocation { id, tenant_id, resource_id, project_sheet_id, row_id, start_date, end_date, planned: Planned (Hours | Percent), role, confidence: Confidence, cost_rate_id: Option<CostRateId>, snapshot_hourly_rate: Option<Decimal>, snapshot_currency: Option<Currency>, snapshot_effective_from: Option<Date>, note, version, audit fields, deleted_at }`, `CapacityPeriod { start, end, calendar_hours, fte_hours, leave_hours, holiday_hours, reduced_hours, available_hours, allocated_hours, remaining_hours, over_allocated, warnings }`.
- Use cases: `create_resource`, `update_resource`, `list_resources`, `get_resource`, `replace_skills`, `replace_availability`, `compute_capacity`, `create_allocation`, `update_allocation`, `delete_allocation`, `list_allocations`, `deactivate_resource`.
- API endpoints (`services/api/src/resources/`): `GET /api/v1/resources`, `POST /api/v1/resources`, `PATCH /api/v1/resources/{id}`, `PUT /api/v1/resources/{id}/skills`, `PUT /api/v1/resources/{id}/availability`, `GET /api/v1/resources/{id}/capacity`, `GET /api/v1/allocations`, `POST /api/v1/allocations`, `PATCH /api/v1/allocations/{id}`, `DELETE /api/v1/allocations/{id}`. DTOs: `CreateResourceRequest`, `UpdateResourceRequest { ..., cost_rates?, end_allocations? }`, `ReplaceSkillsRequest`, `ReplaceAvailabilityRequest`, `ResourceResponse`, `CapacityResponse { granularity, periods, totals }`, `CreateAllocationRequest`, `UpdateAllocationRequest`, `AllocationResponse { ..., planned_cost?, over_allocated_periods }`, `Page<T>`.
- Events: `resource.updated.v1`, `allocation.created.v1`, `allocation.updated.v1`, `allocation.deleted.v1`, `capacity.computed.v1`; payload per contract conventions with `changed_fields`.
- Authorization: `resource-admin` for all mutations; `resource-viewer` or `resource-admin` for reads; `self` reads own profile and capacity; cost fields filtered by `ResponseScope::with_costs(actor)`; explicit deny wins; missing access maps to `not_found`.
- Validation: limits from FR-F033-01 through FR-F033-09; dates validated against the resource's calendar; range ≤ 366 days for capacity and allocations. Idempotency via `idempotency_keys` for 24 hours. Concurrency: `If-Match` on resource and allocation.
- Error mapping: `ResourceError::UserAlreadyLinked → 409 conflict`, `ResourceError::HasFutureAllocations → 409 conflict`, `ResourceError::StaleVersion → 409 conflict`, `ResourceError::NotFound → 404 not_found`, `ResourceError::OverlappingAvailability(i) → 400 invalid`, `AllocationError::PlannedAmbiguous → 400 invalid`, `AllocationError::RangeTooLong → 400 invalid`, `AuthzError::Denied → 403 denied`.

### Interface

Ids are UUIDv7 strings, timestamps RFC 3339 UTC, dates `YYYY-MM-DD`, decimals are JSON numbers with
the scale each field states, `version` increments by one per write. `T?` is nullable and an absent
optional field equals an explicit `null`. Unlisted fields are rejected with `400 invalid`. `Page<T>`,
the opaque cursor and the error body are F028's. Mutations require `Idempotency-Key`; `PATCH`, `PUT`
and `DELETE` require `If-Match: <version>`.

Cost is field-level filtered, not route-level: `cost_rates`, `cost_rate_snapshot` and `planned_cost`
are **absent** from every response to an actor without `resource-admin`. Absent, not null — a null
would tell a viewer that a rate exists.

**`CreateResourceRequest`** — `POST /api/v1/resources`

| Field | Type | Required | Constraint |
|---|---|---|---|
| `display_name` | string | yes | 1–200 chars after trim |
| `kind` | `"person" \| "placeholder"` | yes | `placeholder` must not carry `user_id` |
| `user_id` | uuid? | no | an active F002 user of this tenant; a second **active** resource for the same user is `409 conflict` with `field_errors.user_id = "linked"` |
| `role_title` | string? | no | ≤ 100 chars |
| `working_calendar_id` | uuid? | no | an F011 calendar of this tenant; default the tenant's default calendar |
| `fte` | decimal | no | `0.05..=1.00`, two decimals, default `1.00` |
| `timezone` | string | yes | IANA name |
| `status` | `"active" \| "inactive"` | no | default `"active"` |
| `cost_rates` | CostRate[] | no | `resource-admin` only; a viewer sending it gets `403 denied`; ranges must not overlap |

**`UpdateResourceRequest`** — `PATCH /api/v1/resources/{id}`, every field optional, at least one
present: the create fields plus `cost_rates` (replaces the set whole) and `end_allocations` (bool,
default `false`). Setting `status: "inactive"` while allocations end after today is `409 conflict`
with `field_errors.status` listing those allocation ids in `details.allocation_ids`, unless
`end_allocations: true`, which sets their `end_date` to today in the same transaction.

**`CostRate`**: `{ id: uuid (response only), hourly_rate: decimal (0–100,000, two decimals), currency: string (ISO 4217 alpha-3, uppercase), effective_from: date, effective_to: date? }`. Ranges are inclusive and must not overlap for one resource, else `400 invalid` with `field_errors.cost_rates[i] = "overlap"`; `effective_to` null means open-ended.

**`ReplaceSkillsRequest`** — `PUT /api/v1/resources/{id}/skills`: `{ skills: [{ skill: string (1–80 chars), level: integer (1–5) }] }`, 0–50 entries. Names are matched case-insensitively per tenant; a repeated name is `400 invalid` with `field_errors.skills[i] = "duplicate"`. The set is replaced whole.

**`ReplaceAvailabilityRequest`** — `PUT /api/v1/resources/{id}/availability`: `{ availability: AvailabilityEntry[] }`, 0–500 entries, replaced whole.

**`AvailabilityEntry`**

| Field | Type | Required | Constraint |
|---|---|---|---|
| `id` | uuid | response only | |
| `kind` | `"leave" \| "holiday" \| "reduced"` | yes | |
| `start_date` / `end_date` | date | yes | `end_date >= start_date`; entries must not overlap for one resource, else `400 invalid` with `field_errors.availability[i] = "overlap"` |
| `hours_per_day` | decimal? | conditional | required for `reduced`, `0..=23.75` with two decimals; rejected for `leave` and `holiday` |
| `note` | string? | no | ≤ 500 chars |

**`ResourceResponse`**: the profile fields plus `{ id, skills: [{ skill, level }] (ordered by skill name), availability: AvailabilityEntry[] (ordered by start_date, detail read only), cost_rates: CostRate[] (admin only, ordered by effective_from), version, created_at, created_by, updated_at, updated_by, deleted_at? }`.

**`GET /api/v1/resources`** returns `Page<ResourceResponse>` without `availability`, sorted by `sort` = `display_name` or `updated_at` (default `display_name`), with F028's `cursor`, `limit` (1–200, default 50) and `include_total`, and these filters:

| Parameter | Type | Constraint |
|---|---|---|
| `status` | `"active"\|"inactive"`? | |
| `kind` | `"person"\|"placeholder"`? | |
| `skill` | string? | a skill name; `min_level` (1–5) may accompany it and is ignored without it |
| `role_title` | string? | prefix match, case-insensitive |
| `available_between` | `{ from: date, to: date, min_hours: decimal }`? | matches resources whose `remaining_hours` over the range is at least `min_hours`; `to − from` ≤ 366 days |

**`CapacityResponse`** — `GET /api/v1/resources/{id}/capacity?from&to&granularity`

| Field | Type | Notes |
|---|---|---|
| `granularity` | `"day" \| "week"` | required parameter; `week` periods start on the calendar's week start |
| `periods` | CapacityPeriod[] | one per period in the range, ascending; `to − from` ≤ 366 days, else `400 invalid` with `field_errors.to = "range"` |
| `totals` | CapacityPeriod | the same fields summed over the range, with `start`/`end` equal to `from`/`to` and `over_allocated` true when any period is |

**`CapacityPeriod`**: `{ start: date, end: date, calendar_hours: decimal, fte_hours: decimal, leave_hours: decimal, holiday_hours: decimal, reduced_hours: decimal, available_hours: decimal, allocated_hours: decimal, remaining_hours: decimal, over_allocated: bool, warnings: string[] }`. All hours have two decimals. `available_hours = max(0, fte_hours − leave_hours − holiday_hours − reduced_hours)`; `remaining_hours = available_hours − allocated_hours` and may be negative; `over_allocated` is `allocated_hours > available_hours`. `warnings` carries `no_working_days` for a period an allocation spans with no working day in it.

**`CreateAllocationRequest`** — `POST /api/v1/allocations`

| Field | Type | Required | Constraint |
|---|---|---|---|
| `resource_id` | uuid | yes | an `active` resource of this tenant; an `inactive` one is `409 conflict` with `field_errors.resource_id = "inactive"` |
| `project_sheet_id` | uuid | yes | a project sheet the caller may read; unreadable → `404 not_found` |
| `row_id` | uuid? | no | a live row of `project_sheet_id`, else `400 invalid` with `field_errors.row_id = "different_sheet"` |
| `start_date` / `end_date` | date | yes | `end_date >= start_date` and the span ≤ 366 days, else `field_errors.end_date = "range"` |
| `planned_hours` | decimal? | conditional | `0.25..=10000`, two decimals |
| `planned_percent` | integer? | conditional | `1..=100` |
| `role` | string? | no | ≤ 100 chars |
| `confidence` | `committed\|likely\|tentative` | no | default `"committed"` |
| `note` | string? | no | ≤ 1,000 chars |

Exactly one of `planned_hours` and `planned_percent` must be present; both or neither is
`400 invalid` with `field_errors.planned = "ambiguous"`.

**`UpdateAllocationRequest`** — `PATCH /api/v1/allocations/{id}`: the same fields, all optional, at
least one present; `resource_id` may change, which recomputes capacity for both resources.

**`AllocationResponse`**: the request fields plus `{ id, cost_rate_snapshot: { cost_rate_id, hourly_rate, currency, effective_from }? (admin only; null when no rate was effective on start_date), planned_cost: decimal? (admin only; planned_hours × hourly_rate, null when either input is), over_allocated_periods: CapacityPeriod[], version, created_at, created_by, updated_at, updated_by, deleted_at? }`. `over_allocated_periods` is the subset of the affected resource's periods that this write pushed over, returned on create, update and delete so a caller sees the conflict without a second request; it is empty on a read.

**`GET /api/v1/allocations`** returns `Page<AllocationResponse>` sorted `start_date` then `id`, with `limit` 1–500 (default 100) and filters `resource_id`, `project_sheet_id`, `row_id`, `confidence`, and `from`/`to` which match by **overlap**, not containment. `DELETE /api/v1/allocations/{id}` soft-deletes and returns `200` with the response body, because the caller still needs `over_allocated_periods`.

Status codes:

| Code | Produced by |
|---|---|
| `200` | reads, `PATCH`, `PUT` skills, `PUT` availability, `DELETE` |
| `201` | `POST /api/v1/resources`, `POST /api/v1/allocations` |
| `400 invalid` | any field bound above, `overlap`, `duplicate`, `ambiguous`, `range`, `different_sheet`, `limit` out of range |
| `403 denied` | a `resource-viewer` on any mutation, or any actor without `resource-admin` sending `cost_rates` |
| `404 not_found` | resource, allocation, sheet, row or calendar in another tenant, or invisible to the caller |
| `409 conflict` | `linked`, `inactive`, deactivation with future allocations, stale `If-Match`, `Idempotency-Key` replayed with a different body |
| `429 rate_limited` | tenant write quota exceeded |

There is no `502` on these routes: F033 calls no external service.

### Use case signatures

In `crates/domain/src/resources/`. `Ctx` is F038's `ActorContext`; the calendar comes from F011's
repository trait, never from this feature's SQL.

```rust
fn create_resource(ctx: &Ctx, uow: &mut UnitOfWork, req: CreateResource) -> Result<Resource, DomainError>;
fn update_resource(ctx: &Ctx, uow: &mut UnitOfWork, id: ResourceId, expected: Version, req: UpdateResource) -> Result<Resource, DomainError>;
fn list_resources(ctx: &Ctx, repo: &dyn ResourceRepository, filter: ResourceFilter, page: Cursor) -> Result<Page<Resource>, DomainError>;
fn get_resource(ctx: &Ctx, repo: &dyn ResourceRepository, id: ResourceId) -> Result<Resource, DomainError>;
fn replace_skills(ctx: &Ctx, uow: &mut UnitOfWork, id: ResourceId, expected: Version, skills: Vec<SkillEntry>) -> Result<Resource, DomainError>;
fn replace_availability(ctx: &Ctx, uow: &mut UnitOfWork, id: ResourceId, expected: Version, entries: Vec<AvailabilityEntry>) -> Result<Resource, DomainError>;
fn compute_capacity(ctx: &Ctx, repos: &CapacityInputs<'_>, id: ResourceId, range: DateRange, granularity: Granularity) -> Result<Capacity, DomainError>;
fn create_allocation(ctx: &Ctx, uow: &mut UnitOfWork, req: CreateAllocation) -> Result<(Allocation, Vec<CapacityPeriod>), DomainError>;
fn update_allocation(ctx: &Ctx, uow: &mut UnitOfWork, id: AllocationId, expected: Version, req: UpdateAllocation) -> Result<(Allocation, Vec<CapacityPeriod>), DomainError>;
fn delete_allocation(ctx: &Ctx, uow: &mut UnitOfWork, id: AllocationId, expected: Version) -> Result<(Allocation, Vec<CapacityPeriod>), DomainError>;
fn list_allocations(ctx: &Ctx, repo: &dyn AllocationRepository, filter: AllocationFilter, page: Cursor) -> Result<Page<Allocation>, DomainError>;
fn deactivate_resource(ctx: &Ctx, uow: &mut UnitOfWork, id: ResourceId, expected: Version, end_allocations: bool) -> Result<Resource, DomainError>;
```

`CapacityInputs<'_>` bundles the four traits `compute_capacity` reads — the F011 calendar repository
and this feature's resource, availability and allocation repositories — so the calculator takes one
argument instead of four and cannot be handed a pool. Cost filtering is not a use-case concern: the
handler applies `ResponseScope::with_costs(actor)` to the returned entity, so a use case never has two
shapes.

Transaction boundaries:

- `create_resource` and `update_resource` write the `resources` row, any `skills` rows the names
  resolve to, the `resource_skills` replacement, the `cost_rates` replacement, the audit row and the
  `resource.updated.v1` outbox row in one `UnitOfWork`. The non-overlap exclusion constraint on
  `cost_rates` is only meaningful if the whole set lands at once.
- `replace_skills` and `replace_availability` each open one boundary covering the delete of removed
  rows, the insert of the rest, the resource's version bump and the audit row. A half-replaced
  availability set would compute a capacity nobody agreed to.
- `create_allocation`, `update_allocation` and `delete_allocation` each open one `UnitOfWork` covering
  the allocation write, the cost-rate snapshot read and copy, the capacity recompute for the affected
  resource and span, the audit row, the `allocation.*.v1` event and the `capacity.computed.v1` event.
  Capacity is recomputed **inside** the write transaction, not by a follow-up job, which is the
  invariant that stops a caller reading an allocation that its capacity does not yet reflect. An
  update that moves an allocation to another resource recomputes both resources in that same
  boundary.
- `deactivate_resource` with `end_allocations: true` writes the status change and every affected
  allocation's new `end_date` in one boundary; otherwise a resource could be inactive while still
  consuming capacity.
- `compute_capacity` opens no `UnitOfWork` and takes repositories directly — a read that could write
  would make the capacity endpoint unsafe for a `resource-viewer`.

### PostgreSQL/SQLx

- Migration `*_resources_*.sql` creates `resources(id uuid pk, tenant_id uuid not null, user_id uuid null references users(id) on delete restrict, display_name text not null, kind text not null check (kind in ('person','placeholder')), role_title text, working_calendar_id uuid not null references working_calendars(id) on delete restrict, fte numeric(3,2) not null default 1.00, timezone text not null, status text not null default 'active' check (status in ('active','inactive')), version bigint, audit fields, deleted_at)`, `resource_availability(id uuid pk, tenant_id, resource_id uuid not null references resources(id) on delete cascade, kind text not null check (kind in ('leave','holiday','reduced')), start_date date not null, end_date date not null, hours_per_day numeric(4,2), note text)`, `cost_rates(id uuid pk, tenant_id, resource_id uuid not null references resources(id) on delete cascade, hourly_rate numeric(12,2) not null, currency char(3) not null, effective_from date not null, effective_to date)`, `allocations(id uuid pk, tenant_id, resource_id uuid not null references resources(id) on delete restrict, project_sheet_id uuid not null references sheets(id) on delete restrict, row_id uuid null references rows(id) on delete restrict, start_date date not null, end_date date not null, planned_hours numeric(10,2), planned_percent smallint, role text, confidence text not null check (confidence in ('committed','likely','tentative')), cost_rate_id uuid null references cost_rates(id) on delete restrict, snapshot_hourly_rate numeric(12,2), snapshot_currency char(3), snapshot_effective_from date, note text, version bigint, audit fields, deleted_at)`.
- Normalized sets (decision section 2, no array or delimited columns): the skill set is a tenant lookup plus a junction carrying the proficiency level — `skills(id uuid pk, tenant_id uuid not null, name text not null, created_by, created_at, unique (tenant_id, lower(name)))` holds each distinct skill name once so it can be renamed, counted, and reported on, and `resource_skills(tenant_id, resource_id uuid not null references resources(id) on delete cascade, skill_id uuid not null references skills(id) on delete restrict, level smallint not null check (level between 1 and 5), created_at, primary key (resource_id, skill_id))` carries the level. `skills` rows outlive any one resource, so the junction cascades from the resource and restricts on the skill. `ResourceRepository::replace_skills` resolves names through `SkillRepository::find_or_create_by_name`, deletes removed rows, and inserts the rest in one statement pair inside the resource `UnitOfWork`; the `skills` array of `{ skill, level }` objects in requests and responses is reassembled on read, so no externally visible behaviour changes. The allocation cost snapshot is likewise typed: `cost_rate_id`, `snapshot_hourly_rate`, `snapshot_currency`, and `snapshot_effective_from` replace the former `cost_rate_snapshot jsonb`, and the DTO still emits a `cost_rate_snapshot` object.
- `jsonb` audit: no `jsonb` column remains in this module. `allocations.cost_rate_snapshot` was a modelling error under decision section 2 — the product read `hourly_rate` by key to compute `planned_cost`, filtered cost fields by role, and needs cost roll-ups per project, so it became the four typed columns above with a real foreign key to the `cost_rates` row it was taken from. `capacity.computed.v1` payloads and audit diffs stay `jsonb` in the F004 outbox and F027 audit tables, which this feature writes through but does not own.
- Invariants: unique partial index `resources_tenant_user_idx on (tenant_id, user_id) where status = 'active' and deleted_at is null and user_id is not null`; check `fte between 0.05 and 1.00`; `skills` unique on `(tenant_id, lower(name))` with `char_length(name) between 1 and 80`; `resource_skills` primary key `(resource_id, skill_id)` rejects a duplicate skill on a resource, replacing the former repeated-name key, and `level between 1 and 5` is checked on the junction row; exclusion constraint `resource_availability_no_overlap exclude using gist (resource_id with =, daterange(start_date, end_date, '[]') with &&)`; check `kind <> 'reduced' or hours_per_day is not null`; exclusion `cost_rates_no_overlap` on `(resource_id, daterange(effective_from, coalesce(effective_to, 'infinity'), '[]'))`; check `(planned_hours is null) <> (planned_percent is null)`; check `end_date >= start_date and end_date - start_date <= 366`; check `(cost_rate_id is null) = (snapshot_hourly_rate is null)` so a snapshot is never half-written; every foreign key above is declared, `cascade` only where the child cannot outlive its parent (`resource_skills`, `resource_availability`, `cost_rates`) and `restrict` elsewhere.
- Indexes: `resources(tenant_id, status, display_name)`, `skills(tenant_id, name)` for name resolution and the directory filter list, `resource_skills(skill_id, level)` for the `skill` + `min_level` filter and the reverse "who has this skill" query, `resource_skills(tenant_id, resource_id)` for badge hydration of a directory page, `allocations(resource_id, start_date, end_date) where deleted_at is null`, `allocations(project_sheet_id) where deleted_at is null`, `allocations(row_id)`, `allocations(cost_rate_id)`, gist `allocations using gist (resource_id, daterange(start_date, end_date, '[]'))`.
- Audit events: `resource.create`, `resource.update`, `resource.skills.replace`, `resource.availability.replace`, `resource.deactivate`, `allocation.create`, `allocation.update`, `allocation.delete` with field-level diffs (cost values masked in audit display for non-admins).
- Retention/deletion: resources and allocations soft-delete; purge via F027; migration rollback drops the six tables children first (`allocations`, `resource_skills`, `resource_availability`, `cost_rates`, then `skills` and `resources`) and the `btree_gist` extension dependency remains.

### React/TypeScript

- Routes: `/w/:workspaceId/resources`, `/w/:workspaceId/resources/:resourceId`, `/w/:workspaceId/allocations` in `apps/web/src/features/resources/`; components `ResourceDirectoryPage`, `ResourceCard`, `ResourcePage`, `SkillsEditor`, `AvailabilityEditor`, `CostRatesEditor`, `CapacityStrip`, `AllocationPlannerPage`, `PlannerGrid`, `PlannerCell`, `AllocationDialog`, `NewResourceDialog`, `DeactivateResourceDialog`.
- State: TanStack Query keys `['resources', workspaceId, filters, cursor]`, `['resource', id]`, `['capacity', id, from, to, granularity]`, `['allocations', filters, cursor]`; allocation mutations invalidate `['capacity', resourceId]` and `['allocations']`.
- API client: generated `ResourcesApi` with `listResources`, `createResource`, `updateResource`, `replaceSkills`, `replaceAvailability`, `getCapacity`, `listAllocations`, `createAllocation`, `updateAllocation`, `deleteAllocation`.
- Optimistic updates: allocation create and move apply locally in the planner and roll back on `invalid` or `conflict` with the stale banner.
- Telemetry: `resource_created`, `resource_deactivated`, `skills_replaced`, `availability_replaced`, `capacity_viewed`, `allocation_created`, `allocation_updated`, `allocation_deleted` with `resource_id` and `granularity`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F033-01 through FR-F033-14 in `testing/features/F033/requirements/cases.md`
- [ ] Failure/edge-case tests: duplicate user link, overlapping availability, both hours and percent, 367-day allocation, allocation with no working days, deactivate with future allocations, capacity range over 366 days
- [ ] Permission-negative and tenant-isolation tests: cross-tenant `not_found`, viewer mutation `denied`, cost fields absent for viewers, self reads own profile
- [ ] Rust unit tests: `crates/domain/src/resources/` capacity arithmetic with FTE, leave, holidays, reduced days, even distribution, percent allocations, rate selection
- [ ] API contract/integration tests: every route above with success and each error code
- [ ] Database migration/constraint tests: user uniqueness, `skills` name uniqueness per tenant, `resource_skills` duplicate `(resource_id, skill_id)` rejection and level range, cascade of `resource_skills` when a resource is purged, restrict when a skill still has rows, exclusion constraints, planned check, snapshot pairing check, range check, foreign keys, rollback ordering
- [ ] Persistence tests: `crates/persistence/src/resources/` repositories are the only writers of the six tables; `cargo xtask check-persistence` finds no SQL in `crates/domain/src/resources/`, `services/api/src/resources/`, or `testing/features/F033/`
- [ ] React component tests: `CapacityStrip`, `PlannerGrid`, `AllocationDialog`, `AvailabilityEditor` states
- [ ] Browser E2E tests: create resource, add leave, allocate, see over-allocation, viewer without costs
- [ ] Accessibility tests: axe on directory, profile, planner; keyboard planner navigation; meter semantics
- [ ] Performance/load tests: 52-week capacity with 200 allocations, 5,000-resource list, allocation create p95

### Fast fanout configuration

- Test harness path: `testing/features/F033/`
- Feature flag: `F033_FEATURE`
- Fixture/seed factory: `testing/fixtures/resources.rs` builds tenant, workspace, resource-admin, resource-viewer, a linked user, foreign tenant, an F011 calendar (Mon–Fri 8 h with a holiday on `2026-10-12`), two resources (FTE 1.0 and 0.5), skills, a leave week, cost rates, and a project sheet with rows; every fixture row is written through the `crates/persistence/src/resources/` repositories, never by raw SQL
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, UTC calendar
- Mock/stub contracts: outbox publisher recorded in memory; F011 calendar service real against fixture; authz uses the real F003 engine
- Parallel isolation: one schema per test worker, tenant ID per test
- Targeted command: `cargo xtask test-feature F033`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F033/`

## 6. Acceptance criteria

```gherkin
Feature: Resources and capacity

Scenario: Capacity subtracts leave, holiday, and part-time availability
  Given resource "Ana" with FTE 0.5 on a Mon-Fri 8h calendar with a holiday on 2026-10-12
  And leave from 2026-10-05 to 2026-10-09
  When capacity is requested for 2026-10-05 to 2026-10-18 by week
  Then week 1 has fte_hours 20, leave_hours 20, available_hours 0
  And week 2 has calendar_hours 32, fte_hours 16, holiday_hours 4, available_hours 16

Scenario: Allocation flags over-allocation immediately
  Given "Ana" has available_hours 16 in the week of 2026-10-12
  When an administrator allocates 20 planned_hours to project "Rollout" for that week
  Then the response lists that week in over_allocated_periods
  And allocation.created.v1 and capacity.computed.v1 are in the outbox

Scenario: Hours and percent are mutually exclusive
  When an administrator posts an allocation with planned_hours 8 and planned_percent 50
  Then the response is 400 invalid with field_errors.planned

Scenario: Viewer cannot see costs or mutate
  Given a resource-viewer
  When they read "Ana" and then POST an allocation
  Then the profile omits cost_rates and the POST returns 403 denied

Scenario: Cross-tenant read does not leak
  Given a resource in tenant A
  When an administrator from tenant B requests it by id
  Then the response is 404 not_found
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F011 (working calendars and exceptions), F002 (users for `user_id` links); decisions sections 2–4; contracts row F033
- Blocks: F034
- Conflicts with: none (disjoint owned paths)
- External dependencies: PostgreSQL `btree_gist` extension for exclusion constraints
- Risks and mitigations: capacity over long ranges with many allocations can be slow, so periods are computed from a precomputed working-day table per calendar and allocations are fetched with the gist range index; percent allocations depend on available hours that change with leave, so the mutation response recomputes and returns affected periods; cost visibility errors would leak pay data, so the field filter is applied in the DTO layer and tested for every route.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F011 and F002 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F033/`
- [ ] Migration file name and owned paths claimed; `btree_gist` available on CI PostgreSQL 18
- [ ] Fixture factory with calendar, holiday, and leave available in `testing/fixtures/resources.rs`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for every mutation
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F033_FEATURE`, run down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Administrators can maintain resource profiles with skills, availability, and cost rates, allocate resources to projects by period in hours or percent with role and confidence, and see capacity that accounts for calendars, leave, holidays, and part-time availability with immediate over-allocation flags.
- Migration adds `resources`, `skills`, `resource_skills`, `resource_availability`, `cost_rates`, and `allocations`; rollback drops them children first. Feature is off by default behind `F033_FEATURE`.
