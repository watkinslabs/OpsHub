---
id: T007
type: task
status: planned
parent_epic: E001
parent_feature: F002
parent_story: S004
depends_on: [T006]
owned_paths: [crates/domain/src/tenants/**, services/api/src/tenants/**, apps/web/src/features/tenants/**, testing/features/F002/api/**, testing/features/F002/frontend/**]
feature_flag: F002_FEATURE
branch: t007-membership-state
started_at: null
finished_at: null
---

# T007 — Membership state

## Identity

- Parent story: `S004` Users and groups
- Owner: platform
- Branch: `t007-membership-state`

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 6
- Canonical contract: `docs/capability-contracts.md` row F002

## Objective

Implement the user status machine, the eight user and group routes with atomic membership replacement and the last-admin guard, and the admin pages that drive them.

## Specification

- Owned paths: `crates/domain/src/tenants/{user.rs, group.rs, status.rs, service_user.rs, service_group.rs}`, `services/api/src/tenants/{handlers_user.rs, handlers_group.rs}`, `crates/persistence/src/users/user_repository.rs` and `crates/persistence/src/tenants/group_repository.rs` (the only files here that may contain SQL), `apps/web/src/features/tenants/{TenantSettingsPage.tsx, TenantSettingsForm.tsx, SuspendTenantDialog.tsx, UsersPage.tsx, UsersTable.tsx, InviteUserDialog.tsx, DeactivateUserDialog.tsx, GroupsPage.tsx, GroupDetailPage.tsx, GroupMembersEditor.tsx, UserStatusBadge.tsx, api.ts, hooks.ts, routes.ts}`
- Contract/input: `CreateUserRequest { email, display_name, external_id? }`, `UpdateUserRequest { display_name?, external_id?, status? }`, `CreateGroupRequest { name, description? }`, `UpdateGroupRequest { name?, description? }`, `ReplaceMembersRequest { user_ids: Vec<Uuid> }` (≤ 5,000, deduplicated); list query `{ cursor?, limit? ≤ 200, status?, email_prefix?, group_id?, sort? }`; `UserRepository` (`users`) and `GroupRepository` (`groups`, `group_members`) expose the named queries these services call (`list_page`, `find_by_email`, `count_active_admins_for_update`, `replace_members`, `remove_user_from_all_groups`) and no generic query escape hatch.
- Output/behavior: routes `GET/POST /api/v1/users`, `PATCH /api/v1/users/{id}`, `POST /api/v1/users/{id}/deactivate`, `GET/POST /api/v1/groups`, `PATCH /api/v1/groups/{id}`, `PUT /api/v1/groups/{id}/members` return `UserResponse { id, email, display_name, status, external_id, last_login_at, group_ids, version, created_at, updated_at }` and `GroupResponse { id, name, description, member_count, version, ... }`; `status.rs` implements `UserStatus::transition`; deactivate runs `SELECT ... FOR UPDATE` on the tenant row, counts active tenant-admins, deletes memberships, calls `SessionRevoker`, and emits `user.deactivated.v1`; membership replace computes `added_user_ids` and `removed_user_ids`, deletes and bulk-inserts in one transaction, and emits `group.updated.v1`; the React pages implement the states, dialogs, and telemetry from ticket section 3.
- Dependencies: T006 tenant service, DTO module, gate, and hooks; F001 web shell for the `/admin` navigation entry.
- Feature flag: `F002_FEATURE` gates routes and the admin navigation entry.

## TDD

- Failing test first: `testing/features/F002/api/user_tests.rs::user_create_invited_unique_email`, `::user_list_pages_filters_sorts`, `::user_illegal_transition_invalid`, `::user_deactivate_revokes_sessions_and_memberships`, `::user_deactivate_last_admin_rejected`; `testing/features/F002/api/group_tests.rs::group_members_replace_atomic`, `::group_members_foreign_user_invalid`, `::group_members_over_cap_invalid`; `testing/features/F002/frontend/UsersTable.test.tsx::renders_status_badges`, `::shows_denied_for_member`, `GroupMembersEditor.test.tsx::rolls_back_on_invalid`
- Targeted command: `cargo xtask test-feature F002`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/tenants.rs` full fixture; MSW handlers derived from it

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Routes mounted behind the flag; OpenAPI regenerated; pages registered in `routes.ts`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S004
- [ ] `finished_at` recorded
