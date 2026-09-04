---
id: T201
type: task
status: planned
parent_epic: E008
parent_feature: F051
parent_story: S101
depends_on: [S101]
owned_paths: [services/api/migrations/*_workapps_*.sql, crates/domain/src/workapps/**, crates/persistence/src/workapps/**, services/api/src/workapps/**, testing/features/F051/database/**, testing/features/F051/api/**]
feature_flag: F051_FEATURE
branch: t201-app-manifest
started_at: null
finished_at: null
---

# T201 — App manifest

## Identity

- Parent story: `S101` App composition
- Owner: platform
- Branch: `t201-app-manifest`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4; `docs/capability-contracts.md` row F051

## Objective

Create the WorkApps schema, the manifest domain model with slug, page, and role validation, and the app, pages, and roles routes so a draft app can be composed and read.

## Specification

- Owned paths: `services/api/migrations/<ts>_workapps_create_tables.sql`, `services/api/migrations/<ts>_workapps_create_tables.down.sql`, `crates/domain/src/workapps/{mod.rs, app.rs, slug.rs, page.rs, role.rs, manifest.rs, validate.rs, errors.rs, service.rs, schema.rs}`, `services/api/src/workapps/{mod.rs, routes.rs, handlers_app.rs, handlers_pages.rs, handlers_roles.rs, dto.rs}`
- Contract/input: DDL per F051 ticket section 4 (four tables, slug/position/name/version uniqueness, text-or-source check, deferred published-version foreign key, indexes); `CreateWorkAppRequest { name, slug, workspace_id, icon?, description? }`, `UpdateWorkAppRequest { name?, icon?, description?, status? }`, `SetPagesRequest { pages[] }`, `SetRolesRequest { roles[] }`, list query `{ cursor?, limit?, status?, name_prefix? }`; headers `Idempotency-Key`, `If-Match`.
- Output/behavior: routes `GET /api/v1/workapps`, `POST /api/v1/workapps`, `GET /api/v1/workapps/{id}`, `PATCH /api/v1/workapps/{id}`, `PUT /api/v1/workapps/{id}/pages`, `PUT /api/v1/workapps/{id}/roles`; `validate_manifest` enforces ≤ 50 pages, ≤ `max_pages_per_app`, 1–20 roles, role references, landing-page visibility, text-page rules, and unique positions with indexed `field_errors`; `max_apps` enforced from F048 limits; `WorkAppResponse` carries `draft_dirty`; audit rows and `workapp.updated.v1` written in the same transaction; errors map per ticket section 4.
- Dependencies: F005 `workspaces`; F002 `group_members` for member kinds; F048 `RequireModule(ModuleSlug::Workapps)` and `Evaluator::limits`; source existence checks arrive in T202 (this task validates shape and role references only and stubs `SourceResolver` to accept fixture IDs).
- Feature flag: `F051_FEATURE` gates router mounting; migration runs regardless.

## TDD

- Failing test first: `testing/features/F051/database/migration_tests.rs::workapp_tables_exist_with_constraints`, `::duplicate_slug_per_tenant_rejected`, `::duplicate_page_position_rejected`, `::text_page_requires_body_not_source`, `::rollback_drops_tables`; `testing/features/F051/api/app_tests.rs::app_create_rejects_duplicate_slug`, `::app_create_rejects_invalid_slug`, `::app_limit_reached_conflicts`, `::non_admin_mutation_denied`; `testing/features/F051/api/manifest_tests.rs::pages_reject_51st_page`, `::roles_reject_landing_page_not_visible`, `::roles_reject_duplicate_name`
- Targeted command: `cargo xtask test-feature F051`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/workapps.rs` app admin and member; schema-per-worker database; in-memory outbox recorder; accepting `SourceResolver` stub

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; router mounted in `services/api/src/router.rs` behind the flag and module guard; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S101
- [ ] `finished_at` recorded
