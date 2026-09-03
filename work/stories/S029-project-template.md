---
id: S029
type: story
status: planned
parent_epic: E003
parent_feature: F015
depends_on: [F012, F013, F014]
owned_paths: [crates/domain/src/templates/**, services/api/src/templates/**, services/worker/src/templates/**, apps/web/src/features/templates/**, services/api/migrations/*_templates_*.sql, testing/features/F015/**]
feature_flag: F015_FEATURE
branch: s029-project-template
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 7, 9
- Capability contract: `docs/capability-contracts.md` row F015

# S029 — Project template

## Identity

- Parent feature: `F015` Templates and baselines
- Owner: platform
- Branch: `s029-project-template`
- Decision references: `docs/architecture-decisions.md` sections 2–4, 7, 9; `docs/capability-contracts.md` row F015

## Vertical slice

As a portfolio admin, I want to publish a versioned project template (or start from a built-in one) and provision a complete project from it into a workspace with a start date, so that every project starts with the same sheets, rows, dependencies, views, and intake form without manual rebuilding.

## Requirements

- **SR-S029-01:** `POST /api/v1/project-templates` creates a tenant template or clones a built-in with `copy_from`; names are unique per tenant and the response carries `version` 1 (FR-F015-01, FR-F015-05).
- **SR-S029-02:** `POST /api/v1/project-templates/{id}/versions` validates the `TemplateManifest` (keys, column types, dependency references, limits from FR-F015-03) and creates a draft; `action: publish` makes it immutable and emits `template.published.v1` (FR-F015-02, FR-F015-03, FR-F015-04).
- **SR-S029-03:** The migration seeds the ten built-in templates with published manifests that pass `validate_manifest`; built-ins are listable by every tenant and reject mutation with `403 denied` (FR-F015-05, FR-F015-14).
- **SR-S029-04:** `POST /api/v1/project-templates/{id}/provision` returns `202` with a queued run within 2 s and rejects draft versions; the worker executes the ordered steps idempotently, resolves default-row dates on the sheet working calendar, and records skipped modules (FR-F015-06, FR-F015-07).
- **SR-S029-05:** A failing step retries three times, then rolls back created objects in reverse order and emits `provisioning.failed.v1`; a completed run emits `project.provisioned.v1` (FR-F015-08).
- **SR-S029-06:** `GET /api/v1/provisioning-runs/{id}` returns per-step status and `created_ids`, and returns `404 not_found` for users without access to the target workspace or from another tenant (FR-F015-09, FR-F015-14).
- **SR-S029-07:** `TemplateCatalogPage`, `TemplateDetail`, `ProvisionDialog`, and `ProvisioningStatus` render loading, empty, error, denied, failed, stale, and offline states with live-region progress (FR-F015-15, NFR-F015-03).
- **SR-S029-08:** Provision acknowledgement and a 500-row template completion meet NFR-F015-01; job metrics and spans from NFR-F015-04 are emitted.

## Surfaces

- Infrastructure/container: JetStream consumer `templates.provision` registered in `services/worker` with the F004 per-tenant quota
- Rust service/API: `crates/domain/src/templates/{mod.rs, template.rs, version.rs, manifest.rs, errors.rs, service_template.rs, service_provision.rs, builtin/*.json}`; `services/api/src/templates/{mod.rs, routes.rs, handlers_template.rs, handlers_provision.rs, dto.rs}`; `services/worker/src/templates/{mod.rs, provision_job.rs, steps.rs, rollback.rs}`
- Data/migration: `services/api/migrations/<ts>_templates_create_tables.sql` creating the five tables, immutability trigger, indexes, and the built-in seed
- React/UI: `apps/web/src/features/templates/{TemplateCatalogPage.tsx, TemplateCard.tsx, CategoryFilter.tsx, TemplateDetail.tsx, ManifestSummary.tsx, VersionHistory.tsx, ProvisionDialog.tsx, RoleAssignmentPicker.tsx, ProvisioningStatus.tsx, StepList.tsx, api.ts, hooks.ts, routes.ts}`
- Mocks/fixtures: `testing/fixtures/templates.rs` custom 120-row manifest, 500-row load manifest, failing-dependency manifest; in-memory outbox and JetStream recorder; in-process worker runner

## TDD harness

- Test path: `testing/features/F015/{api,database,frontend,e2e,accessibility,performance}/`
- Feature flag: `F015_FEATURE`
- Targeted command: `cargo xtask test-feature F015`
- Full command: `cargo xtask test-all`
- First failing tests: `template_create_and_copy_builtin`, `version_publish_is_immutable`, `manifest_rejects_dangling_key`, `provision_run_completes_all_steps`, `provision_failure_rolls_back`, `builtin_seed_validates`

## Exit criteria

- [ ] Requirement tests SR-S029-01 through SR-S029-08 written first and failing
- [ ] Tasks T057 and T058 complete and wired through `services/api` router and `services/worker` consumer registry
- [ ] Unit, API, worker, database, React, permission, and performance tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/templates/routes.rs` mounted in `services/api/src/router.rs`; `services/worker/src/templates/provision_job.rs` registered in `services/worker/src/consumers.rs`
- [ ] Handoff evidence recorded in the F015 ticket
