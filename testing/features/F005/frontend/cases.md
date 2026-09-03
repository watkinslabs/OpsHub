# F005 frontend cases

File: `testing/features/F005/frontend/{WorkspaceList.test.tsx,WorkspaceShell.test.tsx,NewWorkspaceDialog.test.tsx,FolderTree.test.tsx,MembersDialog.test.tsx,MoveFolderDialog.test.tsx}`. Vitest with MSW. Flag `F005_FEATURE`.

- `renders_member_workspaces` — FR-F005-15: fixture of 3 workspaces renders 3 cards sorted by name with the trash toggle hiding the deleted one.
- `shows_empty_state_with_new_workspace` — FR-F005-15: empty list shows the `New workspace` call to action.
- `shows_error_banner_with_correlation_id` — NFR-F005-04: 500 response shows banner containing `correlation_id` and retry.
- `validates_name_length` — FR-F005-01: empty and 121-char names block submit with inline text.
- `shows_duplicate_name_field_error` — FR-F005-02: 409 with `field_errors.name` renders under the name input.
- `hides_admin_controls_for_viewer` — FR-F005-15: `my_role: viewer` hides `Members`, `New folder`, `Delete workspace`, and move handles.
- `shows_not_found_for_non_member` — FR-F005-14: 404 renders the not-found page.
- `rename_conflict_shows_stale_banner` — FR-F005-04: PATCH 409 shows `This workspace changed` with `Reload`.
- `offline_disables_mutations` — FR-F005-15: `navigator.onLine=false` shows the offline badge and disables dialogs.
- `tree_renders_nested_nodes_with_aria` — NFR-F005-03: 12-folder tree renders `role="tree"`, `treeitem` with `aria-level` and `aria-expanded`.
- `keyboard_move_calls_api` — FR-F005-09: Space, ArrowDown, Enter on "Q4" calls `moveFolder` with the target parent.
- `move_cycle_rolls_back_with_inline_error` — FR-F005-09: `moveFolder` 400 `cycle` restores the node and shows the inline error.
- `members_dialog_blocks_save_without_owner` — FR-F005-06: removing the last owner disables save and shows `owner_required` text.
- `move_dialog_excludes_self_and_descendants` — FR-F005-09: picker for "Projects" omits "Projects" and "Q4".
- `folder_move_emits_telemetry` — FR-F005-15: successful move emits `folder_moved` with `workspace_id` and `depth`.

Evidence: Vitest JUnit under `testing/evidence/F005/frontend/`.
