---
id: F030
type: feature
status: planned
priority: P1
owner: platform
estimate: 8
target_milestone: M5
parent_epic: E006
depends_on: [F029]
blocks: [F054]
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/connectors/**, crates/persistence/src/connectors/**, services/api/src/connectors/**, services/worker/src/connectors/**, apps/web/src/features/connectors/**, services/api/migrations/*_connectors_*.sql, testing/features/F030/**]
feature_flag: F030_FEATURE
flag_default: off
branch: f030-jira-salesforce-files
started_at: null
finished_at: null
---

# F030 — Jira/Salesforce/files

## 1. Identity and dates

- Branch: `f030-jira-salesforce-files`
- Capability area: integrations and APIs (spec 5.9 INT-02, INT-03; section 10 connector-ownership decision)
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 7; `docs/capability-contracts.md` row F030
- Aggregate: `sync-connection`
- Module slug: `connectors`

## 2. Requirement specification

### Problem and user outcome

F029 gave OpsHub authenticated connections to three vendors and one purpose-built calendar sync. That does not generalize. Jira issues, Salesforce records, Box and Dropbox folders, Tableau extracts, and reporting databases each move different objects on different clocks, and every team that wires them by hand ends up with silent drift: a field that stopped mapping, a run that died halfway and restarted from zero, an edit overwritten on both sides with no record of what was lost.

F030 makes synchronization itself the product surface. One sync object names a connection, a source, a target, a direction, a field mapping with transforms, a deletion policy, and a conflict policy. One run engine reads changes since a durable cursor, applies mappings, checkpoints, retries transient failures, records every record outcome, and can be replayed. One conflict queue holds every case where both sides moved, with both values visible until a human or the policy decides.

As an integration administrator, I want to define a Jira, Salesforce, Box, Dropbox, Tableau, or read-only database sync with an explicit field mapping, watch its runs, replay a failed run, and resolve conflicts from a queue, so that cross-system data stays trustworthy and every failure is visible and recoverable in one place.

### Functional requirements

- **FR-F030-01:** F030 registers six connectors — `jira`, `salesforce`, `box`, `dropbox`, `tableau`, `database` — into the F029 provider registry through `ConnectorRegistry::register`, each declaring `sync_kinds` (`work`, `crm`, `file`, `analytics`, `db_read`), supported `directions`, required scopes or credential keys, and cursor kind; `GET /api/v1/integrations/providers` (F029) then returns nine providers. F030 never inserts, updates, or reads plaintext from `integration_connections` or `oauth_tokens`; it holds only a `connection_id` foreign key and calls the F029 vault through `TokenSource::access_token(connection_id)`.
- **FR-F030-02:** `POST /api/v1/syncs` with `{ connection_id, name, kind, source: { object, filter? }, target: { sheet_id }, direction: inbound|outbound|bidirectional, schedule, conflict_policy?, deletion_policy?, mappings }` by an `integration-admin` returns `201` with the sync, `version: 1`, and `state: paused`; the connector must support the requested `kind` and `direction` (`400 invalid` with `field_errors.direction` otherwise) and the connection must be F029 `status: active` (`409 conflict` when `needs_reauth` or `revoked`).
- **FR-F030-03:** `GET /api/v1/syncs` returns cursor-paginated syncs with `connection`, `connector`, `kind`, `direction`, `state` (`paused`, `active`, `error`), `schedule`, `last_run_at`, `last_run_state`, `open_conflicts`, and filters `connection_id`, `connector`, `kind`, `state`; `GET /api/v1/syncs/{id}` adds the mapping list, cursor snapshot, and the last five runs.
- **FR-F030-04:** `PATCH /api/v1/syncs/{id}` with `If-Match` updates `name`, `schedule`, `state`, `conflict_policy`, `deletion_policy`, and `source.filter`, returns the new `version`, and publishes `sync.updated.v1` with the changed keys; a stale `If-Match` returns `409 conflict` with the current version; activating a sync whose mapping set is empty returns `400 invalid`.
- **FR-F030-05:** `PUT /api/v1/syncs/{id}/mappings` replaces the whole mapping set in one transaction; the request and response keep each entry as `{ external_field, column_id, direction, transform: { name, args }, required, default_value? }`, and `SyncMappingRepository::replace_mapping_set` stores one `sync_mappings` row per entry with `transform_name`, one `sync_mapping_transform_args` row per scalar argument, and one `sync_mapping_value_map` row per `value_map` pair, reassembling the `transform` object on read so the API shape is unchanged; the response returns the stored set and a new sync `version`; validation rejects a duplicate `external_field` or `column_id` per direction, a duplicate argument name or duplicate external value inside one transform, a `required` mapping with no `default_value` on a nullable external field, and a transform whose output type does not match the column type, reporting `field_errors["mappings[3].transform"]`; a sync may hold at most 300 mappings.
- **FR-F030-06:** Transforms are pure functions from the fixed catalog `identity`, `trim`, `lower`, `upper`, `date_tz(tz)`, `datetime_format(pattern)`, `number_scale(factor)`, `value_map({external: opshub})`, `join(separator)`, `split(separator, index)`, `template(pattern)`, `lookup(sheet_id, key_column_id, value_column_id)`, held as the checked `sync_mappings.transform_name` enum; scalar arguments are `sync_mapping_transform_args` rows keyed by argument name and `value_map` pairs are `sync_mapping_value_map` rows, so an unmapped external value is a missing row rather than a missing object key; an unknown name, an argument name outside the catalog, or a bad argument value returns `400 invalid`; evaluation is sandboxed with no I/O other than `lookup`, is bounded to 5 ms per cell, and a transform failure marks that record `mapping_failed` without aborting the run.
- **FR-F030-07:** `POST /api/v1/syncs/{id}/run` enqueues an immediate run and returns `202` with `{ run_id, state: queued }` within 2 s, publishing `sync-run.started.v1` when the worker picks it up; per-sync concurrency is 1, so a request while a run is `queued` or `running` returns `409 conflict` with the active `run_id`; `POST /api/v1/syncs/{id}/pause` sets `state: paused`, cancels the queued run, and lets a running one finish its current checkpoint.
- **FR-F030-08:** `schedule` is one of `manual`, `every_5m`, `every_15m` (default), `hourly`, `daily_at_02_00_utc`; the worker job `connectors.schedule` enqueues due syncs, skips a sync whose connection is not `active`, and honors a connector push channel where one exists — a verified Jira `jira:issue_updated` webhook or Box `events` notification enqueues a run within 30 s instead of waiting for the tick.
- **FR-F030-09:** `sync_cursors` holds one row per `(sync_id, direction)` with `cursor_kind` (`timestamp`, `token`, `page`, `sequence`), `cursor_value`, `high_water_mark`, `checkpoint_record_id`, and `updated_at`; a run reads changes strictly after `cursor_value`, checkpoints the cursor every 500 records inside the same transaction as the applied rows, and after a worker crash resumes from `checkpoint_record_id` rather than restarting the page; a cursor may be reset to a chosen timestamp only through `PATCH /api/v1/syncs/{id}` with `reset_cursor_to`, which records an audit event.
- **FR-F030-10:** Every record failure is classified `transient` (HTTP 429, 502, 503, 504, timeout, connection reset), `permanent` (400, 401, 403, 404, 422 from the provider), or `mapping` (transform or type failure); `transient` is retried up to 5 times with exponential backoff 1 s, 2 s, 4 s, 8 s, 16 s plus ±20% jitter honoring `Retry-After`; `permanent` and `mapping` failures are appended to the run as `sync_run_failed_records` rows without retry; a run ends `completed` with zero failures, `partial` when `records_failed` is under 10% of `records_read`, and `failed` at 10% or more, which also sets the sync to `state: error` and pauses its schedule; both counters are integer columns on `sync_runs`, so the threshold is evaluated and reported in SQL rather than parsed out of a document.
- **FR-F030-11:** `GET /api/v1/syncs/{id}/runs` returns cursor-paginated runs with `state` (`queued`, `running`, `completed`, `partial`, `failed`, `cancelled`), `trigger` (`schedule`, `manual`, `webhook`, `replay`), `started_at`, `finished_at`, `duration_ms`, the counter columns `records_read`, `records_created`, `records_updated`, `records_skipped`, `records_conflicted`, `records_failed`, `cursor_before`, `cursor_after`, `error_class`, and up to 50 failed records read from `sync_run_failed_records` with `external_id`, `classification`, and provider error code; the response keeps the `counters` object and the `failed_samples` array, which `SyncRunRepository` assembles from the columns and the child rows; runs publish `sync-run.completed.v1` or `sync-run.failed.v1` and are retained 90 days under the F027 sweep.
- **FR-F030-12:** `POST /api/v1/sync-runs/{id}/replay` with `{ dry_run?, only_failed? }` starts a new run of `trigger: replay` from the source run's `cursor_before`, or over just the external IDs returned by `SyncRunRepository::list_failed_records_for_replay(run_id)` when `only_failed` is true; `dry_run: true` returns `{ would_create, would_update, would_skip, would_conflict, samples[] }` without writing anything; replay is idempotent through `sync_record_links` keyed `(sync_id, external_id)` compared on `external_version`, so re-applying an already-applied record counts as `skipped`.
- **FR-F030-13:** When a record's OpsHub row and its external counterpart both changed since `cursor_value` — detected by comparing `sync_record_links.opshub_updated_at` and `external_updated_at` against the stored values — the run writes one `sync_conflicts` row with both timestamps and `state: open` plus one `sync_conflict_fields` row per conflicting field holding `column_id`, `external_field`, `opshub_value`, and `external_value`, and publishes `sync-conflict.detected.v1`; the API response still exposes `field_diffs` as an array, assembled by `SyncConflictRepository` from those rows; `conflict_policy` `manual` (default for F030) leaves both sides untouched, while `opshub_wins`, `external_wins`, and `newest_wins` apply the winner immediately and store the conflict `state: auto_resolved` with `resolution` for audit.
- **FR-F030-14:** `GET /api/v1/syncs/{id}/conflicts` lists conflicts filtered by `state`, joining `sync_conflict_fields` for both values per field, and `POST /api/v1/sync-conflicts/{id}/resolve` with `{ resolution: keep_opshub|keep_external|merge, field_values? }` under `If-Match` on the parent sync writes the chosen values to both sides, stores each chosen value in that field's `sync_conflict_fields.resolved_value`, sets `state: resolved` with `resolved_by` and `resolved_at`, and publishes `sync-conflict.resolved.v1`; `merge` requires `field_values` covering every `sync_conflict_fields` row of the conflict (`400 invalid` otherwise) and a conflict already `resolved` or `auto_resolved` returns `409 conflict`.
- **FR-F030-15:** `deletion_policy` is `ignore` (default), `mark_deleted` (write `true` into a nominated checkbox column), or `soft_delete` (set the row's `deleted_at` through the F006 service); OpsHub never issues a hard delete from a sync and never deletes in the external system unless `direction` is `outbound` and the policy is explicitly `soft_delete`, which maps to the connector's archive or closed state rather than a destructive call.
- **FR-F030-16:** The Jira connector syncs issues against a sheet: `source.object` is a project key with an optional JQL `filter`, mappable fields are `summary`, `description`, `status`, `assignee`, `reporter`, `duedate`, `priority`, `labels`, `issuetype`, `parent`, and `customfield_*` discovered through `/rest/api/3/field`; the cursor kind is `timestamp` over `updated` with a 2-minute overlap window for Jira's index lag; status writes go through the transition graph from `/rest/api/3/issue/{key}/transitions`, and a status with no legal transition fails that record as `permanent` with code `no_transition`.
- **FR-F030-17:** The Salesforce connector syncs `Account`, `Opportunity`, `Contact`, `Case`, and `Lead`: `source.filter` is a SOQL `WHERE` fragment validated against an allowlist that rejects subqueries and DML keywords, reads use `SystemModstamp` as a `timestamp` cursor, deletes come from `getDeleted`, and writes batch through the composite API in groups of 200 with per-record results mapped back to record outcomes; a Salesforce `REQUEST_LIMIT_EXCEEDED` is classified `transient` and pauses the run until the header-reported reset.
- **FR-F030-18:** The Box and Dropbox connectors bind an external folder to a sheet attachment column: new and changed external files are downloaded through the F013 file service (ClamAV scan, MIME allowlist, 100 MB per file, 2 GB per run) and attached to the row whose key column matches the file-name key pattern; the cursor is Box `stream_position` or Dropbox `list_folder/continue`; outbound direction uploads OpsHub attachments to the folder; a file failing the scan is recorded `permanent` with code `scan_rejected` and never attached.
- **FR-F030-19:** The Tableau connector is outbound only: `analytics` syncs publish a F023 report result as a Hyper extract to a named Tableau project and datasource, replacing the datasource per run, recording the returned datasource LUID in `sync_record_links`; the read-only `database` connector is inbound only, taking a DSN from the F004 secret manager key `connectors/database/{sync_id}/dsn`, an explicit `schema.table` or named-query allowlist held as `sync_database_objects` rows (one row per permitted object, `object_kind` in `('table','named_query')`, the named query's parameterized text in `statement_text`) so the allowlist is joined and constrained rather than parsed from a list, parameterized statements only, a 30 s statement timeout, and a 50,000-row per-run cap that ends the run `partial` with code `row_cap_reached`; no DDL or DML statement may be issued on either path.
- **FR-F030-20:** Every route requires the `integration-admin` role; mutations require `Idempotency-Key` and write audit events; cross-tenant sync, run, and conflict IDs return `404 not_found`; a sync may not target a sheet the actor cannot edit, and losing that permission later fails the run `permanent` with code `target_denied` rather than writing.
- **FR-F030-21:** `/admin/syncs` lists syncs with connector, direction, state, last run, and open-conflict count; a three-step wizard picks a connection and object, maps fields with type-checked pickers and a live preview of five source records, and sets schedule, conflict, and deletion policy; a sync detail page shows run history with counters, a failed-record table, `Run now`, `Replay`, `Dry-run replay`, and a conflict queue where each row shows both values per field with `Keep OpsHub`, `Keep external`, and `Merge`.

### Non-functional requirements

- **NFR-F030-01 Performance:** `GET /api/v1/syncs` and `GET /api/v1/syncs/{id}/conflicts` under 500 ms p95 with 200 syncs and 5,000 open conflicts; run enqueue acknowledges under 2 s p95; a 10,000-record inbound run completes within 10 minutes with the mock connector at 200 records per page; mapping preview of five records returns under 1 s; a single transform evaluates under 5 ms.
- **NFR-F030-02 Security/privacy:** F030 stores no credentials — access tokens come from the F029 vault per call and database DSNs from the secret manager, never from `syncs` or `sync_mappings`; the database connector is read-only with parameterized statements and an object allowlist; transforms have no network or filesystem access; `sync_run_failed_records` stores field values only as SHA-256 digests in `message_digest` and leaves `provider_payload` null unless the sync sets `debug_payloads: true`, which retains the raw provider response snapshot for 7 days and writes an audit event; provider webhooks are signature-verified before enqueueing; cross-tenant reads and writes are tested negative on every route.
- **NFR-F030-03 Accessibility:** `/admin/syncs`, the wizard, the mapping editor, and the conflict queue pass axe with zero serious or critical violations; mapping rows are reorderable and editable from the keyboard with no drag-only path; the conflict diff exposes OpsHub and external values as a labelled comparison readable in sequence by a screen reader; run and conflict states use text plus icon, never color alone.
- **NFR-F030-04 Reliability/observability:** runs are idempotent per `(sync_id, external_id, external_version)`, resume from the last checkpoint after a worker restart, and dead-letter after 5 transient attempts with the sync marked `error`; metrics `sync_records_total{connector,direction,outcome}`, `sync_run_duration_seconds{connector,kind}`, `sync_conflicts_open{connector}`, and `sync_cursor_lag_seconds{sync_id}`; every run has a tracing span carrying `sync_id`, `run_id`, `connector`, and `correlation_id`, and every provider call reuses the F029 `integration_events` log.
- **NFR-F030-05 Limits and compatibility:** at most 200 syncs per tenant, 300 mappings per sync, 5 concurrent runs per tenant and 1 per sync, and one active sync per `(connection_id, source.object, target.sheet_id, direction)`; connector API versions are pinned (Jira REST v3, Salesforce v61.0, Box 2.0, Dropbox v2, Tableau REST 3.21) and recorded on every run so a version bump is a deliberate, tested change.

### Scope

Included: the connector registry and shared run engine, six connectors (Jira, Salesforce, Box, Dropbox, Tableau, read-only database), sync definitions and lifecycle, field mappings and the transform catalog, cursor and checkpoint state, error classification with retry and backoff, run history and failed-record samples, replay including dry-run and failed-only, the conflict queue with detection, policy resolution, and manual resolution, deletion policies, and the `/admin/syncs` surface.

Excluded: OAuth authorization, the token vault, connection lifecycle, and the three Microsoft/Google/Slack adapters (F029, consumed here); calendar and chat sync (F029); REST API conventions, pagination, and outbound webhooks (F028); notification routing and digests (F037); cross-system multi-step workflow runs and connector actions (F054, which consumes F030); sheet, row, and column semantics (F006); file storage and scanning internals (F013); report generation for Tableau extracts (F023); entitlement packaging of premium connectors (F049).

## 3. UX specification

- Entry points: admin navigation `Syncs`; routes `/admin/syncs`, `/admin/syncs/new`, `/admin/syncs/:syncId`, `/admin/syncs/:syncId/conflicts`; a sheet's `Connected syncs` panel links to any sync targeting it.
- Primary flow: an administrator opens `/admin/syncs`, clicks `New sync`, picks the Jira connection and project `OPS`, chooses sheet `Delivery board`, maps `summary → Task name`, `status → Status` with `value_map`, `duedate → Due` with `date_tz("America/Chicago")`, and `assignee → Owner` with `lookup`, sees a five-record preview, picks `every_15m`, `manual` conflicts, `mark_deleted`, saves, and activates. The first run reports `read 412, created 412`. A later run reports `conflicted 3`; the administrator opens the conflict queue, sees the OpsHub and Jira due dates side by side, and clicks `Keep external` on two and `Merge` on one.
- Loading: table and mapping skeletons; Empty: `/admin/syncs` shows connector cards with `New sync` and a note when no F029 connection is active; Error: banner with `correlation_id` and retry; Denied: non-admins get the denied page; Success: toasts for save, activate, run, replay, and resolve.
- Wizard: step 1 connection and object with `filter` field and inline validation of JQL or SOQL; step 2 mapping editor with a source-field list, a column picker filtered to compatible types, a transform picker with argument inputs, a `required` toggle, and `Preview 5 records`; step 3 schedule, direction, conflict policy, and deletion policy radio groups with one-line explanations.
- Run history: table with state pill, trigger, counters, duration, cursor before/after, and an expandable failed-record table showing `external_id`, classification, and provider code; `Replay` and `Dry-run replay` open a confirmation that names the record count.
- Conflict queue: one row per record with the field diff expanded inline, `Keep OpsHub`, `Keep external`, `Merge` (opens a per-field chooser), bulk `Keep external` limited to 100 selected rows, and a filter for `open` and `resolved`.
- Responsive: the mapping editor becomes a stacked card list under 900 px; the conflict diff stacks OpsHub above external under 768 px; the wizard fits 320 px.
- Keyboard: mapping rows move with `Alt+ArrowUp`/`Alt+ArrowDown`; the wizard traps focus per step and restores it to the invoking control; `Escape` closes the merge chooser without applying; reduced motion disables the run-state pulse.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062); Lucide icons `RefreshCcw`, `ArrowLeftRight`, `Columns3`, `History`, `GitMerge`, `AlertTriangle`, `Database`; tokens from `apps/web/src/design/tokens.css`.

- Design: `design/artboards/Integrations.dc.html` on the canvas indexed by `design/canvas.json`. The ticket is the contract and the artboard is the picture; when they disagree the ticket wins.

## 4. Technical specification

### Rust backend

- Data access (decision section 2.1): `crates/persistence/src/connectors/` holds `SyncRepository` (owns `syncs`, `sync_database_objects`), `SyncMappingRepository` (`sync_mappings`, `sync_mapping_transform_args`, `sync_mapping_value_map`), `SyncRunRepository` (`sync_runs`, `sync_run_failed_records`), `SyncCursorRepository` (`sync_cursors`), `SyncConflictRepository` (`sync_conflicts`, `sync_conflict_fields`), and `SyncRecordLinkRepository` (`sync_record_links`); each child table is written only by the repository of its parent object type, so no two classes write the same table. Named queries: `find_active_sync_for_tuple`, `list_syncs_for_connection`, `list_due_syncs`, `set_sync_state`, `replace_database_objects`, `list_database_objects`, `replace_mapping_set`, `list_mappings_with_transforms`, `list_value_map_entries`, `open_run`, `finalize_run`, `list_runs_for_sync`, `append_failed_records`, `list_failed_records_for_replay`, `delete_runs_older_than`, `expire_debug_payloads`, `load_cursor`, `checkpoint_cursor`, `reset_cursor_to`, `insert_conflict_with_fields`, `list_conflicts_by_state`, `count_open_conflicts`, `settle_conflict`, `delete_resolved_conflicts_before`, `find_link_by_external_id`, `upsert_record_links`, `mark_external_deleted` — there is no generic query entry point. Every use case, adapter, engine stage, API handler, and worker job below depends on these traits and contains no SQL or SQLx call; a mapping replacement, a checkpoint (cursor plus record links plus applied rows), a run finalization with its failed records, and a conflict resolution each run as one `UnitOfWork` shared with the F006 row repositories.
- Domain entities in `crates/domain/src/connectors/`: `Connector { id: ConnectorId (Jira|Salesforce|Box|Dropbox|Tableau|Database), sync_kinds, directions, cursor_kind, api_version }`, `Sync { id, tenant_id, connection_id, name, connector, kind, source_object, source_filter, target_sheet_id, direction, schedule, conflict_policy, deletion_policy, deletion_column_id, debug_payloads, state: Paused|Active|Error, last_run_id, version, audit fields, deleted_at }`, `SyncMapping { id, sync_id, external_field, column_id, direction, transform: Transform, required, default_value, position }`, `SyncRun { id, sync_id, trigger, state, counters: RunCounters, cursor_before, cursor_after, error_class, api_version, started_at, finished_at }`, `SyncCursor { sync_id, direction, cursor_kind, cursor_value, high_water_mark, checkpoint_record_id }`, `SyncConflict { id, sync_id, record_link_id, field_diffs, opshub_updated_at, external_updated_at, state, resolution, resolved_by, resolved_at, version }`, `SyncRecordLink { sync_id, external_id, row_id, external_version, external_updated_at, opshub_updated_at, deleted_external }`.
- Traits in `crates/domain/src/connectors/adapter.rs`: `RecordSource { list_changes(cursor, page_size) -> ChangePage { records, next_cursor, has_more } , describe_fields() }`, `RecordSink { upsert(batch) -> Vec<RecordOutcome>, archive(external_id) }`, `FileSource { list_changes, download(file_id) }`, `ExtractSink { publish(extract) }`; each implementation in `crates/domain/src/connectors/adapters/{jira.rs, salesforce.rs, box_files.rs, dropbox.rs, tableau.rs, database.rs}` builds on the F029 `HttpClient` (timeout, retry, `Retry-After`, `integration_events` logging) and the F029 `TokenSource`; `database.rs` uses a separate SQLx pool with `default_transaction_read_only = on`.
- Run engine in `crates/domain/src/connectors/engine/{mod.rs, plan.rs, apply.rs, checkpoint.rs, classify.rs}`: `run(sync, trigger)` loads the cursor, pages the source, maps records through `mapping::apply`, detects conflicts through `conflict::detect`, applies writes through the F006 row service, checkpoints every 500 records, and finalizes counters; `classify.rs` maps provider errors to `Transient | Permanent | Mapping`; `checkpoint.rs` holds no SQL and calls `SyncCursorRepository::checkpoint_cursor` and `SyncRecordLinkRepository::upsert_record_links` inside the same `UnitOfWork` transaction that applies the rows.
- Mapping and transforms in `crates/domain/src/connectors/mapping/{mod.rs, transform.rs, validate.rs}`: `Transform` is a closed enum parsed from `{ name, args }`; `transform::apply(&Transform, ExternalValue, &LookupCtx) -> Result<CellValue, MappingError>`; `validate::check(mapping, column, connector_field)` enforces type compatibility and the duplicate, required, and count rules.
- Use cases: `create_sync`, `update_sync`, `list_syncs`, `get_sync`, `replace_mappings`, `preview_mapping`, `trigger_run`, `pause_sync`, `list_runs`, `replay_run`, `list_conflicts`, `resolve_conflict`, `reset_cursor`.
- API endpoints (`services/api/src/connectors/`): `GET /api/v1/syncs`, `POST /api/v1/syncs`, `GET /api/v1/syncs/{id}`, `PATCH /api/v1/syncs/{id}`, `PUT /api/v1/syncs/{id}/mappings`, `POST /api/v1/syncs/{id}/run`, `POST /api/v1/syncs/{id}/pause`, `GET /api/v1/syncs/{id}/runs`, `POST /api/v1/sync-runs/{id}/replay`, `GET /api/v1/syncs/{id}/conflicts`, `POST /api/v1/sync-conflicts/{id}/resolve`. DTOs: `SyncRequest`, `SyncResponse`, `Page<SyncSummary>`, `MappingSetRequest { mappings: Vec<MappingRequest> }`, `MappingSetResponse`, `MappingPreviewResponse { records: Vec<PreviewRecord> }`, `RunResponse`, `Page<RunSummary>`, `ReplayRequest { dry_run, only_failed }`, `ReplayResponse`, `ConflictResponse { field_diffs }`, `ResolveConflictRequest { resolution, field_values }`.
- Worker jobs (`services/worker/src/connectors/`): `schedule.rs` (every minute, enqueues due active syncs), `run.rs` (JetStream consumer executing one run with per-sync concurrency 1 held by an advisory lock on `sync_id`), `webhook.rs` (verifies Jira and Box push payloads and enqueues), `sweep.rs` (nightly: 90-day run retention, 7-day `debug_payloads` sample expiry, 180-day resolved-conflict removal). No worker job opens a pool or issues SQL: `schedule.rs` calls `SyncRepository::list_due_syncs`, `run.rs` drives the engine through the repository traits, `webhook.rs` resolves the sync with `SyncRepository::list_syncs_for_connection`, and `sweep.rs` calls `SyncRunRepository::delete_runs_older_than`, `::expire_debug_payloads`, and `SyncConflictRepository::delete_resolved_conflicts_before`.
- Events: `sync.updated.v1`, `sync-run.started.v1`, `sync-run.completed.v1`, `sync-run.failed.v1`, `sync-conflict.detected.v1`, `sync-conflict.resolved.v1`.
- Authorization: `integration-admin` on every route plus edit permission on `target_sheet_id`; cross-tenant maps to `not_found`.
- Validation: connector supports `kind` and `direction`; connection `active`; `source_filter` parsed by the connector's filter validator; mapping rules from FR-F030-05; `deletion_column_id` required when `deletion_policy = mark_deleted`; limits from NFR-F030-05.
- Error mapping: `ConnectorError::UnsupportedKind → 400 invalid`, `::InvalidFilter → 400 invalid`, `::MappingInvalid → 400 invalid`, `::ConnectionNotActive → 409 conflict`, `::RunInProgress → 409 conflict`, `::StaleVersion → 409 conflict`, `::ConflictSettled → 409 conflict`, `::LimitExceeded → 429 rate_limited`, `::ProviderUnavailable → 502 unavailable`, `::NotFound → 404 not_found`, `AuthzError::Denied → 403 denied`.

### Interface

Ids are UUIDv7 strings, timestamps RFC 3339 UTC, `version` an integer incrementing by one per write.
`T?` is nullable and an absent optional field equals an explicit `null`. Unlisted fields are rejected
with `400 invalid`. `Page<T>`, the opaque cursor and the error body are F028's; `CellValue` is F007's
and is not restated here. Every route requires `integration-admin`; mutations require
`Idempotency-Key`. Mutations also require `If-Match` carrying the
aggregate's current `version`, the convention `docs/engineering-standards.md` §6 makes binding; a
stale value is `409 conflict` with the current `version` in the body. `PUT /api/v1/syncs/{id}/mappings`
and `POST /api/v1/sync-conflicts/{id}/resolve` each match against the parent sync's version, which is
the aggregate they belong to, so neither needs a version field of its own inside the body.

**`SyncRequest`** — `POST /api/v1/syncs`, and the same shape as `PATCH /api/v1/syncs/{id}` with every
field optional, at least one present, and the version carried in `If-Match` rather than the body.

| Field | Type | Required | Constraint |
|---|---|---|---|
| `connection_id` | uuid | create only | an F029 connection of this tenant in `status: active`; `needs_reauth` or `revoked` → `409 conflict` with `field_errors.connection_id = "connection_not_active"`; immutable after create |
| `name` | string | yes | 1–200 chars after trim |
| `kind` | `work\|crm\|file\|analytics\|db_read` | create only | must be in the connector's declared `sync_kinds`, else `400 invalid` with `field_errors.kind = "unsupported"` |
| `source` | `{ object: string, filter: string? }` | create only for `object` | `object` 1–512 chars; `filter` ≤ 4,000 chars and parsed by the connector's filter validator (JQL for `jira`, allowlisted SOQL `WHERE` for `salesforce`), a rejection giving `field_errors.source.filter = "invalid_filter"` |
| `target` | `{ sheet_id: uuid }` | create only | the caller must hold edit on the sheet; unreadable → `404 not_found`, readable but not editable → `403 denied`; immutable after create |
| `direction` | `inbound\|outbound\|bidirectional` | create only | must be in the connector's `directions`, else `field_errors.direction = "unsupported"` |
| `schedule` | `manual\|every_5m\|every_15m\|hourly\|daily_at_02_00_utc` | no | default `every_15m` |
| `state` | `paused\|active\|error` | no | create ignores it and returns `paused`; `PATCH` to `active` with an empty mapping set → `400 invalid` with `field_errors.state = "no_mappings"`; `error` is set by the engine and is rejected from a client |
| `conflict_policy` | `manual\|opshub_wins\|external_wins\|newest_wins` | no | default `manual` |
| `deletion_policy` | `ignore\|mark_deleted\|soft_delete` | no | default `ignore` |
| `deletion_column_id` | uuid? | conditional | required when `deletion_policy` is `mark_deleted`, must be a `checkbox` column of the target sheet |
| `debug_payloads` | bool | no | default `false`; enabling writes an audit event and retains raw provider snapshots 7 days |
| `database_objects` | DatabaseObject[] | conditional | `database` connector only, 1–50 entries, each `{ object_kind: "table"\|"named_query", object_ref, statement_text? }` with `statement_text` required for `named_query` and parameterized; replaces the allowlist whole |
| `reset_cursor_to` | timestamp? | no | `PATCH` only; rewinds the inbound cursor and writes `sync.cursor-reset` |

The 201st live sync in a tenant is `429 rate_limited`. A second live sync with the same
`(connection_id, source.object, target.sheet_id, direction)` is `409 conflict` with
`field_errors.source.object = "duplicate_binding"`.

**`SyncResponse`** — `GET /api/v1/syncs/{id}` and the body of create, `PATCH` and pause

| Field | Type | Notes |
|---|---|---|
| `id`, `connection_id`, `name`, `kind`, `direction`, `schedule`, `state` | | |
| `connector` | `jira\|salesforce\|box\|dropbox\|tableau\|database` | derived from the connection, never sent |
| `source` / `target` | as request | |
| `conflict_policy`, `deletion_policy`, `deletion_column_id?`, `debug_payloads` | | |
| `mappings` | MappingResponse[] | detail read only; omitted from the list route |
| `cursors` | CursorSnapshot[] | detail read only; one per direction, `{ direction, cursor_kind, cursor_value?, high_water_mark?, updated_at }` |
| `recent_runs` | RunSummary[] | detail read only; the last five, newest first |
| `last_run_at` / `last_run_state` | timestamp? / string? | null before the first run |
| `open_conflicts` | integer | count of `sync_conflicts` in `state: open` |
| `version`, `created_at`, `created_by`, `updated_at`, `updated_by`, `deleted_at?` | | |

**`GET /api/v1/syncs`** returns `Page<SyncSummary>` — `SyncResponse` without `mappings`, `cursors` and
`recent_runs` — sorted `updated_at desc`, filtered by `connection_id`, `connector`, `kind` and `state`,
with F028's `cursor`, `limit` (1–100, default 50) and `include_total`.

**`MappingSetRequest`** — `PUT /api/v1/syncs/{id}/mappings`: `{ mappings: MappingRequest[] }` under `If-Match` on the parent sync. The set is replaced whole; 0–300 entries, and array order is the stored `position`.

**`MappingRequest`**

| Field | Type | Required | Constraint |
|---|---|---|---|
| `external_field` | string | yes | 1–256 chars; must exist in the connector's `describe_fields()`; unique per `(direction)` in the set |
| `column_id` | uuid | yes | a live column of `target.sheet_id`; unique per `(direction)` in the set |
| `direction` | `inbound\|outbound` | yes | must be compatible with the sync's `direction` |
| `transform` | Transform | no | default `{ name: "identity", args: {} }` |
| `required` | bool | no | default `false`; `true` on a nullable external field with no `default_value` → `400 invalid` with `field_errors["mappings[i].required"] = "needs_default"` |
| `default_value` | CellValue? | no | must satisfy the column's F007 type |

**`Transform`** — `{ name, args }` where `name` is one of the twelve catalog members and `args` carries
exactly the argument names that member takes. The pairs are: `identity`, `trim`, `lower`, `upper` take
none; `date_tz` takes `tz` (IANA name); `datetime_format` takes `pattern`; `number_scale` takes
`factor` (decimal); `value_map` takes `map` (object of external string to OpsHub string, 1–1,000
pairs, distinct keys); `join` takes `separator`; `split` takes `separator` and `index` (≥ 0);
`template` takes `pattern`; `lookup` takes `sheet_id`, `key_column_id` and `value_column_id`. An
unknown `name`, a missing argument, an extra argument or an unparseable value is `400 invalid` with
`field_errors["mappings[i].transform"]` naming which. A transform whose output type cannot fill the
column is `400 invalid` with the same pointer and `"type_mismatch"`.

**`MappingResponse`** is `MappingRequest` plus `{ id, position }`; **`MappingSetResponse`** is
`{ mappings: MappingResponse[], version }` where `version` is the sync's new version.

**`MappingPreviewResponse`**: `{ records: [{ external_id, source: map<string, string>, mapped: map<uuid, CellValue>, errors: [{ external_field, code, message }] }] }` for the first five source records. A preview reads the provider and writes nothing.

**`POST /api/v1/syncs/{id}/run`** takes no body and returns `202` with `{ run_id, state: "queued" }`. A
run while one is `queued` or `running` is `409 conflict` with `details.run_id` naming the active one.
**`POST /api/v1/syncs/{id}/pause`** takes no body and returns `200` with `SyncResponse` in `paused`.

**`RunSummary`** — the item of `Page<RunSummary>` from `GET /api/v1/syncs/{id}/runs`, sorted `started_at desc`

| Field | Type | Notes |
|---|---|---|
| `id`, `sync_id` | uuid | |
| `trigger` | `schedule\|manual\|webhook\|replay` | |
| `state` | `queued\|running\|completed\|partial\|failed\|cancelled` | `partial` under 10% failed, `failed` at 10% or more |
| `counters` | `{ records_read, records_created, records_updated, records_skipped, records_conflicted, records_failed }` | assembled from the six integer columns |
| `cursor_before` / `cursor_after` | string? | null on a run that never checkpointed |
| `error_class` | `transient\|permanent\|mapping`? | null unless the run ended `failed` |
| `api_version` | string | the pinned connector API version this run used |
| `started_at` / `finished_at` / `duration_ms` | | null while `queued` |
| `failed_samples` | FailedRecord[] | at most 50, newest first; present on the run detail and omitted from the page items |

**`FailedRecord`**: `{ external_id, classification: "transient"|"permanent"|"mapping", provider_code: string?, message_digest: string (lowercase hex SHA-256), occurred_at }`. The message itself is never returned — only its digest — which is what keeps provider payloads out of the API.

**`ReplayRequest`** — `POST /api/v1/sync-runs/{id}/replay`: `{ dry_run: bool = false, only_failed: bool = false }`. With `dry_run: false` the response is `202` with a new `RunSummary` of `trigger: replay`; with `dry_run: true` it is `200` with **`ReplayResponse`** `{ would_create, would_update, would_skip, would_conflict, samples: [{ external_id, action: "create"|"update"|"skip"|"conflict" }] }` capped at 50 samples and writing nothing.

**`ConflictResponse`** — the item of `GET /api/v1/syncs/{id}/conflicts`

| Field | Type | Notes |
|---|---|---|
| `id`, `sync_id`, `external_id`, `row_id?` | | `row_id` null when the OpsHub side was deleted |
| `field_diffs` | `[{ column_id, external_field, opshub_value: CellValue?, external_value: CellValue?, resolved_value: CellValue? }]` | assembled from `sync_conflict_fields`; `resolved_value` null while `open` |
| `opshub_updated_at` / `external_updated_at` | timestamp? | the two timestamps whose disagreement made this a conflict |
| `state` | `open\|resolved\|auto_resolved` | |
| `resolution` | `keep_opshub\|keep_external\|merge\|opshub_wins\|external_wins\|newest_wins`? | the last three are policy outcomes, the first three human ones |
| `resolved_by?`, `resolved_at?`, `detected_at`, `version` | | |

The list is `Page<ConflictResponse>` sorted `detected_at desc`, filtered by `state`, `limit` 1–100.

**`ResolveConflictRequest`** — `POST /api/v1/sync-conflicts/{id}/resolve`

| Field | Type | Required | Constraint |
|---|---|---|---|
| `resolution` | `keep_opshub\|keep_external\|merge` | yes | a policy name here is `400 invalid`: policies are applied by the engine, not by a person |
| `field_values` | map<uuid, CellValue> | conditional | required with `merge`, rejected otherwise; keys must cover **every** `field_diffs` entry, else `400 invalid` with `field_errors.field_values = "incomplete"` |

A conflict already `resolved` or `auto_resolved` is `409 conflict` with `field_errors.state = "settled"`.

Status codes:

| Code | Produced by |
|---|---|
| `200` | reads, `PATCH`, `PUT` mappings, pause, resolve, dry-run replay |
| `201` | `POST /api/v1/syncs` |
| `202` | `POST /api/v1/syncs/{id}/run`, non-dry replay |
| `400 invalid` | unsupported `kind` or `direction`, `invalid_filter`, any mapping rule, `no_mappings` on activation, `needs_default`, `type_mismatch`, `incomplete` merge, a client-supplied `state: error` |
| `403 denied` | not `integration-admin`, or no edit permission on `target.sheet_id` |
| `404 not_found` | sync, run, conflict, connection or sheet in another tenant or invisible to the caller |
| `409 conflict` | `connection_not_active`, `duplicate_binding`, a run already in flight, stale `If-Match`, a settled conflict, `Idempotency-Key` replayed with a different body |
| `429 rate_limited` | 200 syncs per tenant, 5 concurrent runs per tenant, or the route quota |
| `502 unavailable` | the provider is unreachable or returns 5xx during a preview or a synchronous describe; a provider failure **inside a run** is not an HTTP error but a record classification |

### Use case signatures

In `crates/domain/src/connectors/`; workers in `services/worker/src/connectors/`. `Ctx` is F038's
`ActorContext`.

```rust
fn create_sync(ctx: &Ctx, uow: &mut UnitOfWork, req: SyncRequest) -> Result<Sync, DomainError>;
fn update_sync(ctx: &Ctx, uow: &mut UnitOfWork, id: SyncId, expected: Version, req: SyncPatch) -> Result<Sync, DomainError>;
fn list_syncs(ctx: &Ctx, repo: &dyn SyncRepository, filter: SyncFilter, page: Cursor) -> Result<Page<SyncSummary>, DomainError>;
fn get_sync(ctx: &Ctx, repo: &dyn SyncRepository, id: SyncId) -> Result<SyncDetail, DomainError>;
fn replace_mappings(ctx: &Ctx, uow: &mut UnitOfWork, id: SyncId, expected: Version, set: Vec<MappingRequest>) -> Result<MappingSet, DomainError>;
fn preview_mapping(ctx: &Ctx, repo: &dyn SyncRepository, id: SyncId, source: &dyn RecordSource) -> Result<Vec<PreviewRecord>, DomainError>;
fn trigger_run(ctx: &Ctx, uow: &mut UnitOfWork, id: SyncId, trigger: RunTrigger) -> Result<SyncRun, DomainError>;
fn pause_sync(ctx: &Ctx, uow: &mut UnitOfWork, id: SyncId, expected: Version) -> Result<Sync, DomainError>;
fn list_runs(ctx: &Ctx, repo: &dyn SyncRunRepository, id: SyncId, page: Cursor) -> Result<Page<RunSummary>, DomainError>;
fn replay_run(ctx: &Ctx, uow: &mut UnitOfWork, run: RunId, req: Replay) -> Result<ReplayOutcome, DomainError>;
fn list_conflicts(ctx: &Ctx, repo: &dyn SyncConflictRepository, id: SyncId, filter: ConflictFilter, page: Cursor) -> Result<Page<SyncConflict>, DomainError>;
fn resolve_conflict(ctx: &Ctx, uow: &mut UnitOfWork, id: ConflictId, expected: Version, req: ResolveConflict) -> Result<SyncConflict, DomainError>;
fn reset_cursor(ctx: &Ctx, uow: &mut UnitOfWork, id: SyncId, expected: Version, to: Timestamp) -> Result<SyncCursor, DomainError>;
```

#### Adapter traits

One implementation per provider in `crates/domain/src/connectors/adapters/`, so these are the contract
between the shared engine and six different vendors. They are defined here in full because a provider
author implements them without reading the engine.

```rust
/// Inbound: read changes since a cursor. Implemented by jira, salesforce, box, dropbox, database.
pub trait RecordSource: Send + Sync {
    fn cursor_kind(&self) -> CursorKind;
    /// Records strictly after `cursor`. `page_size` is a hint the adapter may lower to the
    /// provider's maximum but must never raise.
    fn list_changes(&self, ctx: &Ctx, cursor: Option<&CursorValue>, page_size: u32) -> Result<ChangePage, ConnectorError>;
    /// The mappable fields, for the mapping editor and for `validate::check`.
    fn describe_fields(&self, ctx: &Ctx) -> Result<Vec<ExternalField>, ConnectorError>;
}

/// Outbound: write records back. Implemented by jira, salesforce, box, dropbox.
pub trait RecordSink: Send + Sync {
    /// One outcome per input record, in input order. A partial batch failure is reported
    /// per record, never as an `Err` for the whole batch.
    fn upsert(&self, ctx: &Ctx, batch: &[OutboundRecord]) -> Result<Vec<RecordOutcome>, ConnectorError>;
    /// The non-destructive deletion path: archive or close, never a hard delete.
    fn archive(&self, ctx: &Ctx, external_id: &ExternalId) -> Result<RecordOutcome, ConnectorError>;
}

/// File-bearing connectors. Implemented by box and dropbox.
pub trait FileSource: RecordSource {
    fn download(&self, ctx: &Ctx, file_id: &ExternalId) -> Result<FileStream, ConnectorError>;
}

/// Analytics publication. Implemented by tableau, outbound only.
pub trait ExtractSink: Send + Sync {
    fn publish(&self, ctx: &Ctx, extract: Extract, target: &DatasourceRef) -> Result<DatasourceLuid, ConnectorError>;
}
```

`ChangePage` is `{ records: Vec<ExternalRecord>, next_cursor: Option<CursorValue>, has_more: bool }`;
`ExternalRecord` is `{ external_id, external_version: Option<String>, external_updated_at: Option<Timestamp>, fields: Map<String, ExternalValue>, deleted: bool }`; `RecordOutcome` is
`Created | Updated | Skipped | Failed { classification, provider_code, message }`. Every adapter method
returns `ConnectorError`, never `DomainError`: classification into `Transient | Permanent | Mapping`
is `classify.rs`'s job, so a new provider cannot decide its own retry policy.

Transaction boundaries:

- `create_sync` and `update_sync` write the `syncs` row, the replaced `sync_database_objects` set, the
  audit row and the `sync.updated.v1` outbox row in one `UnitOfWork`. The uniqueness index on the
  binding tuple only means something if the row and its allowlist land together.
- `replace_mappings` writes the delete of removed `sync_mappings` rows, the insert or update of the
  kept ones, every `sync_mapping_transform_args` and `sync_mapping_value_map` row, the sync's version
  bump and the audit row in one boundary. A mapping whose transform arguments are missing would run
  and silently produce wrong cells, which is worse than not running.
- The engine's **checkpoint** is the important one: every 500 records, one `UnitOfWork` covers the
  F006 row writes for those records, their `sync_record_links` upserts, any `sync_conflicts` and
  `sync_conflict_fields` rows detected, and the `sync_cursors` advance. All four or none — a cursor
  that advanced past rows that were not written loses data permanently, and record links written
  without the cursor advance cause the next run to re-apply them.
- `trigger_run` writes the `sync_runs` row in `queued` and the JetStream message through the outbox in
  one boundary; the run's finalization writes the six counters, `state`, `finished_at`, every
  `sync_run_failed_records` row and the completion event in another.
- `resolve_conflict` writes each `sync_conflict_fields.resolved_value`, the OpsHub cell writes through
  the F006 repositories, the outbound record write, the conflict's `state`, `resolved_by`,
  `resolved_at` and the outbox event in one `UnitOfWork`. Resolving one side and failing the other
  would leave the two systems disagreeing with no conflict row left to say so.
- `preview_mapping`, `list_*` and a `dry_run` replay open no `UnitOfWork` and take repositories
  directly; a dry run that could write would not be a dry run.

### PostgreSQL/SQLx

- Migration `*_connectors_*.sql` creates `syncs(id uuid pk, tenant_id uuid not null, connection_id uuid not null references integration_connections(id) on delete restrict, name text not null, connector text not null check (connector in ('jira','salesforce','box','dropbox','tableau','database')), kind text not null check (kind in ('work','crm','file','analytics','db_read')), source_object text not null, source_filter text, target_sheet_id uuid not null references sheets(id) on delete restrict, direction text not null check (direction in ('inbound','outbound','bidirectional')), schedule text not null default 'every_15m' check (schedule in ('manual','every_5m','every_15m','hourly','daily_at_02_00_utc')), conflict_policy text not null default 'manual' check (conflict_policy in ('manual','opshub_wins','external_wins','newest_wins')), deletion_policy text not null default 'ignore' check (deletion_policy in ('ignore','mark_deleted','soft_delete')), deletion_column_id uuid references columns(id) on delete restrict, debug_payloads boolean not null default false, state text not null default 'paused' check (state in ('paused','active','error')), last_run_id uuid, version bigint not null default 1, audit fields, deleted_at)`, `sync_mappings(id uuid pk, tenant_id, sync_id uuid not null references syncs(id) on delete cascade, external_field text not null, column_id uuid not null references columns(id) on delete restrict, direction text not null check (direction in ('inbound','outbound')), transform_name text not null default 'identity' check (transform_name in ('identity','trim','lower','upper','date_tz','datetime_format','number_scale','value_map','join','split','template','lookup')), required boolean not null default false, default_value jsonb, position int not null)`, `sync_runs(id uuid pk, tenant_id, sync_id uuid not null references syncs(id) on delete cascade, trigger text not null check (trigger in ('schedule','manual','webhook','replay')), state text not null check (state in ('queued','running','completed','partial','failed','cancelled')), records_read bigint not null default 0, records_created bigint not null default 0, records_updated bigint not null default 0, records_skipped bigint not null default 0, records_conflicted bigint not null default 0, records_failed bigint not null default 0, cursor_before text, cursor_after text, error_class text check (error_class is null or error_class in ('transient','permanent','mapping')), api_version text not null, mapping_version bigint, started_at timestamptz, finished_at timestamptz, duration_ms int)`, `sync_cursors(sync_id uuid not null references syncs(id) on delete cascade, direction text not null check (direction in ('inbound','outbound')), cursor_kind text not null check (cursor_kind in ('timestamp','token','page','sequence')), cursor_value text, high_water_mark timestamptz, checkpoint_record_id text, updated_at timestamptz not null, primary key (sync_id, direction))`, `sync_conflicts(id uuid pk, tenant_id, sync_id uuid not null references syncs(id) on delete cascade, external_id text not null, row_id uuid references rows(id) on delete cascade, opshub_updated_at timestamptz, external_updated_at timestamptz, state text not null default 'open' check (state in ('open','resolved','auto_resolved')), resolution text check (resolution is null or resolution in ('keep_opshub','keep_external','merge','opshub_wins','external_wins','newest_wins')), resolved_by uuid references users(id) on delete restrict, resolved_at timestamptz, version bigint not null default 1, detected_at timestamptz not null)`, `sync_record_links(sync_id uuid not null references syncs(id) on delete cascade, external_id text not null, tenant_id, row_id uuid not null references rows(id) on delete cascade, external_version text, external_updated_at timestamptz, opshub_updated_at timestamptz, deleted_external boolean not null default false, primary key (sync_id, external_id))`; `syncs.last_run_id` gains `references sync_runs(id) on delete set null` in a follow-up `alter table` once `sync_runs` exists, since the two tables reference each other.
- Normalized sets (decision section 2, no array or repeating-group columns): `sync_mapping_transform_args(mapping_id uuid not null references sync_mappings(id) on delete cascade, tenant_id, arg_name text not null check (arg_name in ('tz','pattern','factor','separator','index','sheet_id','key_column_id','value_column_id')), arg_value text not null, primary key (mapping_id, arg_name))` and `sync_mapping_value_map(mapping_id uuid not null references sync_mappings(id) on delete cascade, tenant_id, external_value text not null, opshub_value text not null, primary key (mapping_id, external_value))` replace `sync_mappings.transform jsonb`, whose `name` and `args` keys the validator and evaluator read by key; `sync_run_failed_records(run_id uuid not null references sync_runs(id) on delete cascade, tenant_id, external_id text not null, classification text not null check (classification in ('transient','permanent','mapping')), provider_code text, message_digest bytea not null, provider_payload jsonb, occurred_at timestamptz not null, primary key (run_id, external_id))` replaces `sync_runs.failed_samples jsonb`, which `only_failed` replay reads and the failed-record table paginates; `sync_conflict_fields(conflict_id uuid not null references sync_conflicts(id) on delete cascade, tenant_id, column_id uuid not null references columns(id) on delete restrict, external_field text not null, opshub_value jsonb, external_value jsonb, resolved_value jsonb, primary key (conflict_id, column_id))` replaces `sync_conflicts.field_diffs jsonb`, which `merge` validates field by field; `sync_database_objects(sync_id uuid not null references syncs(id) on delete cascade, tenant_id, object_kind text not null check (object_kind in ('table','named_query')), object_ref text not null, statement_text text, primary key (sync_id, object_ref), check (object_kind <> 'named_query' or statement_text is not null))` holds the `database` connector allowlist as rows instead of a delimited list. `sync_runs.counters jsonb` becomes the six `records_*` integer columns above: the keys are fixed, the API reads every one of them, and the `partial`/`failed` threshold is arithmetic over two of them. The DTOs are unchanged — `MappingRequest` keeps `transform: { name, args }`, `RunSummary` keeps `counters` and `failed_samples`, `ConflictResponse` keeps `field_diffs`, and the database allowlist keeps its `objects` array — and `SyncMappingRepository`, `SyncRunRepository`, `SyncConflictRepository`, and `SyncRepository` fan each shape out to rows on write (`delete` of removed rows plus `insert ... on conflict do update`) and reassemble it on read inside the same `UnitOfWork`.
- `jsonb` audit (decision section 2): kept — `sync_mappings.default_value` and `sync_conflict_fields.opshub_value`/`external_value`/`resolved_value` are typed F007 cell values whose shape belongs to the column type, never filtered or joined on; `sync_run_failed_records.provider_payload` is the verbatim provider response snapshot kept 7 days under `debug_payloads`, read only when a human opens one failed record. Converted — `sync_mappings.transform`, `sync_runs.counters`, `sync_runs.failed_samples`, and `sync_conflicts.field_diffs` were all read by known key, filtered, or aggregated, and became the tables and columns above. The closed enums `connector`, `kind`, `direction`, `schedule`, `conflict_policy`, `deletion_policy`, `state`, `trigger`, `cursor_kind`, `classification`, and `resolution` carry no data of their own, so they stay `text` with `check` constraints rather than lookup tables. No other `jsonb` column exists in this module.
- Invariants: unique `syncs(connection_id, source_object, target_sheet_id, direction) where deleted_at is null and state <> 'paused'`; unique `sync_mappings(sync_id, external_field, direction)` and `sync_mappings(sync_id, column_id, direction)`; check `sync_mappings` count per sync ≤ 300 enforced in `SyncMappingRepository::replace_mapping_set` inside the transaction plus a statement trigger; `sync_mapping_transform_args` primary key blocks a repeated argument name and its `check` blocks an argument outside the catalog, and `SyncMappingRepository` rejects an argument name that the row's `transform_name` does not take; `sync_mapping_value_map` primary key blocks a repeated external value in one `value_map`; `sync_run_failed_records` primary key makes a retried record one row per run, so the 50-sample cap is a `limit` rather than a truncation on write; `sync_conflict_fields` primary key blocks a duplicate field in one conflict and `SyncConflictRepository::settle_conflict` requires every row of the conflict to carry a `resolved_value` before `state` moves to `resolved`; `sync_database_objects` primary key blocks a duplicate allowlist entry; unique `sync_record_links(sync_id, row_id)`; check `syncs.deletion_column_id is not null or deletion_policy <> 'mark_deleted'`.
- Indexes: `syncs(tenant_id, state, connector)`, `syncs(connection_id)`, `sync_runs(sync_id, started_at desc)`, `sync_runs(tenant_id, state, started_at desc)`, `sync_conflicts(sync_id, state, detected_at desc)`, `sync_conflicts(tenant_id, state)`, `sync_record_links(sync_id, row_id)`, `sync_mappings(sync_id, position)`, `sync_mapping_transform_args(mapping_id)` and `sync_mapping_value_map(mapping_id, external_value)` for evaluator load and `value_map` lookup, `sync_run_failed_records(run_id, occurred_at desc)` for the failed-record table and `sync_run_failed_records(run_id, classification)` for `only_failed` replay, `sync_conflict_fields(conflict_id)` and `sync_conflict_fields(column_id)` for the reverse "which conflicts touch this column" read, `sync_database_objects(sync_id)`.
- Audit events: `sync.created`, `sync.updated`, `sync.activated`, `sync.paused`, `sync.mappings-replaced`, `sync.cursor-reset`, `sync-run.triggered`, `sync-run.replayed`, `sync-conflict.resolved`, `sync.debug-payloads-enabled`.
- Retention/deletion: `sync_runs` older than 90 days deleted nightly, taking their `sync_run_failed_records` with them; `sync_run_failed_records.provider_payload` is nulled after 7 days by `expire_debug_payloads`; resolved conflicts and their `sync_conflict_fields` kept 180 days; deleting a sync cascades mappings and their transform-argument and value-map rows, runs and their failed records, cursors, conflicts and their fields, record links, and database allowlist rows; rollback drops the eleven tables and their indexes, children before parents, after dropping the `syncs.last_run_id` foreign key.

### React/TypeScript

- Routes `/admin/syncs`, `/admin/syncs/new`, `/admin/syncs/:syncId`, `/admin/syncs/:syncId/conflicts` in `apps/web/src/features/connectors/`; components `SyncListPage`, `SyncWizard`, `ConnectionObjectStep`, `MappingEditor`, `MappingRow`, `TransformPicker`, `MappingPreview`, `PolicyStep`, `SyncDetailPage`, `RunHistoryTable`, `FailedRecordTable`, `ReplayDialog`, `ConflictQueue`, `ConflictDiff`, `MergeChooser`.
- State: TanStack Query keys `['syncs', filter, cursor]`, `['sync', id]`, `['sync-mappings', id]`, `['sync-runs', id, cursor]`, `['sync-conflicts', id, state, cursor]`, `['mapping-preview', id, mappingsHash]`; a run trigger optimistically inserts a `queued` row and polls `['sync-runs', id]` every 5 s while any run is `queued` or `running`.
- API client: generated `SyncsApi` with `listSyncs`, `createSync`, `getSync`, `updateSync`, `replaceMappings`, `previewMapping`, `triggerRun`, `pauseSync`, `listRuns`, `replayRun`, `listConflicts`, `resolveConflict`.
- Telemetry: `sync_created`, `sync_activated`, `sync_mapping_previewed`, `sync_run_triggered`, `sync_run_replayed`, `sync_conflict_resolved` with `connector`, `kind`, `direction`, and `sync_id`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F030-01 through FR-F030-21 and NFR-F030-01 through NFR-F030-05 in `testing/features/F030/requirements/cases.md`
- [ ] Failure/edge-case tests: worker killed mid-page, provider 429 with `Retry-After`, 10% failure threshold boundary, unknown transform, duplicate mapping, stale `If-Match`, second run while running, replay of an already-applied record, SOQL with a DML keyword, database connector attempting `UPDATE`, file failing ClamAV, Jira status with no legal transition
- [ ] Permission-negative and tenant-isolation tests: member cannot create, run, replay, or resolve; admin without edit rights on the target sheet is denied; foreign-tenant sync, run, and conflict IDs return `not_found`
- [ ] Rust unit tests: `crates/domain/src/connectors/` transform catalog, mapping validation, error classification, conflict detection, checkpoint arithmetic, cursor overlap windows
- [ ] API contract/integration tests: all eleven routes with success and each mapped error code against mock connector servers
- [ ] Database migration/constraint tests: unique active sync tuple, mapping uniqueness and cap, duplicate transform argument name and duplicate `value_map` external value rejected, duplicate failed-record and conflict-field rows rejected, duplicate allowlist entry rejected, cascade delete from `syncs` through every child table, `deletion_column_id` check, enum checks on `connector`, `direction`, `schedule`, `state`, and `trigger`, no `jsonb` column outside the audited list, rollback ordering
- [ ] React component tests: `MappingEditor`, `TransformPicker`, `MappingPreview`, `RunHistoryTable`, `ConflictDiff`, `MergeChooser` states
- [ ] Browser E2E tests: build a Jira sync end to end, force a conflict and resolve it, replay a failed run
- [ ] Accessibility tests: axe on `/admin/syncs`, wizard steps, mapping editor, conflict queue; keyboard mapping reorder; conflict diff reading order
- [ ] Performance/load tests: 10,000-record run under 10 minutes, sync list and conflict list p95 under 500 ms, preview under 1 s

### Fast fanout configuration

- Test harness path: `testing/features/F030/`
- Feature flag: `F030_FEATURE`
- Fixture/seed factory: `testing/fixtures/connectors.rs` builds tenants A and B, an integration-admin, a member, an admin without sheet edit rights, one F029 active connection per connector, sheet `Delivery board` with typed columns, 10,000-record generators for Jira and Salesforce, a Box folder with 20 files including one EICAR sample, and syncs in `paused`, `active`, and `error` states
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, UTC storage with `America/Chicago` used for `date_tz` cases, stable external IDs `OPS-0001`+ and Salesforce 18-character IDs
- Mock/stub contracts: mock connector servers in `testing/harness/connectors/` for Jira REST v3, Salesforce v61.0 (`getUpdated`, `getDeleted`, composite), Box 2.0 events, Dropbox v2 `list_folder`, and Tableau REST 3.21 publish, each with programmable 429/5xx injection, page sizes, and clock skew; a read-only PostgreSQL fixture database for the `database` connector; F029 `TokenSource` stub returning fixed tokens
- Parallel isolation: one schema per test worker, tenant ID per test, mock connector port per worker, advisory-lock namespace per worker
- Targeted command: `cargo xtask test-feature F030`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F030/`

## 6. Acceptance criteria

```gherkin
Feature: General connectors with mapping, cursors, replay, and a conflict queue

Scenario: Jira sync creates rows and stores a cursor
  Given an active Jira connection and a sync mapping summary, status, and duedate to Delivery board
  When the administrator triggers a run and the mock returns 412 issues over three pages
  Then the run completes with read 412 and created 412, sync_cursors holds the last updated timestamp, and sync-run.completed.v1 is published

Scenario: A crashed run resumes from its checkpoint
  Given a run that checkpointed at record 500 of 1200 before the worker was killed
  When the run job restarts
  Then it resumes after the checkpoint, no row is written twice, and the final counters total 1200 records read

Scenario: Both sides changed and the conflict waits for a person
  Given a sync with conflict_policy manual and a record whose OpsHub row and Jira issue both changed since the cursor
  When the run applies that record
  Then neither side is written, a sync_conflicts row with one sync_conflict_fields row per changed field records both values, and sync-conflict.detected.v1 is published

Scenario: Replaying only the failed records is idempotent
  Given a partial run with 40 failed records out of 500
  When the administrator replays that run with only_failed true and the mock now succeeds
  Then 40 records are applied, the 460 already-applied records are not touched, and the replay run reports skipped 0 and updated 40

Scenario: Member cannot create a sync
  Given a member without the integration-admin role
  When they POST /api/v1/syncs
  Then the response is 403 denied and no sync row is created
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F029 (provider registry, OAuth vault and `TokenSource`, `HttpClient` with retry and `Retry-After`, `integration_events` call log, connection lifecycle and `needs_reauth` state); through F029 also F028 conventions and F037 notifications; F006 sheet and row services for writes; F013 file service for Box and Dropbox downloads; F023 report results for Tableau extracts; F004 secret manager for database DSNs; decisions sections 2, 3, 7; contracts row F030
- Blocks: F054 (Bridge reuses connector adapters as workflow actions)
- Conflicts with: none — F030 owns `crates/domain/src/connectors/**`, `crates/persistence/src/connectors/**`, `services/api/src/connectors/**`, `services/worker/src/connectors/**`, `apps/web/src/features/connectors/**`, and `*_connectors_*.sql`, all disjoint from F029's `integrations` module
- External dependencies: Jira REST v3, Salesforce REST/composite v61.0, Box 2.0, Dropbox v2, Tableau REST 3.21, and customer-provided read-only databases; mock connector servers stand in during tests
- Risks and mitigations: sync loops between systems, mitigated by `sync_record_links` version and timestamp comparison so a record we just wrote is recognized as our own echo; provider index lag returning stale change lists, mitigated by the 2-minute cursor overlap window plus idempotent application; a bad mapping corrupting a sheet at scale, mitigated by preview, type validation, `dry_run` replay, and the 10% failure threshold that pauses the sync; provider API version drift, mitigated by pinned versions recorded per run and recorded-response contract tests; long-running database queries, mitigated by the read-only pool, statement timeout, and row cap
- Open questions: none

## 7.1 Amendments

Every change made to this ticket after it was first accepted, newest first.

| Date | Caused by | What changed | Why |
|---|---|---|---|
| 2026-09-04 | Interface review | The body field `expected_version` replaced by the `If-Match` header on every mutation, including the mapping replace and the conflict resolve, which match against the parent sync's version | `docs/engineering-standards.md` §6 makes `If-Match` binding and requires a decision record for a departure; there was none, so this was the only feature in the product where a client had to send its version somewhere else |

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F029 accepted and archived with `TokenSource`, `HttpClient`, and the provider registry available
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F030/`
- [ ] Migration file name and owned paths claimed
- [ ] Mock connector servers and the read-only fixture database available in `testing/harness/connectors/`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for every sync mutation, run outcome, and conflict resolution
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F030_FEATURE`, run down migration on an empty tenant, confirm F029 connections are unaffected
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Integration administrators can define syncs between OpsHub sheets and Jira, Salesforce, Box, Dropbox, Tableau, and read-only databases, map fields with a validated transform catalog, run them on a schedule or on demand, watch run history with per-record outcomes, replay a failed run in dry-run or failed-only mode, and resolve conflicts from a queue that shows both values.
- Migration adds `syncs`, `sync_mappings`, `sync_mapping_transform_args`, `sync_mapping_value_map`, `sync_runs`, `sync_run_failed_records`, `sync_cursors`, `sync_conflicts`, `sync_conflict_fields`, `sync_record_links`, and `sync_database_objects`; rollback drops them and leaves F029 connections intact. Feature is off by default behind `F030_FEATURE`.
