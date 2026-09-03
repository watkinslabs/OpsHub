# F006 api cases

File: `testing/features/F006/api/{sheet_tests.rs,row_tests.rs,group_tests.rs}`. Flag `F006_FEATURE`.

- `sheet_create_returns_version_one` — FR-F006-01: POST `/api/v1/sheets` as editor returns 201, `version: 1`, `default_group_id`.
- `sheet_duplicate_name_conflicts` — FR-F006-02: same name, same folder, different case → 409 `conflict`.
- `sheet_list_pages_filters_sorts` — FR-F006-03: 120 sheets, `limit=50`, three pages; `folder_id` and `name_prefix` filters; `sort=updated_at`.
- `sheet_stale_version_conflicts` — FR-F006-04: `If-Match: 2` against version 3 → 409 with `current_version: 3`, no write.
- `sheet_restore_keeps_ids` — FR-F006-05: delete, restore → identical ids, `deleted_at` null, rows visible.
- `sheet_idempotent_replay_returns_original` — FR-F006-10: same key twice → one row, same body; different body → 409.
- `sheet_cross_tenant_not_found` — FR-F006-12: tenant B GET/PATCH/DELETE → 404 on every route.
- `sheet_viewer_mutation_denied` — NFR-F006-02: viewer POST/PATCH/DELETE → 403 `denied`.
- `sheet_mutation_writes_audit_and_outbox` — FR-F006-11: each mutation → one `audit_events` row with diff and one `outbox_events` row.
- `row_create_assigns_position` — FR-F006-06: `after_row_id` yields a key strictly between neighbours.
- `row_list_pages_by_position` — FR-F006-07: 1,200 rows, `limit=500`, three pages in order, cells carry `raw`, `display`, `validation`.
- `row_move_between_groups_emits_event` — FR-F006-08: move → new `group_id`, version +1, `row.moved.v1`.
- `row_move_rebalances_long_keys` — FR-F006-08: 70 inserts at the same spot → keys rebalanced under 64 chars.
- `group_delete_moves_rows_to_default` — FR-F006-09: delete group → rows in default; delete default → 400 `invalid`.
- `row_cross_tenant_not_found` — FR-F006-12: tenant B row routes → 404.
- `row_unknown_column_key_invalid` — FR-F006-06: cells keyed by a foreign column id → 400 with `field_errors.cells`.
- `request_span_carries_ids` — NFR-F006-04: tracing span has `tenant_id`, `sheet_id`, `correlation_id`.

Evidence: JUnit output and request logs under `testing/evidence/F006/api/`.
