---
id: T119
type: task
status: planned
parent_epic: E006
parent_feature: F030
parent_story: S060
depends_on: [S060]
owned_paths: [crates/domain/src/connectors/engine/**, crates/domain/src/connectors/adapters/**, services/worker/src/connectors/**, services/api/src/connectors/**, testing/features/F030/api/**, testing/features/F030/database/**]
feature_flag: F030_FEATURE
branch: t119-cursor-retry-state
started_at: null
finished_at: null
---

# T119 — Cursor and retry state

## Identity

- Parent story: `S060` CRM and file sync
- Owner: platform
- Branch: `t119-cursor-retry-state`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 5, 7; `docs/capability-contracts.md` row F030

## Objective

Implement the durable half of the run engine — cursor checkpointing and resume, error classification with bounded backoff, run finalization thresholds, the conflict queue — plus the Salesforce, Box, Dropbox, Tableau, and read-only database adapters that exercise it.

## Specification

- Owned paths: `crates/domain/src/connectors/engine/{mod.rs, plan.rs, apply.rs, checkpoint.rs, classify.rs}`, `crates/domain/src/connectors/{cursor.rs, conflict.rs}`, `crates/persistence/src/connectors/{cursor_repository.rs, conflict_repository.rs, record_link_repository.rs}`, `crates/domain/src/connectors/adapters/{salesforce.rs, box_files.rs, dropbox.rs, tableau.rs, database.rs}`, `services/worker/src/connectors/{run.rs, sweep.rs}`, `services/api/src/connectors/handlers_conflict.rs`
- Contract/input: engine input `RunPlan { sync, mappings, cursor, page_size: 200, trigger }`; `POST /api/v1/sync-conflicts/{id}/resolve` body `{ resolution: keep_opshub|keep_external|merge, field_values?, expected_version }`; `GET /api/v1/syncs/{id}/conflicts` query `{ state?, cursor?, limit? }`; secret-manager key `connectors/database/{sync_id}/dsn`.
- Output/behavior: `checkpoint.rs` calls `SyncCursorRepository::checkpoint_cursor` (`cursor_kind`, `cursor_value`, `high_water_mark`, `checkpoint_record_id`) and `SyncRecordLinkRepository::upsert_record_links` in the same `UnitOfWork` transaction as the applied rows every 500 records, so a restarted `run.rs` resumes after `checkpoint_record_id`; `classify.rs` maps 429/502/503/504/timeout/reset to `Transient`, 400/401/403/404/422 to `Permanent`, and transform failures to `Mapping`, retrying `Transient` five times at 1 s, 2 s, 4 s, 8 s, 16 s with ±20% jitter honoring `Retry-After` before dead-lettering; `apply.rs` appends each unretried failure through `SyncRunRepository::append_failed_records` and finalizes `completed`, `partial` (`records_failed` under 10% of `records_read`), or `failed` (≥10%, sets sync `state: error` and pauses the schedule) by writing the six `records_*` counter columns, with the run response reading at most 50 `sync_run_failed_records` rows; `conflict.rs` compares `sync_record_links.opshub_updated_at` and `external_updated_at` against the stored values and calls `SyncConflictRepository::insert_conflict_with_fields`, writing one `sync_conflicts` row plus one `sync_conflict_fields` row per changed field and publishing `sync-conflict.detected.v1` under `manual`, or applies `opshub_wins`, `external_wins`, `newest_wins` and stores `auto_resolved`; resolve applies to both sides, publishes `sync-conflict.resolved.v1`, and returns `409 conflict` when already settled; `salesforce.rs` uses `SystemModstamp`, `getUpdated`, `getDeleted`, and composite batches of 200 with an allowlisted SOQL `WHERE` fragment; `box_files.rs` and `dropbox.rs` cursor on `stream_position` and `list_folder/continue` and download through the F013 file service with a 100 MB per-file and 2 GB per-run cap; `tableau.rs` publishes a Hyper extract and stores the datasource LUID; `database.rs` uses a read-only SQLx pool against the customer database only, an allowlist read as `sync_database_objects` rows through `SyncRepository::list_database_objects`, parameterized statements, a 30 s statement timeout, and a 50,000-row cap ending the run `partial` with `row_cap_reached`; `sweep.rs` calls `SyncRunRepository::delete_runs_older_than` (90 days, cascading `sync_run_failed_records`), `::expire_debug_payloads` (nulls `provider_payload` after 7 days), and `SyncConflictRepository::delete_resolved_conflicts_before` (180 days); failure rows store field values in `message_digest` as SHA-256 digests and leave `provider_payload` null unless `debug_payloads` is set; metrics `sync_records_total`, `sync_run_duration_seconds`, `sync_conflicts_open`, `sync_cursor_lag_seconds` are emitted per run.
- Data access: no engine stage, adapter, worker job, or handler in this task issues SQL or opens a transaction against the OpsHub schema; `SyncCursorRepository` (owns `sync_cursors`), `SyncConflictRepository` (owns `sync_conflicts`, `sync_conflict_fields`), and `SyncRecordLinkRepository` (owns `sync_record_links`) are added in `crates/persistence/src/connectors/` with `load_cursor`, `checkpoint_cursor`, `reset_cursor_to`, `insert_conflict_with_fields`, `list_conflicts_by_state`, `count_open_conflicts`, `settle_conflict`, `delete_resolved_conflicts_before`, `find_link_by_external_id`, `upsert_record_links`, and `mark_external_deleted`, and this task extends `SyncRunRepository` with `append_failed_records`, `finalize_run`, `delete_runs_older_than`, and `expire_debug_payloads`; the checkpoint, the run finalization with its failed records, and the conflict resolution each run in one `UnitOfWork` shared with the F006 row repositories (decision section 2.1).
- Dependencies: T117 schema, sync aggregate, repositories, and adapter traits; T118 mapping evaluation; F013 file service and ClamAV; F023 report results for Tableau; F004 secret manager and JetStream; F006 row writes and soft delete.
- Feature flag: `F030_FEATURE` gates the run consumer, the sweep job, and the conflict routes.

## TDD

- Failing test first: `testing/features/F030/api/cursor_tests.rs::cursor_checkpoints_every_500_records`, `::run_resumes_from_checkpoint_after_restart`, `::reset_cursor_writes_audit_event`; `testing/features/F030/api/retry_tests.rs::transient_error_retries_five_times_with_backoff`, `::retry_after_header_is_honored`, `::permanent_error_is_not_retried`, `::run_partial_under_ten_percent_failures`, `::run_fails_and_pauses_sync_at_ten_percent`; `testing/features/F030/api/conflict_tests.rs::conflict_detected_leaves_both_sides_untouched`, `::newest_wins_auto_resolves_with_resolution`, `::resolve_merge_requires_all_field_values`, `::resolve_settled_conflict_conflicts`; `testing/features/F030/api/salesforce_tests.rs::soql_with_dml_keyword_rejected`, `::composite_batch_maps_per_record_results`, `::request_limit_exceeded_is_transient`; `testing/features/F030/api/files_tests.rs::scan_rejected_file_is_not_attached`, `::run_stops_at_two_gigabyte_cap`; `testing/features/F030/api/database_tests.rs::database_connector_rejects_update_statement`, `::row_cap_ends_run_partial`; `testing/features/F030/database/constraint_tests.rs::record_link_unique_per_sync_row`, `::run_state_check_rejects_unknown_state`, `::conflict_field_row_unique_per_column`, `::failed_record_row_unique_per_run`, `::database_object_row_unique_per_sync`, `::named_query_row_requires_statement_text`, `::conflict_delete_cascades_field_rows`
- Targeted command: `cargo xtask test-feature F030`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/connectors.rs` 10,000-record Salesforce generator, Box folder with 20 files including an EICAR sample, read-only PostgreSQL fixture database; `testing/harness/connectors/` mocks for Salesforce v61.0, Box 2.0, Dropbox v2, Tableau REST 3.21 with injectable 429, 503, mid-page disconnects, and clock skew; fixed clock and deterministic jitter seed

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Run consumer, sweep job, and conflict routes registered behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit, lint, and security gates pass, including the read-only pool assertion
- [ ] Handoff evidence recorded in S060
- [ ] `finished_at` recorded
