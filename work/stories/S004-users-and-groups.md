---
id: S004
type: story
status: planned
parent_epic: E001
parent_feature: F002
depends_on: [S003]
owned_paths: [crates/domain/src/tenants/**, services/api/src/tenants/**, apps/web/src/features/tenants/**, testing/features/F002/**]
feature_flag: F002_FEATURE
branch: s004-users-and-groups
started_at: null
finished_at: null
---

# S004 — Users and groups

## Identity

- Parent feature: `F002` Tenant, users, and groups
- Owner: platform
- Branch: `s004-users-and-groups`

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 6, 9
- Canonical contract: `docs/capability-contracts.md` row F002

## Vertical slice

As a tenant administrator, I want to invite, update, and deactivate users and organize them into groups from the admin pages, so that roles and identity sync have real principals and the membership state machine is enforced by the API rather than the UI.

## Requirements

- **SR-S004-01:** `POST /api/v1/users` creates an `invited` user with per-tenant unique `citext` email and emits `user.created.v1`; duplicates return `409 conflict` with `field_errors.email` (FR-F002-05).
- **SR-S004-02:** `GET /api/v1/users` pages by cursor with `limit` ≤ 200, filters `status`, `email` prefix, `group_id`, and sorts by `display_name`, `email`, `created_at` (FR-F002-06).
- **SR-S004-03:** `PATCH /api/v1/users/{id}` enforces the `invited → active → suspended → active` machine with `If-Match`; self-edits are limited to `display_name` (FR-F002-07).
- **SR-S004-04:** `POST /api/v1/users/{id}/deactivate` removes group memberships, calls `SessionRevoker`, emits `user.deactivated.v1`, and rejects the last active tenant-admin with `400 invalid` reason `last_admin` (FR-F002-08).
- **SR-S004-05:** `POST /api/v1/groups` and `PATCH /api/v1/groups/{id}` enforce case-insensitive unique names and emit `group.updated.v1`; `PUT /api/v1/groups/{id}/members` replaces the set atomically, caps at 5,000 ids, and reports foreign or deactivated ids in `field_errors.user_ids` (FR-F002-09, FR-F002-10).
- **SR-S004-06:** `/admin/tenant`, `/admin/users`, `/admin/groups` render loading, empty, error, denied, stale, and offline states; members see the denied state (FR-F002-14, NFR-F002-03).
- **SR-S004-07:** The 100,000-user list and 5,000-member replace meet NFR-F002-01, and the cross-tenant suite proves NFR-F002-02 for all twelve routes.

## Surfaces

- Infrastructure/container: none
- Rust service/API: `crates/domain/src/tenants/{user.rs, group.rs, status.rs, service_user.rs, service_group.rs}`; `services/api/src/tenants/{handlers_user.rs, handlers_group.rs}`
- Data/migration: none new; uses tables from S003
- React/UI: `apps/web/src/features/tenants/{TenantSettingsPage.tsx, TenantSettingsForm.tsx, SuspendTenantDialog.tsx, UsersPage.tsx, UsersTable.tsx, InviteUserDialog.tsx, DeactivateUserDialog.tsx, GroupsPage.tsx, GroupDetailPage.tsx, GroupMembersEditor.tsx, UserStatusBadge.tsx, api.ts, hooks.ts, routes.ts}`
- Mocks/fixtures: `testing/fixtures/tenants.rs` completed (members, invited, deactivated users, three groups per tenant); 100,000-user generator; MSW handlers for component tests

## TDD harness

- Test path: `testing/features/F002/{api,database,frontend,e2e,accessibility,performance}/`
- Feature flag: `F002_FEATURE`
- Targeted command: `cargo xtask test-feature F002`
- Full command: `cargo xtask test-all`
- First failing tests: `user_create_invited_unique_email`, `user_illegal_transition_invalid`, `user_deactivate_last_admin_rejected`, `group_members_replace_atomic`, `group_members_foreign_user_invalid`, `users_table_shows_denied_for_member`, `user_list_100k_p95`

## Exit criteria

- [ ] Requirement tests SR-S004-01 through SR-S004-07 written first and failing
- [ ] Tasks T007 and T008 complete; UI wired to the real API through the generated client
- [ ] Unit, API, React, E2E, accessibility, permission, and performance tests pass
- [ ] Production call path named: `apps/web/src/features/tenants/UsersPage.tsx` mounted at `/admin/users` in `apps/web/src/features/tenants/routes.ts`
- [ ] Handoff evidence recorded in the F002 ticket
