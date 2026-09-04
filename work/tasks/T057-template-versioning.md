---
id: T057
type: task
status: planned
parent_epic: E003
parent_feature: F015
parent_story: S029
depends_on: [S029]
owned_paths: [crates/domain/src/templates/**, crates/persistence/src/templates/**, services/api/src/templates/**, services/api/migrations/*_templates_*.sql, testing/features/F015/api/**, testing/features/F015/database/**, testing/features/F015/requirements/**]
feature_flag: F015_FEATURE
branch: t057-template-versioning
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4
- Capability contract: `docs/capability-contracts.md` row F015

# T057 — Template versioning

## Identity

- Parent story: `S029` Project template
- Owner: platform
- Branch: `t057-template-versioning`
- Decision references: `docs/architecture-decisions.md` sections 2–4; `docs/capability-contracts.md` row F015

## Objective

Create the ten template tables with the built-in catalog seed, and implement template CRUD, manifest validation, and immutable draft-to-published versioning behind the four template routes.

## Specification

- Owned paths: `services/api/migrations/<ts>_templates_create_tables.sql`, `services/api/migrations/<ts>_templates_create_tables.down.sql`, `crates/domain/src/templates/{mod.rs, template.rs, version.rs, manifest.rs, errors.rs, schema.rs, service_template.rs, builtin/{pmo,it,incidents,onboarding,change,vendors,marketing,crm,budget,compliance}.json}`, `crates/persistence/src/templates/{mod.rs, project_template_repository.rs, template_version_repository.rs}`, `services/api/src/templates/{mod.rs, routes.rs, handlers_template.rs, dto.rs}`
- Contract/input: `CreateTemplateRequest { name, category, description?, tags?, copy_from? }`, `CreateVersionRequest { manifest?, action: draft|publish, version_id? }`, list query `{ cursor?, limit? ≤ 100, category?, include_builtin? }`; headers `Idempotency-Key`, `If-Match`.
- Output/behavior: routes `GET /api/v1/project-templates`, `POST /api/v1/project-templates`, `GET /api/v1/project-templates/{id}`, `POST /api/v1/project-templates/{id}/versions` return `TemplateResponse { id, name, category, description, tags, is_builtin, current_version, versions: [VersionResponse], version }` where `tags` are `project_template_tags` rows (≤ 10 enforced by the service, unique per template on `lower(tag)`) and the catalog `tag` filter reads the same table; `ProjectTemplateRepository` (owning `project_templates` and `project_template_tags`, named query `list_with_builtins`) and `TemplateVersionRepository` (owning `template_versions`, named queries `next_version_number` and `publish_version`) hold all SQL, and the handlers and domain services call them; `validate_manifest` enforces key uniqueness, dependency references, F007 column types, and the FR-F015-03 limits with `field_errors.manifest.<path>` in memory, since `manifest` is a payload the database never queries; publish sets `published_at`, updates `current_version_id`, and emits `template.published.v1`; DDL per ticket section 4 including the `template_versions_immutable` trigger, unique indexes, `manifest_bytes <= 2097152` check, the measure and step `check` constraints, and the seed of ten built-ins with their tag rows under the reserved tenant; `sqlx migrate revert` drops the ten tables and the trigger.
- Dependencies: F006 `sheets` table for the baseline foreign key; F007 column type enum; F003 `authz::require(actor, Permission::TemplateManage, tenant)`; F004 outbox writer.
- Feature flag: `F015_FEATURE` gates router mounting; migration runs regardless.
- Large-table note: no existing data; seed rows are idempotent by fixed built-in IDs.

## TDD

- Failing test first: `testing/features/F015/database/migration_tests.rs::template_tables_exist_with_constraints`, `::published_version_update_raises`, `::builtin_seed_has_ten_published_templates`, `::rollback_drops_tables_and_trigger`, `::template_tag_is_unique_per_template`; `testing/features/F015/api/template_tests.rs::template_create_and_copy_builtin`, `::template_duplicate_name_conflicts`, `::version_publish_is_immutable`, `::manifest_rejects_dangling_key`, `::manifest_rejects_over_limits`, `::builtin_mutation_denied`, `::template_cross_tenant_not_found`; `testing/features/F015/api/manifest_tests.rs::builtin_seed_validates`
- Targeted command: `cargo xtask test-feature F015`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: schema-per-worker database from `testing/harness/db.rs`; `testing/fixtures/templates.rs` manifests; in-memory outbox recorder

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; router mounted in `services/api/src/router.rs`; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit, lint, and `cargo xtask check-persistence` gates pass
- [ ] Handoff evidence recorded in S029
- [ ] `finished_at` recorded
