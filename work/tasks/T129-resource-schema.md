---
id: T129
type: task
status: planned
parent_epic: E007
parent_feature: F033
parent_story: S065
depends_on: [S065]
owned_paths: [services/api/migrations/*_resources_*.sql, crates/domain/src/resources/**, crates/persistence/src/resources/**, services/api/src/resources/**, testing/features/F033/database/**, testing/features/F033/api/**]
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
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4; `docs/capability-contracts.md` row F033

## Objective

Create the six resource tables with their foreign keys, enum checks, and exclusion constraints, implement their repositories in `crates/persistence/src/resources/`, and implement the resource profile service with the create, list, patch, skills, and availability routes.

## Specification

- Owned paths: `services/api/migrations/<ts>_resources_create_tables.sql`, `services/api/migrations/<ts>_resources_create_tables.down.sql`, `crates/domain/src/resources/{mod.rs, schema.rs, resource.rs, skills.rs, availability.rs, cost_rates.rs, errors.rs, service_resources.rs}`, `crates/persistence/src/resources/{mod.rs, resource_repository.rs, skill_repository.rs, availability_repository.rs, cost_rate_repository.rs, allocation_repository.rs}`, `services/api/src/resources/{mod.rs, routes.rs, handlers_resource.rs, dto.rs, scope.rs}`
- Contract/input: DDL per F033 ticket section 4 PostgreSQL: `create extension if not exists btree_gist`; `resources`, `skills`, `resource_skills`, `resource_availability`, `cost_rates`, `allocations` with tenant/UUIDv7/version/audit/soft-delete columns, unique active `user_id` partial index, `skills` unique on `(tenant_id, lower(name))`, `resource_skills(resource_id, skill_id, level)` with primary key `(resource_id, skill_id)`, `fte` and `level` checks, `check (kind in ('person','placeholder'))`, `check (status in ('active','inactive'))`, `check (kind in ('leave','holiday','reduced'))` on availability, `check (confidence in ('committed','likely','tentative'))`, typed allocation snapshot columns `cost_rate_id`/`snapshot_hourly_rate`/`snapshot_currency`/`snapshot_effective_from` with `check ((cost_rate_id is null) = (snapshot_hourly_rate is null))` in place of the former `cost_rate_snapshot jsonb`, gist exclusion constraints on availability and cost-rate ranges, planned hours/percent exclusive check, 366-day range check, and declared foreign keys with `on delete cascade` from `resource_skills`, `resource_availability`, and `cost_rates` to `resources` and `on delete restrict` everywhere else; `CreateResourceRequest`, `UpdateResourceRequest { display_name?, role_title?, working_calendar_id?, fte?, timezone?, status?, cost_rates?, end_allocations? }`, `ReplaceSkillsRequest { skills }`, `ReplaceAvailabilityRequest { entries }`; headers `Idempotency-Key`, `If-Match`.
- Output/behavior: `sqlx migrate run` applies after F002, F006, and F011 migrations; `revert` drops the six tables children first (`allocations`, `resource_skills`, `resource_availability`, `cost_rates`, then `skills` and `resources`); routes `GET/POST /api/v1/resources`, `PATCH /api/v1/resources/{id}`, `PUT /api/v1/resources/{id}/skills`, `PUT /api/v1/resources/{id}/availability` return `ResourceResponse` with `skills`, `availability`, and `cost_rates` (the last only through `scope.rs` for `resource-admin`); duplicate active user link → 409; overlapping availability or cost rate → 400 with indexed field errors; deactivation with future allocations → 409 unless `end_allocations`; every mutation writes audit and `resource.updated.v1`; errors map per ticket section 4.
- Data access: the migration is the only raw SQL file in this task; `resource.rs`, `skills.rs`, `availability.rs`, `cost_rates.rs`, `service_resources.rs`, and the handlers hold no SQL and reach every table through `ResourceRepository` (`resources`, `resource_skills`), `SkillRepository` (`skills`), `AvailabilityRepository` (`resource_availability`), `CostRateRepository` (`cost_rates`), and `AllocationRepository` (`allocations`); a profile save resolves skill names with `SkillRepository::find_or_create_by_name` and replaces the `resource_skills` and `cost_rates` rows inside one `UnitOfWork` transaction (decision section 2.1)
- Dependencies: F002 `users` for `user_id` validation; F011 `working_calendars`; F003 `authz::require(actor, Permission::ResourceAdmin, workspace)`; F004 outbox writer.
- Feature flag: `F033_FEATURE` gates router mounting; migration runs regardless.
- Large-table note: no existing data; `skills` stays small and is read through `SkillRepository::resolve_names` in one round trip per request; `allocations` is expected to reach millions of rows, so the gist range index is created in this migration.

## TDD

- Failing test first: `testing/features/F033/database/migration_tests.rs::resource_tables_exist_with_constraints`, `::duplicate_active_user_link_rejected`, `::availability_overlap_rejected_by_exclusion`, `::skill_name_unique_per_tenant`, `::resource_skills_rejects_duplicate_skill_id`, `::resource_skills_cascade_on_resource_purge`, `::skill_delete_restricted_while_referenced`, `::allocation_snapshot_columns_pair_or_are_both_null`, `::cost_rate_overlap_rejected_by_exclusion`, `::allocation_planned_check_and_range_check`, `::rollback_drops_tables`; `testing/features/F033/api/resource_tests.rs::resource_create_returns_version_one`, `::resource_duplicate_user_link_conflicts`, `::resource_list_filters_by_skill_and_availability`, `::skills_replace_rejects_duplicates`, `::availability_overlap_invalid`, `::deactivate_with_future_allocations_conflicts`, `::viewer_response_omits_cost_rates`, `::resource_cross_tenant_not_found`
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
