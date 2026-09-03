# F050 api cases

File: `testing/features/F050/api/{view_tests.rs,policy_tests.rs,rows_tests.rs,token_tests.rs,edit_tests.rs,isolation_tests.rs}`. Flag `F050_FEATURE`.

- `view_create_starts_with_empty_policy` — FR-F050-01: POST as owner → 201, `version: 1`, policy `edit_mode: none`, `visible_fields: []`.
- `view_limit_reached_conflicts` — FR-F050-11: fourth view under `max_views: 3` → 409 `field_errors.limit = "max_views"`.
- `view_not_entitled_denied` — FR-F050-11: tenant without `dynamic-views` entitlement → 403 `field_errors.module = "not_entitled"` before the handler runs.
- `unshared_sheet_viewer_not_found` — FR-F050-12: sheet viewer without a share → 404 on GET view, rows, and edit.
- `policy_rejects_editable_not_visible` — FR-F050-02: `editable_fields` containing a column outside `visible_fields` → 400 `field_errors.editable_fields`.
- `policy_rejects_depth_over_4` — FR-F050-02: nested `and`/`or` five levels deep → 400 `field_errors.row_filter`.
- `policy_allow_new_rows_requires_edit_mode` — FR-F050-03: `allow_new_rows: true` with `edit_mode: none` → 400.
- `rows_drop_hidden_fields_from_request` — FR-F050-04: `fields=Task,Budget&sort=Budget` → only Task and other visible fields, sort ignored, 200.
- `rows_assigned_to_current_user_filter` — FR-F050-04: vendor 1 sees exactly its 40 rows out of 200; vendor 2 sees a disjoint 40.
- `rows_page_by_cursor_limit_500` — FR-F050-04: `limit=501` → 400; three pages over 1,200 matching rows.
- `token_enable_returns_raw_once_and_stores_hash` — FR-F050-05: PATCH enable → `public_link` present once; DB stores SHA-256; GET view never returns raw.
- `token_expiry_over_30_days_invalid` — FR-F050-05: `expires_at` now + 31 days → 400 `field_errors.public_token.expires_at`.
- `public_view_response_has_no_tenant_ids` — FR-F050-05, NFR-F050-02: body contains no `tenant_id`, `workspace_id`, `sheet_id`, or sheet name.
- `revoked_token_denied_on_next_request` — FR-F050-08: revoke → next GET and PATCH → 403 `field_errors.token = "inactive"`.
- `expired_token_denied` — FR-F050-08: clock past `expires_at` → 403; metric `dynamic_view_token_expired_total` +1.
- `token_edit_rate_limited_at_61` — FR-F050-08: 60 edits pass; 61st in the same minute → 429 `rate_limited`.
- `edit_outside_editable_fields_denied` — FR-F050-06: cells including `Due` (visible, not editable) → 403 `field_errors.cells.<due_id> = "not_editable"`, no write.
- `edit_assigned_rows_only_for_current_user` — FR-F050-03: vendor 1 editing vendor 2's row → 404 `not_found`; own row → 200 with new version.
- `edit_writes_record_and_event` — FR-F050-07, FR-F050-10: accepted edit → `dynamic_view_edits` row with before/after, cell history origin = view id, `dynamic-view.row-edited.v1` without values.
- `edit_stale_version_conflicts` — FR-F050-06: `version` behind → 409 `conflict` with `current_version`.
- `delete_view_inerts_token_and_shares` — FR-F050-09: delete → public GET 403, shared user GET 404, sheet cells unchanged.
- `hidden_values_absent_from_bodies_events_logs` — NFR-F050-02: captured HTTP bodies, outbox payloads, audit diffs, and logs contain no hidden column value.
- `cross_tenant_every_route_not_found` — FR-F050-12: tenant B on all eight routes → 404 (public route → 403 under tenant A guard only).
- `preview_as_ignored_for_non_owner` — FR-F050-14: vendor passing `preview_as` → same rows as without it.
- `edit_span_and_metrics_recorded` — NFR-F050-04: denied edit increments `dynamic_view_edit_denied_total{reason="not_editable"}`; span has `dynamic_view_id`, `token_id` prefix, `correlation_id`.

Evidence: JUnit output and request logs under `testing/evidence/F050/api/`.
