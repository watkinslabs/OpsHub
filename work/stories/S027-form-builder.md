---
id: S027
type: story
status: planned
parent_epic: E003
parent_feature: F014
depends_on: [F007]
owned_paths: [crates/domain/src/forms/**, crates/persistence/src/forms/**, services/api/src/forms/**, apps/web/src/features/forms/**, services/api/migrations/*_forms_*.sql, testing/features/F014/**]
feature_flag: F014_FEATURE
branch: s027-form-builder
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 6
- Capability contract: `docs/capability-contracts.md` row F014

# S027 — Form builder

## Identity

- Parent feature: `F014` Forms
- Owner: platform
- Branch: `s027-form-builder`
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 6; `docs/capability-contracts.md` row F014

## Vertical slice

As a form admin, I want to create a form over a sheet's typed columns, configure fields with validation and conditional display, brand it, and publish an immutable version, so that a safe, versioned intake definition exists before any public submission is accepted.

## Requirements

- **SR-S027-01:** `POST /api/v1/forms` with `{ sheet_id, title, description?, branding? }` creates `forms` and draft `form_versions` version 1 through `FormRepository` and `FormVersionRepository` in one `UnitOfWork`, writing `branding` to the typed columns `branding_logo_file_id`, `branding_accent_color`, `branding_title`, `branding_description`, and returns `FormResponse` with `status: draft` and the branding object recomposed by the repository (covers FR-F014-01).
- **SR-S027-02:** `PATCH /api/v1/forms/{id}` with `fields[]` validates every `column_id` against the sheet, enforces unique `key` per version, stores `validation.regex|min|max` as `form_fields.validation_regex|validation_min|validation_max`, stores `options_subset` as ordered `form_field_options` rows unique per `(field_id, option_key)` and per `(field_id, position)`, and keeps `show_if` as the AST payload; a foreign column returns `400 invalid` with `field_errors.fields[n].column_id` (FR-F014-02, FR-F014-03).
- **SR-S027-03:** `crates/domain/src/forms/conditions.rs` evaluates the `show_if` AST (`eq`, `ne`, `gt`, `lt`, `contains`, `is_empty`, `and`, `or`, depth ≤ 4) and marks hidden fields as not required; the JSON fixture set is shared with the browser evaluator (FR-F014-03).
- **SR-S027-04:** `POST /api/v1/forms/{id}/publish` calls `FormVersionRepository::publish_version`, which freezes the draft, sets `published_at`, generates a 32-byte token stored as a hash, and sets `forms.current_version_id` in one `UnitOfWork`, and emits `form.published.v1`; a later `PATCH` uses `next_version_number(form_id)` to create draft version `n+1`, copying the version's frame-ancestor, MIME-allowlist, field, and field-option rows, and emits `form.updated.v1` (FR-F014-04, FR-F014-05).
- **SR-S027-05:** `PATCH` with `rotate_token` or `revoke_token` replaces or clears the hash on the current version and writes an audit event; `FormRepository::list_for_sheet` backs `GET /api/v1/sheets/{sheet_id}/forms`, listing forms with status and current `version_number` (FR-F014-05, FR-F014-17).
- **SR-S027-06:** Every mutation checks `Idempotency-Key` and `If-Match`, writes an audit event, and enqueues the outbox event; a `form-submitter` on admin routes receives `403 denied`; a foreign tenant receives `404 not_found` (FR-F014-18).
- **SR-S027-07:** `FormBuilderPage` with `FieldPalette`, `FieldEditor`, `ConditionEditor`, `FormPreview`, and `PublishDialog` renders loading, empty, error, denied, stale, and success states and updates the preview as conditions change (FR-F014-01, FR-F014-03, NFR-F014-03).

## Surfaces

- Infrastructure/container: none beyond F004 baseline
- Rust service/API: `crates/domain/src/forms/{form.rs, version.rs, field.rs, conditions.rs, token.rs, errors.rs, service.rs}` (repository traits only, no SQL); `crates/persistence/src/forms/{mod.rs, form_repository.rs, form_version_repository.rs}` holding every SQL statement for `forms`, `form_versions`, `form_version_frame_ancestors`, `form_version_upload_mime_types`, `form_fields`, and `form_field_options`; `services/api/src/forms/{routes.rs, handlers_form.rs, dto.rs}`
- Data/migration: `services/api/migrations/<ts>_forms_create_tables.sql` creating `forms`, `form_versions`, `form_version_frame_ancestors`, `form_version_upload_mime_types`, `form_fields`, `form_field_options`, and `form_submissions` with the immutability and append-only triggers from ticket section 4
- React/UI: `apps/web/src/features/forms/{FormBuilderPage.tsx, FieldPalette.tsx, FieldEditor.tsx, ConditionEditor.tsx, FormPreview.tsx, PublishDialog.tsx, ShareDialog.tsx, conditions.ts, api.ts, hooks.ts, routes.ts}`
- Mocks/fixtures: `testing/fixtures/forms.rs` tenant, 12-column sheet, form admin, submitter, foreign tenant; `testing/fixtures/forms/conditions.json` shared evaluator cases; MSW handlers for component tests

## TDD harness

- Test path: `testing/features/F014/{api,database,frontend,accessibility}/`
- Feature flag: `F014_FEATURE`
- Targeted command: `cargo xtask test-feature F014`
- Full command: `cargo xtask test-all`
- First failing tests: `form_create_returns_draft_version_one`, `form_field_foreign_column_invalid`, `condition_hidden_field_not_required`, `form_publish_freezes_version_and_emits_event`, `form_patch_after_publish_creates_draft`, `form_field_options_round_trip_through_repository`, `form_submitter_admin_routes_denied`

## Exit criteria

- [ ] Requirement tests SR-S027-01 through SR-S027-07 written first and failing
- [ ] Tasks T053 and T054 complete and wired through `services/api` router
- [ ] Unit, API, database, React, accessibility, and permission tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/forms/routes.rs` mounted in `services/api/src/router.rs`; `apps/web/src/features/forms/FormBuilderPage.tsx` mounted at `/w/:workspaceId/forms/:formId`
- [ ] Handoff evidence recorded in the F014 ticket
