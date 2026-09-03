---
id: T009
type: task
status: planned
parent_epic: E001
parent_feature: F003
parent_story: S005
depends_on: [S005]
owned_paths: [services/api/migrations/*_authz_*.sql, crates/domain/src/authz/**, testing/features/F003/database/**, testing/features/F003/api/**]
feature_flag: F003_FEATURE
branch: t009-policy-engine
started_at: null
finished_at: null
---

# T009 — Policy engine

## Identity

- Parent story: `S005` Roles/policies
- Owner: platform
- Branch: `t009-policy-engine`

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 4
- Canonical contract: `docs/capability-contracts.md` row F003

## Objective

Create the four authorization tables with seeds, triggers, and partitions, and implement the pure policy engine (permission catalogue, evaluation order, ancestry, group expansion, caching) as library code with no HTTP surface.

## Specification

- Owned paths: `services/api/migrations/<ts>_authz_create_tables.sql` and `.down.sql`, `crates/domain/src/authz/{mod.rs, permissions.rs, role.rs, acl.rs, principal.rs, ancestry.rs, engine.rs, cache.rs, errors.rs, schema.rs}`
- Contract/input: DDL per F003 ticket section 4 including `seed_system_roles(tenant_id)` and its trigger, `audit_immutable` trigger, monthly range partitions for the current and next three months; `Permission::parse("sheet:edit")`, wildcard `*:read`; `Engine::check(&self, principal: &PrincipalSet, permission, resource) -> Decision` where `PrincipalSet` holds the user id, group ids, and `is_guest`; `AncestryResolver::ancestors(resource) -> Vec<ResourceRef>` trait with the built-in tenant resolver; `DecisionCache` with 30-second TTL keyed by `(principal, resource, permission)` and `invalidate_resource` / `invalidate_role`.
- Output/behavior: evaluation order suspended → explicit deny on resource or ancestor → allow entry or role binding at scope or ancestor → `no_match` deny; guests skip tenant-scoped bindings; result carries `reason` and `matched_rule`; `sqlx migrate run` applies on a database with F002 and F038 tables and `revert` drops everything; seeds verified for a newly inserted tenant.
- Dependencies: F002 `group_members` for membership expansion; F038 `ActorContext.auth_kind` for guest detection (guest marker defined by F036 later, read through a trait method defaulting to false).
- Feature flag: `F003_FEATURE` (migration runs regardless; library code is inert until T010 wires it)
- Large-table note: `audit_events` partitions are pre-created; `resource_acls` indexes cover both resource and principal lookups.

## TDD

- Failing test first: `testing/features/F003/database/migration_tests.rs::authz_tables_exist_with_constraints`, `::system_roles_seeded_per_tenant`, `::audit_update_and_delete_raise_immutable`, `::audit_partitions_created_for_four_months`, `::rollback_drops_tables`; `testing/features/F003/api/engine_tests.rs::deny_on_ancestor_beats_allow_on_resource`, `::role_binding_at_ancestor_grants`, `::guest_ignores_tenant_binding`, `::wildcard_permission_matches`, `::cache_invalidated_after_acl_update`
- Targeted command: `cargo xtask test-feature F003`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/authz.rs` synthetic 4-level ancestry resolver; schema-per-worker database

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; engine unit tests green
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S005
- [ ] `finished_at` recorded
