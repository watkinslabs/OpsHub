---
id: S060
type: story
status: planned
parent_epic: E006
parent_feature: F030
depends_on: [F030]
owned_paths: [crates/domain/src/connectors/**, crates/persistence/src/connectors/**, services/worker/src/connectors/**, services/api/src/connectors/**, apps/web/src/features/connectors/**, testing/features/F030/**]
feature_flag: F030_FEATURE
branch: s060-crm-file-sync
started_at: null
finished_at: null
---

# S060 — CRM and file sync

## Identity

- Parent feature: `F030` Jira/Salesforce/files
- Owner: platform
- Branch: `s060-crm-file-sync`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 5, 7; `docs/capability-contracts.md` row F030

## Vertical slice

As an integration administrator, I want Salesforce records, Box and Dropbox files, Tableau extracts, and a read-only reporting database to move through the same sync engine as Jira, with durable cursors that survive a crash, retries that distinguish a rate limit from a bad record, a replay I can dry-run, and a conflict queue that shows me both values before anything is overwritten, so that a large sync is safe to leave running unattended.

This slice adds five connectors and the durability half of the engine — cursor checkpointing, error classification and backoff, run finalization thresholds, replay, and conflict detection and resolution — on the framework S059 established.

## Requirements

- **SR-S060-01:** The Salesforce adapter reads `Account`, `Opportunity`, `Contact`, `Case`, and `Lead` with a `SystemModstamp` timestamp cursor, sources deletions from `getDeleted`, writes through the composite API in batches of 200 mapping per-record results back to outcomes, validates the SOQL `WHERE` fragment against an allowlist that rejects subqueries and DML keywords, and classifies `REQUEST_LIMIT_EXCEEDED` as `transient` (covers FR-F030-17, FR-F030-10).
- **SR-S060-02:** The Box and Dropbox adapters bind an external folder to a sheet attachment column, cursor on Box `stream_position` and Dropbox `list_folder/continue`, download through the F013 file service with ClamAV, MIME allowlist, 100 MB per file and 2 GB per run, upload OpsHub attachments on `outbound`, and record a scan rejection as `permanent` with code `scan_rejected` without attaching the file (FR-F030-18).
- **SR-S060-03:** The Tableau adapter publishes a F023 report result as a Hyper extract to a named project and datasource, replacing the datasource per run and storing the returned LUID; the `database` adapter reads only, using a secret-manager DSN, an allowlist held as `sync_database_objects` rows read through `SyncRepository::list_database_objects` and rewritten through `replace_database_objects`, parameterized statements, a 30 s statement timeout, and a 50,000-row cap that ends the run `partial` with code `row_cap_reached`; any DDL or DML attempt is rejected before execution (FR-F030-19, NFR-F030-02).
- **SR-S060-04:** `sync_cursors` holds one row per `(sync_id, direction)`, `SyncCursorRepository::checkpoint_cursor` and `SyncRecordLinkRepository::upsert_record_links` run every 500 records inside the same `UnitOfWork` transaction as the applied rows, a restarted worker resumes from `checkpoint_record_id` without reprocessing the page, and `reset_cursor_to` on `PATCH /api/v1/syncs/{id}` writes the `sync.cursor-reset` audit event (FR-F030-09, NFR-F030-04).
- **SR-S060-05:** Errors classify as `transient`, `permanent`, or `mapping`; `transient` retries five times at 1 s, 2 s, 4 s, 8 s, 16 s with ±20% jitter honoring `Retry-After`, then dead-letters; each unretried failure is one `sync_run_failed_records` row appended through `SyncRunRepository::append_failed_records`, and `finalize_run` sets `completed` at zero failures, `partial` when `records_failed` is under 10% of `records_read`, and `failed` at 10% or more, which sets the sync `state: error`, pauses its schedule, and publishes `sync-run.failed.v1` (FR-F030-10, NFR-F030-04).
- **SR-S060-06:** `POST /api/v1/sync-runs/{id}/replay` restarts from the source run's `cursor_before`, or over just the external IDs from `SyncRunRepository::list_failed_records_for_replay` with `only_failed`, and with `dry_run` returns `{ would_create, would_update, would_skip, would_conflict, samples }` without writing; idempotency comes from `sync_record_links` compared on `external_version` so an already-applied record counts as `skipped` (FR-F030-12).
- **SR-S060-07:** A record whose OpsHub row and external counterpart both changed since the cursor produces a `sync_conflicts` row plus one `sync_conflict_fields` row per conflicting field carrying `column_id`, `external_field`, `opshub_value`, and `external_value`, both timestamps, and `state: open`, written by `SyncConflictRepository::insert_conflict_with_fields` and published as `sync-conflict.detected.v1` with the API still exposing `field_diffs` as an array; `manual` leaves both sides untouched while `opshub_wins`, `external_wins`, and `newest_wins` apply the winner and store `state: auto_resolved` with the resolution (FR-F030-13).
- **SR-S060-08:** `GET /api/v1/syncs/{id}/conflicts` filters by `state` through `list_conflicts_by_state`, and `POST /api/v1/sync-conflicts/{id}/resolve` applies `keep_opshub`, `keep_external`, or `merge` under `If-Match` on the parent sync, requires `field_values` covering every `sync_conflict_fields` row of the conflict for `merge` and stores each chosen value in that row's `resolved_value`, publishes `sync-conflict.resolved.v1`, and returns `409 conflict` for an already-settled conflict (FR-F030-14).
- **SR-S060-09:** `sync_run_failed_records.message_digest` stores field values as SHA-256 digests and `provider_payload` stays null unless `debug_payloads` is set, which retains the raw provider snapshot for 7 days and writes the `sync.debug-payloads-enabled` audit event; metrics `sync_records_total`, `sync_run_duration_seconds`, `sync_conflicts_open`, and `sync_cursor_lag_seconds` are emitted and every run carries a tracing span with `sync_id` and `run_id` (NFR-F030-02, NFR-F030-04).
- **SR-S060-10:** The conflict queue and run detail UI show both values per field, `Keep OpsHub`, `Keep external`, `Merge`, bulk keep-external capped at 100 selected rows, the failed-record table, and `Replay` and `Dry-run replay` confirmations naming the record count, all axe-clean and readable in sequence by a screen reader (FR-F030-21, NFR-F030-03).

## Surfaces

- Infrastructure/container: a second SQLx pool configured `default_transaction_read_only = on` for the `database` connector; secret-manager key path `connectors/database/{sync_id}/dsn`
- Data access: `crates/persistence/src/connectors/{cursor_repository.rs, conflict_repository.rs, record_link_repository.rs, run_repository.rs}` hold every SQL statement this slice adds — `SyncCursorRepository` owns `sync_cursors`, `SyncConflictRepository` owns `sync_conflicts` and `sync_conflict_fields`, `SyncRecordLinkRepository` owns `sync_record_links`, and `SyncRunRepository` (from S059) owns `sync_runs` and `sync_run_failed_records`; the engine stages, the adapters, `services/worker/src/connectors/{run.rs, sweep.rs}`, and `handlers_conflict.rs` call those traits and open no connection or transaction of their own, and the `database` adapter's read-only pool is confined to `adapters/database.rs`, which reads external systems only and never the OpsHub schema (decision section 2.1)
- Rust service/API: `crates/domain/src/connectors/{engine/{mod.rs, plan.rs, apply.rs, checkpoint.rs, classify.rs}, conflict.rs, cursor.rs, replay.rs, adapters/{salesforce.rs, box_files.rs, dropbox.rs, tableau.rs, database.rs}}`; `services/api/src/connectors/{handlers_replay.rs, handlers_conflict.rs}`; `services/worker/src/connectors/{mod.rs, schedule.rs, run.rs, webhook.rs, sweep.rs}`
- Data/migration: no new tables; this story fills `sync_cursors`, `sync_conflicts`, `sync_conflict_fields`, `sync_run_failed_records`, `sync_record_links`, and `sync_database_objects` created by the S059 migration and adds the nightly retention sweep
- React/UI: `apps/web/src/features/connectors/{ConflictQueue.tsx, ConflictDiff.tsx, MergeChooser.tsx, FailedRecordTable.tsx, ReplayDialog.tsx}`
- Mocks/fixtures: `testing/fixtures/connectors.rs` 10,000-record Salesforce generator, Box folder with 20 files including an EICAR sample, read-only PostgreSQL fixture database; mocks in `testing/harness/connectors/` for Salesforce v61.0, Box 2.0, Dropbox v2, and Tableau REST 3.21 with injectable 429, 503, and mid-page disconnects

## TDD harness

- Test path: `testing/features/F030/{api,e2e,performance}/`
- Feature flag: `F030_FEATURE`
- Targeted command: `cargo xtask test-feature F030`
- Full command: `cargo xtask test-all`
- First failing tests: `cursor_checkpoints_every_500_records`, `run_resumes_from_checkpoint_after_restart`, `transient_error_retries_five_times_with_backoff`, `run_fails_and_pauses_sync_at_ten_percent`, `replay_only_failed_skips_applied_records`, `dry_run_replay_writes_nothing`, `conflict_detected_writes_one_field_row_per_change`, `conflict_detected_leaves_both_sides_untouched`, `resolve_merge_requires_all_field_values`, `failed_record_rows_drive_only_failed_replay`, `soql_with_dml_keyword_rejected`, `database_connector_rejects_update_statement`

## Exit criteria

- [ ] Requirement tests SR-S060-01 through SR-S060-10 written first and failing
- [ ] Tasks T119 and T120 complete and wired through the worker registry and API router
- [ ] Unit, API, E2E, permission, accessibility, and performance tests pass in targeted and full modes
- [ ] Production call path named: `services/worker/src/connectors/run.rs` and `sweep.rs` registered in `services/worker/src/registry.rs`; `services/api/src/connectors/handlers_replay.rs` and `handlers_conflict.rs` mounted through `services/api/src/connectors/routes.rs`
- [ ] Handoff evidence recorded in the F030 ticket
