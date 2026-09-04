---
id: S003
type: story
status: planned
parent_epic: E001
parent_feature: F002
depends_on: [F001]
owned_paths: [crates/domain/src/tenants/**, services/api/src/tenants/**, services/api/migrations/*_tenants_*.sql, testing/features/F002/**]
feature_flag: F002_FEATURE
branch: s003-tenant-lifecycle
started_at: null
finished_at: null
---

# S003 — Tenant lifecycle

## Identity

- Parent feature: `F002` Tenant, users, and groups
- Owner: platform
- Branch: `s003-tenant-lifecycle`

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4
- Canonical contract: `docs/capability-contracts.md` row F002

## Vertical slice

As a platform operator, I want to bootstrap a tenant with its first administrator, and as that administrator I want to read, update, and suspend my tenant, so that every later record has an owning tenant whose isolation is enforced from the first migration.

## Requirements

- **SR-S003-01:** `POST /api/v1/tenants` with `{ name, slug, plan, region, admin_email, admin_display_name }` inserts `tenants` and the first `users` row in one transaction and returns `TenantResponse` at version 1 with `admin_user_id` (covers FR-F002-01).
- **SR-S003-02:** Slug regex, length 3–63, `plan` enum, and `region = us-east` are validated with `400 invalid` and `field_errors`; a taken slug returns `409 conflict` (FR-F002-02).
- **SR-S003-03:** `GET /api/v1/tenants/{id}` and `PATCH /api/v1/tenants/{id}` require the caller's own tenant id; `PATCH` requires `If-Match` and returns `409 conflict` with `current_version` when stale; settings are the typed columns of the tenant's one `tenant_settings` row (`default_locale`, `default_timezone`, `allow_guest_invites`, `operator_contact`) loaded and saved by `TenantRepository` in the same transaction as the tenant (FR-F002-03).
- **SR-S003-04:** `POST /api/v1/tenants/{id}/suspend` sets `status = suspended`, emits `tenant.suspended.v1`, and the `TenantGate` layer returns `403 denied` with `reason = tenant_suspended` on every other `/api/v1` route (FR-F002-04).
- **SR-S003-05:** Every mutation checks `Idempotency-Key`, writes one audit row, and enqueues exactly one `tenant.*.v1` outbox event in the same transaction (FR-F002-11, FR-F002-12).
- **SR-S003-06:** A foreign tenant id on any tenant route returns `404 not_found` (FR-F002-13).
- **SR-S003-07:** The `tenant_settings`, `users`, `groups`, and `group_members` tables and their constraints exist from this story's migration, including the trigger that creates one `tenant_settings` row per tenant, so S004 adds no schema (FR-F002-05, FR-F002-09 prerequisites).

## Surfaces

- Infrastructure/container: none beyond the F001 CI PostgreSQL 18 service
- Rust service/API: `crates/domain/src/tenants/{mod.rs, tenant.rs, settings.rs, slug.rs, errors.rs, service_tenant.rs, hooks.rs}`; `services/api/src/tenants/{mod.rs, routes.rs, handlers_tenant.rs, dto.rs, gate.rs}`; all table access goes through `TenantRepository` (`tenants`, `tenant_settings`) and `GroupRepository` (`groups`, `group_members`) in `crates/persistence/src/tenants/` and `UserRepository` (`users`) in `crates/persistence/src/users/` — the domain services, handlers, and gate depend on those repository traits and the shared `UnitOfWork` and contain no SQL (decision 2.1)
- Data/migration: `services/api/migrations/<ts>_tenants_create_tables.sql` creating `tenants`, `tenant_settings` (one typed row per tenant, primary key `tenant_id`, created by the insert trigger on `tenants`, no `jsonb` settings column), `users`, `groups`, `group_members` with the indexes, check constraints, and same-tenant trigger from ticket section 4; the migration is the only SQL this story owns outside `crates/persistence`
- React/UI: none in this story (S004 delivers the admin pages)
- Mocks/fixtures: `testing/fixtures/tenants.rs` first cut (tenants A and B with their admins); in-memory outbox recorder and audit sink

## TDD harness

- Test path: `testing/features/F002/api/` and `testing/features/F002/database/`
- Feature flag: `F002_FEATURE`
- Targeted command: `cargo xtask test-feature F002`
- Full command: `cargo xtask test-all`
- First failing tests: `tenant_create_bootstraps_admin`, `tenant_slug_taken_conflicts`, `tenant_invalid_region_rejected`, `tenant_stale_version_conflicts`, `tenant_settings_row_created_by_trigger`, `tenant_settings_patch_updates_typed_columns`, `tenant_suspend_blocks_api_routes`, `tenant_cross_tenant_not_found`

## Exit criteria

- [ ] Requirement tests SR-S003-01 through SR-S003-07 written first and failing
- [ ] Tasks T005 and T006 complete and wired through the `services/api` router
- [ ] Unit, API, database, and permission tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/tenants/routes.rs` mounted in `services/api/src/router.rs` with `gate.rs` applied as a layer on `/api/v1`
- [ ] Handoff evidence recorded in the F002 ticket
