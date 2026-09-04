---
id: T049
type: task
status: planned
parent_epic: E003
parent_feature: F013
parent_story: S025
depends_on: [S025]
owned_paths: [services/api/migrations/*_views_*.sql, crates/domain/src/views/**, crates/persistence/src/views/**, services/api/src/views/**, testing/features/F013/database/**, testing/features/F013/api/**]
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

Create the `views`, `view_shares`, `view_sorts`, `view_columns`, `view_card_fields`, and `view_filter_columns` tables, the `ViewRepository` and `ViewShareRepository` that own them, the typed `ViewSettings` and `FilterNode` model with per-kind validation and filter compilation, and the five view CRUD routes with authorization, idempotency, optimistic concurrency, audit, and outbox publication.

## Specification

- Owned paths: `services/api/migrations/<ts>_views_create_tables.sql`, `services/api/migrations/<ts>_views_create_tables.down.sql`, `crates/domain/src/views/{mod.rs, view.rs, settings.rs, filter.rs, errors.rs, service.rs, schema.rs}` (repository traits only, no SQL), `crates/persistence/src/views/{mod.rs, view_repository.rs, view_share_repository.rs}`, `services/api/src/views/{mod.rs, routes.rs, handlers_view.rs, dto.rs}`
- Contract/input: DDL per F013 ticket section 4 (`views` with typed per-kind column references, `calendar_mode`, `timeline_zoom`, `filter jsonb`, `gantt_settings jsonb`; `view_shares`; the `view_sorts`, `view_columns`, `view_card_fields`, `view_filter_columns` projection tables; kind/visibility/principal/role and per-kind check constraints; `position` bound checks; default-per-sheet and owner-name partial unique indexes; b-tree `view_filter_columns(column_id)` in place of the former GIN index on `settings`); `CreateViewRequest { sheet_id, name, kind, visibility, is_default?, settings }`, `UpdateViewRequest { name?, visibility?, is_default?, settings? }`, list query `{ cursor?, limit?, kind?, sort? }`; headers `Idempotency-Key`, `If-Match`.
- Output/behavior: routes `GET /api/v1/sheets/{sheet_id}/views`, `POST /api/v1/views`, `GET /api/v1/views/{id}`, `PATCH /api/v1/views/{id}`, `DELETE /api/v1/views/{id}` return `ViewResponse { id, sheet_id, owner_id, name, kind, visibility, is_default, settings, version, created_at, updated_at, deleted_at }`; the `settings` object on the wire is unchanged and `ViewRepository` composes and decomposes it across the typed columns and projection tables; `validate_settings` enforces the select lane column, date column pairs, and ≤ 50 filter leaves, while ≤ 5 sorts, ≤ 8 card fields, and the per-kind required columns are database check constraints, and ≤ 100 views per sheet is checked in the create path; `compile_filter` turns the AST into a filter specification the persistence layer parameterizes by column type; `replace_projection` rewrites the sort, column, card-field, and filter-column rows and `clear_default` clears the previous default, both inside the same `UnitOfWork` as the `views` write; deleting the default returns `invalid`; events `view.created.v1`, `view.updated.v1`, `view.deleted.v1` written to `outbox_events` in the same transaction; `sqlx migrate revert` drops all six tables.
- Dependencies: F006 `sheets` and F007 `columns` tables for foreign keys and column types; F003 `authz::require(actor, Permission::SheetView, sheet)`; F004 outbox writer.
- Feature flag: `F013_FEATURE` gates router mounting; migration runs regardless.
- Large-table note: no existing data; later settings members are additive — a new scalar is a nullable typed column, a new repeated member is a new projection table, and the DTO tolerates absence with `serde(default)`.

## TDD

- Failing test first: `testing/features/F013/database/migration_tests.rs::views_tables_exist_with_constraints`, `::second_default_view_rejected`, `::share_check_constraints_enforced`, `::per_kind_check_constraints_enforced`, `::sort_position_bounded_to_five`, `::card_field_position_bounded_to_eight`, `::filter_column_fk_blocks_column_delete`, `::rollback_drops_tables`; `testing/features/F013/api/view_tests.rs::view_create_returns_version_one`, `::view_filter_rejects_type_mismatch`, `::view_filter_rejects_51_leaves`, `::view_limit_100_per_sheet`, `::view_default_delete_invalid`, `::view_settings_roundtrip_through_projection_tables`, `::view_stale_version_conflicts`, `::view_cross_tenant_not_found`
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
