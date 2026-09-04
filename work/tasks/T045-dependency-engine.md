---
id: T045
type: task
status: planned
parent_epic: E003
parent_feature: F012
parent_story: S023
depends_on: [S023]
owned_paths: [services/api/migrations/*_dependencies_*.sql, crates/domain/src/dependencies/**, crates/persistence/src/dependencies/**, services/api/src/dependencies/**, testing/features/F012/database/**, testing/features/F012/api/**]
feature_flag: F012_FEATURE
branch: t045-dependency-engine
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4
- Capability contract: `docs/capability-contracts.md` row F012

# T045 — Dependency engine

## Identity

- Parent story: `S023` Dependency links
- Owner: platform
- Branch: `t045-dependency-engine`
- Decision references: `docs/architecture-decisions.md` sections 2–4; `docs/capability-contracts.md` row F012

## Objective

Create the `row_dependencies` and `schedule_results` schema and implement the dependency domain service with the four CRUD routes, typed link kinds, signed lag validation, duplicate and limit rules, authorization, idempotency, audit, and outbox events.

## Specification

- Owned paths: `services/api/migrations/<ts>_dependencies_create_tables.sql`, `services/api/migrations/<ts>_dependencies_create_tables.down.sql`, `crates/domain/src/dependencies/{mod.rs, dependency.rs, errors.rs, service.rs, schema.rs}` (repository traits only, no SQL), `crates/persistence/src/dependencies/{mod.rs, row_dependency_repository.rs, schedule_result_repository.rs}`, `services/api/src/dependencies/{mod.rs, routes.rs, handlers_dependency.rs, dto.rs}`
- Contract/input: DDL per F012 ticket section 4 (`row_dependencies` with kind and lag checks, pair unique index, side indexes; `schedule_results` keyed by `(sheet_id, row_id)`); `CreateDependencyRequest { predecessor_row_id, successor_row_id, kind, lag?, lag_unit? }`, `UpdateDependencyRequest { kind?, lag?, lag_unit? }`, list query `{ cursor?, limit? ≤ 1000, row_id?, kind? }`; headers `Idempotency-Key`, `If-Match`.
- Output/behavior: routes `GET /api/v1/sheets/{sheet_id}/dependencies`, `POST /api/v1/dependencies`, `PATCH /api/v1/dependencies/{id}`, `DELETE /api/v1/dependencies/{id}` return `DependencyResponse { id, sheet_id, predecessor_row_id, successor_row_id, kind, lag, lag_unit, version, created_at, updated_at }`; self, cross-sheet, parent-row, and lag-range errors map to `400 invalid`; duplicate pair to `409 conflict` with `existing_id`; 20,001st link to `400 invalid` `field_errors.sheet_id = "limit"`; `RowDependencyRepository` exposes `list_for_sheet`, `find_pair`, `load_graph_for_sheet`, and `delete_for_sheet`, and `ScheduleResultRepository` exposes `upsert_schedule_results` and `list_critical`; events `dependency.created.v1`, `dependency.updated.v1`, `dependency.deleted.v1` are enqueued to `outbox_events` by the base `Repository` contract in the same `UnitOfWork`; `sqlx migrate run` and `revert` apply cleanly; the cycle hook from T046 is called through a trait `CycleChecker` that this task stubs as always-pass.
- Dependencies: F006 `rows` and `sheets` tables; F009 `row_hierarchy` for the parent-row check; F011 `SheetScheduleSettingsRepository::lock_for_schedule(sheet_id)` taking the `sheet_schedule_settings` row lock as the per-sheet serializer; F003 `authz::require(actor, Permission::ProjectEdit, sheet)`; F004 outbox writer.
- Feature flag: `F012_FEATURE` gates router mounting; migration runs regardless.
- Large-table note: no existing data; future columns must be additive and nullable.

## TDD

- Failing test first: `testing/features/F012/database/migration_tests.rs::dependency_tables_exist_with_constraints`, `::duplicate_pair_rejected_by_index`, `::invalid_kind_rejected`, `::rollback_drops_tables`; `testing/features/F012/api/dependency_tests.rs::dependency_create_returns_version_one`, `::dependency_self_link_invalid`, `::dependency_cross_sheet_invalid`, `::dependency_parent_row_invalid`, `::dependency_duplicate_pair_conflicts`, `::dependency_sheet_limit_invalid`, `::dependency_list_filters_by_row_and_kind`, `::dependency_cross_tenant_not_found`, `::dependency_viewer_mutation_denied`
- Targeted command: `cargo xtask test-feature F012`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/dependencies.rs` tenants A and B, editor, viewer, seeded sheet; schema-per-worker database from `testing/harness/db.rs`; in-memory outbox recorder

## Exit criteria

- [ ] Tests written before the migration and service and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18
- [ ] Router mounted in `services/api/src/router.rs` behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S023
- [ ] `finished_at` recorded
