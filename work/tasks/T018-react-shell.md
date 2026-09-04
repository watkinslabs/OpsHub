---
id: T018
type: task
status: planned
parent_epic: E002
parent_feature: F005
parent_story: S009
depends_on: [T017]
owned_paths: [apps/web/src/features/workspaces/**, testing/features/F005/frontend/**]
feature_flag: F005_FEATURE
branch: t018-react-shell
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 3, 6
- Capability contract: `docs/capability-contracts.md` row F005

# T018 — React shell

## Identity

- Parent story: `S009` Create workspace
- Owner: platform
- Branch: `t018-react-shell`
- Decision references: `docs/architecture-decisions.md` sections 3, 6; `docs/capability-contracts.md` row F005

## Objective

Build the workspace list, the workspace shell with sidebar and content outlet, the new-workspace dialog, and the trash restore view wired to the real workspace API.

## Specification

- Owned paths: `apps/web/src/features/workspaces/{routes.ts, WorkspaceList.tsx, WorkspaceShell.tsx, WorkspaceHeader.tsx, NewWorkspaceDialog.tsx, WorkspaceTrash.tsx, api.ts, hooks.ts, telemetry.ts}`
- Contract/input: generated `WorkspacesApi` client (`listWorkspaces`, `createWorkspace`, `updateWorkspace`, `deleteWorkspace`, `restoreWorkspace`); TanStack Router routes `/w`, `/w/:workspaceId`, `/w/:workspaceId/folders/:folderId` (the folder route renders the outlet placeholder until T020 adds the tree); query keys `['workspaces']`, `['workspace', id]`.
- Output/behavior: `WorkspaceList` renders paged member workspaces with name-prefix filter and sort, `New workspace` button, and the trash toggle; `NewWorkspaceDialog` validates name 1–120 chars client-side and maps `field_errors.name` to inline text; `WorkspaceShell` renders the header, a sidebar slot, and an outlet, reads `my_role` to hide admin controls for editors, commenters, and viewers, renders the workspace icon from the typed `settings.icon` and opens `settings.default_folder_id` when it is set, and shows loading skeleton, empty call to action, error banner with `correlation_id`, not-found page on 404, stale banner on 409 rename, and offline badge; rename uses `If-Match` from the cached `version`; sidebar collapses to a drawer under 1,024 px; Inter, Lucide icons, and tokens per ticket section 3; telemetry `workspace_created`, `workspace_opened`.
- Dependencies: T017 routes, repositories, and DTOs (the client consumes `WorkspaceResponse.settings` as the typed `{ default_folder_id, icon }` pair from `workspace_settings`, never a free-form object); F001 app shell, router, and flag hook; F003 role context from the gateway.
- Feature flag: `F005_FEATURE` read through the flag hook; routes are not registered when off.

## TDD

- Failing test first: `testing/features/F005/frontend/WorkspaceList.test.tsx::renders_member_workspaces`, `::shows_empty_state_with_new_workspace`, `::shows_error_banner_with_correlation_id`; `NewWorkspaceDialog.test.tsx::validates_name_length`, `::shows_duplicate_name_field_error`; `WorkspaceShell.test.tsx::hides_admin_controls_for_viewer`, `::opens_default_folder_from_settings`, `::shows_not_found_for_non_member`, `::rename_conflict_shows_stale_banner`, `::offline_disables_mutations`
- Targeted command: `cargo xtask test-feature F005`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: MSW handlers from `testing/fixtures/workspaces.rs` JSON export (owner and viewer variants, 3 workspaces, one deleted)

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Component lane passes; routes registered only when the flag is on
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S009
- [ ] `finished_at` recorded
