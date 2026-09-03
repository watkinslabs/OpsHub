# F005 e2e cases

File: `testing/features/F005/e2e/workspace.spec.ts`. Playwright against seeded tenant. Flag `F005_FEATURE`.

- `create_workspace_build_tree_move_folder` — FR-F005-01, FR-F005-08, FR-F005-09, FR-F005-15: owner creates "Ops", adds "Projects" and child "Q4", drags "Q4" to root, reload shows "Q4" at depth 1.
- `duplicate_workspace_name_shows_field_error` — FR-F005-02: second "Ops" shows the inline name error and no new card.
- `move_into_descendant_shows_inline_error` — FR-F005-09: keyboard move of "Projects" under "Projects/Q4" shows the cycle error and the tree is unchanged.
- `edit_members_add_group_editor` — FR-F005-06: owner opens `Members`, adds group "Finance" as editor, saves; a group member can then create a folder.
- `remove_last_owner_is_blocked` — FR-F005-06: owner tries to demote self to editor; save is disabled with `owner_required` text.
- `restore_deleted_workspace` — FR-F005-05: delete "Ops", open trash, restore, tree shows the same folders at the same URL.
- `viewer_is_read_only` — FR-F005-15: viewer login sees the tree without `New folder`, move handles, or `Members`.
- `non_member_sees_not_found` — FR-F005-14: user outside the workspace opens `/w/{id}` → not-found page.
- `concurrent_rename_shows_stale_banner` — FR-F005-04: second session renames the workspace; the first session's rename shows the stale banner and reload.

Evidence: Playwright traces and videos under `testing/evidence/F005/e2e/`.
