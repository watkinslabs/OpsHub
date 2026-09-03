---
id: T129
type: task
status: planned
parent_epic: E007
parent_feature: F033
parent_story: S065
depends_on: [S065]
owned_paths: [services/api/migrations/*_resources_*.sql, crates/domain/src/resources/**, services/api/src/resources/**, testing/features/F033/database/**, testing/features/F033/api/**]
feature_flag: F033_FEATURE
branch: t129-resource-schema
started_at: null
finished_at: null
---

# T129 — Resource schema

## Identity

- Parent story: `S065` Resource profiles
- Owner: platform
- Branch: `t129-resource-schema`
- Decision references: `docs/architecture-decisions.md` sections 2–4; `docs/capability-contracts.md` row F033

## Objective

Create the five resource tables with exclusion constraints and rollback, and implement the resource profile service with the create, list, patch, skills, and availability routes.

## Specification

- Owned paths: `services/api/migrations/<ts>_resources_create_tables.sql`, `services/api/migrations/<ts>_resources_create_tables.down.sql`, `crates/domain/src/resources/{mod.rs, schema.rs, resource.rs, skills.rs, availability.rs, cost_rates.rs, errors.rs, service_resources.rs}`, `services/api/src/resources/{mod.rs, routes.rs, handlers_resource.rs, dto.rs, scope.rs}`
- Contract/input: DDL per F033 ticket section 4 PostgreSQL: `create extension if not exists btree_gist`; `resources`, `resource_skills`, `resource_availability`, `cost_rates`, `allocations` with tenant/UUIDv7/version/audit/soft-delete columns, unique active `user_id` partial index, `fte` and `level` checks, gist exclusion constraints on availability and cost-rate ranges, planned hours/percent exclusive check, 366-day range check, foreign keys with `on delete restrict`; `CreateResourceRequest`, `UpdateResourceRequest { display_name?, role_title?, working_calendar_id?, fte?, timezone?, status?, cost_rates?, end_allocations? }`, `ReplaceSkillsRequest { skills }`, `ReplaceAvailabilityRequest { entries }`; headers `Idempotency-Key`, `If-Match`.
- Output/behavior: `sqlx migrate run` applies after F002, F006, and F011 migrations; `revert` drops the five tables; routes `GET/POST /api/v1/resources`, `PATCH /api/v1/resources/{id}`, `PUT /api/v1/resources/{id}/skills`, `PUT /api/v1/resources/{id}/availability` return `ResourceResponse` with `skills`, `availability`, and `cost_rates` (the last only through `scope.rs` for `resource-admin`); duplicate active user link → 409; overlapping availability or cost rate → 400 with indexed field errors; deactivation with future allocations → 409 unless `end_allocations`; every mutation writes audit and `resource.updated.v1`; errors map per ticket section 4.
- Dependencies: F002 `users` for `user_id` validation; F011 `working_calendars`; F003 `authz::require(actor, Permission::ResourceAdmin, workspace)`; F004 outbox writer.
- Feature flag: `F033_FEATURE` gates router mounting; migration runs regardless.
- Large-table note: no existing data; `allocations` is expected to reach millions of rows, so the gist range index is created in this migration.

## TDD

- Failing test first: `testing/features/F033/database/migration_tests.rs::resource_tables_exist_with_constraints`, `::duplicate_active_user_link_rejected`, `::availability_overlap_rejected_by_exclusion`, `::cost_rate_overlap_rejected_by_exclusion`, `::allocation_planned_check_and_range_check`, `::rollback_drops_tables`; `testing/features/F033/api/resource_tests.rs::resource_create_returns_version_one`, `::resource_duplicate_user_link_conflicts`, `::resource_list_filters_by_skill_and_availability`, `::skills_replace_rejects_duplicates`, `::availability_overlap_invalid`, `::deactivate_with_future_allocations_conflicts`, `::viewer_response_omits_cost_rates`, `::resource_cross_tenant_not_found`
- Targeted command: `cargo xtask test-feature F033`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: schema-per-worker database from `testing/harness/db.rs`; `testing/fixtures/resources.rs`; in-memory outbox recorder

## Exit criteria

- [ ] Tests written before the migration and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; router mounted behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S065
- [ ] `finished_at` recorded
