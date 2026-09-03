# F053 api cases

File: `testing/features/F053/api/{mapping_tests.rs,match_tests.rs,preview_tests.rs,sync_tests.rs,conflict_tests.rs,concurrency_tests.rs}`. Flag `F053_FEATURE`.

- `mapping_create_returns_version_one` — FR-F053-01: POST mapping `Vendors → Purchase requests` → 201, `version: 1`, `last_cursor: null`.
- `mapping_same_sheet_invalid` — FR-F053-01: identical `source_sheet_id` and `target_sheet_id` → 400 `field_errors.target_sheet_id = same_as_source`.
- `mapping_field_map_rejects_incompatible_types` — FR-F053-02: `date → number` without transform → 400 `field_errors.field_maps[0].target_column_id`.
- `mapping_expression_over_200_nodes_invalid` — FR-F053-02: 201-node expression → 400 `field_errors.field_maps[1].expression`.
- `mapping_bidirectional_with_transform_invalid` — FR-F053-02: `bidirectional` plus `expression` → 400.
- `mapping_target_column_owned_conflicts` — FR-F053-02: second enabled mapping onto the same target column → 409 `owned_by_mapping`.
- `mapping_limit_reached_conflicts` — FR-F053-10: sixth mapping with `max_mappings 5` → 409 `field_errors.mappings = limit_reached`.
- `mapping_no_entitlement_denied_by_guard` — FR-F053-12: tenant B admin GET mappings → 403 `field_errors.module = not_entitled`, handler never ran.
- `mapping_cross_tenant_not_found` — FR-F053-13: tenant B GET/PATCH/preview/sync on tenant A mapping → 404.
- `normalize_key_per_mode` — FR-F053-03: `" ACME  Ltd "` under `trim`, `case_insensitive`, `whitespace`, `date`, `exact` yields the specified keys.
- `match_engine_matches_fixture_840_rows` — FR-F053-03: 840 match rows, each target row at most once.
- `match_engine_flags_ambiguous_matches` — FR-F053-03: two duplicate vendor ids → zero match rows for them and two `ambiguous_match` plan entries.
- `plan_changes_honours_overwrite_modes` — FR-F053-06: `always` writes 96, `if_empty` writes 31, `never` writes 0 and reports 96.
- `preview_counts_match_fixture` — FR-F053-04: preview returns matched 840, unmatched_source 12, unmatched_target 348, would_update 96, conflicts 2.
- `preview_writes_nothing` — FR-F053-04: `cells`, `cell_links`, `datamesh_conflicts` row counts unchanged after preview.
- `preview_redacts_unreadable_columns` — NFR-F053-02: caller without read on `Payment terms` gets the sample without that column.
- `sync_request_conflicts_while_active` — FR-F053-05: second sync during `queued` → 409 `field_errors.run = already_active`.
- `sync_repeated_cursor_writes_nothing` — FR-F053-05: same `source_version_cursor` → `succeeded`, `updated 0`.
- `sync_writes_with_provenance_links` — FR-F053-06: 96 cells updated as the owner with `source = datamesh`; each has a `datamesh` link with `mapping_id` and `source_row_id`.
- `sync_unmatched_create_adds_rows` — FR-F053-06: `unmatched_policy: create` adds 12 target rows; `flag` records 12 `unmatched_source` conflicts instead.
- `sync_deletion_clear_empties_cells` — FR-F053-06: 3 source rows deleted since cursor → mapped target cells cleared; `flag` records `source_deleted`.
- `sync_both_changed_records_conflict` — FR-F053-07: both sides edited `Vendor contact` → no writes, one `both_changed` conflict with both values and versions.
- `sync_writes_back_target_only_change` — FR-F053-07: target-only edit on a bidirectional map → source cell updated.
- `sync_sheet_denied_when_owner_lost_access` — FR-F053-13: owner demoted to viewer on target → run `failed`, `sheet_denied`, no writes.
- `sync_too_many_rows_fails_before_write` — FR-F053-10: 60,000 changed rows with `max_rows_per_sync 50000` → `too_many_rows`, no writes.
- `listener_debounces_and_ignores_own_writes` — FR-F053-09: five `cell.updated.v1` in 10 s → one run after 60 s; events with `source = datamesh` ignored.
- `resolve_keep_target_writes_value` — FR-F053-08: resolve `keep_target` writes the target value to the source, conflict `resolved` with actor.
- `resolve_rejects_moved_row` — FR-F053-08: target version advanced since the conflict → 409, conflict still `open`.
- `resolve_non_admin_denied` — NFR-F053-02: editor POST resolve → 403 `denied`.
- `sync_publishes_synced_and_conflict_events` — FR-F053-11: outbox holds `mapping.synced.v1` with counts and one `mapping-conflict.detected.v1` per conflict.
- `run_dead_letters_after_three_retries` — NFR-F053-04: cell service stub fails four times → run dead-lettered with reason; span carries `mapping_id`, `run_id`, `correlation_id`.

Evidence: JUnit output and request logs under `testing/evidence/F053/api/`.
