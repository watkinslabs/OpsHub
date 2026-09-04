---
id: S052
type: story
status: planned
parent_epic: E006
parent_feature: F026
depends_on: [S051]
owned_paths: [crates/domain/src/sso/**, crates/persistence/src/sso/**, services/api/src/sso/**, apps/web/src/features/sso/**, testing/features/F026/**]
feature_flag: F026_FEATURE
branch: s052-lifecycle-sync
started_at: null
finished_at: null
---

# S052 — Lifecycle sync

## Identity

- Parent feature: `F026` SSO/SCIM
- Owner: platform
- Branch: `s052-lifecycle-sync`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4; `docs/capability-contracts.md` row F026

## Vertical slice

As a tenant administrator, I want SCIM suspension to lock a leaver out and hand their work to a named owner, and I want identity-provider groups to drive OpsHub roles, so that joiners, movers, and leavers are handled by the directory rather than by hand, with the whole path proven by negative and load tests.

## Requirements

- **SR-S052-01:** `PATCH /scim/v2/Users/{id}` with `active: false` revokes F038 sessions, refresh tokens, and API tokens, keeps shares, and transfers owned sheets, workspaces, dashboards, and workflows to `ownership_transfer_to` or the primary admin, one `ownership.transferred` audit event per object (covers FR-F026-11).
- **SR-S052-02:** `active: true` reinstates the user without moving ownership back; `DELETE /scim/v2/Users/{id}` deactivates and returns 204, then 404 on repeat (FR-F026-11, FR-F026-12).
- **SR-S052-03:** `group_mappings` map a SCIM group `external_id` or `display_name` to roles, one `group_mapping_roles` row per role; group member add/remove/replace recomputes mapped role bindings in the same request through `GroupMappingRepository::replace_mapping_roles` and never removes manual bindings (FR-F026-14).
- **SR-S052-04:** Every user and group sync writes a `scim_sync_log` row with outcome `applied`, `partial`, or `failed` and publishes `scim.user-synced.v1` or `scim.group-synced.v1` (FR-F026-13, NFR-F026-04).
- **SR-S052-05:** `GroupMappingEditor` on the connection's `Provisioning` tab lets an admin add, edit, and remove mappings and shows the last sync outcome per group (FR-F026-16).
- **SR-S052-06:** A foreign-tenant SCIM token, a revoked token, and a member without `tenant-admin` are all refused on every SCIM and connection route (NFR-F026-02).
- **SR-S052-07:** A group PATCH with 500 members completes in under 2 s and a suspension with 40 owned objects completes within the 5 s budget (NFR-F026-01).

## Surfaces

- Infrastructure/container: none
- Data access: `crates/persistence/src/sso/{mapping_repository.rs, sync_log_repository.rs}`; suspension and role recomputation run in one `UnitOfWork` that also holds the F002 `UserRepository` and F003 `RoleBindingRepository`, and the SCIM handlers issue no SQL of their own (decision section 2.1)
- Rust service/API: `crates/domain/src/sso/{lifecycle.rs, ownership.rs, mapping.rs, scim/users.rs, scim/groups.rs}`; `services/api/src/sso/{handlers_scim.rs, handlers_mapping.rs}`
- Data/migration: none new; uses `group_mappings`, `group_mapping_roles`, and `scim_sync_log` from S051
- React/UI: `apps/web/src/features/sso/{GroupMappingEditor.tsx, SyncLogTable.tsx, ProvisioningTab.tsx}`
- Mocks/fixtures: `testing/fixtures/sso.rs` seeds Ben with 3 sheets, 1 workspace, 1 dashboard, 1 workflow; 500-member group generator; MSW handlers for component tests

## TDD harness

- Test path: `testing/features/F026/{api,database,frontend,e2e,accessibility,performance}/`
- Feature flag: `F026_FEATURE`
- Targeted command: `cargo xtask test-feature F026`
- Full command: `cargo xtask test-all`
- First failing tests: `scim_suspend_revokes_sessions_and_transfers_ownership`, `scim_reinstate_keeps_transferred_ownership`, `group_mapping_assigns_and_removes_roles`, `group_mapping_preserves_manual_bindings`, `scim_foreign_tenant_token_not_found`, `scim_group_patch_500_members_p95`

## Exit criteria

- [ ] Requirement tests SR-S052-01 through SR-S052-07 written first and failing
- [ ] Tasks T103 and T104 complete; mapping UI wired to real API through generated client
- [ ] Unit, API, database, React, E2E, permission, accessibility, and performance tests pass
- [ ] Production call path named: `services/api/src/sso/handlers_scim.rs` mounted at `/scim/v2` via `services/api/src/sso/routes.rs` in `services/api/src/router.rs`
- [ ] Handoff evidence recorded in the F026 ticket
