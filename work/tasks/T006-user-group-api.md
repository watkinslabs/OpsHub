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

- Owned paths: `crates/domain/src/tenants/{mod.rs, tenant.rs, slug.rs, errors.rs, service_tenant.rs, hooks.rs}`, `services/api/src/tenants/{mod.rs, routes.rs, handlers_tenant.rs, dto.rs, gate.rs}`
- Contract/input: `CreateTenantRequest { name, slug, plan, region, admin_email, admin_display_name }`, `UpdateTenantRequest { name?, plan?, settings? }`; headers `Idempotency-Key`, `If-Match`; `hooks.rs` defines `SessionRevoker` and `AuditSink` traits with in-memory defaults.
- Output/behavior: routes `POST /api/v1/tenants`, `GET /api/v1/tenants/{id}`, `PATCH /api/v1/tenants/{id}`, `POST /api/v1/tenants/{id}/suspend` return `TenantResponse { id, name, slug, plan, region, status, settings, admin_user_id, version, created_at, updated_at }`; `gate.rs` is an Axum layer that loads tenant status from a 30-second cache and returns `403 denied` with `reason = tenant_suspended`; events `tenant.created.v1`, `tenant.updated.v1`, `tenant.suspended.v1` enqueued through `crates/events` in the same transaction; errors map per ticket section 4.
- Dependencies: T005 schema; F004 outbox `enqueue` (in-memory recorder until F004 lands); `ActorContext` from F038 is stubbed by a test-only header extractor until F038 lands, and the real extractor replaces it without changing handlers.
- Feature flag: `F002_FEATURE` gates router mounting.

## TDD

- Failing test first: `testing/features/F002/api/tenant_tests.rs::tenant_create_bootstraps_admin`, `::tenant_slug_taken_conflicts`, `::tenant_invalid_region_rejected`, `::tenant_stale_version_conflicts`, `::tenant_suspend_blocks_api_routes`, `::tenant_idempotent_replay_returns_original`, `::tenant_cross_tenant_not_found`, `::tenant_member_mutation_denied`
- Targeted command: `cargo xtask test-feature F002`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/tenants.rs` tenants A and B with admins; in-memory outbox recorder and audit sink

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Router mounted in `services/api/src/router.rs` behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S003
- [ ] `finished_at` recorded
