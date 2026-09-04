---
id: T019
type: task
status: planned
parent_epic: E002
parent_feature: F005
parent_story: S010
depends_on: [T018]
owned_paths: [crates/domain/src/workspaces/**, services/api/src/workspaces/**, testing/features/F005/api/**, testing/features/F005/requirements/**]
feature_flag: F005_FEATURE
branch: t019-permission-fixtures
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 9
- Capability contract: `docs/capability-contracts.md` row F005

# T019 — Permission fixtures

## Identity

- Parent story: `S010` Membership and folders
- Owner: platform
- Branch: `t019-permission-fixtures`
- Decision references: `docs/architecture-decisions.md` sections 2–4, 9; `docs/capability-contracts.md` row F005

## Objective

Implement the membership, folder, and tree services with the six member/tree/folder routes, and build the role, deny, and cross-tenant fixtures that every permission-negative case in the F005 harness runs against.

## Specification

- Owned paths: `crates/persistence/src/workspaces/{folder_repository.rs, workspace_repository.rs}` extended with the named queries `load_tree`, `ancestors`, and `soft_delete_subtree`, `crates/domain/src/workspaces/{folder.rs, path.rs, tree.rs, service_members.rs, service_folders.rs}`, `services/api/src/workspaces/{handlers_member.rs, handlers_folder.rs, handlers_tree.rs}`, `testing/features/F005/api/{member_tests.rs, folder_tests.rs, tree_tests.rs, permission_tests.rs}`, `testing/features/F005/requirements/cases.md`
- Contract/input: `ReplaceMembersRequest { members: [{ subject_kind, subject_id, role }] }` (≤ 500 entries), `CreateFolderRequest { workspace_id, name, parent_folder_id?, after_folder_id? }`, `UpdateFolderRequest { name? }`, `MoveFolderRequest { parent_folder_id?, after_folder_id? }`; headers `Idempotency-Key`, `If-Match`; fixture matrix in `testing/fixtures/workspaces.rs`: tenant A owner, admin, editor, commenter, viewer, group member, non-member, tenant B actor, and one folder with an explicit F003 deny for the editor.
- Output/behavior: routes `PUT /api/v1/workspaces/{id}/members`, `GET /api/v1/workspaces/{id}/tree`, `POST /api/v1/folders`, `PATCH /api/v1/folders/{id}`, `POST /api/v1/folders/{id}/move`, `DELETE /api/v1/folders/{id}` return `MemberResponse[]`, `FolderTreeResponse { tree_version, roots }`, and `FolderResponse { id, workspace_id, parent_folder_id, name, path, depth, position, version, deleted_at }`; `path.rs` builds and rewrites materialized paths and rejects cycles using `FolderRepository::ancestors` before the trigger fires; `service_members.rs` calls `WorkspaceRepository` to lock the workspace row, enforces at least one `owner`, and rejects duplicate subjects; folder delete calls `FolderRepository::soft_delete_subtree`, which also clears any `workspace_settings.default_folder_id` pointing into the subtree; `tree.rs` walks the `load_tree` result once, applying denies fetched in one query; every service, handler, and test here calls repository traits and contains no SQL (decision 2.1); events `workspace-member.updated.v1`, `folder.updated.v1`, `folder.moved.v1`; errors map per ticket section 4.
- Dependencies: T017 schema, repositories, workspace service, and router; F003 ACL lookup `authz::denies_for(actor, ResourceKind::Folder, workspace)`.
- Feature flag: `F005_FEATURE`

## TDD

- Failing test first: `testing/features/F005/api/member_tests.rs::members_replace_requires_owner`, `::members_replace_rejects_duplicate_subject`, `::members_replace_emits_event`; `folder_tests.rs::folder_move_into_descendant_rejected`, `::folder_move_rewrites_descendant_paths`, `::folder_depth_eleven_invalid`, `::folder_delete_cascades_descendants`, `::folder_delete_nulls_default_folder_setting`; `tree_tests.rs::tree_hides_denied_subtree`, `::tree_etag_matches_tree_version`; `permission_tests.rs::folder_viewer_mutation_denied`, `::folder_cross_tenant_not_found`, `::non_member_tree_not_found`
- Targeted command: `cargo xtask test-feature F005`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/workspaces.rs` role matrix and 12-folder seeded tree; real F003 engine with fixture bindings; in-memory outbox recorder

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Every role in the fixture matrix has a positive and a negative case in the api lane
- [ ] `cargo xtask check-persistence` passes: the new named queries live only in `crates/persistence/src/workspaces/`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S010
- [ ] `finished_at` recorded
