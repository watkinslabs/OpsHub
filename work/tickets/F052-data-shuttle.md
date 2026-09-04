---
id: F052
type: feature
status: planned
priority: P1
owner: platform
estimate: 8
target_milestone: M7
parent_epic: E008
depends_on: [F010, F048]
blocks: []
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/data-shuttle/**, crates/persistence/src/data-shuttle/**, services/api/src/data-shuttle/**, services/worker/src/data-shuttle/**, apps/web/src/features/data-shuttle/**, services/api/migrations/*_data-shuttle_*.sql, testing/features/F052/**]
feature_flag: F052_FEATURE
flag_default: off
branch: f052-data-shuttle
started_at: null
finished_at: null
---

# F052 — Data Shuttle

## 1. Identity and dates

- Branch: `f052-data-shuttle`
- Capability area: advanced modules (spec 5.11 Data Shuttle, 5.2 DATA-04 and the import low-level bullets, 5.1 import/export bullet, section 6 async acknowledgement, section 10 "Advanced modules use entitlement records plus feature flags")
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 7, 9, 10; `docs/capability-contracts.md` row F052
- Module slug: `data-shuttle`

## 2. Requirement specification

### Problem and user outcome

Operations teams receive CSV and XLSX extracts from finance, HR, and vendor systems on a schedule and re-key or hand-import them into sheets. F010 gives a one-off import and export job, but nothing remembers the mapping, watches a drop location, validates each file the same way, archives what was processed, or lets an operator replay a bad run. Data Shuttle turns the F010 job into a governed, scheduled flow with run history.

As a data administrator, I want to define a flow that picks up a file from a drop location on a schedule, maps its columns onto a sheet with a duplicate strategy, validates it, archives it, and records every run, so that recurring data movement is automatic, auditable, and recoverable without touching the sheet by hand.

### Functional requirements

- **FR-F052-01:** An actor with the `data-admin` role can create a flow with `name` (1–120 chars), `direction` (`import` | `export`), `location` (`{ kind: attachment | inbox | connector, file_id? | prefix? | connection_id + path? }`), `sheet_id`, `mapping`, `validation`, `schedule`, and `archive_policy`; the response returns a UUIDv7 `id`, `version` 1, and `next_run_at` (null for manual flows). `location` persists as the typed columns `location_kind`, `location_file_id`, `location_prefix`, `location_connection_id`, and `location_path` with a check that the kind's own field is present and the others null, and `archive_policy.keep_days` persists as `archive_keep_days`; both keep their JSON object shape in the request and response.
- **FR-F052-02:** `mapping` is a list of `{ source_column: string, column_id: uuid, coerce: text | number | currency | date | datetime | boolean | select }` plus `key_column_ids` (1–5 ids) and `duplicate_strategy` (`append` | `update` | `replace` | `skip`); each list entry is stored as one `shuttle_flow_column_maps` row and each key as one `shuttle_flow_key_columns` row, while `duplicate_strategy` is a checked `text` column on `shuttle_flows`; a `column_id` not on the sheet (rejected by the row's foreign key to `columns`), a `coerce` incompatible with the column type, a `source_column` repeated within the flow (rejected by the row's primary key), or `update`/`replace`/`skip` with no `shuttle_flow_key_columns` row returns `400 invalid` with `field_errors.mapping[i].<field>`. The request and response keep `mapping` as one JSON object with its arrays.
- **FR-F052-03:** `schedule` is either `{ kind: manual }` or `{ kind: cron, expression, timezone }`; a manual flow has no `shuttle_schedules` row and a cron flow has exactly one, where the expression fires no more often than every 15 minutes and `timezone` is an IANA name; a denser cadence returns `400 invalid` with `field_errors.schedule.expression = "min_interval_15m"`; `shuttle_schedules` stores the computed `next_run_at` in UTC.
- **FR-F052-04:** `validation` holds `required_column_ids` — one `shuttle_flow_required_columns` row per id, so a required column that is deleted from the sheet is refused by the foreign key instead of dangling in a list — plus `max_errors` (0–10,000, default 100) and `on_error` (`abort` | `partial`), both checked columns on `shuttle_flows`; the request and response keep `validation` as one JSON object with its array. When rejected rows exceed `max_errors` the run stops with status `failed` and no rows are committed under `abort`, or commits valid rows and finishes `partial` under `partial`.
- **FR-F052-05:** Per-tenant limits come from the F048 entitlement `limits` for `data-shuttle`: creating more than `max_flows` flows returns `409 conflict` with `field_errors.flows = "limit_reached"`; a file above `max_file_mb` fails the run with `error_code = file_too_large`; a file with more rows than `max_rows_per_run` fails with `error_code = too_many_rows` before any row is written.
- **FR-F052-06:** `POST /api/v1/data-shuttle/flows/{id}/run` enqueues a run and returns `202` with the run `id` and `status: queued` within 2 seconds; a second run request while a run for the same flow is `queued` or `running` returns `409 conflict` with `field_errors.run = "already_active"`; scheduled runs obey the same single-active rule and skip with a recorded `skipped_reason = overlap`.
- **FR-F052-07:** The worker executes a run by locating the file, computing its SHA-256, creating an F010 `import_jobs` or `export_jobs` record, streaming rows through the mapping and validation, and recording `rows_read`, `rows_inserted`, `rows_updated`, `rows_skipped`, `rows_rejected`, `duration_ms`, `error_code`, and `validation_report_file_id` on `shuttle_runs` with one `shuttle_run_rejections` row per rejected source row (`row_number`, `reason_code`, `source_column`, and the offending cell values as the row-level error sample); a run whose `(flow_id, file_checksum)` pair already succeeded finishes `succeeded` with `skipped_reason = duplicate_file` and writes nothing.
- **FR-F052-08:** Every processed import file is copied to tenant object storage under `shuttle/{tenant_id}/{flow_id}/{run_id}` and recorded in `shuttle_archives` with `storage_key`, `checksum`, `size_bytes`, `mime`, and `retain_until = completed_at + archive_policy.keep_days` (1–365, default 30); export runs archive the produced file the same way; the nightly purge deletes archives past `retain_until` and sets `shuttle_archives.purged_at`, which run detail reports as `archive_purged` rather than duplicating the state on the run row.
- **FR-F052-09:** `POST /api/v1/data-shuttle/runs/{id}/replay` starts a new run from the archived file using the flow version captured on the original run; a purged archive returns `409 conflict` with `field_errors.archive = "purged"`; the replay run records `replay_of_run_id`.
- **FR-F052-10:** `GET /api/v1/data-shuttle/flows/{id}/runs` pages runs by cursor newest first with `limit` up to 100 and filters `status` and `since`; `GET /api/v1/data-shuttle/runs/{id}` returns the run, its counts, the first 50 `shuttle_run_rejections` rows by `row_number` with their reasons, and an expiring (15-minute) download URL for the archive and the validation report when the caller may read the sheet.
- **FR-F052-11:** Every run publishes `shuttle-run.started.v1` when the worker claims it and `shuttle-run.completed.v1` or `shuttle-run.failed.v1` when it ends, with `flow_id`, `run_id`, counts, and `error_code` in the payload; every flow mutation and run request requires `Idempotency-Key`, uses `If-Match` for `PATCH`, and writes an `audit_events` row with the diff.
- **FR-F052-12:** Every route is mounted behind `RequireModule(ModuleSlug::DataShuttle)` from `crates/auth/src/entitlements/`, so a tenant without an active or trial entitlement and an enabled `F052_FEATURE` receives `403 denied` with `field_errors.module` before any handler runs; disabling the flag stops scheduled runs at the next tick and leaves flows and history intact.
- **FR-F052-13:** Rows written by a run carry the flow owner's actor id with `source = data_shuttle` and `run_id` in the cell history, and a run never writes to a sheet the flow owner can no longer edit (the run fails with `error_code = sheet_denied`).
- **FR-F052-14:** The web app renders the flow list at `/w/{workspace_id}/data-shuttle`, a flow editor with mapping preview from the first 20 rows of a sample file, and a run history page with a run drawer showing counts, rejected rows, replay, and archive download; cross-tenant access to any flow or run by id returns `not_found`.

### Non-functional requirements

- **NFR-F052-01 Performance:** run acknowledgement under 2 seconds; a 100,000-row, 50-column CSV import finishes in under 10 minutes on the reference worker; flow and run list routes respond in under 500 ms p95 (spec section 6).
- **NFR-F052-02 Security/privacy:** files stay in tenant-scoped storage keys; download URLs expire after 15 minutes; connector credentials are never returned by any route; rejected-row samples redact columns the caller cannot read; cross-tenant and role negatives are in the harness.
- **NFR-F052-03 Accessibility:** flow editor, mapping table, and run drawer pass axe with zero serious violations; the mapping table is keyboard-operable with row-level labels; run status uses text plus icon.
- **NFR-F052-04 Reliability/observability:** runs are JetStream jobs with per-tenant quota, three bounded retries for transient storage errors, a 30-minute timeout, and dead-letter state visible in the run; metrics `shuttle_run_total{status}`, `shuttle_run_duration_seconds`, and `shuttle_rows_rejected_total`; each run span carries `tenant_id`, `flow_id`, `run_id`, `correlation_id`.

### Scope

Included: flow CRUD, mapping and validation model, schedule computation, worker execution over F010 jobs, duplicate detection by checksum, archive and retention, run history, replay, entitlement limits, audit, outbox events, flow editor and run history UI.

Excluded: new file-format parsers beyond F010 CSV/XLSX; connector authentication (F029); sheet-to-sheet synchronization (F053); PDF export (F025); transformation expressions beyond type coercion; notification delivery for run failures beyond the F037 event subscription.

## 3. UX specification

- Entry points: workspace navigation `Data Shuttle` (visible only when `useModuleAllowed('data-shuttle')` is true); route `/w/{workspace_id}/data-shuttle` for the flow list; `/w/{workspace_id}/data-shuttle/{flow_id}` for editor and run history; sheet menu `Automate imports` deep-links to a new flow with the sheet preselected.
- Primary flow: admin clicks `New flow`, picks `Import`, chooses the inbox prefix `finance/`, selects the `Budget` sheet, uploads a sample file, maps `Cost Center` to the `Cost center` column and `Amount` to `Amount (currency)`, marks `Cost center` as key with `update`, sets cron `0 6 * * 1-5` in `America/New_York`, keeps archives 30 days, saves, presses `Run now`, sees the run move `queued → running → succeeded` with counts, opens the drawer, and downloads the archived file.
- Loading: skeleton list and drawer; Empty: `No flows yet` with `New flow`; Error: inline banner with `correlation_id` and retry; Success: toast `Flow saved` / `Run queued`; Stale/conflict: banner `This flow changed` with `Reload`; `already_active` shows an inline notice with the active run link; Offline: editor disabled with offline badge.
- Permission-denied: non-`data-admin` users see flows read-only and no `Run`/`Replay`; a tenant without entitlement sees the shared `ModuleNotEntitled` panel.
- Run drawer: status, timestamps, counts as labelled numbers, rejected rows table with reason column, `Replay` (disabled with tooltip when archive purged), `Download archive`, `Download validation report`.
- Responsive: mapping table scrolls horizontally under 768 px with the source column frozen; drawer becomes a full-screen sheet under 640 px.
- Keyboard: `Tab` order covers list, filters, rows, actions; mapping rows are edited with arrow keys and `Enter`; `Escape` closes the drawer and returns focus; motion respects `prefers-reduced-motion`.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062), Lucide icons `Truck`, `Upload`, `Download`, `Play`, `RotateCcw`, `Archive`, `AlertTriangle`; tokens from `apps/web/src/design/tokens.css`.

- Design: `design/artboards/DataShuttle.dc.html` on the canvas indexed by `design/canvas.json`. The ticket is the contract and the artboard is the picture; when they disagree the ticket wins.

## 4. Technical specification

Canonical contract: `docs/capability-contracts.md` row F052 (aggregate `shuttle-flow`, module `data-shuttle`, role `data-admin`).

### Rust backend

- Data access (decision section 2.1): `crates/persistence/src/data-shuttle/` holds `ShuttleFlowRepository` (owns `shuttle_flows`, `shuttle_flow_column_maps`, `shuttle_flow_key_columns`, `shuttle_flow_required_columns`), `ShuttleScheduleRepository` (`shuttle_schedules`), `ShuttleRunRepository` (`shuttle_runs`, `shuttle_run_rejections`), and `ShuttleArchiveRepository` (`shuttle_archives`); each child table is written only by the repository of its parent object type, so no two classes write the same table. Named queries: `find_flow_with_mapping`, `list_flows_with_last_run`, `count_active_flows`, `replace_column_maps`, `replace_key_columns`, `replace_required_columns`, `list_column_maps_for_run`, `upsert_schedule`, `delete_schedule`, `claim_due_schedules` (`for update skip locked`), `record_schedule_fired`, `insert_queued_run`, `claim_run`, `find_succeeded_run_by_checksum`, `record_run_outcome`, `append_rejections`, `list_rejections_head`, `list_runs_by_flow`, `insert_archive`, `find_archive_for_run`, `list_expired_archives`, `mark_archive_purged` — no generic query escape hatch is exposed. Every use case below depends on these repository traits and contains no SQL; the API handlers, the scheduler tick, the run consumer, the archiver, and the nightly purge all reach PostgreSQL only through them, and a flow save (flow row plus its column-map, key-column, required-column, and schedule rows) and a run completion (run row, rejection rows, archive row, audit row, outbox row) each run in one `UnitOfWork` transaction.
- Domain entities in `crates/domain/src/data-shuttle/`: `ShuttleFlow { id, tenant_id, workspace_id, sheet_id, name, direction: Direction, location: FileLocation, mapping: Mapping, validation: ValidationPolicy, schedule: Schedule, archive_policy: ArchivePolicy, owner_id, enabled: bool, version, audit fields, deleted_at }`, `Mapping { columns: Vec<ColumnMap>, key_column_ids: Vec<Uuid>, duplicate_strategy: DuplicateStrategy }`, `ShuttleSchedule { flow_id, expression, timezone, next_run_at, last_fired_at }`, `ShuttleRun { id, tenant_id, flow_id, flow_version, status: RunStatus, trigger: manual | scheduled | replay, replay_of_run_id, file_checksum, import_job_id, export_job_id, counts: RunCounts, error_code, skipped_reason, validation_report_file_id, started_at, completed_at, duration_ms, correlation_id }`, `RejectedRow { run_id, row_number, reason_code, source_column, cell_values }`, `ShuttleArchive { id, run_id, storage_key, checksum, size_bytes, mime, retain_until, purged_at }`. `Mapping`, `ValidationPolicy`, `FileLocation`, and `Schedule` are in-memory aggregates that `ShuttleFlowRepository` fans out to rows and columns on write and reassembles on read; the domain depends on the repository traits, never on SQLx.
- Use cases: `create_flow`, `update_flow`, `list_flows`, `request_run`, `list_runs`, `get_run`, `replay_run`, `compute_next_run`, `execute_run` (worker), `purge_archives` (worker nightly); pure functions `validate_mapping(sheet_columns, mapping)`, `min_interval_ok(expression)`, and `apply_duplicate_strategy(existing, incoming)` are unit tested.
- Worker in `services/worker/src/data-shuttle/`: `RunConsumer` on subject `data-shuttle.run`, `FileFetcher` (attachment via F017, inbox via S3 prefix listing newest-first, connector via the F030 adapter `download`), `Importer` and `Exporter` wrapping F010 job APIs, `Archiver`, `Scheduler` tick every 60 seconds calling `ShuttleScheduleRepository::claim_due_schedules(now)`, which selects due `shuttle_schedules` rows `for update skip locked` inside the tick's `UnitOfWork`. No worker module opens a connection or issues SQL: the scheduler, the consumer, the archiver, and the purge job call the four repositories only (decision section 2.1).
- API endpoints (`services/api/src/data-shuttle/`): `GET /api/v1/data-shuttle/flows`, `POST /api/v1/data-shuttle/flows`, `PATCH /api/v1/data-shuttle/flows/{id}`, `POST /api/v1/data-shuttle/flows/{id}/run`, `GET /api/v1/data-shuttle/flows/{id}/runs`, `GET /api/v1/data-shuttle/runs/{id}`, `POST /api/v1/data-shuttle/runs/{id}/replay`. DTOs `CreateFlowRequest`, `UpdateFlowRequest`, `FlowResponse`, `RunRequestResponse { run_id, status }`, `RunResponse { …, rejected_sample: Vec<RejectedRow>, archive_url?, report_url? }`, `Page<RunResponse>`.
- Events: `shuttle-run.started.v1`, `shuttle-run.completed.v1`, `shuttle-run.failed.v1` with `{ flow_id, run_id, trigger, counts, error_code }` in addition to the contract envelope.
- Authorization: `RequireModule(ModuleSlug::DataShuttle)` on the router; `data-admin` for create/update/run/replay; sheet read permission for run detail and downloads; the run executes with the flow owner's actor and re-checks `sheet-editor` at execution time.
- Validation: name 1–120 chars; mapping 1–500 columns; `key_column_ids` 1–5; cron five-field syntax; `keep_days` 1–365; `max_errors` 0–10,000; `limit` 1–100.
- Error mapping: `FlowError::LimitReached → 409 conflict`, `FlowError::RunActive → 409 conflict`, `FlowError::ArchivePurged → 409 conflict`, `FlowError::StaleVersion → 409 conflict`, `FlowError::NotFound → 404 not_found`, mapping/schedule validation → `400 invalid`, `AuthzError::Denied → 403 denied`, module guard → `403 denied`.

### PostgreSQL/SQLx

- Migration `*_data-shuttle_*.sql` creates `shuttle_flows(id uuid pk, tenant_id uuid not null, workspace_id uuid not null references workspaces(id) on delete restrict, sheet_id uuid not null references sheets(id) on delete restrict, name text not null, direction text not null check (direction in ('import','export')), location_kind text not null check (location_kind in ('attachment','inbox','connector')), location_file_id uuid null references files(id) on delete restrict, location_prefix text null, location_connection_id uuid null references integration_connections(id) on delete restrict, location_path text null, duplicate_strategy text not null check (duplicate_strategy in ('append','update','replace','skip')), max_errors int not null default 100 check (max_errors between 0 and 10000), on_error text not null check (on_error in ('abort','partial')), archive_keep_days smallint not null default 30 check (archive_keep_days between 1 and 365), owner_id uuid not null references users(id) on delete restrict, enabled bool not null default true, version bigint not null default 1, created_by, created_at, updated_by, updated_at, deleted_at, check (case location_kind when 'attachment' then location_file_id is not null and location_prefix is null and location_connection_id is null when 'inbox' then location_prefix is not null and location_file_id is null and location_connection_id is null else location_connection_id is not null and location_path is not null and location_file_id is null end))`, `shuttle_schedules(flow_id uuid pk references shuttle_flows(id) on delete cascade, tenant_id uuid not null, expression text not null, timezone text not null, next_run_at timestamptz, last_fired_at timestamptz)`, `shuttle_runs(id uuid pk, tenant_id uuid not null, flow_id uuid not null references shuttle_flows(id) on delete restrict, flow_version bigint not null, status text not null check (status in ('queued','running','succeeded','failed','partial')), trigger text not null check (trigger in ('manual','scheduled','replay')), replay_of_run_id uuid null references shuttle_runs(id) on delete restrict, file_checksum text, import_job_id uuid null references import_jobs(id) on delete restrict, export_job_id uuid null references export_jobs(id) on delete restrict, rows_read int not null default 0, rows_inserted int not null default 0, rows_updated int not null default 0, rows_skipped int not null default 0, rows_rejected int not null default 0, error_code text null check (error_code in ('file_too_large','too_many_rows','sheet_denied','fetch_failed','parse_failed','validation_failed','timeout','dead_lettered')), skipped_reason text null check (skipped_reason in ('overlap','duplicate_file')), validation_report_file_id uuid null references files(id) on delete restrict, started_at, completed_at, duration_ms int, correlation_id uuid, created_at, check ((import_job_id is null) or (export_job_id is null)))`, `shuttle_archives(id uuid pk, tenant_id uuid not null, run_id uuid not null references shuttle_runs(id) on delete cascade, storage_key text not null, checksum text not null, size_bytes bigint not null, mime text not null, retain_until timestamptz not null, purged_at timestamptz)`.
- Normalized sets (decision section 2, no array or list-bearing columns): `shuttle_flow_column_maps(flow_id uuid not null references shuttle_flows(id) on delete cascade, tenant_id uuid not null, source_column text not null, column_id uuid not null references columns(id) on delete restrict, coerce text not null check (coerce in ('text','number','currency','date','datetime','boolean','select')), position int not null, primary key (flow_id, source_column), unique (flow_id, column_id), unique (flow_id, position))` replaces `mapping.columns`; `shuttle_flow_key_columns(flow_id uuid not null references shuttle_flows(id) on delete cascade, tenant_id uuid not null, column_id uuid not null references columns(id) on delete restrict, key_ordinal smallint not null check (key_ordinal between 1 and 5), primary key (flow_id, column_id), unique (flow_id, key_ordinal))` replaces `mapping.key_column_ids`; `shuttle_flow_required_columns(flow_id uuid not null references shuttle_flows(id) on delete cascade, tenant_id uuid not null, column_id uuid not null references columns(id) on delete restrict, primary key (flow_id, column_id))` replaces `validation.required_column_ids`; `shuttle_run_rejections(run_id uuid not null references shuttle_runs(id) on delete cascade, tenant_id uuid not null, row_number int not null, reason_code text not null check (reason_code in ('missing_required','coerce_failed','duplicate_key','unknown_column','row_denied')), source_column text, cell_values jsonb not null, primary key (run_id, row_number))` holds the rejected-row detail that run detail returns. The API keeps `mapping`, `validation`, `location`, `archive_policy`, and `rejected_sample` as JSON objects and arrays, so no request or response shape changes; `ShuttleFlowRepository::replace_column_maps`, `replace_key_columns`, and `replace_required_columns` fan a saved set out to rows in one `delete` plus `insert` pair inside the flow's `UnitOfWork`, and reassemble the arrays on read in `position`/`key_ordinal` order.
- `jsonb` audit: `shuttle_flows.location`, `.mapping`, `.validation`, `.schedule`, and `.archive_policy` were all queried structures the product validates against sheet columns, entitlement limits, and cron rules, so all five are gone — `mapping` and `validation` to the three child tables above, `location`, `on_error`, `max_errors`, `duplicate_strategy`, and `archive_keep_days` to typed checked columns, and `schedule` to the existing `shuttle_schedules` row. `shuttle_run_rejections.cell_values` is the only `jsonb` column in the module: it is the verbatim row-level error sample copied from the source file for the operator to read, never filtered, joined, sorted, or constrained on — rejection queries use `run_id`, `row_number`, and `reason_code`. `shuttle_schedules.expression` stays one `text` cron literal parsed as a unit by `compute_next_run`; no component of it is filtered or indexed, and the queried derived value is `next_run_at`.
- Invariants: unique `shuttle_flows(tenant_id, workspace_id, lower(name)) where deleted_at is null`; partial unique `shuttle_runs(flow_id) where status in ('queued','running')` enforces one active run; unique `shuttle_runs(flow_id, file_checksum) where status = 'succeeded' and trigger <> 'replay'` backs duplicate detection; one archive per run via unique `shuttle_archives(run_id)`; a flow carries 1–500 `shuttle_flow_column_maps` rows whose primary key blocks a repeated `source_column` and whose `unique (flow_id, column_id)` blocks two source columns targeting one sheet column; `shuttle_flow_key_columns` holds 1–5 rows for `update`/`replace`/`skip` and none for `append`, enforced by `ShuttleFlowRepository` inside the save transaction and asserted by the constraint suite; every `shuttle_flow_required_columns.column_id` and every mapped `column_id` must belong to the flow's `sheet_id`, checked by the repository against F007 before the insert; `shuttle_run_rejections(run_id, row_number)` blocks a duplicated rejection when a run is retried.
- Indexes: `shuttle_runs(flow_id, created_at desc)`, `shuttle_runs(tenant_id, status)`, `shuttle_schedules(next_run_at) where next_run_at is not null`, `shuttle_archives(retain_until) where purged_at is null`, `shuttle_flow_column_maps(flow_id, position)` for mapping reassembly and `shuttle_flow_column_maps(column_id)` for the reverse "which flows write this column" check when F007 deletes a column, `shuttle_flow_key_columns(flow_id, key_ordinal)`, `shuttle_flow_required_columns(column_id)`, `shuttle_run_rejections(run_id, row_number)` serving the first-50 detail read.
- Audit events: `shuttle-flow.create`, `shuttle-flow.update`, `shuttle-flow.delete`, `shuttle-run.request`, `shuttle-run.replay`, `shuttle-archive.purge` with field diffs.
- Retention/deletion: flows soft delete; runs and archives are retained per `archive_keep_days` and the F027 tenant retention; a purged archive keeps its `shuttle_archives` row with `purged_at` set so run detail can report `archive_purged` and refuse replay; rollback drops the eight tables, children before parents (`shuttle_run_rejections`, `shuttle_archives`, `shuttle_runs`, `shuttle_flow_required_columns`, `shuttle_flow_key_columns`, `shuttle_flow_column_maps`, `shuttle_schedules`, `shuttle_flows`).

### React/TypeScript

- Routes: `/w/:workspaceId/data-shuttle`, `/w/:workspaceId/data-shuttle/new`, `/w/:workspaceId/data-shuttle/:flowId` in `apps/web/src/features/data-shuttle/`; components `FlowListPage`, `FlowRow`, `FlowEditorPage`, `LocationPicker`, `MappingTable`, `MappingRow`, `SamplePreview`, `ValidationFields`, `ScheduleFields`, `ArchiveFields`, `RunHistoryPage`, `RunRow`, `RunDrawer`, `RejectedRowsTable`, `ReplayConfirmDialog`.
- State: TanStack Query keys `['shuttle-flows', workspaceId]`, `['shuttle-flow', flowId]`, `['shuttle-runs', flowId, cursor]`, `['shuttle-run', runId]`; run pages poll every 5 seconds while a run is `queued` or `running`.
- API client: generated `DataShuttleApi` with `listFlows`, `createFlow`, `updateFlow`, `requestRun`, `listRuns`, `getRun`, `replayRun`; module gate via `useModuleAllowed('data-shuttle')` from `apps/web/src/features/entitlements`.
- Optimistic updates: none for runs (server state polled); flow save shows the stale banner on `conflict`.
- Telemetry: `shuttle_flow_created`, `shuttle_flow_updated`, `shuttle_run_requested`, `shuttle_run_replayed`, `shuttle_archive_downloaded`, `shuttle_mapping_previewed` with `flow_id`, `direction`, `trigger`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F052-01 through FR-F052-14 in `testing/features/F052/requirements/cases.md`
- [ ] Failure/edge-case tests: mapping to foreign column, coerce mismatch, cron under 15 minutes, `max_errors` exceeded under abort and partial, duplicate checksum, oversize file, replay of purged archive, owner lost sheet access
- [ ] Permission-negative and tenant-isolation tests: non-admin run denied, no entitlement denied by guard, tenant B run detail not_found, download URL expired
- [ ] Rust unit tests: `validate_mapping`, `min_interval_ok`, `apply_duplicate_strategy`, `compute_next_run` across DST
- [ ] API contract/integration tests: every route above with success and each error code
- [ ] Database migration/constraint tests: single active run index, checksum uniqueness, schedule index, archive retention index, duplicate `source_column` rejected by `shuttle_flow_column_maps`, two source columns mapped to one `column_id` rejected, a mapped or required `column_id` from another sheet rejected by the foreign key, sixth `shuttle_flow_key_columns` row rejected, duplicate `shuttle_run_rejections(run_id, row_number)` rejected, flow delete cascades its child rows while runs are restricted, rollback ordering
- [ ] React component tests: `MappingTable`, `RunDrawer`, `FlowEditorPage`, `RunHistoryPage` states
- [ ] Browser E2E tests: create import flow, run now, see counts, replay, archive download, scheduled run fires
- [ ] Accessibility tests: axe on list, editor, drawer; keyboard mapping edit
- [ ] Performance/load tests: 100k-row import under 10 minutes, run ack under 2 seconds, run list p95 under 500 ms

### Fast fanout configuration

- Test harness path: `testing/features/F052/`
- Feature flag: `F052_FEATURE`
- Fixture/seed factory: `testing/fixtures/data_shuttle.rs` builds tenant A (data-admin, editor, viewer), tenant B, an active `data-shuttle` entitlement with `max_flows 3`, `max_rows_per_run 200000`, `max_file_mb 50`, a `Budget` sheet with 6 typed columns, sample CSV/XLSX files in MinIO, and one flow with two historical runs
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, UTC, fixed file checksums
- Mock/stub contracts: outbox publisher recorded in memory; MinIO from compose; F030 connector adapter stubbed with a recorded `download`; scheduler tick driven by an injectable clock
- Parallel isolation: one schema per test worker, tenant ID per test, MinIO bucket prefix per test
- Targeted command: `cargo xtask test-feature F052`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F052/`

## 6. Acceptance criteria

```gherkin
Feature: Data Shuttle scheduled file flows

Scenario: Scheduled import updates matching rows
  Given flow "Budget import" with key column "Cost center", strategy update, and cron 0 6 * * 1-5 in America/New_York
  When the scheduler fires at 2026-09-03T10:00:00Z and the inbox holds budget-2026-09-03.csv with 120 rows
  Then the run finishes succeeded with rows_updated 100 and rows_inserted 20
  And shuttle-run.started.v1 and shuttle-run.completed.v1 are in the outbox
  And the file is archived with retain_until 30 days later

Scenario: Duplicate file is skipped
  Given the same file checksum already succeeded for the flow
  When an admin presses Run now
  Then the run finishes succeeded with skipped_reason duplicate_file and no rows change

Scenario: Validation abort writes nothing
  Given validation max_errors 5 and on_error abort
  When a file with 12 rows missing the required "Amount" column is processed
  Then the run status is failed with rows_rejected 12 and the sheet row count is unchanged
  And 12 shuttle_run_rejections rows carry reason_code missing_required

Scenario: Editor without data-admin cannot run
  Given a sheet editor without the data-admin role
  When they POST /api/v1/data-shuttle/flows/{id}/run
  Then the response is 403 denied and no run row exists

Scenario: Tenant without entitlement is blocked
  Given tenant B has no data-shuttle entitlement
  When its admin lists flows
  Then the response is 403 denied with field_errors.module not_entitled
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F010 (`import_jobs`, `export_jobs`, CSV/XLSX parsing, job status), F048 (`RequireModule`, entitlement limits, `useModuleAllowed`); decisions sections 2–4, 7, 9, 10; contracts row F052
- Blocks: none
- Conflicts with: none (disjoint owned paths)
- External dependencies: S3-compatible storage (MinIO locally); connector drives via F029/F030 for `connector` locations
- Risks and mitigations: a scheduler running on several workers could fire the same flow twice, so schedule rows are claimed with `for update skip locked` and the single-active-run index rejects the second claim; large files can exhaust worker memory, so rows stream through the F010 parser with a 50 MB default cap from the entitlement; DST transitions can double-fire or skip cron slots, so `compute_next_run` is tested across the 2026-11-01 and 2027-03-14 transitions.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F010 and F048 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F052/`
- [ ] Migration file name and owned paths claimed, including `crates/persistence/src/data-shuttle/**` and `services/worker/src/data-shuttle/**`
- [ ] Fixture factory, MinIO bucket isolation, and schema-per-worker available in `testing/harness/`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database/worker, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for every mutation and run
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets`, `check-contracts`, and `check-persistence` pass
- [ ] Rollback verified: disable `F052_FEATURE` (routes unmounted, scheduler idle, history intact), run down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Data administrators can define scheduled import and export flows with column mapping, duplicate strategy, validation, archiving, run history, and replay at `/w/{workspace_id}/data-shuttle`.
- Migration adds `shuttle_flows`, `shuttle_flow_column_maps`, `shuttle_flow_key_columns`, `shuttle_flow_required_columns`, `shuttle_schedules`, `shuttle_runs`, `shuttle_run_rejections`, and `shuttle_archives`; rollback drops them. Feature is off by default behind `F052_FEATURE` and requires a `data-shuttle` entitlement.
