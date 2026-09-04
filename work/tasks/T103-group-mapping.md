---
id: T103
type: task
status: planned
parent_epic: E006
parent_feature: F026
parent_story: S052
depends_on: [S052]
owned_paths: [crates/domain/src/sso/**, crates/persistence/src/sso/**, services/api/src/sso/**, apps/web/src/features/sso/**, testing/features/F026/api/**, testing/features/F026/frontend/**]
feature_flag: F026_FEATURE
branch: t103-group-mapping
started_at: null
finished_at: null
---

# T103 — Group mapping

## Identity

- Parent story: `S052` Lifecycle sync
- Owner: platform
- Branch: `t103-group-mapping`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 4; `docs/capability-contracts.md` row F026

## Objective

Implement suspended-user behavior with ownership transfer, group-to-role mapping that recomputes role bindings on every SCIM group change, and the mapping editor and sync-log UI.

## Specification

- Owned paths: `crates/domain/src/sso/{lifecycle.rs, ownership.rs, mapping.rs}`, `crates/persistence/src/sso/mapping_repository.rs`, `services/api/src/sso/handlers_mapping.rs`, `apps/web/src/features/sso/{GroupMappingEditor.tsx, SyncLogTable.tsx}`
- Contract/input: `UpdateConnectionRequest.group_mappings: [ { external_id?, display_name?, role_ids } ]` (at least one of `external_id`/`display_name`, 1–10 roles each, max 200 mappings) — the request keeps the `role_ids` array, `GroupMappingRepository::replace_mapping_roles` stores it as `group_mapping_roles` rows, and the response reassembles the array so the API is unchanged; SCIM `PATCH Users { active }` and `PATCH Groups { Operations }` from T102.
- Output/behavior: `lifecycle::suspend(user)` revokes sessions, refresh tokens, and API tokens through F038, keeps shares, and calls `ownership::transfer_all(from, to)` which reassigns `owner_id` on sheets, workspaces, dashboards, and workflows in one transaction with a 5 s budget, writing `ownership.transferred` per object and `scim_sync_log.outcome = partial` with the remaining IDs when the budget is exceeded; `lifecycle::reinstate` sets `active` without touching ownership; `mapping::apply(connection, group, members)` computes the role set from all mappings for the user's current mapped groups, reads the role set with `GroupMappingRepository::list_mappings_for_external_id` joined to `group_mapping_roles`, inserts F003 `role_bindings` with `source = 'scim:<mapping_id>'` through `RoleBindingRepository`, deletes only bindings with that source prefix that are no longer implied, and publishes `scim.group-synced.v1`; the editor lists mappings with role pickers and shows last sync outcome from `scim_sync_log`.
- Dependencies: T102 SCIM handlers; F003 `role_bindings` with `source` column and `authz::rebind`; F038 revocation; F005/F006/F018/F023 owner columns.
- Data access: `lifecycle.rs`, `ownership.rs`, and `mapping.rs` hold no SQL; ownership transfer runs one `UnitOfWork` over the F005/F006/F018/F023 repositories, and the sync-log row is appended by `ScimSyncLogRepository::append_sync_entry` (decision section 2.1).
- Feature flag: `F026_FEATURE`

## TDD

- Failing test first: `testing/features/F026/api/lifecycle_tests.rs::scim_suspend_revokes_sessions_and_transfers_ownership`, `::scim_suspend_defaults_transfer_to_primary_admin`, `::scim_reinstate_keeps_transferred_ownership`, `::scim_suspend_over_budget_marks_partial`; `testing/features/F026/api/mapping_tests.rs::group_mapping_assigns_and_removes_roles`, `::group_mapping_preserves_manual_bindings`, `::group_mapping_limits_enforced`; `testing/features/F026/frontend/GroupMappingEditor.test.tsx::adds_mapping_with_role_picker`
- Targeted command: `cargo xtask test-feature F026`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: Ben with 3 sheets, 1 workspace, 1 dashboard, 1 workflow; groups `opshub-admins`, `pmo`, `viewers`; MSW handlers for the editor

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Suspension and mapping paths emit audit and outbox events verified in tests
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S052
- [ ] `finished_at` recorded
