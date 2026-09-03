# F021 api cases

File: `testing/features/F021/api/{report_tests.rs,definition_tests.rs,query_tests.rs,property_tests.rs,permission_tests.rs}`. Flag `F021_FEATURE`.

- `report_create_returns_version_one` — FR-F021-01: POST `/api/v1/reports` as editor returns 201, `version: 1`, `snapshot: null`.
- `report_duplicate_name_conflicts` — FR-F021-01: same name, same folder, different case → 409 `field_errors.name = "taken"`.
- `alias_regex_enforced` — FR-F021-02: alias `Bad Alias` → 400 `definition.sources[0]`.
- `report_source_alias_invalid` — FR-F021-02: duplicate alias `projects` twice → 400.
- `join_by_link_column_matches_row_id` — FR-F021-03: Risks.project link join yields 120 rows each carrying `sources.projects`.
- `join_cycle_rejected` — FR-F021-03: joins A→B, B→A → 400 `definition.joins[1]`.
- `join_type_mismatch_rejected` — FR-F021-03: text column joined to number column → 400.
- `filter_relative_date_uses_timezone` — FR-F021-04: `due gte -7d` at clock `2026-09-03T03:00Z` in `America/New_York` includes rows dated 2026-08-27 local.
- `filter_depth_limit_rejected` — FR-F021-04: depth 5 tree → 400 `definition.filters`.
- `group_headers_carry_aggregates` — FR-F021-05: group by owner, sum(budget), count → headers with `depth 0`, `row_count`.
- `calculated_field_parse_error_names_field` — FR-F021-06: `DAYS(` → 400 `definition.calculated_fields[0].expression`.
- `calculated_field_budget_marks_row` — FR-F021-06: pathological expression over 2 s → display `#BUDGET`, snapshot succeeded.
- `report_refresh_acknowledged_under_two_seconds` — FR-F021-07: 202 with `run_id` while the worker is paused.
- `report_refresh_active_conflicts` — FR-F021-07: second refresh while queued → 409 with active `run_id`.
- `refresh_job_writes_snapshot_and_event` — FR-F021-07: worker run → `succeeded`, `row_count 120`, `source_versions` for three sheets, `report.refreshed.v1`.
- `refresh_keeps_last_three_snapshots` — FR-F021-07: five refreshes → three succeeded rows remain.
- `interval_policy_validated` — FR-F021-08: `interval_minutes 4` and `timezone "Mars/Olympus"` → 400.
- `report_rows_pages_with_meta` — FR-F021-09: `limit=500`, three pages, `meta.snapshot_id` and `computed_at` present.
- `report_rows_drop_restricted_sheet` — FR-F021-10: restricted viewer receives 0 Risks rows and `restricted_sources = [risks_sheet_id]`.
- `report_rows_strip_hidden_columns` — FR-F021-10: `Budget.margin` absent from `cells`, present in `hidden_columns`.
- `group_aggregates_exclude_hidden_column` — FR-F021-11: sum(margin) is null for the viewer, numeric for the editor.
- `owner_aggregate_policy_requires_tenant_setting` — FR-F021-11: `aggregate_policy owner` without tenant setting → aggregates still viewer-scoped; with setting → `meta.aggregate_scope = "owner"`.
- `report_list_filters_and_hides_unreadable` — FR-F021-12: 30 reports, viewer sees 20, prefix filter narrows to 3.
- `report_stale_version_conflicts` — FR-F021-13: `If-Match: 2` vs version 3 → 409 `current_version 3`.
- `definition_change_marks_snapshots_stale` — FR-F021-13: PATCH definition → every snapshot `stale = true`.
- `report_cross_tenant_not_found` — FR-F021-13: tenant B GET/PATCH/DELETE/rows/refresh → 404.
- `report_idempotent_replay_returns_original` — FR-F021-14: same key twice → one row; different body → 409.
- `report_mutation_writes_audit_and_outbox` — FR-F021-14: create, update, delete → one audit row and one outbox row each.
- `report_viewer_mutation_denied` — NFR-F021-02: viewer PATCH/DELETE/refresh → 403 `denied`.
- `guest_link_cannot_refresh` — NFR-F021-02: F036 share-link actor GET rows 200, POST refresh 403.
- `field_level_acl_hides_column` — NFR-F021-02: F003 field ACL deny on `Projects.budget` removes it from cells.
- `refresh_job_dead_letters_after_four_failures` — NFR-F021-04: injected failures → 3 retries then `dead_letters` row.
- `refresh_job_idempotent_by_run_id` — NFR-F021-04: redelivered job → no second snapshot.
- `request_span_carries_report_ids` — NFR-F021-04: span has `tenant_id`, `report_id`, `run_id`, `correlation_id`.
- `joined_rows_reference_existing_sources` — FR-F021-03: proptest over random definitions.
- `filter_tree_matches_reference_evaluator` — FR-F021-04: proptest equivalence with in-memory evaluator.

Evidence: JUnit output and request logs under `testing/evidence/F021/api/`.
