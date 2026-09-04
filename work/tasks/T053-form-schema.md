---
id: T053
type: task
status: planned
parent_epic: E003
parent_feature: F014
parent_story: S027
depends_on: [S027]
owned_paths: [services/api/migrations/*_forms_*.sql, crates/domain/src/forms/**, crates/persistence/src/forms/**, services/api/src/forms/**, testing/features/F014/database/**, testing/features/F014/api/**]
feature_flag: F014_FEATURE
branch: t053-form-schema
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4
- Capability contract: `docs/capability-contracts.md` row F014

# T053 — Form schema

## Identity

- Parent story: `S027` Form builder
- Owner: platform
- Branch: `t053-form-schema`
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4; `docs/capability-contracts.md` row F014

## Objective

Create the `forms`, `form_versions`, `form_version_frame_ancestors`, `form_version_upload_mime_types`, `form_fields`, `form_field_options`, and `form_submissions` tables with immutability and append-only triggers, implement `FormRepository`, `FormVersionRepository`, and `FormSubmissionRepository` in `crates/persistence/src/forms/`, and implement the form domain service and the six admin routes with publish, token rotate/revoke, audit, and outbox publication.

## Specification

- Owned paths: `services/api/migrations/<ts>_forms_create_tables.sql`, `services/api/migrations/<ts>_forms_create_tables.down.sql`, `crates/domain/src/forms/{mod.rs, schema.rs, form.rs, version.rs, field.rs, token.rs, errors.rs, service.rs}` (repository traits only, no SQL), `crates/persistence/src/forms/{mod.rs, form_repository.rs, form_version_repository.rs, form_submission_repository.rs}`, `services/api/src/forms/{mod.rs, routes.rs, handlers_form.rs, dto.rs}`
- Contract/input: DDL per F014 ticket section 4 PostgreSQL (seven tables, unique `(form_id, version_number)`, unique `(version_id, key)`, unique token hash, unique `(version_id, origin)`, unique `(version_id, mime_type)`, unique `(field_id, option_key)` and `(field_id, position)`, the accent-colour, upload-limit, schedule-window, and submitter-mode `check` constraints, trigger `form_versions_immutable`, trigger `form_submissions_append_only`, `form_fields.column_id` foreign key `on delete restrict`, child foreign keys `on delete cascade`); `CreateFormRequest { sheet_id, title, description?, branding? }`, `UpdateFormRequest { title?, description?, fields?, branding?, identity_mode?, spam?, uploads?, schedule?, confirmation?, frame_ancestors?, rotate_token?, revoke_token? }` keep their nested JSON shape and are decomposed into columns and child rows by `FormVersionRepository`; headers `Idempotency-Key`, `If-Match`.
- Data access: `FormRepository` owns `forms`; `FormVersionRepository` owns `form_versions`, `form_version_frame_ancestors`, `form_version_upload_mime_types`, `form_fields`, `form_field_options`; `FormSubmissionRepository` owns `form_submissions`. Each implements the shared `Repository` contract and adds `list_for_sheet`, `next_version_number(form_id)`, `publish_version(version_id)`, and `find_by_submission_token_hash(hash)`; publish runs in one `UnitOfWork`. No SQL string, `sqlx::query*` call, or connection appears in `crates/domain/src/forms` or `services/api/src/forms`.
- Output/behavior: `sqlx migrate run` applies on an empty database and on a database with F006 and F007 tables; `sqlx migrate revert` drops all seven tables and both triggers; routes `GET /api/v1/sheets/{sheet_id}/forms`, `POST /api/v1/forms`, `GET /api/v1/forms/{id}`, `PATCH /api/v1/forms/{id}`, `POST /api/v1/forms/{id}/publish`, `DELETE /api/v1/forms/{id}` return `FormResponse { id, sheet_id, workspace_id, title, description, status, current_version: FormVersionResponse, version, created_at, updated_at, deleted_at }`; publish generates a 32-byte URL-safe token, stores its SHA-256 hash, returns the plaintext once, and writes `form.published.v1`; a `PATCH` against a published version creates draft `n+1` and writes `form.updated.v1`; errors map per ticket section 4.
- Dependencies: F006 `sheets` and F007 `columns` tables for foreign keys; F003 `authz::require(actor, Permission::FormAdmin, sheet)`; F004 outbox writer.
- Feature flag: `F014_FEATURE` gates router mounting; migration runs regardless.
- Large-table note: no existing data; `form_submissions` is append-heavy, so future columns must be nullable and indexes partial.

## TDD

- Failing test first: `testing/features/F014/database/migration_tests.rs::forms_tables_exist_with_constraints`, `::published_version_update_rejected_by_trigger`, `::submission_status_transition_enforced`, `::child_table_unique_constraints_enforced`, `::version_children_cascade_on_delete`, `::rollback_drops_seven_tables_and_triggers`; `testing/features/F014/api/form_tests.rs::form_create_returns_draft_version_one`, `::branding_and_validation_round_trip_through_repository`, `::form_publish_freezes_version_and_emits_event`, `::form_patch_after_publish_creates_draft`, `::form_token_rotate_invalidates_old_token`, `::form_cross_tenant_not_found`, `::form_submitter_admin_routes_denied`
- Targeted command: `cargo xtask test-feature F014`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: schema-per-worker database from `testing/harness/db.rs`; `testing/fixtures/forms.rs` tenants A and B, form admin, submitter; in-memory outbox recorder

## Exit criteria

- [ ] Tests written before the migration and service and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; `cargo xtask check-migrations` and `check-persistence` pass
- [ ] Router mounted in `services/api/src/router.rs` behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S027
- [ ] `finished_at` recorded
