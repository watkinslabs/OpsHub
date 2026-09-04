---
id: F053
type: feature
status: planned
priority: P1
owner: platform
estimate: 8
target_milestone: M7
parent_epic: E008
depends_on: [F009, F035, F048]
blocks: []
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/datamesh/**, crates/persistence/src/datamesh/**, services/api/src/datamesh/**, services/worker/src/datamesh/**, apps/web/src/features/datamesh/**, services/api/migrations/*_datamesh_*.sql, testing/features/F053/**]
feature_flag: F053_FEATURE
flag_default: off
branch: f053-datamesh
started_at: null
finished_at: null
---

# F053 — DataMesh

## 1. Identity and dates

- Branch: `f053-datamesh`
- Capability area: advanced modules (spec 5.11 DataMesh, 5.2 DATA-02 and "Cross-sheet references resolve by stable sheet/column/row IDs", 5.9 connector mapping contract "source/target IDs, direction, conflict policy, field transforms, deletion policy, and sync cursor", section 10 "Advanced modules use entitlement records plus feature flags")
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 7, 9, 10; `docs/capability-contracts.md` row F053
- Module slug: `datamesh`

## 2. Requirement specification

### Problem and user outcome

Reference data such as cost centers, vendors, customers, and employees is kept in one master sheet and copied by hand into dozens of project and intake sheets, where it drifts. F009 cell links connect one cell to one cell but cannot match whole rows by a business key or keep many sheets aligned. DataMesh maps a source sheet to a target sheet by match keys, previews what would change, synchronizes in a controlled run, and surfaces conflicts instead of overwriting them.

As a data administrator, I want to define a mapping between a master sheet and a target sheet by key columns, preview matches and changes, run a sync manually or on change, and resolve conflicts explicitly, so that reference data stays consistent across sheets without silent overwrites.

### Functional requirements

- **FR-F053-01:** An actor with the `data-admin` role can create a mapping with `name` (1–120 chars), `source_sheet_id`, `target_sheet_id` (different sheets in the same tenant), `match_keys` (1–3 ordered `{ source_column_id, target_column_id, normalize: exact | trim | case_insensitive | whitespace | date }` entries, each persisted as one `datamesh_mapping_match_keys` row keyed by `(mapping_id, ordinal)`), `field_maps` (1–100, one `datamesh_mapping_field_maps` row each), `sync_mode` (`manual` | `on_change` | `scheduled` with `cron_expression` ≥ 15 minutes), `unmatched_policy` (`create` | `ignore` | `flag`), and `deletion_policy` (`ignore` | `clear` | `flag`); the request and response keep `match_keys` and `field_maps` as JSON arrays, so the API shape is unchanged; the response returns a UUIDv7 `id` and `version` 1.
- **FR-F053-02:** Each field map is one `datamesh_mapping_field_maps` row `{ mapping_id, source_column_id, target_column_id, direction: source_to_target | bidirectional, transform: none | expression, expression?, overwrite: always | if_empty | never }` with primary key `(mapping_id, target_column_id)`, so one mapping writes a target column at most once; a column not on its sheet, a type-incompatible pair without a transform, an `expression` that fails the F035 parser or exceeds 200 AST nodes, a `bidirectional` map with a transform, or a second row for the same `target_column_id` returns `400 invalid` with `field_errors.field_maps[i].<field>`.
- **FR-F053-03:** The match engine computes `datamesh_matches` rows `{ mapping_id, source_row_id, target_row_id, key_hash, match_score }` by normalized key equality, hashing the `datamesh_mapping_match_keys` rows in `ordinal` order; a source row matching more than one target row, or a target row matched by more than one source row, is not written and produces a conflict of kind `ambiguous_match`.
- **FR-F053-04:** `POST /api/v1/datamesh/mappings/{id}/preview` runs the match engine without writing cells and returns `{ matched, unmatched_source, unmatched_target, would_create, would_update, would_clear, conflicts, sample: up to 50 rows }` within 30 seconds for sheets of 100,000 rows each; a preview older than 10 minutes is recomputed on the next request.
- **FR-F053-05:** `POST /api/v1/datamesh/mappings/{id}/sync` enqueues a `datamesh_runs` row and returns `202` with the run `id` within 2 seconds; a run for a mapping that already has a `queued` or `running` run returns `409 conflict` with `field_errors.run = "already_active"`; runs are idempotent by the `(mapping_id, source_cursor_sheet_version)` unique index and a repeated cursor finishes `succeeded` with `rows_written 0`.
- **FR-F053-06:** A sync run reads its plan from the `datamesh_mapping_field_maps` rows and writes matched fields through the F008 bulk cell service as the mapping owner honoring `overwrite` (`always`, `if_empty` writes only empty target cells, `never` reports only), applies `unmatched_policy` (`create` adds target rows with mapped fields, `ignore` skips, `flag` records `unmatched_source` conflicts), and applies `deletion_policy` for source rows deleted since the last cursor (`ignore`, `clear` empties mapped target cells, `flag` records `source_deleted` conflicts); every written cell gets an F009 link record `{ kind: datamesh, mapping_id, source_row_id }` so the grid shows provenance.
- **FR-F053-07:** A `datamesh_mapping_field_maps` row with `direction: bidirectional` writes target changes back to the source when only the target changed since the last cursor; when both sides changed the same field since the last cursor the run writes neither side and records a conflict of kind `both_changed` with both values and versions.
- **FR-F053-08:** `GET /api/v1/datamesh/mappings/{id}/conflicts` pages open conflicts by cursor with `limit` ≤ 100 and filters `kind` and `status`; `POST /api/v1/datamesh/conflicts/{id}/resolve` accepts `{ resolution: keep_source | keep_target | manual_value, value?, reason? }`, applies the chosen value through the cell service, marks the conflict `resolved` with actor and timestamp, and returns `409 conflict` when either row version moved since the conflict was recorded.
- **FR-F053-09:** `sync_mode: on_change` subscribes the worker to `row.updated.v1`, `cell.updated.v1`, `cells.bulk-updated.v1`, and `row.deleted.v1` for the source sheet and debounces a run per mapping to at most once per 60 seconds; `scheduled` runs use `cron_expression` in the tenant timezone and require it to be present; `manual` runs only through the sync route and rejects a `cron_expression`. The listener and the scheduler select their mappings by the indexed `sync_mode` and `source_sheet_id` columns, not by reading a JSON document.
- **FR-F053-10:** Per-tenant limits come from the F048 entitlement `limits` for `datamesh`: creating more than `max_mappings` returns `409 conflict` with `field_errors.mappings = "limit_reached"`; a run whose changed-row set exceeds `max_rows_per_sync` fails with `error_code = too_many_rows` before writing.
- **FR-F053-11:** Every mapping mutation requires `Idempotency-Key` and `If-Match`, writes an `audit_events` row with the diff, and publishes `mapping.updated.v1`; every finished run publishes `mapping.synced.v1` with counts, and every recorded conflict publishes `mapping-conflict.detected.v1` with `conflict_id` and `kind`.
- **FR-F053-12:** Every route is mounted behind `RequireModule(ModuleSlug::Datamesh)` from `crates/auth/src/entitlements/`, so a tenant without an active or trial entitlement and an enabled `F053_FEATURE` receives `403 denied` with `field_errors.module` before any handler runs; disabling the flag stops scheduled and on-change runs and keeps mappings, matches, and conflicts intact.
- **FR-F053-13:** A run fails with `error_code = sheet_denied` and writes nothing when the mapping owner no longer holds `sheet-editor` on the target (or on the source for bidirectional maps); cross-tenant access to any mapping, run, or conflict by id returns `not_found`.
- **FR-F053-14:** The web app renders the mapping list at `/w/{workspace_id}/datamesh`, a mapping editor with key and field map tables, a preview tab showing counts and the sample table with per-cell change markers, a runs tab, and a conflicts tab with side-by-side values and resolve actions.

### Non-functional requirements

- **NFR-F053-01 Performance:** preview of a 100,000-row source against a 100,000-row target completes in under 30 seconds; a sync of 10,000 changed rows finishes in under 2 minutes; conflict and mapping list routes respond in under 500 ms p95; sync acknowledgement under 2 seconds (spec section 6).
- **NFR-F053-02 Security/privacy:** the run acts only with the mapping owner's permissions and re-checks them at execution; preview and conflict payloads exclude columns the caller cannot read; tenant isolation is enforced by the `tenant_id` predicate the shared repository contract applies to every statement in `crates/persistence/src/datamesh/` and by cross-tenant negatives in the harness.
- **NFR-F053-03 Accessibility:** mapping editor, preview table, and conflicts tab pass axe with zero serious violations; change markers and conflict kinds use text plus icon; resolve actions are keyboard-operable with focus returned to the conflict row.
- **NFR-F053-04 Reliability/observability:** runs are JetStream jobs with per-tenant quota, three bounded retries, a 15-minute timeout, and dead-letter state visible on the run; metrics `datamesh_run_total{status}`, `datamesh_run_duration_seconds`, `datamesh_conflicts_open`; run spans carry `tenant_id`, `mapping_id`, `run_id`, `correlation_id`.

### Scope

Included: mapping CRUD, match keys with normalization, field maps with expression transforms, match engine, preview, sync runs with cursors, unmatched and deletion policies, bidirectional writes, conflict detection and resolution, on-change and scheduled triggers, entitlement limits, audit, outbox events, editor and conflicts UI.

Excluded: file-based ingestion (F052); external system sync (F030); new formula functions (F035 owns the parser and library); merging more than one source sheet into one target in a single mapping; automatic conflict resolution policies beyond explicit resolve.

## 3. UX specification

- Entry points: workspace navigation `DataMesh` (visible only when `useModuleAllowed('datamesh')` is true); route `/w/{workspace_id}/datamesh` for the list; `/w/{workspace_id}/datamesh/{mapping_id}` with tabs `Setup`, `Preview`, `Runs`, `Conflicts`; sheet menu `Sync from master sheet` opens a new mapping with the target preselected.
- Primary flow: admin clicks `New mapping`, picks source `Vendors master` and target `Purchase requests`, adds key `Vendor ID → Vendor ID` with `trim`, maps `Payment terms → Terms` (`source_to_target`, `always`) and `Contact → Vendor contact` (`bidirectional`, `if_empty`), chooses `on_change`, `unmatched: flag`, `deletion: flag`, saves, opens `Preview`, sees `matched 840, unmatched source 12, would update 96, conflicts 2`, presses `Sync now`, watches the run finish, opens `Conflicts`, and resolves an `ambiguous_match` by `keep_target`.
- Loading: skeleton tables; Empty: `No mappings yet` with `New mapping`, `No conflicts` on a clean mapping; Error: inline banner with `correlation_id` and retry; Success: toast `Mapping saved` / `Sync queued` / `Conflict resolved`; Stale/conflict: banner `This mapping changed` with `Reload`; resolve on a moved row shows `Row changed since the conflict` with refresh; Offline: editor and resolve disabled with offline badge.
- Permission-denied: non-`data-admin` users see mappings, preview, runs, and conflicts read-only without `Sync now` or resolve actions; a tenant without entitlement sees the shared `ModuleNotEntitled` panel.
- Preview table: sample rows with per-cell markers `create`, `update`, `clear`, `conflict` shown as icon plus text; a counts bar above the table.
- Responsive: tables scroll horizontally under 768 px with the key column frozen; tabs become a select under 640 px.
- Keyboard: `Tab` order covers tabs, tables, and actions; arrow keys move within map tables; `Enter` opens a column picker; `Escape` closes pickers and dialogs and restores focus; motion respects `prefers-reduced-motion`.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062), Lucide icons `GitMerge`, `Link2`, `Play`, `Eye`, `AlertTriangle`, `Check`, `ArrowLeftRight`; tokens from `apps/web/src/design/tokens.css`.

- Design: `design/artboards/DataMesh.dc.html` on the canvas indexed by `design/canvas.json`. The ticket is the contract and the artboard is the picture; when they disagree the ticket wins.

## 4. Technical specification

Canonical contract: `docs/capability-contracts.md` row F053 (aggregate `datamesh-mapping`, module `datamesh`, role `data-admin`).

### Rust backend

- Data access (decision section 2.1): `crates/persistence/src/datamesh/` holds `MappingRepository` (owns `datamesh_mappings`, `datamesh_mapping_match_keys`, `datamesh_mapping_field_maps`), `MatchRepository` (owns `datamesh_matches` and the run-scoped spill table), `MeshRunRepository` (owns `datamesh_runs`), and `ConflictRepository` (owns `datamesh_conflicts`); no other class writes those tables. Named queries: `list_mappings_for_workspace`, `count_mappings_for_tenant`, `list_match_keys`, `replace_match_keys`, `list_field_maps`, `replace_field_maps`, `find_field_map_owner_for_target_column`, `list_enabled_mappings_for_source_sheet`, `claim_due_scheduled_mappings` (`for update skip locked`), `advance_cursor`, `replace_matches_for_mapping`, `stream_matches_by_key_hash`, `find_match_by_target_row`, `spill_batch_insert` / `drain_spill_batch`, `insert_queued_run`, `find_active_run`, `find_succeeded_run_by_cursor`, `claim_run`, `finish_run`, `list_conflicts_page`, `count_open_conflicts`, `insert_open_conflicts`, `find_open_conflict`, `resolve_conflict`. There is no generic query entry point.
- The use cases below depend on these repository traits and contain no SQL, `sqlx::query*` call, or pool handle; the match engine, the sync consumer, the change listener, the scheduler, and the API handlers reach PostgreSQL only through the four repositories. A mapping save (mapping row plus its match-key and field-map rows plus the audit row and outbox record), a run completion (run counts, `last_cursor`, conflicts), and a conflict resolution (cell write plus conflict row) each run inside one `UnitOfWork` that owns the transaction.
- Domain entities in `crates/domain/src/datamesh/`: `Mapping { id, tenant_id, workspace_id, name, source_sheet_id, target_sheet_id, match_keys: Vec<MatchKey>, field_maps: Vec<FieldMap>, sync_mode: SyncMode, cron_expression: Option<CronExpr>, unmatched_policy, deletion_policy, owner_id, enabled, last_cursor: Option<Cursor { sheet_version, observed_at }>, version, audit fields, deleted_at }` assembled by `MappingRepository` from the parent row and its child rows, `MatchKey { ordinal, source_column_id, target_column_id, normalize: Normalize }`, `FieldMap { source_column_id, target_column_id, direction, transform: Transform, overwrite: Overwrite }`, `Match { mapping_id, source_row_id, target_row_id, key_hash, match_score }`, `MeshRun { id, tenant_id, mapping_id, mapping_version, trigger: manual | on_change | scheduled, status, source_cursor_sheet_version, source_cursor_at, counts: RunCounts { matched, created, updated, cleared, written_back, conflicts }, error_code, started_at, completed_at, duration_ms, correlation_id }`, `Conflict { id, tenant_id, mapping_id, run_id, kind: ambiguous_match | both_changed | unmatched_source | source_deleted, source_row_id, target_row_id, column_id, source_value, target_value, source_version, target_version, status: open | resolved, resolution, resolved_by, resolved_at }`.
- Use cases: `create_mapping`, `update_mapping`, `list_mappings`, `preview_mapping`, `request_sync`, `list_conflicts`, `resolve_conflict`, `execute_sync` (worker), `compute_matches`; pure functions `normalize_key(value, normalize)`, `plan_changes(matches, source_rows, target_rows, cursor, field_maps)` returning `ChangePlan { writes, write_backs, conflicts }`, and `validate_field_maps(source_cols, target_cols, maps)` are unit tested.
- Worker in `services/worker/src/datamesh/`: `SyncConsumer` on subject `datamesh.sync`, `ChangeListener` subscribed to the source-sheet row and cell events with a 60-second debounce per mapping, `Scheduler` for cron mappings, `MatchEngine` streaming both sheets by key columns with a hash join bounded at 500 MB, `Writer` calling the F008 bulk cell service and F009 link service in batches of 500 rows. None of them holds SQL: the listener resolves candidate mappings through `MappingRepository::list_enabled_mappings_for_source_sheet`, the scheduler claims work through `MappingRepository::claim_due_scheduled_mappings`, the engine persists and spills through `MatchRepository`, and the writer records conflicts and run counts through `ConflictRepository` and `MeshRunRepository` inside the run's `UnitOfWork`.
- API endpoints (`services/api/src/datamesh/`): `GET /api/v1/datamesh/mappings`, `POST /api/v1/datamesh/mappings`, `PATCH /api/v1/datamesh/mappings/{id}`, `POST /api/v1/datamesh/mappings/{id}/preview`, `POST /api/v1/datamesh/mappings/{id}/sync`, `GET /api/v1/datamesh/mappings/{id}/conflicts`, `POST /api/v1/datamesh/conflicts/{id}/resolve`. DTOs `CreateMappingRequest`, `UpdateMappingRequest`, `MappingResponse`, `PreviewResponse`, `SyncRequestResponse { run_id, status }`, `ConflictResponse`, `ResolveConflictRequest { resolution, value?, reason? }`, `Page<ConflictResponse>`.
- Events: `mapping.updated.v1`, `mapping.synced.v1` (payload adds `run_id`, `trigger`, `counts`, `error_code`), `mapping-conflict.detected.v1` (payload adds `conflict_id`, `kind`, `source_row_id`, `target_row_id`, `column_id`).
- Authorization: `RequireModule(ModuleSlug::Datamesh)` on the router; `data-admin` for create, update, sync, and resolve; sheet read on both sheets for preview and conflicts; the run executes as the mapping owner and re-checks `sheet-editor` on written sheets at execution time.
- Validation: name 1–120 chars; `match_keys` 1–3; `field_maps` 1–100; expression ≤ 200 AST nodes and 100 ms evaluation per cell via the F035 evaluator; cron ≥ 15 minutes; `limit` 1–100; `manual_value` must pass the target column validation from F007.
- Error mapping: `MappingError::SameSheet → 400 invalid`, `MappingError::LimitReached → 409 conflict`, `MappingError::RunActive → 409 conflict`, `MappingError::StaleVersion → 409 conflict`, `ConflictError::RowMoved → 409 conflict`, `MappingError::NotFound → 404 not_found`, field map validation → `400 invalid`, `AuthzError::Denied → 403 denied`, module guard → `403 denied`.

### PostgreSQL/SQLx

- Migration `*_datamesh_*.sql` creates `datamesh_mappings(id uuid pk, tenant_id uuid not null, workspace_id uuid not null references workspaces(id) on delete restrict, name text not null, source_sheet_id uuid not null references sheets(id) on delete restrict, target_sheet_id uuid not null references sheets(id) on delete restrict, sync_mode text not null check (sync_mode in ('manual','on_change','scheduled')), cron_expression text, cron_timezone text, unmatched_policy text not null check (unmatched_policy in ('create','ignore','flag')), deletion_policy text not null check (deletion_policy in ('ignore','clear','flag')), owner_id uuid not null references users(id) on delete restrict, enabled bool not null default true, last_cursor_sheet_version bigint, last_cursor_at timestamptz, version bigint not null default 1, created_by, created_at, updated_by, updated_at, deleted_at, check (source_sheet_id <> target_sheet_id), check ((sync_mode = 'scheduled') = (cron_expression is not null)))`, `datamesh_matches(tenant_id, mapping_id uuid not null references datamesh_mappings(id) on delete cascade, source_row_id uuid not null, target_row_id uuid not null, key_hash bytea not null, match_score smallint not null, computed_at timestamptz not null, primary key (mapping_id, source_row_id))`, `datamesh_runs(id uuid pk, tenant_id, mapping_id uuid not null references datamesh_mappings(id) on delete restrict, mapping_version bigint not null, trigger text not null check (trigger in ('manual','on_change','scheduled')), status text not null check (status in ('queued','running','succeeded','failed')), source_cursor_sheet_version bigint not null, source_cursor_at timestamptz not null, matched int, created int, updated int, cleared int, written_back int, conflicts int, error_code text, started_at, completed_at, duration_ms int, correlation_id uuid, created_at)`, `datamesh_conflicts(id uuid pk, tenant_id, mapping_id uuid not null references datamesh_mappings(id) on delete restrict, run_id uuid not null references datamesh_runs(id) on delete restrict, kind text not null check (kind in ('ambiguous_match','both_changed','unmatched_source','source_deleted')), source_row_id uuid, target_row_id uuid, column_id uuid references columns(id) on delete restrict, source_value jsonb, target_value jsonb, source_version bigint, target_version bigint, status text not null check (status in ('open','resolved')), resolution text check (resolution in ('keep_source','keep_target','manual_value')), reason text, resolved_by uuid references users(id) on delete restrict, resolved_at timestamptz, created_at)`.
- Normalized sets (decision section 2, no array or repeating-group columns): `datamesh_mapping_match_keys(mapping_id uuid not null references datamesh_mappings(id) on delete cascade, tenant_id uuid not null, ordinal smallint not null check (ordinal between 1 and 3), source_column_id uuid not null references columns(id) on delete restrict, target_column_id uuid not null references columns(id) on delete restrict, normalize text not null check (normalize in ('exact','trim','case_insensitive','whitespace','date')), primary key (mapping_id, ordinal), unique (mapping_id, source_column_id, target_column_id))` replaces `match_keys jsonb`; `datamesh_mapping_field_maps(mapping_id uuid not null references datamesh_mappings(id) on delete cascade, tenant_id uuid not null, source_column_id uuid not null references columns(id) on delete restrict, target_column_id uuid not null references columns(id) on delete restrict, direction text not null check (direction in ('source_to_target','bidirectional')), transform text not null default 'none' check (transform in ('none','expression')), expression text, overwrite text not null check (overwrite in ('always','if_empty','never')), primary key (mapping_id, target_column_id), check ((transform = 'expression') = (expression is not null)), check (not (direction = 'bidirectional' and transform = 'expression')))` replaces `field_maps jsonb`. Both were structures the product evaluates, validates, and queries by key, so decision section 2 makes them tables. `sync_mode jsonb` becomes the `sync_mode` enum column with `cron_expression` and `cron_timezone`; `last_cursor jsonb` becomes `last_cursor_sheet_version` and `last_cursor_at`, and the run's `source_version_cursor jsonb` becomes `source_cursor_sheet_version` and `source_cursor_at`, because the idempotency unique index constrains that value and decision section 2 forbids constraining a `jsonb` column. `CreateMappingRequest`, `UpdateMappingRequest`, and `MappingResponse` keep `match_keys` and `field_maps` as JSON arrays and `sync_mode` as an object with `cron_expression`, and `PreviewResponse`/`SyncRequestResponse` are unchanged; `MappingRepository::replace_match_keys` and `replace_field_maps` fan the arrays out to rows and `list_match_keys`/`list_field_maps` reassemble them on read, replacing a set with one `delete` of removed rows plus one `insert ... on conflict do update` inside the mapping's `UnitOfWork`.
- `jsonb` audit: `datamesh_conflicts.source_value` and `datamesh_conflicts.target_value` stay `jsonb` — they are F007 typed cell values captured verbatim for side-by-side display, never filtered, joined, or aggregated; the resolve path selects by `id`, `mapping_id`, `status`, and `kind`. `match_keys`, `field_maps`, `sync_mode`, `last_cursor`, and `source_version_cursor` were all `jsonb` the product parses, validates, indexes, or constrains, and are converted above. No other `jsonb` column remains in this module.
- Invariants: unique `datamesh_mappings(tenant_id, workspace_id, lower(name)) where deleted_at is null`; `datamesh_mapping_match_keys` primary key `(mapping_id, ordinal)` gives 1–3 ordered keys with no duplicate column pair, and `MappingRepository::replace_match_keys` rejects a gap in `ordinal`; `datamesh_mapping_field_maps` primary key `(mapping_id, target_column_id)` blocks two maps onto one target column inside a mapping, and partial unique `datamesh_mapping_field_maps(tenant_id, target_column_id)` over rows whose mapping is `enabled and deleted_at is null` enforces the cross-mapping `owned_by_mapping` conflict of FR-F053-02 as a database constraint instead of a scan; unique `datamesh_matches(mapping_id, target_row_id)` so one target row has at most one match; partial unique `datamesh_runs(mapping_id) where status in ('queued','running')`; unique `datamesh_runs(mapping_id, source_cursor_sheet_version) where status = 'succeeded'` backs idempotency; partial unique `datamesh_conflicts(mapping_id, source_row_id, target_row_id, column_id, kind) where status = 'open'` prevents duplicate open conflicts.
- Indexes: `datamesh_matches(mapping_id, key_hash)`, `datamesh_runs(mapping_id, created_at desc)`, `datamesh_conflicts(mapping_id, status, created_at desc)`, `datamesh_mappings(tenant_id, source_sheet_id) where enabled and deleted_at is null and sync_mode = 'on_change'` for the change listener, `datamesh_mappings(tenant_id, sync_mode) where enabled and deleted_at is null` for the cron scheduler claim, `datamesh_mapping_match_keys(mapping_id, ordinal)` and `datamesh_mapping_field_maps(mapping_id)` for mapping assembly, and `datamesh_mapping_field_maps(tenant_id, source_column_id)` for the reverse "which mappings read this column" lookup the column-delete guard and the editor use.
- Audit events: `datamesh-mapping.create`, `datamesh-mapping.update`, `datamesh-mapping.delete`, `datamesh-run.request`, `datamesh-conflict.resolve` with field diffs; cell writes reuse the F008 cell history with `source = datamesh` and `run_id`.
- Retention/deletion: mappings soft delete; a purge cascades to `datamesh_mapping_match_keys`, `datamesh_mapping_field_maps`, and `datamesh_matches`, which cannot outlive the mapping, while `datamesh_runs` and `datamesh_conflicts` are `on delete restrict` history and follow F027 tenant retention; deleting a mapped column is restricted by the field-map and match-key foreign keys, so the mapping must be edited first. Rollback drops the six tables, children before parents.

### React/TypeScript

- Routes: `/w/:workspaceId/datamesh`, `/w/:workspaceId/datamesh/new`, `/w/:workspaceId/datamesh/:mappingId` with `?tab=setup|preview|runs|conflicts` in `apps/web/src/features/datamesh/`; components `MappingListPage`, `MappingRow`, `MappingEditorPage`, `SheetPairPicker`, `MatchKeyTable`, `FieldMapTable`, `FieldMapRow`, `ExpressionField`, `SyncModeFields`, `PreviewTab`, `PreviewCounts`, `PreviewTable`, `RunsTab`, `RunRow`, `ConflictsTab`, `ConflictRow`, `ResolveDialog`.
- State: TanStack Query keys `['datamesh-mappings', workspaceId]`, `['datamesh-mapping', mappingId]`, `['datamesh-preview', mappingId, version]`, `['datamesh-runs', mappingId, cursor]`, `['datamesh-conflicts', mappingId, filters, cursor]`; runs and preview poll every 5 seconds while `queued` or `running`.
- API client: generated `DatameshApi` with `listMappings`, `createMapping`, `updateMapping`, `previewMapping`, `requestSync`, `listConflicts`, `resolveConflict`; module gate via `useModuleAllowed('datamesh')` from `apps/web/src/features/entitlements`.
- Optimistic updates: resolve marks the conflict row resolved locally and rolls back on `conflict` with the row-moved notice.
- Telemetry: `datamesh_mapping_created`, `datamesh_mapping_updated`, `datamesh_preview_run`, `datamesh_sync_requested`, `datamesh_conflict_resolved` with `mapping_id`, `sync_mode`, `kind`, `resolution`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F053-01 through FR-F053-14 in `testing/features/F053/requirements/cases.md`
- [ ] Failure/edge-case tests: same sheet as source and target, expression over 200 nodes, ambiguous match both directions, both-changed conflict, deletion policy `clear`, repeated cursor, resolve on moved row, owner lost target access
- [ ] Permission-negative and tenant-isolation tests: non-admin sync and resolve denied, no entitlement denied by guard, tenant B mapping/conflict not_found, preview redacts unreadable columns
- [ ] Rust unit tests: `normalize_key` per mode, `plan_changes` truth table over `overwrite` and `direction`, `validate_field_maps`, debounce timing
- [ ] API contract/integration tests: every route above with success and each error code
- [ ] Database migration/constraint tests: same-sheet check, match-key ordinal range and duplicate column pair, one field map per target column, cross-mapping target-column uniqueness while enabled, `scheduled` without `cron_expression` rejected, bidirectional-with-expression rejected, mapped-column delete restricted, cascade of match keys and field maps on purge, target uniqueness in matches, single active run, cursor idempotency index, open-conflict uniqueness, rollback
- [ ] React component tests: `FieldMapTable`, `PreviewTab`, `ConflictsTab`, `ResolveDialog`, `MappingListPage` states
- [ ] Browser E2E tests: create mapping, preview, sync, provenance link in grid, resolve conflict, on-change sync
- [ ] Accessibility tests: axe on editor, preview, conflicts; keyboard resolve
- [ ] Performance/load tests: 100k×100k preview under 30 s, 10k-row sync under 2 minutes, conflicts list p95 under 500 ms

### Fast fanout configuration

- Test harness path: `testing/features/F053/`
- Feature flag: `F053_FEATURE`
- Fixture/seed factory: `testing/fixtures/datamesh.rs` builds tenant A (data-admin, editor, viewer), tenant B, an active `datamesh` entitlement with `max_mappings 5` and `max_rows_per_sync 50000`, a `Vendors master` sheet with 1,000 rows, a `Purchase requests` sheet with 1,200 rows (840 matching, 12 unmatched, 2 ambiguous), and one mapping with a completed run and two open conflicts
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, UTC, fixed key hashes
- Mock/stub contracts: outbox publisher recorded in memory; F008 cell service and F009 link service used for real against the fixture; JetStream event replay from recorded `row.updated.v1` payloads; injectable clock for debounce and cron
- Parallel isolation: one schema per test worker, tenant ID per test
- Targeted command: `cargo xtask test-feature F053`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F053/`

## 6. Acceptance criteria

```gherkin
Feature: DataMesh reference-data synchronization

Scenario: Preview then sync updates matched rows with provenance
  Given mapping "Vendors → Purchase requests" keyed by Vendor ID with trim normalization
  When the admin previews and then requests a sync
  Then preview reports matched 840, unmatched_source 12, would_update 96, conflicts 2
  And the run finishes succeeded with updated 96 and each written cell carries a datamesh link
  And mapping.synced.v1 is in the outbox

Scenario: Both sides changed produces a conflict, not an overwrite
  Given a bidirectional map on Vendor contact and edits on both sheets since the last cursor
  When the sync runs
  Then neither cell changes and a both_changed conflict holds both values and versions
  And mapping-conflict.detected.v1 is in the outbox

Scenario: Resolve conflict on a moved row is rejected
  Given an open conflict recorded at target version 4
  When the target row is edited to version 5 and the admin resolves with keep_source
  Then the response is 409 conflict and the conflict stays open

Scenario: Editor without data-admin cannot sync
  Given a sheet editor without the data-admin role
  When they POST /api/v1/datamesh/mappings/{id}/sync
  Then the response is 403 denied and no run row exists

Scenario: Tenant without entitlement is blocked
  Given tenant B has no datamesh entitlement
  When its admin lists mappings
  Then the response is 403 denied with field_errors.module not_entitled
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F009 (link records for provenance, hierarchy-safe row reads), F035 (expression parser and evaluator for transforms), F048 (`RequireModule`, entitlement limits, `useModuleAllowed`); decisions sections 2–4, 7, 9, 10; contracts row F053
- Blocks: none
- Conflicts with: none (disjoint owned paths)
- External dependencies: none
- Risks and mitigations: two mappings writing the same target column can ping-pong, so creating a second enabled mapping onto a target column already owned by another mapping violates the partial unique index on `datamesh_mapping_field_maps(tenant_id, target_column_id)` and returns `409 conflict` with `field_errors.field_maps[i].target_column_id = "owned_by_mapping"`; a bidirectional map can loop through the on-change listener, so runs tag their writes with `source = datamesh` and the listener ignores events carrying that source; large hash joins can exhaust memory, so the engine spills to a temporary table above 500 MB and the preview is bounded by the 30-second budget with a `preview_timeout` error.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F009, F035, and F048 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F053/`
- [ ] Migration file name and owned paths claimed, including `crates/persistence/src/datamesh/**` and `services/worker/src/datamesh/**`
- [ ] Fixture factory with the vendor and purchase-request sheets and schema-per-worker isolation available in `testing/harness/`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database/worker, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for every mutation, run, and conflict
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F053_FEATURE` (routes unmounted, listener and scheduler idle, data intact), run down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Data administrators can map a master sheet to target sheets by key columns, preview changes, synchronize manually, on change, or on a schedule, and resolve conflicts explicitly at `/w/{workspace_id}/datamesh`.
- Migration adds `datamesh_mappings`, `datamesh_mapping_match_keys`, `datamesh_mapping_field_maps`, `datamesh_matches`, `datamesh_runs`, and `datamesh_conflicts`; rollback drops them, children before parents. Feature is off by default behind `F053_FEATURE` and requires a `datamesh` entitlement.
