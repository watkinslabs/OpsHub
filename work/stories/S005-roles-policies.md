---
id: S005
type: story
status: planned
parent_epic: E001
parent_feature: F003
depends_on: [F002, F038]
owned_paths: [crates/domain/src/authz/**, services/api/src/authz/**, apps/web/src/features/authz/**, services/api/migrations/*_authz_*.sql, testing/features/F003/**]
feature_flag: F003_FEATURE
branch: s005-roles-policies
started_at: null
finished_at: null
---

# S005 — Roles/policies

## Identity

- Parent feature: `F003` Authorization and audit
- Owner: platform
- Branch: `s005-roles-policies`

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4
- Canonical contract: `docs/capability-contracts.md` row F003

## Vertical slice

As a tenant administrator, I want system and custom roles, resource ACLs with inheritance and explicit denies, and a single `require` entry point that every handler uses, so that access decisions are deny-by-default, explainable, and enforced in service code rather than the UI.

## Requirements

- **SR-S005-01:** The migration seeds the seven system roles per tenant through a trigger on `tenants` insert, with `is_system = true` and immutable slugs (covers FR-F003-01).
- **SR-S005-02:** `GET/POST /api/v1/roles` and `PATCH /api/v1/roles/{id}` manage custom roles with unique slugs, catalogue-validated permissions, `If-Match`, and `role.updated.v1` (FR-F003-02).
- **SR-S005-03:** `GET /api/v1/resources/{kind}/{id}/acl` returns direct, inherited, and caller-resolved entries; `PUT` replaces direct entries atomically (≤ 500), requires `acl:manage`, and emits `acl.updated.v1` with the entry diff (FR-F003-03, FR-F003-04).
- **SR-S005-04:** `check` evaluates suspended → explicit deny on resource or ancestor → allow entry or role binding at scope or ancestor → deny, returning `decision`, `reason`, `matched_rule`; guests never match tenant-scoped bindings (FR-F003-05, FR-F003-06).
- **SR-S005-05:** `POST /api/v1/authz/check` serves the caller, or another principal for tenant-admin, and denies delegated checks for others (FR-F003-07).
- **SR-S005-06:** `authz::require` and `RequirePermission<P>` map missing read to `404`, missing mutate to `403`, cache per request and 30 s across requests, and invalidate on `acl.updated.v1` / `role.updated.v1` (FR-F003-08).
- **SR-S005-07:** `/admin/roles` and the reusable `AclEditor` drawer render the matrix, entries, and all UI states (FR-F003-14, NFR-F003-03).
- **SR-S005-08:** Cached and uncached `check` meet NFR-F003-01 on the 4-level fixture ancestry.

## Surfaces

- Infrastructure/container: none
- Rust service/API: `crates/domain/src/authz/{mod.rs, permissions.rs, role.rs, acl.rs, principal.rs, ancestry.rs, engine.rs, cache.rs, require.rs, errors.rs, service_roles.rs, service_acl.rs, schema.rs}`; `services/api/src/authz/{mod.rs, routes.rs, handlers_roles.rs, handlers_acl.rs, handlers_check.rs, extractor.rs, dto.rs}`
- Data/migration: `services/api/migrations/<ts>_authz_create_tables.sql` creating `roles`, `role_bindings`, `resource_acls`, and partitioned `audit_events` with triggers and indexes from ticket section 4 (audit rows are written by S006)
- React/UI: `apps/web/src/features/authz/{RolesPage.tsx, RoleEditor.tsx, PermissionMatrix.tsx, AclEditor.tsx, AclEntryRow.tsx, PrincipalPicker.tsx, api.ts, hooks.ts, routes.ts}`
- Mocks/fixtures: `testing/fixtures/authz.rs` with the synthetic 4-level `AncestryResolver`, role `Reviewer`, bindings, guest principal; in-memory outbox recorder

## TDD harness

- Test path: `testing/features/F003/{api,database,frontend,accessibility,performance}/`
- Feature flag: `F003_FEATURE`
- Targeted command: `cargo xtask test-feature F003`
- Full command: `cargo xtask test-all`
- First failing tests: `system_roles_seeded_per_tenant`, `role_unknown_permission_invalid`, `acl_replace_emits_diff_event`, `deny_on_ancestor_beats_allow_on_resource`, `guest_ignores_tenant_binding`, `require_maps_missing_read_to_not_found`, `cache_invalidated_after_acl_update`, `check_cached_p95`

## Exit criteria

- [ ] Requirement tests SR-S005-01 through SR-S005-08 written first and failing
- [ ] Tasks T009 and T010 complete and wired through the `services/api` router
- [ ] Unit, API, database, React, accessibility, permission, and performance tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/authz/routes.rs` mounted in `services/api/src/router.rs`; `crates/domain/src/authz/require.rs` called from `services/api/src/authz/extractor.rs` and applied to F002 and F038 routes
- [ ] Handoff evidence recorded in the F003 ticket
