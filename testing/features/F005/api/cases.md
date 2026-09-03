# F005 api cases

File: `testing/features/F005/api/{workspace_tests.rs,member_tests.rs,folder_tests.rs,tree_tests.rs,permission_tests.rs}`. Flag `F005_FEATURE`.

- `workspace_create_returns_version_one_and_owner` — FR-F005-01: POST `/api/v1/workspaces` returns 201, `version: 1`, and `workspace_members` holds the creator as `owner`.
- `workspace_duplicate_name_conflicts` — FR-F005-02: "Ops" then "ops" → 409 `conflict`, `field_errors.name = "taken"`; allowed again after the first is deleted.
- `workspace_list_only_member_workspaces` — FR-F005-03: 150 workspaces, actor in 40 → 40 results across cursor pages of 100; `name_prefix=Op`, `sort=updated_at`, `deleted=true` honoured; tenant-admin sees all 150.
- `workspace_stale_version_conflicts` — FR-F005-04: `If-Match: 2` against version 3 → 409 with `current_version: 3`, no write.
- `workspace_restore_keeps_ids_and_folders` — FR-F005-05: delete cascades `deleted_at` to 12 folders; restore clears all with identical ids; restore after retention → 404.
- `workspace_idempotent_replay_returns_original` — FR-F005-12: same key twice → one row, identical body; same key, different body → 409.
- `workspace_mutation_writes_audit_and_outbox` — FR-F005-13: each workspace mutation → one `audit_events` row with diff and one `outbox_events` row with the `workspace.*.v1` name.
- `workspace_cross_tenant_not_found` — FR-F005-14: tenant B GET/PATCH/DELETE/restore → 404 on every route.
- `members_replace_requires_owner` — FR-F005-06: PUT with editors only → 400 `invalid`, `field_errors.members = "owner_required"`, prior set unchanged.
- `members_replace_rejects_duplicate_subject` — FR-F005-06: same `(user, id)` twice → 400 `duplicate_subject`.
- `members_replace_emits_event` — FR-F005-13: valid replacement → `workspace-member.updated.v1` with `changed_fields` listing added and removed subjects.
- `folder_create_sets_path_and_depth` — FR-F005-08: child of "Projects" → `path = "<projects_id>/<id>"`, `depth: 2`, position after `after_folder_id`.
- `folder_depth_eleven_invalid` — FR-F005-08: chain of 10 then one more → 400 `field_errors.parent_folder_id = "max_depth"`.
- `folder_sibling_name_conflicts` — FR-F005-08: "Q4" and "q4" under the same parent → 409.
- `folder_move_into_descendant_rejected` — FR-F005-09: move "Projects" under "Projects/Q4" and under itself → 400 `cycle`, paths unchanged.
- `folder_move_rewrites_descendant_paths` — FR-F005-09: move a 3-level subtree to root → every descendant `path` and `depth` updated, `tree_version` +1, `folder.moved.v1`.
- `folder_delete_cascades_descendants` — FR-F005-10: delete parent with 3 descendants → four `deleted_at` values, tree omits all.
- `tree_hides_denied_subtree` — FR-F005-11: editor with a deny on "Finance" → tree omits "Finance" and children; owner tree includes them.
- `tree_etag_matches_tree_version` — FR-F005-07: `ETag` equals `tree_version`; `If-None-Match` hit → 304.
- `folder_viewer_mutation_denied` — NFR-F005-02: viewer and commenter POST/PATCH/move/DELETE folders and PUT members → 403 `denied`.
- `folder_cross_tenant_not_found` — FR-F005-14: tenant B folder routes → 404.
- `non_member_tree_not_found` — FR-F005-14: existing workspace, non-member GET workspace and tree → 404.
- `request_span_carries_ids` — NFR-F005-04: tracing span has `tenant_id`, `workspace_id`, `correlation_id`.

Evidence: JUnit output and request logs under `testing/evidence/F005/api/`.
