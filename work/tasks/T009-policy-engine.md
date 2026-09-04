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

Create the six authorization tables with seeds, triggers, and partitions, add their repositories in `crates/persistence/src/authz/`, and implement the pure policy engine (permission catalogue, evaluation order, ancestry, group expansion, caching) as library code with no HTTP surface and no SQL.

## Specification

- Owned paths: `services/api/migrations/<ts>_authz_create_tables.sql` and `.down.sql`, `crates/persistence/src/authz/{mod.rs, role_repository.rs, role_binding_repository.rs, resource_acl_repository.rs, group_membership.rs}`, `crates/domain/src/authz/{mod.rs, permissions.rs, role.rs, acl.rs, principal.rs, ancestry.rs, engine.rs, cache.rs, errors.rs, schema.rs}`
- Contract/input: DDL per F003 ticket section 4 — `roles`, `role_permissions(tenant_id, role_id references roles(id) on delete cascade, permission text check (permission ~ '^(\*|[a-z-]+):(\*|[a-z-]+)$'), granted_at, primary key (role_id, permission))`, `role_bindings`, `resource_acls`, `resource_acl_permissions(tenant_id, acl_id references resource_acls(id) on delete cascade, permission with the same format check, primary key (acl_id, permission))`, partitioned `audit_events`, the unique indexes `roles_tenant_slug_idx`, `resource_acls_entry_idx`, `role_bindings_idx`, and the lookup indexes `role_permissions(tenant_id, permission)`, `resource_acl_permissions(tenant_id, permission)`, `resource_acl_permissions(acl_id)`, plus `seed_system_roles(tenant_id)` and its trigger, the `audit_immutable` trigger, and monthly range partitions for the current and next three months; `RoleRepository` (`roles`, `role_permissions`), `RoleBindingRepository` (`role_bindings`), and `ResourceAclRepository` (`resource_acls`, `resource_acl_permissions`) own every statement against those tables and expose named queries (`permissions_for_roles`, `entries_for_resources`, `bindings_for_principals`); `GroupMembershipSource` expands groups through F002's `GroupRepository`; `Permission::parse("sheet:edit")`, wildcard `*:read`; `Engine::check(&self, principal: &PrincipalSet, permission, resource) -> Decision` where `PrincipalSet` holds the user id, group ids, and `is_guest`; `AncestryResolver::ancestors(resource) -> Vec<ResourceRef>` trait with the built-in tenant resolver; `DecisionCache` with 30-second TTL keyed by `(principal, resource, permission)` and `invalidate_resource` / `invalidate_role`.
- Output/behavior: evaluation order suspended → explicit deny on resource or ancestor → allow entry or role binding at scope or ancestor → `no_match` deny, matching a permission by joining `role_permissions` and `resource_acl_permissions` rows inside the repositories rather than testing array containment; guests skip tenant-scoped bindings; result carries `reason` and `matched_rule`; `crates/domain/src/authz/` and the tests contain no SQL string or `sqlx::query*` call and depend only on the repository traits (decision 2.1); `sqlx migrate run` applies on a database with F002 and F038 tables and `revert` drops the six tables, the triggers, the seed function, and the partitions; seeds verified for a newly inserted tenant.
- Dependencies: F002 `GroupRepository` over `group_members` for membership expansion; F038 `ActorContext.auth_kind` for guest detection (guest marker defined by F036 later, read through a trait method defaulting to false).
- Feature flag: `F003_FEATURE` (migration runs regardless; library code is inert until T010 wires it)
- Large-table note: `audit_events` partitions are pre-created; `resource_acls` indexes cover both resource and principal lookups, and the `role_permissions` and `resource_acl_permissions` indexes keep the evaluator's permission match an index scan.

## TDD

- Failing test first: `testing/features/F003/database/migration_tests.rs::authz_tables_exist_with_constraints`, `::system_roles_seeded_per_tenant`, `::role_permissions_primary_key_rejects_duplicate`, `::acl_permissions_cascade_on_entry_delete`, `::permission_format_check_rejects_bad_value`, `::audit_update_and_delete_raise_immutable`, `::audit_partitions_created_for_four_months`, `::rollback_drops_tables`; `testing/features/F003/api/engine_tests.rs::deny_on_ancestor_beats_allow_on_resource`, `::role_binding_at_ancestor_grants`, `::guest_ignores_tenant_binding`, `::wildcard_permission_matches`, `::cache_invalidated_after_acl_update`, `::engine_reads_permissions_through_repositories`
- Targeted command: `cargo xtask test-feature F003`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/authz.rs` synthetic 4-level ancestry resolver; schema-per-worker database

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; engine unit tests green; `cargo xtask check-persistence` passes with all authz SQL inside `crates/persistence/src/authz/`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S005
- [ ] `finished_at` recorded
