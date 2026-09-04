---
id: T010
type: task
status: planned
parent_epic: E001
parent_feature: F003
parent_story: S005
depends_on: [T009]
owned_paths: [crates/domain/src/authz/**, services/api/src/authz/**, apps/web/src/features/authz/**, testing/features/F003/api/**, testing/features/F003/frontend/**, testing/features/F003/performance/**]
feature_flag: F003_FEATURE
branch: t010-acl-middleware
started_at: null
finished_at: null
---

# T010 — ACL middleware

## Identity

- Parent story: `S005` Roles/policies
- Owner: platform
- Branch: `t010-acl-middleware`

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 3, 4, 6
- Canonical contract: `docs/capability-contracts.md` row F003

## Objective

Expose the engine through `authz::require`, the `RequirePermission` extractor, the six role, ACL, and check routes, the cache-invalidating event subscriber, and the roles and ACL editor UI, then switch F002 and F038 routes to the extractor.

## Specification

- Owned paths: `crates/domain/src/authz/{require.rs, service_roles.rs, service_acl.rs}` (repository traits only, no SQL), `services/api/src/authz/{mod.rs, routes.rs, handlers_roles.rs, handlers_acl.rs, handlers_check.rs, extractor.rs, invalidation.rs, dto.rs}`, `apps/web/src/features/authz/{RolesPage.tsx, RoleEditor.tsx, PermissionMatrix.tsx, AclEditor.tsx, AclEntryRow.tsx, PrincipalPicker.tsx, api.ts, hooks.ts, routes.ts}`
- Contract/input: `CreateRoleRequest { slug, name, permissions }`, `UpdateRoleRequest { name?, permissions? }`, `ReplaceAclRequest { entries: [{ principal, effect, permissions?, role_id? }] }` (≤ 500), `CheckRequest { permission, resource, principal? }`; headers `Idempotency-Key`, `If-Match`; `RequirePermission<P: PermissionConst>` extractor reading `ActorContext` and the route's `ResourceRef` path params; `service_roles.rs` and `service_acl.rs` persist through T009's `RoleRepository` and `ResourceAclRepository` on one `UnitOfWork`, replacing a role's `role_permissions` rows and an entry's `resource_acl_permissions` rows inside the same transaction as the parent row.
- Output/behavior: routes `GET /api/v1/roles`, `POST /api/v1/roles`, `PATCH /api/v1/roles/{id}`, `GET /api/v1/resources/{kind}/{id}/acl`, `PUT /api/v1/resources/{kind}/{id}/acl`, `POST /api/v1/authz/check`; `require` maps `Hidden → 404`, `Denied → 403`; `invalidation.rs` subscribes to `role.updated.v1` and `acl.updated.v1` and drops cache keys; events `role.updated.v1`, `acl.updated.v1`; audit rows via the T011 writer (in-memory recorder until T011); UI per ticket section 3 with the exported `AclEditor` drawer and `usePermission` hook; F002 and F038 handlers replace their interim role checks with `RequirePermission`; no handler, use case, or test in this task contains a SQL string, `sqlx::query*` call, or its own pool (decision 2.1).
- Dependencies: T009 engine, cache, tables, and the `crates/persistence/src/authz/` repositories; F038 extractor; F004 outbox subscriber API (in-memory bus until F004 lands).
- Feature flag: `F003_FEATURE` gates router mounting, the extractor swap, and the admin navigation entries.

## TDD

- Failing test first: `testing/features/F003/api/role_tests.rs::role_create_custom_and_list`, `::role_unknown_permission_invalid`, `::role_system_slug_immutable`, `::role_update_replaces_permission_rows_atomically`, `::role_member_create_denied`; `testing/features/F003/api/acl_tests.rs::acl_replace_emits_diff_event`, `::acl_replace_rewrites_permission_rows`, `::acl_over_500_entries_invalid`, `::acl_commenter_replace_denied`, `::acl_effective_includes_inherited`; `testing/features/F003/api/check_tests.rs::check_delegated_requires_admin`, `::require_maps_missing_read_to_not_found`; `testing/features/F003/frontend/PermissionMatrix.test.tsx::toggles_with_keyboard_and_labels`, `AclEditor.test.tsx::adds_deny_with_confirm`; `testing/features/F003/performance/authz_bench.rs::check_cached_p95`, `::check_uncached_four_levels_p95`
- Targeted command: `cargo xtask test-feature F003`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/authz.rs`; MSW handlers; in-memory outbox and bus

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Routes mounted behind the flag; F002 and F038 routes use `RequirePermission`; OpenAPI regenerated; pages registered
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S005
- [ ] `finished_at` recorded
