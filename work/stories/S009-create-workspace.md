---
id: S009
type: story
status: planned
parent_epic: E002
parent_feature: F005
depends_on: [F003, F004]
owned_paths: [crates/domain/src/workspaces/**, services/api/src/workspaces/**, apps/web/src/features/workspaces/**, services/api/migrations/*_workspaces_*.sql, testing/features/F005/**]
feature_flag: F005_FEATURE
branch: s009-create-workspace
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 6
- Capability contract: `docs/capability-contracts.md` row F005

# S009 — Create workspace

## Identity

- Parent feature: `F005` Workspace navigation
- Owner: platform
- Branch: `s009-create-workspace`
- Decision references: `docs/architecture-decisions.md` sections 2–4, 6; `docs/capability-contracts.md` row F005

## Vertical slice

As a tenant user, I want to create, list, open, rename, soft-delete, and restore a workspace and see it in a workspace list and shell, so that my team has a governed container before any folder, member change, or sheet exists.

## Requirements

- **SR-S009-01:** `POST /api/v1/workspaces` with `{ name, description? }` inserts `workspaces` and one `owner` row in `workspace_members` for the creator in one transaction and returns `WorkspaceResponse` with version 1 (covers FR-F005-01).
- **SR-S009-02:** A case-insensitive duplicate name among non-deleted workspaces in the tenant returns `409 conflict` with `field_errors.name = "taken"` (FR-F005-02).
- **SR-S009-03:** `GET /api/v1/workspaces` returns only workspaces the actor belongs to or administers, pages by opaque cursor with `limit` ≤ 100, filters by `name` prefix and `deleted`, sorts by `name` or `updated_at` (FR-F005-03).
- **SR-S009-04:** `PATCH /api/v1/workspaces/{id}` requires `If-Match`; a stale version returns `409 conflict` with `current_version` and no write (FR-F005-04).
- **SR-S009-05:** `DELETE` sets `deleted_at` on the workspace and its folders; `POST /restore` within retention clears both and keeps IDs; after retention returns `404 not_found` (FR-F005-05).
- **SR-S009-06:** Every mutation checks `Idempotency-Key`, writes an audit event, and enqueues `workspace.created.v1`, `workspace.updated.v1`, `workspace.deleted.v1`, or `workspace.restored.v1` in the same transaction (FR-F005-12, FR-F005-13).
- **SR-S009-07:** Cross-tenant and non-member actors receive `404 not_found` on every workspace route (FR-F005-14).
- **SR-S009-08:** `WorkspaceList` and `WorkspaceShell` render the list, the empty shell, and loading, empty, error, denied, stale, and offline states; `NewWorkspaceDialog` validates name length and shows `field_errors.name` (FR-F005-15, NFR-F005-03).

## Surfaces

- Infrastructure/container: none beyond F004 baseline
- Rust service/API: `crates/domain/src/workspaces/{workspace.rs, member.rs, errors.rs, service_workspace.rs}`; `services/api/src/workspaces/{routes.rs, handlers_workspace.rs, dto.rs}`
- Data/migration: `services/api/migrations/<ts>_workspaces_create_tables.sql` creating `workspaces`, `workspace_members`, `folders` with indexes and the cycle trigger from ticket section 4
- React/UI: `apps/web/src/features/workspaces/{WorkspaceList.tsx, WorkspaceShell.tsx, NewWorkspaceDialog.tsx, WorkspaceTrash.tsx, api.ts, hooks.ts, routes.ts}`
- Mocks/fixtures: `testing/fixtures/workspaces.rs` tenant A/B, owner, admin, editor, viewer, non-member builders; in-memory outbox recorder; MSW handlers for component tests

## TDD harness

- Test path: `testing/features/F005/{api,database,frontend}/`
- Feature flag: `F005_FEATURE`
- Targeted command: `cargo xtask test-feature F005`
- Full command: `cargo xtask test-all`
- First failing tests: `workspace_create_returns_version_one_and_owner`, `workspace_duplicate_name_conflicts`, `workspace_list_only_member_workspaces`, `workspace_stale_version_conflicts`, `workspace_restore_keeps_ids_and_folders`, `workspace_cross_tenant_not_found`, `WorkspaceList.test.tsx::renders_member_workspaces`

## Exit criteria

- [ ] Requirement tests SR-S009-01 through SR-S009-08 written first and failing
- [ ] Tasks T017 and T018 complete and wired through `services/api` router and the web route tree
- [ ] Unit, API, database, React, permission tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/workspaces/routes.rs` mounted in `services/api/src/router.rs`; `apps/web/src/features/workspaces/WorkspaceShell.tsx` mounted at `/w/:workspaceId`
- [ ] Handoff evidence recorded in the F005 ticket
