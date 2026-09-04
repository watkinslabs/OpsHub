---
id: F021
type: feature
status: planned
priority: P1
owner: platform
estimate: 8
target_milestone: M4
parent_epic: E005
depends_on: [F008, F035, F003]
blocks: [F022, F023, F031, F039, F056]
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/reports/**, services/api/src/reports/**, services/worker/src/reports/**, apps/web/src/features/reports/**, services/api/migrations/*_reports_*.sql, testing/features/F021/**]
feature_flag: F021_FEATURE
flag_default: off
branch: f021-cross-source-reports
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 7, 9
- Capability contract: `docs/capability-contracts.md` row F021
- Product spec: `docs/product-capability-spec.md` section 5.6 REPORT-01, REPORT-03 (refresh), section 4 Report entity, section 6

# F021 — Cross-source reports

## 1. Identity and dates

- Branch: `f021-cross-source-reports`
- Capability area: reporting (spec 5.6 REPORT-01 combine filtered data from multiple sheets; low-level bullets: report query model with source selection, joins by stable IDs/keys, filters, grouping, calculated fields, row-level permission filtering; refresh jobs cached with last-success, duration, source versions, stale state)
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 7; `docs/capability-contracts.md` row F021
- Aggregate: `report`
- Module slug: `reports`

## 2. Requirement specification

### Problem and user outcome

A PMO tracks projects in one sheet, risks in a second, and budget lines in a third. Today they copy rows into a spreadsheet every Friday to answer "which projects owned by Dana have open high risks and are over budget". They need a report that selects those sheets, joins them by the stable row-link column, filters and groups them, adds a calculated field, refreshes on a schedule, and never shows a viewer a row or column they cannot open in the source sheet.

As a report editor, I want to define a report over several sheets with joins, filters, grouping, and calculated fields and refresh it into a cached snapshot, so that my team reads one governed result instead of consolidating spreadsheets.

### Functional requirements

- **FR-F021-01:** An actor with the `report-editor` role on a workspace can `POST /api/v1/reports` with `{ name, workspace_id, folder_id?, description?, definition: ReportDefinition, refresh_policy }`; the response returns a UUIDv7 `id`, `version` 1, and `snapshot: null`; `name` is unique per folder (case-insensitive) or the call returns `409 conflict` with `field_errors.name = "taken"`.
- **FR-F021-02:** `ReportDefinition.sources` lists 1 to 20 sheets, each `{ alias, sheet_id, column_ids[] }`, stored as one `report_sources` row per source and one `report_source_columns` row per selected column and returned in the same nested shape; an alias not matching `^[a-z][a-z0-9_]{0,31}$`, a duplicate alias, a `sheet_id` outside the tenant, or a `column_id` not on that sheet returns `400 invalid` with `field_errors["definition.sources[i]"]`.
- **FR-F021-03:** `ReportDefinition.joins` lists 0 to 19 joins `{ left: {alias, column_id}, right: {alias, column_id}, kind: inner|left }` that form a tree rooted at `sources[0]`, stored one per `report_joins` row with `kind` constrained to `inner|left` and both sides referencing `report_sources` and `columns`; join columns match by stable ID: a `link` column matches the row `id` of the right source, and `text`, `number`, `select`, `person` columns match by normalized value with the same type on both sides; a cycle, a disconnected source, or a type mismatch returns `400 invalid` with `field_errors["definition.joins[i]"]`.
- **FR-F021-04:** `ReportDefinition.filters` is an `and`/`or` tree of at most depth 4 and 50 predicates; operators are `eq, neq, in, not_in, contains, starts_with, gt, gte, lt, lte, between, is_empty, is_not_empty` plus relative date tokens `today`, `start_of_week`, `-7d`, `+30d` evaluated in `reports.refresh_timezone`; each predicate is a `report_filters` row keyed by its `node_path` in the tree, so the tree round-trips without a JSON blob; an operator not valid for the column type returns `400 invalid`.
- **FR-F021-05:** `ReportDefinition.group_by` lists 0 to 3 `{ alias, column_id, order: asc|desc }` levels and `ReportDefinition.aggregates` lists up to 20 `{ label, alias, column_id, fn: count|count_distinct|sum|avg|min|max }`; stored as `report_group_by` rows keyed `(report_id, level)` and `report_aggregates` rows keyed `(report_id, position)` with unique `(report_id, lower(label))`; `sum` and `avg` require `number`, `currency`, or `duration` columns; the rows endpoint returns group header rows with `kind: "group"`, `depth`, `key`, `aggregates`, and `row_count`.
- **FR-F021-06:** `ReportDefinition.calculated_fields` lists up to 25 `{ label, expression, result_type }` stored one per `report_calculated_fields` row with unique `(report_id, position)` and `(report_id, lower(label))`, where `expression` is an F035 formula over references `{alias.column_id}` and earlier calculated fields; each expression is parsed at save time with the F035 parser (10,000 AST nodes, no cycles) and evaluated per row at refresh under the 2 second per-report formula budget; parse failure returns `400 invalid` with `field_errors["definition.calculated_fields[i].expression"]` and the parser message.
- **FR-F021-07:** `POST /api/v1/reports/{id}/refresh` enqueues a `reports.refresh` job and returns `202` within 2 seconds with `{ run_id, status: "queued" }`; the worker executes the definition, writes a `report_snapshots` row with `status succeeded|failed`, `row_count`, `duration_ms`, `computed_at`, and `error` plus one `report_snapshot_sources` row per source sheet carrying its `sheet_version` (surfaced as the `source_versions` map of `sheet_id` to sheet `version`), keeps the last 3 succeeded snapshots per report, and publishes `report.refreshed.v1`; a second refresh while one is `queued|running` returns `409 conflict` with the active `run_id`.
- **FR-F021-08:** `refresh_policy` is `{ mode: manual|interval, interval_minutes?, timezone }` with `interval_minutes` in 5..1440 and `timezone` an IANA name; interval reports are enqueued by the worker scheduler at most once per interval per report and never while a run is active.
- **FR-F021-09:** `GET /api/v1/reports/{id}/rows?cursor&limit&snapshot_id?` returns the latest succeeded snapshot's rows in definition sort order with `limit` 1..500, each row `{ row_id, sources: {alias: source_row_id}, cells: {column_ref: {raw, display}}, calculated: {label: {raw, display}} }`, and a `meta { snapshot_id, computed_at, duration_ms, source_versions, stale, restricted_sources[], hidden_columns[] }`; `stale` is true when any current sheet `version` exceeds the snapshot's recorded version.
- **FR-F021-10:** Row-level permission filtering: the rows endpoint returns a snapshot row only if the viewer holds `read` on every source sheet contributing a non-null source row for an `inner` join, and drops the right side (nulls) of a `left` join whose sheet the viewer cannot read; sheets the viewer cannot read appear in `meta.restricted_sources`; columns hidden from the viewer by F007 column visibility or F003 field-level ACL are removed from `cells` and listed in `meta.hidden_columns`.
- **FR-F021-11:** Group aggregates are computed at read time over the rows visible to the viewer, so hidden rows and hidden columns never contribute to `count`, `sum`, `avg`, `min`, `max`, or `count_distinct`; when tenant policy `reports.aggregate_hidden_values` is `true` and the report has `aggregate_policy: "owner"`, aggregates use the snapshot computed under the report owner's scope and the response sets `meta.aggregate_scope = "owner"`.
- **FR-F021-12:** `GET /api/v1/reports` pages by opaque cursor with `limit` 1..100, filters by `workspace_id`, `folder_id`, `name` prefix, `deleted`, sorts by `name` or `updated_at`, and returns only reports the actor can read; `GET /api/v1/reports/{id}` returns the definition, `refresh_policy`, `latest_snapshot` summary, and `version`.
- **FR-F021-13:** `PATCH /api/v1/reports/{id}` updates `name`, `description`, `folder_id`, `definition`, `refresh_policy`, `aggregate_policy` with `If-Match`; a stale version returns `409 conflict` with `current_version`; a definition change marks every existing snapshot `stale = true`; `DELETE` soft-deletes the report and cancels its scheduled refreshes; a foreign-tenant actor receives `404 not_found` on every route.
- **FR-F021-14:** Every mutation requires `Idempotency-Key`, writes an `audit_events` row with before/after diff, and publishes `report.created.v1`, `report.updated.v1`, or `report.deleted.v1` through the outbox; replaying a key with a different body returns `409 conflict`.
- **FR-F021-15:** The web app renders a report editor (sources, joins, filters, grouping, calculated fields, refresh policy) and a report viewer (rows, group headers, stale banner, refresh button, restricted-source notice) with loading, empty, error, denied, stale, computing, and offline states.

### Non-functional requirements

- **NFR-F021-01 Performance:** rows page of 500 from a 100,000-row snapshot responds under 500 ms p95 with permission filtering applied; a refresh joining three 100,000-row sheets with 500 columns each completes under 60 s and is acknowledged under 2 s; save with 25 calculated fields parses under 800 ms p95.
- **NFR-F021-02 Security/privacy:** tenant isolation by `tenant_id` predicate on every query; permission filtering evaluated in service code with the F003 engine; cross-tenant, viewer, hidden-column, restricted-sheet, and guest-link negatives are in the harness; snapshot rows are never served to an actor lacking `read` on the report.
- **NFR-F021-03 Accessibility:** editor and viewer pass axe with zero serious violations; the join and filter builders are fully keyboard operable; stale and refresh state changes are announced through a live region; reduced motion disables skeleton shimmer.
- **NFR-F021-04 Reliability/observability:** refresh jobs are idempotent by `run_id`, retry 3 times with backoff, dead-letter after the fourth failure, and record `duration_ms`; spans carry `tenant_id`, `report_id`, `run_id`, `correlation_id`; metrics `report_refresh_duration_seconds`, `report_refresh_failures_total`, `report_rows_filtered_total` are exported.

### Scope

Included: report CRUD, definition validation, joins by stable IDs, filter tree, grouping and aggregates, calculated fields through the F035 engine, cached snapshots with refresh runs, interval scheduling, permission-filtered row reads, stale detection, audit and outbox events, report editor and viewer UI.

Excluded: metrics and KPI values (F022), dashboards and widgets (F023), charts and time series (F024), drill-through and export (F025), portfolio rollups (F031), pivots (F056), natural-language report generation (F039).

## 3. UX specification

- Entry points: workspace tree item `New report`; route `/w/{workspace_id}/reports/{report_id}` for the viewer and `/w/{workspace_id}/reports/{report_id}/edit` for the editor; folder context menu `Restore`.
- Primary flow: click `New report`, name it, pick source sheet "Projects" and columns, add source "Risks", add join `Projects.id = Risks.project` (link column), add filter `Risks.severity in [High, Critical]`, group by `Projects.owner`, add calculated field `Days late = DAYS(TODAY(), {projects.due})`, set refresh every 60 minutes, save; the viewer shows `Computing` until the first snapshot lands, then rows with group headers and aggregates.
- Loading: skeleton table; Empty: "No rows match" with a link to edit filters; Error: banner with `correlation_id` and retry; Computing: progress badge with elapsed time; Stale: banner "Sources changed since {computed_at}" with `Refresh now`; Denied: read-only editor with disabled controls for viewers; Not found for non-members; Offline: refresh disabled and offline badge.
- Restricted sources: an info bar "Rows from 1 sheet you cannot open are hidden" lists `restricted_sources` names the viewer can see and hides the rest.
- Responsive: the editor stacks panels under 1024 px; the viewer freezes the first column under 768 px.
- Keyboard: join and filter builders are lists of rows with `Enter` to edit, `Delete` to remove, arrows to move; group headers toggle with `Space`; focus ring from shared tokens; `prefers-reduced-motion` respected.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062); Lucide `FileBarChart`, `GitMerge`, `Filter`, `Layers`, `Sigma`, `RefreshCw`, `AlertTriangle`; tokens from `apps/web/src/design/tokens.css`.

## 4. Technical specification

### Rust backend

- Domain entities in `crates/domain/src/reports/`: `Report { id, tenant_id, workspace_id, folder_id, name, description, definition: ReportDefinition, refresh_policy: RefreshPolicy, aggregate_policy: AggregatePolicy, version, audit fields, deleted_at }`, `ReportDefinition { sources: Vec<ReportSource>, joins: Vec<ReportJoin>, filters: FilterNode, group_by: Vec<GroupLevel>, aggregates: Vec<AggregateSpec>, calculated_fields: Vec<CalculatedField>, sorts: Vec<SortSpec> }`, `ReportSource { alias: Alias, sheet_id, column_ids }`, `ReportJoin { left: ColumnRef, right: ColumnRef, kind: JoinKind }`, `FilterNode::{And(Vec), Or(Vec), Predicate { column: ColumnRef, op: FilterOp, value }}`, `ReportSnapshot { id, report_id, run_id, status, row_count, duration_ms, source_versions: BTreeMap<SheetId, i64>, computed_at, error, scope: SnapshotScope }`, `SnapshotRow { row_id, sources: BTreeMap<Alias, RowId>, cells: BTreeMap<ColumnRef, CellValue>, calculated: BTreeMap<Label, CellValue> }`. These are in-memory shapes only: `ReportDefinition` is composed from `report_sources`, `report_source_columns`, `report_joins`, `report_filters`, `report_group_by`, `report_aggregates`, and `report_calculated_fields`; `RefreshPolicy` from the typed `refresh_mode`, `refresh_interval_minutes`, `refresh_timezone` columns; `source_versions` from `report_snapshot_sources`; `SnapshotRow.sources` from `report_snapshot_row_sources`.
- Use cases: `create_report`, `update_report`, `delete_report`, `restore_report`, `list_reports`, `get_report`, `validate_definition` (aliases, join tree, operator/type matrix, F035 parse), `request_refresh`, `execute_refresh` (worker), `read_rows` (permission filter + group at read), `compute_stale`.
- Query compiler `crates/domain/src/reports/compiler.rs`: turns a `ValidatedDefinition` into a `CompiledQuery` — a per-source read plan (sheet, projected columns, filter predicates) plus the join graph — and holds no SQL string, `sqlx::query*` call, or connection; the F006/F008 `rows`/`cells` reads are executed by those features' repositories under the plan, and the joined stream feeds the calculated-field evaluator `crates/domain/src/reports/calc.rs` calling `formulas::evaluate` with a `RowScope`.
- Persistence (`crates/persistence/src/reports/`): `ReportRepository` owns `reports`, `report_sources`, `report_source_columns`, `report_joins`, `report_filters`, `report_group_by`, `report_aggregates`, `report_calculated_fields`; `ReportSnapshotRepository` owns `report_snapshots`, `report_snapshot_sources`, `report_snapshot_rows`, `report_snapshot_row_sources`. Each implements the shared `Repository` contract (`get`, `list` with cursor pagination, `insert`, `update` under an expected version, `soft_delete`, `restore`, `purge`) and adds named queries `load_definition(report_id)`, `replace_definition(report_id, definition)`, `list_reports_using_sheet(sheet_id)`, `list_reports_using_column(column_id)`, `page_reports(filter, cursor)`, `claim_refresh(report_id, run_id)`, `find_active_run(report_id)`, `latest_succeeded(report_id)`, `page_snapshot_rows(snapshot_id, cursor, limit)`, `mark_snapshots_stale(report_id)`, `prune_snapshots(report_id, keep)`; the tenant predicate, soft-delete filter, version check, audit row, and outbox enqueue come from the base contract. Replacing a definition (all eight definition tables plus the stale marking) and writing a snapshot (header, `report_snapshot_sources`, rows, `report_snapshot_row_sources`) each run in one `UnitOfWork` that owns the transaction. The permission-aware row read composes a query executed by `ReportSnapshotRepository` under the caller's `ViewerScope`. Per decision 2.1 the use cases above depend on these repository traits and contain no SQL: no SQL string, `sqlx::query*` call, or connection exists in `crates/domain/src/reports`, `services/api/src/reports`, `services/worker/src/reports`, or the F021 tests.
- Permission filter `crates/domain/src/reports/scope.rs`: `ViewerScope { readable_sheets: HashSet<SheetId>, hidden_columns: HashSet<ColumnId>, scope_key: Sha256 }` built from the F003 engine per request and cached 60 s per `(actor_id, report_id)`.
- Worker `services/worker/src/reports/{refresh_job.rs, scheduler.rs}`: consumes the `reports.refresh` JetStream subject, calls `ReportRepository::claim_refresh(report_id, run_id)` to take the run, hands batches of 5,000 rows (with their `report_snapshot_row_sources` entries) to `ReportSnapshotRepository`, enforces the 60 s job timeout, and emits `report.refreshed.v1`; the scheduler selects due interval reports through `page_reports` over `refresh_mode`/`refresh_interval_minutes` and holds no SQL of its own.
- API endpoints (`services/api/src/reports/`): `GET /api/v1/reports`, `POST /api/v1/reports`, `GET /api/v1/reports/{id}`, `PATCH /api/v1/reports/{id}`, `DELETE /api/v1/reports/{id}`, `GET /api/v1/reports/{id}/rows`, `POST /api/v1/reports/{id}/refresh`; DTOs `CreateReportRequest`, `UpdateReportRequest`, `ReportResponse`, `ReportRowsResponse { rows, meta: RowsMeta, next_cursor }`, `RefreshResponse { run_id, status }`.
- Events: `report.created.v1`, `report.updated.v1`, `report.deleted.v1`, `report.refreshed.v1` (payload adds `snapshot_id`, `status`, `row_count`, `duration_ms`, `source_versions`).
- Authorization: `report-editor` on the workspace for mutations and refresh; `report-viewer` or report ACL `read` for reads; source sheet reads use the sheet ACL per viewer; explicit deny wins; missing report access maps to `not_found`.
- Validation limits: name 1..200, description ≤ 4,000, sources ≤ 20, joins ≤ 19, predicates ≤ 50, depth ≤ 4, group levels ≤ 3, aggregates ≤ 20, calculated fields ≤ 25, `limit` ≤ 500; the `definition` object in the request body ≤ 256 KB before it is decomposed into rows.
- Error mapping: `ReportError::NameTaken → 409 conflict`, `ReportError::StaleVersion → 409 conflict`, `ReportError::RefreshActive → 409 conflict`, `ReportError::InvalidDefinition(field, msg) → 400 invalid`, `ReportError::NotFound → 404 not_found`, `AuthzError::Denied → 403 denied`, `FormulaError::Parse → 400 invalid`, job queue unavailable → `503 unavailable`.

### PostgreSQL/SQLx

- Migration `*_reports_*.sql` creates `reports(id uuid pk, tenant_id uuid not null, workspace_id uuid not null, folder_id uuid null, name text not null, description text, refresh_mode text not null check (refresh_mode in ('manual','interval')), refresh_interval_minutes int null check (refresh_interval_minutes between 5 and 1440), refresh_timezone text not null default 'UTC', aggregate_policy text not null default 'viewer', version bigint not null default 1, created_by, created_at, updated_by, updated_at, deleted_at)` with `check (refresh_mode <> 'interval' or refresh_interval_minutes is not null)`. There is no `definition jsonb` and no `refresh_policy jsonb`: the whole `ReportDefinition` is normalized, so it has exactly one source of truth.
- Definition tables (all carry `tenant_id`, `created_by`, `created_at`, `updated_by`, `updated_at` like their siblings): `report_sources(id uuid pk, tenant_id uuid not null, report_id uuid not null references reports(id) on delete cascade, alias text not null, sheet_id uuid not null references sheets(id) on delete restrict, position smallint not null)` with `unique (report_id, alias)` and `unique (report_id, position)`; `report_source_columns(source_id uuid not null references report_sources(id) on delete cascade, tenant_id uuid not null, column_id uuid not null references columns(id) on delete restrict, position smallint not null, primary key (source_id, column_id))` with `unique (source_id, position)`, replacing `report_sources.column_ids uuid[]`; `report_joins(id uuid pk, tenant_id uuid not null, report_id uuid not null references reports(id) on delete cascade, position smallint not null, kind text not null check (kind in ('inner','left')), left_source_id uuid not null references report_sources(id) on delete cascade, left_column_id uuid not null references columns(id) on delete restrict, right_source_id uuid not null references report_sources(id) on delete cascade, right_column_id uuid not null references columns(id) on delete restrict)` with `unique (report_id, position)` and `check (left_source_id <> right_source_id)` — the 0..19 count, the tree/cycle rule and the join type match stay service validations in `validate_definition`.
- `report_filters(id uuid pk, tenant_id uuid not null, report_id uuid not null references reports(id) on delete cascade, node_path text not null, column_id uuid not null references columns(id) on delete restrict, op text not null, value jsonb)` with `unique (report_id, node_path)`; `node_path` encodes the position of the predicate in the `and`/`or` tree, so the tree is rebuilt from rows. `value` stays `jsonb` because it is a typed cell value whose shape follows the referenced column's F007 type (scalar, list for `in`, pair for `between`) and is never read by key or filtered on in SQL.
- `report_group_by(report_id uuid not null references reports(id) on delete cascade, tenant_id uuid not null, level smallint not null check (level between 1 and 3), source_id uuid not null references report_sources(id) on delete cascade, column_id uuid not null references columns(id) on delete restrict, direction text not null check (direction in ('asc','desc')), primary key (report_id, level))` — the ≤ 3 group levels are now declarative.
- `report_aggregates(id uuid pk, tenant_id uuid not null, report_id uuid not null references reports(id) on delete cascade, position smallint not null, label text not null, source_id uuid not null references report_sources(id) on delete cascade, column_id uuid null references columns(id) on delete restrict, fn text not null check (fn in ('count','count_distinct','sum','avg','min','max')))` with `unique (report_id, position)` and `unique (report_id, lower(label))`; the ≤ 20 cap and the numeric-column rule for `sum`/`avg` stay service validations.
- `report_calculated_fields(id uuid pk, tenant_id uuid not null, report_id uuid not null references reports(id) on delete cascade, position smallint not null, label text not null, expression text not null, result_type text not null)` with `unique (report_id, position)` and `unique (report_id, lower(label))`; the ≤ 25 cap and F035 parsing (10,000 AST nodes, no cycles) stay in the service.
- What normalization buys and preserves: `GET` and `PATCH` still take and return one nested `definition` object, composed and decomposed by `ReportRepository`, so no client contract changes; the F007 column-delete guard and the "which reports use this sheet or column" fan-out become declared foreign keys and index scans instead of a JSON scan; every limit and every `field_errors["definition.<path>"]` response in FR-F021-02 through FR-F021-06 is unchanged.
- `report_snapshots(id uuid pk, tenant_id uuid not null, report_id uuid not null references reports(id) on delete cascade, run_id uuid not null, status text not null, scope text not null, row_count int, duration_ms int, computed_at timestamptz, error text, stale bool not null default false, created_at)`; `report_snapshot_sources(snapshot_id uuid not null references report_snapshots(id) on delete cascade, tenant_id uuid not null, sheet_id uuid not null references sheets(id) on delete restrict, sheet_version bigint not null, primary key (snapshot_id, sheet_id))` replaces `source_versions jsonb` — FR-F021-09 computes `stale` by joining these rows against the current `sheets.version`, and the `meta.source_versions` response field is unchanged, assembled from these rows.
- `report_snapshot_rows(snapshot_id uuid not null references report_snapshots(id) on delete cascade, seq int not null, tenant_id uuid not null, row_id uuid not null, cells jsonb not null, calculated jsonb not null, primary key (snapshot_id, seq))`; `cells` and `calculated` stay `jsonb` because they are typed cell values (`{raw, display}` per column ref and per calculated-field label) materialized for one snapshot row, never filtered, joined, or aggregated in SQL — grouping and aggregation are computed at read time over the rows the viewer may see, per FR-F021-11.
- `report_snapshot_row_sources(snapshot_id uuid not null, seq int not null, tenant_id uuid not null, source_id uuid not null references report_sources(id) on delete restrict, source_row_id uuid null, primary key (snapshot_id, seq, source_id), foreign key (snapshot_id, seq) references report_snapshot_rows(snapshot_id, seq) on delete cascade)` replaces `report_snapshot_rows.sources jsonb`: FR-F021-10's per-source permission filtering and F025's drill-through resolve rows through this map, so it is joined data, not a payload. The `sources: {alias: source_row_id}` response shape is unchanged, keyed by the alias on `report_sources`.
- Invariants: unique partial index `reports_tenant_folder_name_idx on (tenant_id, workspace_id, coalesce(folder_id, '00000000-0000-0000-0000-000000000000'), lower(name)) where deleted_at is null`; `report_sources` unique `(report_id, alias)` and `(report_id, position)`; `report_joins`, `report_aggregates`, `report_calculated_fields` unique `(report_id, position)`, the last two also unique `(report_id, lower(label))`; `report_filters` unique `(report_id, node_path)`; `report_group_by` primary key `(report_id, level)` with `level` between 1 and 3; foreign keys to `sheets` and `columns` with `on delete restrict`, to `reports` and `report_sources` with `on delete cascade`; at most one snapshot with `status in ('queued','running')` per report enforced by partial unique index `report_snapshots_active_idx`; `check (aggregate_policy in ('viewer','owner'))`.
- Indexes: `report_sources(sheet_id)` and `report_source_columns(column_id)` for stale and column-delete fan-out, `report_joins(report_id, position)`, `report_filters(column_id)`, `report_aggregates(column_id)`, `reports(refresh_mode, refresh_interval_minutes) where deleted_at is null` for the FR-F021-08 scheduler sweep, `report_snapshots(report_id, computed_at desc) where status = 'succeeded'`, `report_snapshot_sources(sheet_id)`, `report_snapshot_rows(snapshot_id, seq)`, `report_snapshot_row_sources(snapshot_id, source_id, source_row_id)`, `reports(tenant_id, workspace_id, updated_at desc)`.
- Audit events: `report.create`, `report.update`, `report.delete`, `report.restore`, `report.refresh.request`, `report.refresh.complete` with field-level diffs and `run_id`; a definition change diffs the composed `definition` object plus the typed refresh columns, so the diff shape the audit reader consumes is unchanged.
- Retention/deletion: retention keeps the last 3 succeeded snapshots and every failed snapshot for 7 days; soft delete sets `deleted_at`; purge job from F027 removes reports and snapshots past tenant retention; rollback drops the twelve tables `reports`, `report_sources`, `report_source_columns`, `report_joins`, `report_filters`, `report_group_by`, `report_aggregates`, `report_calculated_fields`, `report_snapshots`, `report_snapshot_sources`, `report_snapshot_rows`, `report_snapshot_row_sources`.

### React/TypeScript

- Routes: `/w/:workspaceId/reports/new`, `/w/:workspaceId/reports/:reportId`, `/w/:workspaceId/reports/:reportId/edit` in `apps/web/src/features/reports/`; components `ReportPage`, `ReportViewer`, `ReportTable`, `GroupHeaderRow`, `StaleBanner`, `RestrictedSourcesBar`, `ReportEditor`, `SourcePicker`, `JoinBuilder`, `FilterBuilder`, `GroupingPanel`, `CalculatedFieldEditor`, `RefreshPolicyForm`, `NewReportDialog`.
- State: TanStack Query keys `['report', id]`, `['report-rows', id, snapshotId, cursor]`, `['report-list', workspaceId, filters]`; refresh mutation polls `['report', id]` every 2 s while `latest_snapshot.status` is `queued|running`.
- API client: generated `ReportsApi` with `listReports`, `createReport`, `getReport`, `updateReport`, `deleteReport`, `listReportRows`, `refreshReport`.
- Telemetry: `report_created`, `report_opened`, `report_refresh_requested`, `report_definition_saved` (with `source_count`, `join_count`, `calculated_field_count`), `report_restricted_sources_shown`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F021-01 through FR-F021-15 in `testing/features/F021/requirements/cases.md`
- [ ] Failure/edge-case tests: join cycle, disconnected source, type-mismatched join, operator/type mismatch, formula parse error, refresh while active, definition change marks snapshots stale, interval below 5 minutes
- [ ] Permission-negative and tenant-isolation tests: cross-tenant `not_found`, viewer mutation `denied`, restricted sheet rows dropped, hidden column removed and excluded from aggregates, guest link cannot refresh
- [ ] Rust unit tests: `crates/domain/src/reports/` definition validator, compiler SQL shape, calc evaluator, scope filter, stale computation
- [ ] API contract/integration tests: every route above with success and each error code
- [ ] Database migration/constraint tests: unique name, alias uniqueness, single active snapshot, foreign keys, rollback
- [ ] React component tests: `ReportEditor`, `JoinBuilder`, `FilterBuilder`, `ReportViewer` states
- [ ] Browser E2E tests: build the three-sheet report, refresh, view groups, stale banner, restricted source notice
- [ ] Accessibility tests: axe on editor and viewer, keyboard join/filter building, live region announcements
- [ ] Performance/load tests: 100,000-row rows page p95 under 500 ms, three-sheet refresh under 60 s

### Fast fanout configuration

- Test harness path: `testing/features/F021/`
- Feature flag: `F021_FEATURE`
- Fixture/seed factory: `testing/fixtures/reports.rs` builds tenant A and B, editor, viewer, restricted viewer (no access to "Risks"), sheets "Projects" (50 rows), "Risks" (120 rows, link column `project`), "Budget" (50 rows, hidden column `margin`), and a saved report joining all three
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, timezone fixtures `UTC` and `America/New_York`
- Mock/stub contracts: in-memory outbox recorder; in-memory JetStream stub for `reports.refresh`; real F003 engine with fixture bindings; real F035 parser
- Parallel isolation: one schema per test worker, tenant ID per test, unique worker ID per refresh consumer
- Targeted command: `cargo xtask test-feature F021`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F021/`

## 6. Acceptance criteria

```gherkin
Feature: Cross-source reports

Scenario: Join three sheets and refresh
  Given editor Dana has sheets "Projects", "Risks", and "Budget" in workspace "PMO"
  When she saves report "Portfolio status" joining Risks.project to Projects.id and Budget.project to Projects.id and requests a refresh
  Then the refresh is acknowledged within 2 seconds and a succeeded snapshot records row_count, duration_ms, and source_versions
  And report.created.v1 and report.refreshed.v1 are in the outbox

Scenario: Grouped aggregates exclude hidden values
  Given "Budget.margin" is hidden from viewer Lee and the report groups by Projects.owner with sum(Budget.margin)
  When Lee reads the rows
  Then no cell for Budget.margin is returned, meta.hidden_columns lists it, and the group aggregate for margin is null

Scenario: Restricted sheet rows are dropped
  Given viewer Lee has no read access to sheet "Risks"
  When Lee reads rows of "Portfolio status"
  Then rows contributed by Risks through the inner join are absent and meta.restricted_sources contains the Risks sheet id

Scenario: Viewer cannot mutate or refresh
  Given viewer Lee opens "Portfolio status"
  When Lee sends PATCH or POST refresh
  Then the response is 403 denied and no audit mutation row is written

Scenario: Stale snapshot detected
  Given a succeeded snapshot recorded Projects at version 7
  When a row in Projects is edited making version 8
  Then GET rows returns meta.stale true until the next refresh succeeds
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F008 (cells and cell history tables, bulk row reads), F035 (formula parser and evaluator for calculated fields), F003 (authz engine, field-level ACL, audit writer); decisions sections 2, 3, 4, 7; contracts row F021
- Blocks: F022, F023, F031, F039, F056
- Conflicts with: none (disjoint owned paths)
- External dependencies: NATS JetStream for `reports.refresh`
- Risks and mitigations: join fan-out on non-unique keys can multiply rows, so the compiler caps intermediate results at 1,000,000 rows and fails the run with `error = "join_fanout_exceeded"`; per-viewer aggregation at read time costs CPU, so group results are cached 60 s per `(snapshot_id, scope_key)`; formula budget exhaustion is reported per row as a `#BUDGET` display value rather than failing the snapshot.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F008, F035, and F003 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F021/`
- [ ] Migration file name and owned paths claimed
- [ ] Fixture factory `testing/fixtures/reports.rs` and JetStream stub available in `testing/harness/`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for every mutation and refresh
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F021_FEATURE`, stop the refresh consumer, run down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Users can build reports that join several sheets by stable IDs, filter, group, and add calculated fields, and refresh them into cached snapshots that show stale state and source versions.
- Viewers only see rows and columns they can open in the source sheets; hidden values never enter aggregates unless tenant policy allows.
- Migration adds `reports`, `report_sources`, `report_filters`, `report_snapshots`, and `report_snapshot_rows`; rollback drops them. Feature is off by default behind `F021_FEATURE`.
