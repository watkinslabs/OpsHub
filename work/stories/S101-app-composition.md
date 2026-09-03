---
id: S101
type: story
status: planned
parent_epic: E008
parent_feature: F051
depends_on: [F013, F014, F023, F048]
owned_paths: [crates/domain/src/workapps/**, services/api/src/workapps/**, services/api/migrations/*_workapps_*.sql, testing/features/F051/**]
feature_flag: F051_FEATURE
branch: s101-app-composition
started_at: null
finished_at: null
---

# S101 — App composition

## Identity

- Parent feature: `F051` WorkApps
- Owner: platform
- Branch: `s101-app-composition`
- Decision references: `docs/architecture-decisions.md` sections 2–4, 10; `docs/capability-contracts.md` row F051

## Vertical slice

As an app admin, I want to create an app with a slug, define its pages from existing sheets, forms, reports, dashboards, and dynamic views, define its roles, and publish an immutable version, so that the app has a validated manifest and a stable published snapshot before any viewer opens it.

Out of this slice: role-filtered serving at `/apps/{slug}`, the app shell, and the builder UI (S102).

## Requirements

- **SR-S101-01:** `POST /api/v1/workapps` creates a draft app with slug validation and tenant uniqueness, returning `WorkAppResponse` with version 1, `status: draft`, `published_version: null`; duplicate slug → `409 conflict` `field_errors.slug`; `max_apps` → `409 conflict` `field_errors.limit` (covers FR-F051-01, FR-F051-10).
- **SR-S101-02:** `PUT /api/v1/workapps/{id}/pages` validates up to 50 pages, source existence and kind through `SourceResolver`, text-page body rules, unique positions, and role references, returning `400 invalid` with indexed `field_errors.pages[n]` (FR-F051-02).
- **SR-S101-03:** `PUT /api/v1/workapps/{id}/roles` validates 1–20 roles, unique names, member kinds, and that each `default_landing_page_id` is visible to that role (FR-F051-03).
- **SR-S101-04:** `POST /api/v1/workapps/{id}/publish` writes `workapp_versions` with `version_number` n+1 and the manifest snapshot in one transaction, sets `published_version`, rejects empty manifests with `400 invalid`, republishes an earlier `version_number` as a new version, and emits `workapp.published.v1` (FR-F051-04, FR-F051-13).
- **SR-S101-05:** `GET /api/v1/workapps`, `GET /api/v1/workapps/{id}`, and `PATCH /api/v1/workapps/{id}` list, read (draft plus `draft_dirty` and last five versions), update metadata, and archive (FR-F051-07, FR-F051-08).
- **SR-S101-06:** Every mutation requires `Idempotency-Key` and `If-Match`, writes an audit row with page/role diffs, and publishes `workapp.updated.v1` or `workapp.published.v1` (FR-F051-09).
- **SR-S101-07:** Non-admin members receive `403 denied` on mutations and `404 not_found` on draft reads; tenant B receives `404 not_found`; non-entitled tenants receive `403 denied` from `RequireModule(ModuleSlug::Workapps)` (FR-F051-10, FR-F051-11).
- **SR-S101-08:** Publish is transactional so a failed snapshot never advances `published_version` (NFR-F051-04).

## Surfaces

- Infrastructure/container: none beyond F004 baseline
- Rust service/API: `crates/domain/src/workapps/{mod.rs, app.rs, slug.rs, page.rs, role.rs, manifest.rs, validate.rs, version.rs, sources.rs, errors.rs, service.rs}`; `services/api/src/workapps/{mod.rs, routes.rs, handlers_app.rs, handlers_pages.rs, handlers_roles.rs, handlers_publish.rs, dto.rs}`
- Data/migration: `services/api/migrations/<ts>_workapps_create_tables.sql` creating `workapps`, `workapp_pages`, `workapp_roles`, `workapp_versions` with the constraints from ticket section 4
- React/UI: none in this story (S102 and T203 cover UI)
- Mocks/fixtures: `testing/fixtures/workapps.rs` app admin, procurement user, vendor user, no-role member, tenant B, one sheet/form/report/dashboard/dynamic view, group `Vendors`; in-memory outbox recorder; F048 evaluator with `workapps` active

## TDD harness

- Test path: `testing/features/F051/api/`, `testing/features/F051/database/`
- Feature flag: `F051_FEATURE`
- Targeted command: `cargo xtask test-feature F051`
- Full command: `cargo xtask test-all`
- First failing tests: `app_create_rejects_duplicate_slug`, `pages_reject_51st_page`, `pages_reject_source_of_wrong_kind`, `roles_reject_landing_page_not_visible`, `publish_snapshots_manifest_and_increments_version`, `publish_failure_does_not_advance_published_version`

## Exit criteria

- [ ] Requirement tests SR-S101-01 through SR-S101-08 written first and failing
- [ ] Tasks T201 and T202 complete and wired through `services/api` router
- [ ] Unit, API, database, and permission tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/workapps/routes.rs` mounted in `services/api/src/router.rs` under `RequireModule(ModuleSlug::Workapps)`
- [ ] Handoff evidence recorded in the F051 ticket
