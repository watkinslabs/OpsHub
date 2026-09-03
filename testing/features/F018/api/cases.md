# F018 api cases

File: `testing/features/F018/api/{workflow_tests.rs,condition_tests.rs,publish_tests.rs}`. Flag `F018_FEATURE`.

- `workflow_create_returns_draft_version_one` — FR-F018-01: POST `/api/v1/workflows` as editor returns 201, `state: draft`, `version: 1`.
- `trigger_each_kind_accepted` — FR-F018-02: 8 fixture definitions, one per trigger kind, all return 201.
- `trigger_cron_under_five_minutes_invalid` — FR-F018-02: cron `*/2 * * * *` → 400 `field_errors.trigger.cron`; unknown kind → 400 `field_errors.trigger.kind`.
- `trigger_date_reached_offset_out_of_range_invalid` — FR-F018-02: `offset_minutes: 50000` → 400.
- `condition_operator_type_mismatch_invalid` — FR-F018-03: `Amount starts_with "1"` → 400 with `field_errors.condition.all[0]`.
- `condition_depth_five_invalid` — FR-F018-03: five nested `all` groups → 400 `field_errors.condition`.
- `condition_changed_and_actor_in_leaves_evaluate` — FR-F018-03: `changed(Status)` true only when event lists Status; `actor_in` matches group membership.
- `action_webhook_inline_secret_invalid` — FR-F018-04: `call_webhook` with `secret: "abc"` or `http://` URL → 400.
- `action_twenty_six_invalid` — FR-F018-04: 26 actions → 400 `field_errors.actions`.
- `placeholder_unknown_column_invalid` — FR-F018-05: `{{row.col_missing}}` → 400 naming the placeholder.
- `patch_after_publish_keeps_version` — FR-F018-06: PATCH after publish changes `draft` only; `workflow_versions.definition_hash` unchanged.
- `publish_writes_immutable_version` — FR-F018-07: publish → `version_no: 1`, `workflow_steps` rows, `workflow.published.v1` in outbox.
- `publish_invalid_definition_lists_all_errors` — FR-F018-07: two errors in one definition → 400 with both paths.
- `disable_then_republish_increments_version` — FR-F018-08: disable → `workflow.disabled.v1`; publish → `version_no: 2`.
- `workflow_test_evaluates_without_side_effects` — FR-F018-09: `test` with `row_id` → plan of 2 actions; zero notification or run outbox rows.
- `workflow_list_filters_by_state_and_trigger` — FR-F018-10: 120 workflows, `limit=50`, three pages; `filter[state]`, `filter[trigger_kind]`.
- `workflow_delete_hides_but_keeps_versions` — FR-F018-11: DELETE → 404 on GET; version row still present.
- `sheet_limit_101_conflict` — FR-F018-12: 101st publish → 409 `field_errors.limit`.
- `workflow_mutation_writes_audit_and_outbox` — FR-F018-13: each mutation → one `audit_events` row and one `workflow.*.v1` outbox row.
- `workflow_cross_tenant_not_found` — NFR-F018-02: tenant B on every route → 404.
- `workflow_viewer_mutation_denied` — FR-F018-14: viewer POST/PATCH/publish/disable/DELETE → 403 `denied`.
- `formula_leaf_hidden_sheet_invalid` — NFR-F018-02: formula referencing a sheet the editor cannot read → 400.
- `request_span_carries_ids` — NFR-F018-04: span has `tenant_id`, `workflow_id`, `correlation_id`.

Evidence: JUnit output and request logs under `testing/evidence/F018/api/`.
