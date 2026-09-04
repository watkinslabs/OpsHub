---
id: T006
type: task
status: planned
parent_epic: E001
parent_feature: F002
parent_story: S003
depends_on: [T005]
owned_paths: [crates/domain/src/tenants/**, services/api/src/tenants/**, testing/features/F002/api/**, testing/features/F002/requirements/**]
feature_flag: F002_FEATURE
branch: t006-user-group-api
started_at: null
finished_at: null
---

# T006 — User/group API

## Identity

- Parent story: `S003` Tenant lifecycle
- Owner: platform
- Branch: `t006-user-group-api`

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4
- Canonical contract: `docs/capability-contracts.md` row F002

## Objective

Implement the tenant domain service, the four tenant routes, the `TenantGate` suspension layer, and the shared handler scaffolding (DTOs, error mapping, idempotency, audit, outbox) that the user and group handlers in T007 reuse.

## Specification

- Owned paths: `crates/domain/src/tenants/{mod.rs, tenant.rs, settings.rs, slug.rs, errors.rs, service_tenant.rs, hooks.rs}`, `services/api/src/tenants/{mod.rs, routes.rs, handlers_tenant.rs, dto.rs, gate.rs}`, `crates/persistence/src/tenants/{mod.rs, tenant_repository.rs}` and `crates/persistence/src/users/{mod.rs, user_repository.rs}` — the only files in this task that may contain SQL
- Contract/input: `CreateTenantRequest { name, slug, plan, region, admin_email, admin_display_name }`, `UpdateTenantRequest { name?, plan?, settings? }` where `settings` carries the four typed fields `default_locale`, `default_timezone`, `allow_guest_invites`, `operator_contact`; headers `Idempotency-Key`, `If-Match`; `hooks.rs` defines `SessionRevoker` and `AuditSink` traits with in-memory defaults; `TenantRepository` (`tenants`, `tenant_settings`) and `UserRepository` (`users`) expose the named queries the service calls (`find_by_slug`, `load_with_settings`, `update_settings`, `insert_admin_user`), with no generic query escape hatch.
- Output/behavior: routes `POST /api/v1/tenants`, `GET /api/v1/tenants/{id}`, `PATCH /api/v1/tenants/{id}`, `POST /api/v1/tenants/{id}/suspend` return `TenantResponse { id, name, slug, plan, region, status, settings, admin_user_id, version, created_at, updated_at }` with `settings` read from the tenant's one `tenant_settings` row and written back in the same `UnitOfWork` transaction under the tenant `version`; `gate.rs` is an Axum layer that loads tenant status through `TenantRepository` into a 30-second cache and returns `403 denied` with `reason = tenant_suspended`; the service, handlers, DTOs, gate, and tests hold no SQL string, `sqlx::query*` call, or connection (decision 2.1); events `tenant.created.v1`, `tenant.updated.v1`, `tenant.suspended.v1` enqueued through `crates/events` by the repository base contract in the same transaction; errors map per ticket section 4.
- Dependencies: T005 schema; F004 outbox `enqueue` (in-memory recorder until F004 lands); `ActorContext` from F038 is stubbed by a test-only header extractor until F038 lands, and the real extractor replaces it without changing handlers.
- Feature flag: `F002_FEATURE` gates router mounting.

## TDD

- Failing test first: `testing/features/F002/api/tenant_tests.rs::tenant_create_bootstraps_admin`, `::tenant_slug_taken_conflicts`, `::tenant_invalid_region_rejected`, `::tenant_stale_version_conflicts`, `::tenant_settings_typed_columns_roundtrip`, `::tenant_suspend_blocks_api_routes`, `::tenant_idempotent_replay_returns_original`, `::tenant_cross_tenant_not_found`, `::tenant_member_mutation_denied`
- Targeted command: `cargo xtask test-feature F002`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/tenants.rs` tenants A and B with admins; in-memory outbox recorder and audit sink

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Router mounted in `services/api/src/router.rs` behind the flag; OpenAPI regenerated without drift
- [ ] `cargo xtask check-persistence` passes: SQL only in `crates/persistence`, one repository per table
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S003
- [ ] `finished_at` recorded
