---
id: F005
type: feature
status: planned
priority: P0
owner: platform
estimate: 5
target_milestone: M1
parent_epic: E002
depends_on: [F003, F004]
blocks: [F006, F036, F045, F049]
conflicts_with: []
parallel_safe: true
owned_paths: [crates/persistence/src/workspaces/**, crates/domain/src/workspaces/**, services/api/src/workspaces/**, apps/web/src/features/workspaces/**, services/api/migrations/*_workspaces_*.sql, testing/features/F005/**]
feature_flag: F005_FEATURE
flag_default: off
branch: f005-workspace-navigation
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 6
- Capability contract: `docs/capability-contracts.md` row F005

# F005 — Workspace navigation

## 1. Identity and dates

- Branch: `f005-workspace-navigation`
- Capability area: core work record engine (spec 5.1 WORK-01, section 4 entity Workspace, 5.4a DOC-01 folder hierarchy rules, 5.8 SEC tenant isolation)
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 6; `docs/capability-contracts.md` row F005
- Module slug: `workspaces`

## 2. Requirement specification

### Problem and user outcome

A tenant has users and groups but no place to put work. Teams need a workspace that holds members and a folder tree so that sheets, reports, dashboards, and documents can be created inside a governed container with inherited access. Every later feature mounts under a workspace, so its identity, membership, and folder hierarchy must be stable, tenant-isolated, and recoverable.

As a workspace admin, I want to create a workspace, manage its members and roles, and organize a folder tree with safe moves and trash recovery, so that my team's work has a navigable home before any sheet exists.

### Functional requirements

- **FR-F005-01:** An authenticated tenant user can create a workspace with `name` (1–120 chars) and optional `description` (≤ 2,000 chars); the response returns a UUIDv7 `id`, `version` 1, and the creator as the single `owner` member.
- **FR-F005-02:** Workspace names are unique per tenant (case-insensitive) among non-deleted workspaces; a duplicate returns `409 conflict` with `field_errors.name = "taken"`.
- **FR-F005-03:** `GET /api/v1/workspaces` returns only workspaces where the actor is a member or holds a tenant-admin role, pages by opaque cursor with `limit` 1–100, filters by `name` prefix and `deleted=true|false`, and sorts by `name` or `updated_at`.
- **FR-F005-04:** `PATCH /api/v1/workspaces/{id}` updates `name`, `description`, and the workspace's one `workspace_settings` row (`default_folder_id`, which is a real foreign key to `folders`, and `icon`) with `If-Match` in the same transaction; a stale version returns `409 conflict` with `current_version` and writes nothing.
- **FR-F005-05:** `DELETE /api/v1/workspaces/{id}` soft-deletes the workspace and hides its folders from every list, tree, and read; `POST /api/v1/workspaces/{id}/restore` within the tenant retention window restores the workspace and its folders with original IDs; restore after the window returns `404 not_found`.
- **FR-F005-06:** `PUT /api/v1/workspaces/{id}/members` replaces the full member set with `[{ subject_kind: user|group, subject_id, role }]` where `role` is `owner|admin|editor|commenter|viewer`; a set with zero owners returns `400 invalid` with `field_errors.members = "owner_required"`, and duplicate subjects return `invalid` with `field_errors.members = "duplicate_subject"`.
- **FR-F005-07:** `GET /api/v1/workspaces/{id}/tree` returns the non-deleted folder tree as nested `{ id, name, parent_folder_id, depth, position, children }` ordered by `position`, limited to 2,000 folders per workspace, with `ETag` equal to the workspace tree version.
- **FR-F005-08:** `POST /api/v1/folders` creates a folder with `workspace_id`, `name` (1–120 chars), optional `parent_folder_id`, and optional `after_folder_id`; depth greater than 10 returns `400 invalid` with `field_errors.parent_folder_id = "max_depth"`, and a sibling name clash (case-insensitive) returns `409 conflict`.
- **FR-F005-09:** `POST /api/v1/folders/{id}/move` changes `parent_folder_id` and/or `position`; moving a folder into itself or one of its descendants returns `400 invalid` with `field_errors.parent_folder_id = "cycle"`, and a successful move rewrites the materialized `path` of every descendant in one transaction and emits `folder.moved.v1`.
- **FR-F005-10:** `DELETE /api/v1/folders/{id}` soft-deletes the folder and its descendants and records `deleted_at` on each; contents remain restorable through the parent workspace restore and the F027 purge job, and a deleted folder is never returned by the tree.
- **FR-F005-11:** Folder access inherits downward from the workspace membership; an explicit resource ACL deny on a folder (F003) hides that folder and its subtree from the tree for the denied subject, and explicit deny wins over any inherited grant.
- **FR-F005-12:** Every mutation requires `Idempotency-Key`; replaying the same key with the same body returns the original response and performs no second write, while the same key with a different body returns `409 conflict`.
- **FR-F005-13:** Every mutation writes an `audit_events` row with actor, action, before/after diff, and correlation ID and publishes the matching `workspace.*.v1`, `workspace-member.updated.v1`, or `folder.*.v1` event through the outbox in the same transaction.
- **FR-F005-14:** Cross-tenant access to any workspace or folder by ID returns `404 not_found`, never `denied`, and a non-member of an existing workspace also receives `404 not_found` on reads.
- **FR-F005-15:** The web app renders a workspace list, a workspace shell with a sidebar folder tree and content outlet, and dialogs for new workspace, members, and folder move; viewers see the tree read-only with denied affordances hidden.

### Non-functional requirements

- **NFR-F005-01 Performance:** `GET /tree` on a workspace with 2,000 folders responds in under 500 ms p95 with a warm cache; workspace and folder writes respond in under 800 ms p95 (spec section 6).
- **NFR-F005-02 Security/privacy:** tenant isolation is enforced by a `tenant_id` predicate on every query and in the service layer; membership and ACL negatives (non-member, viewer mutation, guest, cross-tenant, folder deny) are executable harness cases.
- **NFR-F005-03 Accessibility:** the folder tree uses `role="tree"`, `treeitem`, and `group` with `aria-expanded` and `aria-level`; every action is keyboard reachable; axe reports zero serious or critical violations; WCAG 2.2 AA.
- **NFR-F005-04 Reliability/observability:** every request carries a tracing span with `tenant_id`, `workspace_id`, and `correlation_id`; a failed outbox insert rolls back the write; tree rebuild failures surface in `folder_path_rewrite_failures_total`.

### Scope

Included: workspace CRUD, soft delete and restore, membership replacement with role validation, folder create/rename/move/delete with materialized path and cycle detection, tree read with inherited access and explicit denies, idempotency, optimistic concurrency, audit, outbox events, workspace list and shell UI, folder tree UI.

Excluded: sheets and rows (F006), sharing links and guests (F036), documents inside folders (F045), locale settings (F049), tenant and group administration (F002), ACL editing UI (F003), purge (F027).

## 3. UX specification

- Entry points: top navigation `Workspaces` at `/w`; `New workspace` button on the list; sidebar `New folder` and folder context menu `Rename`, `Move`, `Delete`; workspace header menu `Members`, `Delete workspace`; trash section `Restore`.
- Primary flow: open `/w`, click `New workspace`, enter name, submit, land on `/w/{id}` with an empty tree and `Create your first folder` call to action; add folder `Projects`, add child `Q4`, drag `Q4` to root, tree re-renders with the API version; open `Members`, add a group as `editor`, save, toast confirms.
- Loading: skeleton list rows and a skeleton tree; Empty: illustration with `New workspace` or `New folder`; Error: inline banner with `correlation_id` and retry; Success: toast on create, move, restore, and members save; Stale/conflict: banner `This workspace changed` with `Reload`; Offline: mutations disabled with an offline badge.
- Permission-denied: viewers and commenters see no create, move, delete, or members controls; a `denied` response shows an inline explanation; non-members and cross-tenant IDs render the not-found page.
- Responsive: sidebar collapses to a drawer under 1,024 px; tree drawer is full-height under 640 px with a close button.
- Keyboard: arrow keys move focus in the tree, `Right` expands, `Left` collapses, `Enter` opens, `F2` renames, `Space` picks up a folder for move, arrows choose the target, `Enter` drops, `Escape` cancels; moves are announced through a live region; motion respects `prefers-reduced-motion`.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062); Lucide icons `Folder`, `FolderOpen`, `FolderPlus`, `Users`, `Move`, `RotateCcw`, `Trash2`; spacing and color from `apps/web/src/design/tokens.css`.

- Design: `design/artboards/Workspace.dc.html` on the canvas indexed by `design/canvas.json`. The ticket is the contract and the artboard is the picture; when they disagree the ticket wins.

## 4. Technical specification

Canonical contract: `docs/capability-contracts.md` row F005 (aggregate `workspace`, module `workspaces`, roles `workspace-admin`).

### Rust backend

- Domain entities in `crates/domain/src/workspaces/`: `Workspace { id, tenant_id, name, description, version, created/updated actor+time, deleted_at }`, `WorkspaceSettings { workspace_id, default_folder_id: Option<FolderId>, icon, updated_by, updated_at }` loaded and saved with its workspace, `WorkspaceMember { workspace_id, subject_kind: SubjectKind, subject_id, role: WorkspaceRole }`, `Folder { id, tenant_id, workspace_id, parent_folder_id, name, path: FolderPath, depth: u8, position: FracIndex, version, deleted_at }`, `FolderTree { version, roots: Vec<FolderNode> }`.
- Data access (decision 2.1): `WorkspaceRepository` (`workspaces`, `workspace_settings`, `workspace_members`) and `FolderRepository` (`folders`) in `crates/persistence/src/workspaces/`; each table is written by exactly one of them. The use cases below depend on those repository traits and the shared `UnitOfWork`, so `crates/domain/src/workspaces/` and `services/api/src/workspaces/` contain no SQL; the tree read, the cycle check, and the cascade delete are named repository queries (`load_tree`, `ancestors`, `soft_delete_subtree`).
- Use cases: `create_workspace`, `update_workspace`, `delete_workspace`, `restore_workspace`, `list_workspaces`, `get_workspace`, `replace_members`, `get_tree`, `create_folder`, `update_folder`, `move_folder`, `delete_folder`.
- API endpoints (`services/api/src/workspaces/`): `GET /api/v1/workspaces`, `POST /api/v1/workspaces`, `GET /api/v1/workspaces/{id}`, `PATCH /api/v1/workspaces/{id}`, `DELETE /api/v1/workspaces/{id}`, `POST /api/v1/workspaces/{id}/restore`, `PUT /api/v1/workspaces/{id}/members`, `GET /api/v1/workspaces/{id}/tree`, `POST /api/v1/folders`, `PATCH /api/v1/folders/{id}`, `POST /api/v1/folders/{id}/move`, `DELETE /api/v1/folders/{id}`. DTOs: `CreateWorkspaceRequest`, `UpdateWorkspaceRequest`, `ReplaceMembersRequest`, `CreateFolderRequest`, `UpdateFolderRequest`, `MoveFolderRequest`; responses `WorkspaceResponse`, `MemberResponse`, `FolderResponse`, `FolderTreeResponse`, `Page<WorkspaceResponse>`.
- Events: `workspace.created.v1`, `workspace.updated.v1`, `workspace.deleted.v1`, `workspace.restored.v1`, `workspace-member.updated.v1`, `folder.updated.v1`, `folder.moved.v1`; payload per contract conventions with `changed_fields`.
- Authorization: `workspace-admin` (member role `owner` or `admin`, or tenant-admin) for workspace update, delete, restore, and member replacement; `editor` or above for folder mutations; any member for reads; folder reads additionally consult F003 resource ACLs with explicit deny winning; non-member and cross-tenant map to `not_found`.
- Validation: names 1–120 chars trimmed, description ≤ 2,000 chars, member set ≤ 500 entries with at least one `owner`, folder depth ≤ 10, folders per workspace ≤ 2,000, `limit` 1–100. Idempotency via `idempotency_keys(tenant_id, key, request_hash, response)` for 24 hours, written by the shared `IdempotencyKeyRepository` of the base contract rather than by this feature's repositories. Concurrency: `If-Match` compared inside the update transaction.
- Error mapping: `WorkspaceError::NameTaken → 409 conflict`, `WorkspaceError::StaleVersion → 409 conflict`, `WorkspaceError::OwnerRequired → 400 invalid`, `FolderError::Cycle → 400 invalid`, `FolderError::MaxDepth → 400 invalid`, `FolderError::SiblingNameTaken → 409 conflict`, `NotFound → 404 not_found`, `AuthzError::Denied → 403 denied`, validation → `400 invalid` with `field_errors`.

### PostgreSQL/SQLx

- Migration `*_workspaces_*.sql` creates `workspaces(id uuid pk, tenant_id uuid not null, name text not null, description text, tree_version bigint not null default 1, version bigint not null default 1, created_by, created_at, updated_by, updated_at, deleted_at)`, `workspace_settings(workspace_id uuid primary key references workspaces(id) on delete cascade, tenant_id uuid not null, default_folder_id uuid null references folders(id) on delete set null, icon text, updated_by uuid, updated_at timestamptz not null)` — typed columns instead of a `jsonb` blob, so the default folder is a declared foreign key that cannot dangle and the icon is constrained, `workspace_members(tenant_id, workspace_id, subject_kind text check (subject_kind in ('user','group')), subject_id uuid, role text check (role in ('owner','admin','editor','commenter','viewer')), created_by, created_at, primary key (workspace_id, subject_kind, subject_id))`, `folders(id uuid pk, tenant_id uuid not null, workspace_id uuid not null, parent_folder_id uuid null references folders(id) on delete restrict, name text not null, path text not null, depth smallint not null check (depth between 1 and 10), position text not null, version bigint not null default 1, audit fields, deleted_at)`.
- Invariants: a trigger on `workspaces` insert creates the matching `workspace_settings` row with `default_folder_id` null and no icon, which is exactly what the empty settings object meant; `workspace_settings.default_folder_id` must belong to the same workspace (trigger `workspace_settings_folder_scope`) and is set null when that folder is deleted; unique partial index `workspaces_tenant_name_idx on (tenant_id, lower(name)) where deleted_at is null`; unique partial index `folders_sibling_name_idx on (workspace_id, coalesce(parent_folder_id, '00000000-0000-0000-0000-000000000000'), lower(name)) where deleted_at is null`; `path` is a `/`-joined chain of ancestor IDs ending in the folder ID; a trigger `folders_check_cycle` rejects a `parent_folder_id` whose path contains the moving folder's ID; owner presence is checked in the service transaction with `select ... for update` on the workspace row.
- Indexes: `workspace_settings(default_folder_id) where default_folder_id is not null` so deleting a folder can find the settings rows pointing at it, `folders(workspace_id, path text_pattern_ops) where deleted_at is null`, `folders(parent_folder_id, position) where deleted_at is null`, `workspace_members(subject_kind, subject_id)`, `workspaces(tenant_id, updated_at desc)`.
- Audit events: `workspace.create`, `workspace.update`, `workspace.delete`, `workspace.restore`, `workspace.members.replace`, `folder.create`, `folder.update`, `folder.move`, `folder.delete` with field-level diffs.
- Retention/deletion: soft delete sets `deleted_at` on the workspace and cascades `deleted_at` to folders in one statement; restore clears both; purge job from F027 removes rows past tenant retention; migration rollback drops the four tables and the triggers (no data before this feature).

### React/TypeScript

- Routes: `/w`, `/w/:workspaceId`, `/w/:workspaceId/folders/:folderId` in `apps/web/src/features/workspaces/`; components `WorkspaceList`, `WorkspaceShell` (sidebar tree plus outlet), `FolderTree`, `FolderTreeItem`, `NewWorkspaceDialog`, `MembersDialog`, `MoveFolderDialog`, `WorkspaceTrash`.
- State: TanStack Query keys `['workspaces']`, `['workspace', id]`, `['workspace-tree', id]`; mutations invalidate by key and store the returned `version` and `tree_version`.
- API client: generated `WorkspacesApi` from OpenAPI with `listWorkspaces`, `createWorkspace`, `updateWorkspace`, `deleteWorkspace`, `restoreWorkspace`, `replaceMembers`, `getTree`, `createFolder`, `updateFolder`, `moveFolder`, `deleteFolder`.
- Optimistic updates: folder move applies locally, rolls back on `conflict` or `invalid` (cycle) and shows the stale or inline error state.
- Telemetry: `workspace_created`, `workspace_opened`, `folder_moved`, `members_updated` with `workspace_id` and, for moves, `depth`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F005-01 through FR-F005-15 in `testing/features/F005/requirements/cases.md`
- [ ] Failure/edge-case tests: duplicate workspace name, stale version, member set without owner, folder depth 11, move into descendant, sibling name clash, restore after retention window, idempotent replay with mismatched body
- [ ] Permission-negative and tenant-isolation tests: cross-tenant read returns `not_found`, non-member read returns `not_found`, viewer mutation returns `denied`, folder ACL deny hides subtree
- [ ] Rust unit tests: `crates/domain/src/workspaces/` path rewrite, cycle detection, role validation, error mapping
- [ ] API contract/integration tests: every route above with success and each error code
- [ ] Database migration/constraint tests: unique name indexes, depth check, cycle trigger, foreign keys, rollback
- [ ] React component tests: `WorkspaceList`, `WorkspaceShell`, `FolderTree`, `MembersDialog`, `MoveFolderDialog` states
- [ ] Browser E2E tests: create workspace, build folder tree, move folder, edit members, restore deleted workspace
- [ ] Accessibility tests: axe on list and shell, keyboard tree navigation and move
- [ ] Performance/load tests: 2,000-folder tree p95 under 500 ms, folder move p95 under 800 ms

### Fast fanout configuration

- Test harness path: `testing/features/F005/`
- Feature flag: `F005_FEATURE`
- Fixture/seed factory: `testing/fixtures/workspaces.rs` builds tenant A, tenant B, owner, admin, editor, viewer, non-member, a group, and a seeded workspace with a 3-level tree of 12 folders
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, UTC
- Mock/stub contracts: outbox publisher recorded in memory; authz uses the real F003 engine with fixture bindings and one folder deny
- Parallel isolation: one schema per test worker, tenant ID per test
- Targeted command: `cargo xtask test-feature F005`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F005/`

## 6. Acceptance criteria

```gherkin
Feature: Workspaces, members, and folders

Scenario: Create a workspace and a nested folder
  Given an authenticated user in tenant A
  When they create workspace "Ops" and folders "Projects" and "Projects/Q4"
  Then the workspace has version 1 with the creator as owner
  And the tree returns "Q4" at depth 2 under "Projects"
  And events workspace.created.v1 and folder.updated.v1 are in the outbox

Scenario: Move into a descendant is rejected
  Given folder "Projects" with child "Q4"
  When an editor moves "Projects" under "Q4"
  Then the response is 400 invalid with field_errors.parent_folder_id "cycle" and no path changes

Scenario: Last owner cannot be removed
  Given workspace "Ops" with one owner
  When an admin replaces members with only editors
  Then the response is 400 invalid with field_errors.members "owner_required"

Scenario: Viewer cannot mutate and non-member cannot see
  Given a viewer member and a non-member of workspace "Ops"
  When the viewer creates a folder and the non-member reads the tree
  Then the viewer receives 403 denied and the non-member receives 404 not_found
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F003 (roles, resource ACLs, audit writer); F004 (outbox, JetStream, tracing); decisions sections 2–4, 6; contracts row F005
- Blocks: F006, F036, F045, F049
- Conflicts with: none (disjoint owned paths)
- External dependencies: none
- Risks and mitigations: materialized path rewrites on a large subtree move can be slow, so the move runs as one `update ... where path like` statement inside the transaction and is benchmarked at 2,000 folders; membership replacement can race with a concurrent role change, so the workspace row is locked with `for update` and `If-Match` is required; ACL deny evaluation on the tree could be quadratic, so denies are fetched in one query and applied during a single tree walk.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F003 and F004 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F005/`
- [ ] Migration file name and owned paths claimed
- [ ] Fixture factory and schema-per-worker isolation available in `testing/harness/`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for every mutation
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F005_FEATURE`, run down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Users can create workspaces, manage members and roles, and organize a folder tree with move, delete, and restore.
- Migration adds `workspaces`, `workspace_members`, and `folders` with a cycle-check trigger; rollback drops them. Feature is off by default behind `F005_FEATURE`.
