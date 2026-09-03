# F009 api cases

File: `testing/features/F009/api/{hierarchy_tests.rs,rollup_tests.rs,link_tests.rs}`. Flag `F009_FEATURE`.

- `indent_nests_under_previous_sibling` — FR-F009-01: POST `/api/v1/rows/{id}/indent` as editor → 200, `parent_row_id` = previous sibling, `depth` 1, `row.reparented.v1` with `changed_fields [parent_row_id, depth, path]`.
- `indent_moves_descendants_and_rewrites_paths` — FR-F009-01: indent a row with 3 descendants → all four `path` values start with the new parent path, depths +1.
- `indent_rejects_first_row_in_group` — FR-F009-03: first row in group → 400 `invalid`, `field_errors.row_id = "no_previous_sibling"`.
- `indent_rejects_depth_over_20` — FR-F009-03: chain of 21 rows, indent the root under another row → 400 `depth_exceeded`, nothing written.
- `indent_rejects_cycle_under_descendant` — FR-F009-03: move so previous sibling is a descendant → 400 `cycle`.
- `outdent_places_row_after_parent` — FR-F009-02: outdent → `parent_row_id` = grandparent, `child_position` directly after former parent, event emitted.
- `outdent_root_is_invalid` — FR-F009-02: root row → 400 `already_root`.
- `children_direct_pages_by_child_position` — FR-F009-04: 1,200 children, `limit=500`, three pages in `child_position` order.
- `children_depth_all_returns_path_order` — FR-F009-04: `depth=all` → depth-first order, `depth` and `has_children` correct, deleted rows absent.
- `delete_parent_cascades_and_restore_reverses` — FR-F009-05: F006 delete parent → descendants `deleted_at` set; restore → cleared; restore child alone → 409 `field_errors.parent_row_id = "deleted"`.
- `hierarchy_stale_version_conflicts` — FR-F009-01: `If-Match` behind by one → 409 `conflict` with `current_version`.
- `hierarchy_viewer_denied` — FR-F009-14: viewer indent/outdent → 403 `denied`, no event.
- `hierarchy_cross_tenant_not_found` — FR-F009-14: tenant B row id on indent, outdent, children → 404.
- `rollup_sum_recomputes_ancestors_only` — FR-F009-07: edit one leaf Cost → exactly 2 ancestor cells rewritten, `rollup.recomputed.v1` `cell_count` 2, sibling subtrees untouched.
- `rollup_any_uses_status_priority` — FR-F009-06: `any` on Status with priority `[Blocked, In progress, Done]` → parent shows `Blocked` when any child blocked.
- `rollup_weighted_percent_uses_weight_column` — FR-F009-06: children 50% (weight 2) and 100% (weight 1) → parent 66.67%.
- `rollup_incompatible_function_invalid` — FR-F009-06: `avg` on a `select` column → 400 `invalid`, `field_errors.function`.
- `rollup_parent_cell_rejects_direct_edit` — FR-F009-08: F008 write to a rolled-up parent cell → 400 `field_errors.value = "rolled_up"`.
- `rollup_childless_parent_is_blank_valid` — FR-F009-08: parent with no children → blank raw, `validation.state = valid`.
- `rollup_event_replay_is_idempotent` — NFR-F009-04: replay the same `cell.updated.v1` version → no second recompute, no second event.
- `link_create_copies_target_value` — FR-F009-09: POST `/api/v1/links` → 201, source cell display equals target primary value, `link.created.v1`.
- `link_create_requires_target_read_access` — FR-F009-14: editor without `Vendors` access → 404 `not_found`.
- `link_create_rejects_incompatible_type` — FR-F009-09: target `file` column not in `accepted_types` → 400 `invalid`.
- `link_create_rejects_second_active_link_per_cell` — FR-F009-09: second link on the same cell → 409 `conflict`.
- `link_list_filters_and_redacts` — FR-F009-10: filter by `target_sheet_id`; viewer without target access sees `target_redacted: true` and no `target_primary_value`.
- `link_patch_and_delete_emit_events` — FR-F009-11: PATCH target row → `link.updated.v1`; DELETE → display cleared, `link.deleted.v1`.
- `link_target_delete_marks_broken` — FR-F009-12: delete target row → `status = broken`, source `validation.code = broken_link`, `link.updated.v1` `changed_fields [status]`; restore → `active`.
- `link_pull_sync_copies_value` — FR-F009-13: target `cell.updated.v1` → source display updated for `pull` and `both`, not for `push`.
- `link_push_sync_denied_without_target_edit` — FR-F009-13: source edit with `push` by an actor lacking target `sheet-editor` → 403, target unchanged.
- `link_cross_tenant_not_found` — FR-F009-14: tenant B `target_sheet_id` or `target_row_id` → 404 on create and patch.
- `link_mutations_write_audit_and_outbox` — FR-F009-16: each of indent, outdent, link create/patch/delete, rollup put → one audit row with diff and one outbox row.
- `request_span_carries_row_and_link_ids` — NFR-F009-04: spans on hierarchy and link routes carry `tenant_id`, `sheet_id`, `row_id` or `link_id`, `correlation_id`.

Evidence: JUnit output and request logs under `testing/evidence/F009/api/`.
