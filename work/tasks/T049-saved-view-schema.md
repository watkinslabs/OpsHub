---
id: T049
type: task
status: planned
parent_epic: E003
parent_feature: F013
parent_story: S025
depends_on: [S025]
owned_paths: [services/api/migrations/*_views_*.sql, crates/domain/src/views/**, services/api/src/views/**, testing/features/F013/database/**, testing/features/F013/api/**]
feature_flag: F013_FEATURE
branch: t049-saved-view-schema
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4
- Capability contract: `docs/capability-contracts.md` row F013

# T049 — Saved-view schema

## Identity

- Parent story: `S025` Card/calendar
- Owner: platform
- Branch: `t049-saved-view-schema`
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4; `docs/capability-contracts.md` row F013

## Objective

Create the `views` and `view_shares` tables, the typed `ViewSettings` and `FilterNode` model with per-kind validation and filter compilation, and the five view CRUD routes with authorization, idempotency, optimistic concurrency, audit, and outbox publication.

## Specification

- Owned paths: `services/api/migrations/<ts>_views_create_tables.sql`, `services/api/migrations/<ts>_views_create_tables.down.sql`, `crates/domain/src/views/{mod.rs, view.rs, settings.rs, filter.rs, errors.rs, service.rs, schema.rs}`, `services/api/src/views/{mod.rs, routes.rs, handlers_view.rs, dto.rs}`
- Contract/input: DDL per F013 ticket section 4 (two tables, kind/visibility/principal/role checks, default-per-sheet and owner-name partial unique indexes, token hash unique index, GIN on `settings`); `CreateViewRequest { sheet_id, name, kind, visibility, is_default?, settings }`, `UpdateViewRequest { name?, visibility?, is_default?, settings? }`, list query `{ cursor?, limit?, kind?, sort? }`; headers `Idempotency-Key`, `If-Match`.
- Output/behavior: routes `GET /api/v1/sheets/{sheet_id}/views`, `POST /api/v1/views`, `GET /api/v1/views/{id}`, `PATCH /api/v1/views/{id}`, `DELETE /api/v1/views/{id}` return `ViewResponse { id, sheet_id, owner_id, name, kind, visibility, is_default, settings, version, created_at, updated_at, deleted_at }`; `validate_settings` enforces select lane column, date column pairs, ≤ 50 filter leaves, ≤ 5 sorts, ≤ 8 card fields, ≤ 100 views per sheet; `compile_filter` turns the AST into a parameterized SQLx predicate keyed by column type; setting `is_default` clears the previous default; deleting the default returns `invalid`; events `view.created.v1`, `view.updated.v1`, `view.deleted.v1` written to `outbox_events` in the same transaction; `sqlx migrate revert` drops both tables.
- Dependencies: F006 `sheets` and F007 `columns` tables for foreign keys and column types; F003 `authz::require(actor, Permission::SheetView, sheet)`; F004 outbox writer.
- Feature flag: `F013_FEATURE` gates router mounting; migration runs regardless.
- Large-table note: no existing data; later settings keys must be additive and tolerated by `serde(default)`.

## TDD

- Failing test first: `testing/features/F013/database/migration_tests.rs::views_tables_exist_with_constraints`, `::second_default_view_rejected`, `::share_check_constraints_enforced`, `::rollback_drops_tables`; `testing/features/F013/api/view_tests.rs::view_create_returns_version_one`, `::view_filter_rejects_type_mismatch`, `::view_filter_rejects_51_leaves`, `::view_limit_100_per_sheet`, `::view_default_delete_invalid`, `::view_stale_version_conflicts`, `::view_cross_tenant_not_found`
- Targeted command: `cargo xtask test-feature F013`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: schema-per-worker database from `testing/harness/db.rs`; `testing/fixtures/views.rs` tenants A and B, owner, editor, viewer; in-memory outbox recorder

## Exit criteria

- [ ] Tests written before the migration and services and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18
- [ ] Router mounted in `services/api/src/router.rs` behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S025
- [ ] `finished_at` recorded
