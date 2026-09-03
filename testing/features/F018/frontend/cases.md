# F018 frontend cases

File: `testing/features/F018/frontend/{WorkflowBuilderPage.test.tsx,ConditionTree.test.tsx,ActionList.test.tsx,TestPanel.test.tsx,WorkflowListPage.test.tsx}`. Vitest with MSW. Flag `F018_FEATURE`.

- `builder_publish_disabled_until_valid` — FR-F018-14: empty trigger disables `Publish`; picking `Field changed` + column enables it.
- `builder_shows_server_field_errors_on_leaf` — FR-F018-03: 400 with `field_errors.condition.all[0]` highlights that leaf and links via `aria-describedby`.
- `nested_groups_expose_aria_level` — NFR-F018-03: depth-3 tree renders `role=tree` with `aria-level` 1..3.
- `add_fifth_nesting_level_blocked` — FR-F018-03: `Add group` hidden at depth 4.
- `keyboard_reorder_updates_indexes` — FR-F018-14: `Alt+ArrowDown` on action 0 swaps with action 1 and updates the plan indexes.
- `action_editor_validates_webhook_url` — FR-F018-04: `http://` URL shows inline error; secret field accepts references only.
- `placeholder_picker_inserts_column_token` — FR-F018-05: picking `Status` inserts `{{row.col_status}}` at the caret.
- `test_panel_shows_plan_and_no_actions_run` — FR-F018-09: pick row, click `Test`, plan table renders `trigger_matched`, `condition_result`, 2 rows.
- `shows_denied_read_only_for_viewer` — FR-F018-14: viewer role hides `Publish`, `Disable`, `Delete`; fields disabled with explanation.
- `shows_not_found_for_foreign_workflow` — FR-F018-14: 404 renders not-found page.
- `stale_banner_on_conflict` — FR-F018-06: PATCH 409 shows `This workflow changed` with reload.
- `list_shows_state_badges_and_empty_state` — FR-F018-10: published/draft/disabled badges; empty list shows `New workflow`.
- `publish_emits_telemetry` — FR-F018-07: successful publish emits `workflow_published` with `trigger_kind`.

Evidence: Vitest JUnit under `testing/evidence/F018/frontend/`.
