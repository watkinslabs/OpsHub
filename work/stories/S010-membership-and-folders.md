---
id: S010
type: story
status: planned
parent_epic: E002
parent_feature: F005
depends_on: [S009]
owned_paths: [crates/domain/src/workspaces/**, services/api/src/workspaces/**, apps/web/src/features/workspaces/**, testing/features/F005/**]
feature_flag: F005_FEATURE
branch: s010-membership-and-folders
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 6
- Capability contract: `docs/capability-contracts.md` row F005

# S010 — Membership and folders

## Identity

- Parent feature: `F005` Workspace navigation
- Owner: platform
- Branch: `s010-membership-and-folders`
- Decision references: `docs/architecture-decisions.md` sections 2–4, 6; `docs/capability-contracts.md` row F005

## Vertical slice

As a workspace admin, I want to replace the member set with roles and build, rename, move, and delete a folder tree with inherited access, so that collaborators can navigate a safe hierarchy and later features can mount inside folders.

## Requirements

- **SR-S010-01:** `PUT /api/v1/workspaces/{id}/members` replaces the full member set through `WorkspaceRepository` under `for update`; zero owners returns `400 invalid` with `field_errors.members = "owner_required"`, duplicate subjects return `invalid` with `field_errors.members = "duplicate_subject"`, and success emits `workspace-member.updated.v1` (FR-F005-06, FR-F005-13).
- **SR-S010-02:** `POST /api/v1/folders` creates a folder with materialized `path`, `depth` ≤ 10, and fractional `position`; depth 11 returns `invalid` with `field_errors.parent_folder_id = "max_depth"`; sibling name clash returns `conflict` (FR-F005-08).
- **SR-S010-03:** `POST /api/v1/folders/{id}/move` rejects self and descendant targets with `invalid` and `field_errors.parent_folder_id = "cycle"`; success rewrites descendant paths in one statement, bumps `tree_version`, and emits `folder.moved.v1` (FR-F005-09).
- **SR-S010-04:** `PATCH /api/v1/folders/{id}` renames with `If-Match` and emits `folder.updated.v1`; `DELETE /api/v1/folders/{id}` runs `FolderRepository::soft_delete_subtree` to soft-delete the folder and its descendants and nulls any `workspace_settings.default_folder_id` pointing at them (FR-F005-10).
- **SR-S010-05:** `GET /api/v1/workspaces/{id}/tree` reads through the `FolderRepository` named query `load_tree` and returns nested nodes ordered by `position` with `ETag` equal to `tree_version`, omits deleted folders, and omits subtrees under an explicit F003 deny for the actor (FR-F005-07, FR-F005-11).
- **SR-S010-06:** Viewers and commenters receive `403 denied` on folder and member mutations; non-members and cross-tenant actors receive `404 not_found` on folder routes (FR-F005-14, NFR-F005-02).
- **SR-S010-07:** `FolderTree`, `MembersDialog`, and `MoveFolderDialog` support mouse and keyboard, announce moves through a live region, roll back on `conflict` or `invalid`, and hide mutation controls for viewers (FR-F005-15, NFR-F005-03).
- **SR-S010-08:** A 2,000-folder tree read and folder move meet NFR-F005-01.

## Surfaces

- Infrastructure/container: none
- Rust service/API: `crates/domain/src/workspaces/{folder.rs, path.rs, service_members.rs, service_folders.rs, tree.rs}`; `services/api/src/workspaces/{handlers_member.rs, handlers_folder.rs, handlers_tree.rs}`; `folders` is reached only through `FolderRepository` and members only through `WorkspaceRepository` (`crates/persistence/src/workspaces/`), whose named queries `load_tree`, `ancestors`, and `soft_delete_subtree` carry the tree read, cycle check, and cascade, so these use cases, handlers, and tests hold no SQL (decision 2.1)
- Data/migration: none new; uses `workspaces`, `workspace_settings`, `workspace_members`, and `folders` with their triggers from S009
- React/UI: `apps/web/src/features/workspaces/{FolderTree.tsx, FolderTreeItem.tsx, MembersDialog.tsx, MoveFolderDialog.tsx}`
- Mocks/fixtures: seeded workspace with a 3-level tree of 12 folders and one folder deny; 2,000-folder generator for the performance lane; MSW handlers for component tests; Playwright seeded tenant

## TDD harness

- Test path: `testing/features/F005/{api,frontend,e2e,accessibility,performance}/`
- Feature flag: `F005_FEATURE`
- Targeted command: `cargo xtask test-feature F005`
- Full command: `cargo xtask test-all`
- First failing tests: `members_replace_requires_owner`, `folder_move_into_descendant_rejected`, `folder_move_rewrites_descendant_paths`, `tree_hides_denied_subtree`, `folder_delete_nulls_default_folder_setting`, `folder_viewer_mutation_denied`, `FolderTree.test.tsx::keyboard_move_calls_api`, `tree_2000_folders_p95`

## Exit criteria

- [ ] Requirement tests SR-S010-01 through SR-S010-08 written first and failing
- [ ] Tasks T019 and T020 complete; UI wired to the real API through the generated client
- [ ] Unit, API, React, E2E, accessibility, permission, and performance tests pass
- [ ] Production call path named: `apps/web/src/features/workspaces/FolderTree.tsx` rendered by `WorkspaceShell.tsx` at `/w/:workspaceId` and `/w/:workspaceId/folders/:folderId`
- [ ] Handoff evidence recorded in the F005 ticket
