---
id: F025
type: feature
status: planned
priority: P1
owner: platform
estimate: 8
target_milestone: M4
parent_epic: E005
depends_on: [F023, F010]
blocks: []
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/report_exports/**, crates/persistence/src/report_exports/**, services/api/src/report_exports/**, services/worker/src/report_exports/**, apps/web/src/features/report-exports/**, services/api/migrations/*_report_exports_*.sql, testing/features/F025/**]
feature_flag: F025_FEATURE
flag_default: off
branch: f025-export-drill-through
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 6, 7, 9
- Capability contract: `docs/capability-contracts.md` row F025
- Product spec: `docs/product-capability-spec.md` section 5.6 REPORT-03, section 5.3 DATA-04, section 6

# F025 — Export/drill-through

## 1. Identity and dates

- Branch: `f025-export-drill-through`
- Capability area: reporting (spec 5.6 REPORT-03 drill-through, sharing, export; low-level bullets: drill-through opens the source row/sheet only if the viewer has access, hidden values are not included in aggregates unless policy allows, export to PDF/PNG/CSV is asynchronous and records who exported what)
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 6, 7, 9; `docs/capability-contracts.md` row F025
- Aggregate: `report-export`
- Module slug: `report-exports`

## 2. Requirement specification

### Problem and user outcome

A dashboard bar says "Dana — 7 risks" and a report group says "Owner: Dana, count 7". The next question is always "which seven?", and the answer today means leaving the dashboard, opening each source sheet, and re-applying the filter by hand. The review then ends with "send me that as a PDF", which today means a screenshot that leaks whatever the sender could see rather than what the recipient may see. Both need the same governed path: a viewer-scoped resolution from an aggregate back to the source rows, and an asynchronous render that reproduces exactly the cells the requester is allowed to read, with a record of who exported what.

As a report viewer, I want to click a KPI, chart point, or grouped row and land on the source records I am allowed to open, and to export a report or dashboard to CSV, XLSX, PDF, or PNG asynchronously with a download that expires, so that reviews answer their own questions and shared files never carry data the requester could not see.

### Functional requirements

- **FR-F025-01:** `GET /api/v1/reports/{id}/drill/{row_id}` resolves one F021 snapshot row to its sources and returns `DrillResult { target: { kind: "row", row_id, snapshot_id }, sources: [{ alias, sheet_id, sheet_name, source_row_id, access: "allowed"|"denied", deep_link, cells: { column_ref: { raw, display } } }], hidden_columns: [], restricted_sources: [], meta: { computed_at, scope: "viewer", correlation_id } }`; a `row_id` absent from the report's latest succeeded snapshot returns `404 not_found`, and `?snapshot_id=` pins an older retained snapshot.
- **FR-F025-02:** The same route accepts an aggregate target `row_id = group:<base64url>` produced by this feature's `DrillKey::encode(widget_id, dimension_values, filters, snapshot_id)`; the response is `{ target: { kind: "group", widget_id, dimensions: [{ field, value }], snapshot_id }, rows: [ { row_id, sources: [...] } ], meta: { total, returned, truncated, next_cursor } }` paging by `?cursor=&limit=` with `limit` 1..200 and `total` capped at 5,000; a key whose `snapshot_id` is no longer retained returns `409 conflict` with `reason: "snapshot_expired"` and the current `snapshot_id`.
- **FR-F025-03:** Drill results are computed under the caller's F021 `ViewerScope`: a source sheet the caller cannot read yields `access: "denied"` with `cells` omitted and the alias listed in `restricted_sources`, columns hidden by F007 visibility or F003 field ACL are removed from `cells` and listed in `hidden_columns`, and a group target returns only contributing rows the caller can see, so `total` for a viewer never exceeds the aggregate the same viewer sees. When the report's F021 `aggregate_policy` is `owner`, the response adds `meta.aggregate_scope: "owner"` and `meta.hidden_row_count` so the UI can state that the aggregate counts rows this viewer cannot open.
- **FR-F025-04:** Every drill call publishes `drill-through.opened.v1` with `{ report_id, snapshot_id, target_kind, widget_id?, source_count, denied_count, returned_row_count, scope_key }` and writes an `audit_events` row `report.drill-through` with the actor, report, target, and denied count; `deep_link` is `/w/{workspace_id}/sheets/{sheet_id}?row={source_row_id}` for allowed sources and `null` for denied ones.
- **FR-F025-05:** `POST /api/v1/reports/{id}/exports` with `{ format: csv|xlsx|pdf, snapshot_id?, columns?, filter?, include_group_headers?, include_aggregates?, timezone, locale?, page?: { size: a4|letter, orientation: portrait|landscape } }` requires the `resource-exporter` role plus `read` on the report and an `Idempotency-Key`, creates a `report_exports` row in `queued` with the caller's `scope_key`, the options written to its typed columns and the selected `columns` written to `report_export_columns` in submission order, returns `202 { export_id, status: "queued", expires_at }` in under 500 ms, and publishes `report-export.requested.v1`; `page` is required for `pdf` and rejected for `csv` and `xlsx` with `400 invalid`, a rule the `page_size` and `page_orientation` format checks also enforce in the schema.
- **FR-F025-06:** `POST /api/v1/dashboards/{id}/exports` with `{ format: pdf|png, widget_ids?, timezone, page?: { size: a4|letter, orientation }, refresh: bool }` renders the F023 dashboard for the caller's `scope_key`, storing the selected `widget_ids` as ordered `report_export_widgets` rows and `refresh` in `refresh_requested`: `refresh: true` first enqueues `POST /api/v1/dashboards/{id}/refresh` and waits up to 120 s for widget cache entries to reach `fresh`, widgets that resolve `denied` render as a "No access" tile carrying only the widget title, and widgets still `computing` after the wait render as "Not available" and set `partial: true` on the finished export.
- **FR-F025-07:** `GET /api/v1/report-exports/{id}` returns `{ export_id, source_kind, source_id, format, status: queued|running|completed|failed|expired, progress_pct, row_count?, page_count?, byte_size?, partial?, requested_by, requested_at, completed_at?, expires_at, error?: { code, message, correlation_id } }` with the error object composed from the `error_code`, `error_message`, and `error_correlation_id` columns; only the requester or a `tenant-admin` may read it, and a foreign-tenant id returns `404 not_found`.
- **FR-F025-08:** `GET /api/v1/report-exports/{id}/download` returns `302` to a signed object-storage URL valid for 15 minutes when `status` is `completed`, `409 conflict` with the current status while `queued` or `running`, `404 not_found` after `expires_at` (7 days after completion) or for a `failed` export, and `403 denied` for anyone but the requester or a `tenant-admin`; every successful redirect writes an `audit_events` row `report-export.download` with actor, export id, format, and byte size.
- **FR-F025-09:** The worker job `report-exports.render` claims a `queued` row through `ReportExportRepository::claim_next_queued`, which sets `running` with `run_id` and `started_at` under the row lock so two workers never claim the same export, rebuilds the requester's `ViewerScope` from the stored `scope_key` inputs, reads the export's ordered `report_export_columns` and `report_export_widgets` rows, streams the render to object storage under `{tenant_id}/report-exports/{export_id}/{slug}.{ext}` with server-side encryption, then calls `complete(export_id, artifact)` to record `storage_key`, `checksum` (SHA-256), `byte_size`, `row_count`, `page_count`, `expires_at`, set `completed`, and publish `report-export.completed.v1` in one `UnitOfWork`; `progress_pct` is updated through `update_progress` at least every 5 s or every 10,000 rows.
- **FR-F025-10:** Renderers: `csv` writes RFC 4180 with a UTF-8 BOM, one header row of visible column labels, values formatted through the F049 formatter in the requested `locale` and `timezone`; `xlsx` writes one sheet with a frozen header row, typed cells for number, date, and boolean columns, and group header rows when `include_group_headers` is set; `pdf` paginates the visible grid with repeated header rows, group headers, optional aggregate rows, and a footer naming the report, the exporter, the snapshot timestamp, and page `n of m`; `png` renders the dashboard at 1440×1024 CSS pixels at device pixel ratio 2.
- **FR-F025-16:** The export centre lists every status the model can hold, including `expired` — the nightly sweep produces it and an export that vanished from the list would look like data loss. An expired row shows when it expired and offers `Re-run`, and its download returns `404 not_found` rather than a broken link.
- **FR-F025-11:** Limits enforced at request and render time: `csv` and `xlsx` at most 250,000 rows, `pdf` at most 20,000 rows or 200 pages, any output at most 200 MB, `columns` at most 200 as a request validation on the submitted list before its rows are written to `report_export_columns`, 20 export requests per actor per hour counted by `ReportExportRepository::count_requests_since` and 3 concurrently `running` per tenant counted by `count_running_for_tenant`; exceeding a row or size cap fails the export with `error_code` `limit_exceeded` and an `error_message` naming the cap, and exceeding a rate or concurrency limit returns `429 rate_limited` with `Retry-After`.
- **FR-F025-12:** A render failure retries 3 times with exponential backoff; the fourth failure sets `failed` through `ReportExportRepository::fail`, which writes `error_code` from the checked list `source_unavailable`, `limit_exceeded`, `render_timeout`, `storage_unavailable`, `internal` plus `error_message` and `error_correlation_id`, publishes `report-export.failed.v1`, and dead-letters the job; a repeated `POST` with the same `Idempotency-Key` returns the existing `export_id` instead of creating a second row, and expired exports are swept nightly to `expired` with the object deleted.
- **FR-F025-13:** The web app adds a `DrillPanel` opened from a report group row, a chart point, or a KPI tile that lists sources with `Open row` links, denied rows as "No access", and a footer stating `total` and `hidden_row_count`; an `ExportDialog` on report and dashboard toolbars choosing format, columns, timezone, and page setup; and an `Export center` at `/exports` listing this actor's exports with status, progress, `Download`, and `Retry`, with a toast linking to the download when an export completes.

### Non-functional requirements

- **NFR-F025-01 Performance:** drill on a row target responds under 400 ms p95 and on a group target under 900 ms p95 over a 100,000-row snapshot; export acknowledgement under 500 ms p95 and status reads under 200 ms p95; a 50,000-row CSV completes in under 20 s and 250,000 rows in under 120 s; a 12-widget dashboard PDF completes in under 45 s p95 excluding an optional refresh wait.
- **NFR-F025-02 Security/privacy:** every drill result and every exported byte is produced under the requester's `scope_key`, never the report owner's, and a `scope_key` mismatch between the request and the claim aborts the render; objects are written under the tenant prefix with server-side encryption, signed URLs live 15 minutes, downloads are restricted to the requester or a `tenant-admin` and audited; cross-tenant, share-link, hidden-column, restricted-sheet, and expired-download negatives are in the harness.
- **NFR-F025-03 Accessibility:** the drill panel, export dialog, and export center pass axe with zero serious or critical violations, the panel is a focus-trapped dialog returning focus to the originating point, export progress is announced through a polite live region, denied rows carry text and a labelled icon rather than color alone, and generated PDFs are tagged with a document title, table headers, and reading order.
- **NFR-F025-04 Reliability/observability:** renders are idempotent by `(tenant_id, requested_by, idempotency_key)`, enforced by that unique constraint through `ReportExportRepository::create_if_absent`, and safe to re-claim after a worker restart because partial objects are written to a temporary key and moved on success; spans carry `tenant_id`, `export_id`, `report_id`, `dashboard_id`, `run_id`, `scope_key`; metrics `report_export_duration_seconds{format}`, `report_export_failures_total{format,reason}`, `report_export_bytes_total{format}`, `drill_through_denied_total`.

### Scope

Included: viewer-scoped drill-through for snapshot rows and aggregate group keys, drill events and audit, report exports in CSV, XLSX, and PDF, dashboard exports in PDF and PNG, the render worker with progress, retries, and dead letters, signed expiring downloads with audit, request and render limits, drill panel, export dialog, and export center.

Excluded: sheet and view exports and the import pipeline (F010), report definitions and snapshots (F021), metric values (F022), dashboards, widgets, and widget cache (F023), chart specs and renderers (F024), scheduled email delivery of exports (F037), tenant-wide compliance export and purge (F027), anonymous published embeds (F059).

## 3. UX specification

- Entry points: report viewer group row `Show rows`, chart point context menu `Drill through`, KPI tile `View records`, report toolbar `Export`, dashboard toolbar `Export`, navigation `Exports` at `/exports`, deep link `/exports/:exportId`.
- Primary flow: Dana opens dashboard "Weekly review", clicks the bar "Dana — 7 risks", the drill panel lists 7 risk rows with their project source and `Open row` links, one row shows "No access" with the note "1 row counted but not visible"; Dana clicks `Export` on the dashboard, picks PDF, A4 landscape, `Refresh first`, and receives a toast "Export ready" 30 s later; the export center shows `Weekly review · PDF · 4 pages · 2.1 MB` with `Download`.
- Loading: drill panel skeleton rows; export dialog submit shows a spinner until `202`; export rows show a determinate progress bar with `progress_pct`.
- Empty: drill with zero visible contributing rows shows "No records you can open"; export center empty shows "No exports yet" with the toolbar hint.
- Error: failed export row shows the `error.code` sentence, `correlation_id`, and `Retry`; `snapshot_expired` in the panel shows "This snapshot has been replaced" with `Reload`.
- Denied: a viewer without `resource-exporter` sees the `Export` button disabled with a tooltip naming the role; a download attempt by another user shows the denied page.
- Success: completion toast with `Download`; download starts and the row records `Last downloaded`.
- Responsive: the drill panel is a right side sheet at 480 px and full-screen under 768 px; the export dialog fits 320 px; the export center table collapses to cards.
- Keyboard: `Enter` on a chart point or group row opens the panel, focus moves to the panel heading and is trapped, `Escape` returns focus to the originating element, `Ctrl+Shift+E` opens the export dialog from report and dashboard toolbars.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062); Lucide icons `SquareArrowOutUpRight`, `Download`, `FileSpreadsheet`, `FileText`, `Image`, `Lock`, `RefreshCw`; tokens from `apps/web/src/design/tokens.css`.

- Design: `design/artboards/Exports.dc.html` on the canvas indexed by `design/canvas.json`. The ticket is the contract and the artboard is the picture; when they disagree the ticket wins.

## 4. Technical specification

### Rust backend

- Domain entities in `crates/domain/src/report_exports/`: `DrillTarget::{Row { row_id, snapshot_id }, Group { widget_id, dimensions: Vec<(FieldRef, CellValue)>, filters: FilterNode, snapshot_id }}`, `DrillKey` (base64url of a canonical JSON body plus a truncated SHA-256 tag), `DrillSource { alias, sheet_id, sheet_name, source_row_id, access: Allowed|Denied, deep_link, cells }`, `DrillResult { target, sources, rows, hidden_columns, restricted_sources, meta }`, `ExportJob { id, tenant_id, source_kind: Report|Dashboard, source_id, snapshot_id, format: Csv|Xlsx|Pdf|Png, options: ExportOptions, scope_key, status: Queued|Running|Completed|Failed|Expired, progress_pct, storage_key, checksum, byte_size, row_count, page_count, partial, requested_by, idempotency_key, run_id, attempts, error: Option<ExportFailure>, started_at, completed_at, expires_at, version }`, `ExportOptions { columns: Vec<ColumnRef>, filter: Option<FilterNode>, include_group_headers, include_aggregates, timezone, locale, page: Option<PageSetup { size, orientation }>, widget_ids: Vec<WidgetId>, refresh }`, `ExportFailure { code: ExportErrorCode, message, correlation_id }`. `ExportOptions` and `ExportFailure` are domain value objects the repository maps onto typed columns and the ordered `report_export_columns` and `report_export_widgets` rows, not stored documents.
- Use cases: `drill_row`, `drill_group`, `encode_drill_key`, `decode_drill_key`, `create_report_export`, `create_dashboard_export`, `get_export`, `sign_download`, `claim_render`, `run_render` (worker), `fail_render`, `expire_exports`.
- Drill resolution `crates/domain/src/report_exports/drill.rs`: reads the F021 snapshot through `read_rows` with the caller's `ViewerScope`, maps `SnapshotRow.sources` aliases to sheet ids through the report definition, fetches the source rows in one batched query per sheet, and marks unreadable sheets `Denied` without querying their rows.
- Renderers `crates/domain/src/report_exports/render/{csv.rs, xlsx.rs, pdf.rs, png.rs}` behind `trait ExportRenderer { fn format(&self) -> ExportFormat; async fn render(&self, ctx: RenderContext, sink: &mut dyn ObjectSink) -> Result<RenderSummary, RenderError>; }`; `csv` and `xlsx` stream 5,000-row pages from F021 `read_rows`; `pdf` and `png` drive the headless Chromium pool in `services/worker/src/report_exports/browser.rs` against an internal print route with a service token bound to `scope_key`.
- API endpoints (`services/api/src/report_exports/`): `POST /api/v1/reports/{id}/exports`, `POST /api/v1/dashboards/{id}/exports`, `GET /api/v1/report-exports/{id}`, `GET /api/v1/report-exports/{id}/download`, `GET /api/v1/reports/{id}/drill/{row_id}`. DTOs `CreateReportExportRequest`, `CreateDashboardExportRequest`, `ExportJobResponse`, `DrillResponse`, `DrillRowsPage`.
- Persistence (`crates/persistence/src/report_exports/`): `ReportExportRepository` owns `report_exports`, `report_export_columns`, and `report_export_widgets`. It implements the shared `Repository` contract (`get`, `list` with cursor pagination, `insert`, `update` under an expected version, `soft_delete`, `restore`, `purge`) and adds the named queries `create_if_absent(tenant_id, requested_by, idempotency_key, export)`, `get_for_actor(export_id, actor)`, `page_for_actor(actor, cursor)`, `claim_next_queued(limit)`, `update_progress(export_id, progress_pct)`, `complete(export_id, artifact)`, `fail(export_id, error)`, `claim_expired(cutoff, limit)`, `count_running_for_tenant(tenant_id)`, and `count_requests_since(actor, cutoff)`; the tenant predicate, soft-delete filter, version check, audit row, and outbox enqueue come from the base contract. `count_running_for_tenant` and `count_requests_since` back FR-F025-11's 3-concurrent-per-tenant and 20-per-hour-per-actor limits, which are unchanged. Creating an export (the `report_exports` row plus its `report_export_columns` and `report_export_widgets` rows plus the `report-export.requested.v1` outbox event) and completing one (the artifact fields plus the `report-export.completed.v1` outbox event) each run in one `UnitOfWork` that owns the transaction. Drill-through reads F021 snapshots through `ReportSnapshotRepository`, F023 widgets and cache through `DashboardWidgetRepository` and `WidgetCacheRepository`, and sheets and rows through the F006/F007 repositories. Object storage stays in the storage adapter. Per decision 2.1 the use cases above depend on these repository traits and contain no SQL: no SQL string, `sqlx::query*` call, or connection exists in `crates/domain/src/report_exports`, `services/api/src/report_exports`, `services/worker/src/report_exports`, or the F025 test lanes.
- Filter operators: `docs/filter-vocabulary.md`, subset all — inherited unchanged from the F021 definition being drilled into or exported.
- Worker `services/worker/src/report_exports/{render_job.rs, browser.rs, expiry_job.rs}`: consumes `report-exports.render`, claims and updates rows only through `ReportExportRepository::claim_next_queued`, `update_progress`, `complete`, `fail`, and `claim_expired`, enforces a 120 s timeout for `csv` and `xlsx` and 180 s for `pdf` and `png`, retries 3 times, dead-letters on the fourth failure, and runs the nightly expiry sweep.
- Events: `report-export.requested.v1`, `report-export.completed.v1` (adds `row_count`, `page_count`, `byte_size`, `duration_ms`, `partial`), `report-export.failed.v1` (adds `error_code`, `attempts`), `drill-through.opened.v1`.
- Authorization: `read` on the report or dashboard for drill; `resource-exporter` plus `read` on the source for both export creators; requester or `tenant-admin` for status and download; share-link actors from F036 may drill but never export; foreign-tenant ids map to `not_found`.
- Validation: `format` allowed per source kind; `page` required for `pdf` and forbidden otherwise; `timezone` a valid IANA name; `columns` a subset of the report's visible columns and at most 200; `widget_ids` a subset of the dashboard's widgets; `limit` 1..200 on group drill; `Idempotency-Key` 16..128 characters.
- Error mapping: `DrillError::UnknownRow → 404 not_found`, `DrillError::SnapshotExpired → 409 conflict`, `DrillError::BadKey → 400 invalid`, `ExportError::UnsupportedFormat → 400 invalid`, `ExportError::RateLimited → 429 rate_limited`, `ExportError::NotReady → 409 conflict`, `ExportError::Expired → 404 not_found`, `ExportError::StorageUnavailable → 503 unavailable`, `AuthzError::Denied → 403 denied`.

### Interface

Exact shapes. Every field gives its JSON name, its type, whether it is required, and the constraint
that makes it invalid. `T?` is nullable; an absent optional field and an explicit `null` mean the
same thing. Ids are UUIDv7 strings, timestamps are RFC 3339 UTC. Unlisted fields are rejected with
`400 invalid`. `Page<T>`, the opaque cursor and `ListQuery` are F028's; the error body and the six
codes are the shared ones; `CellValue` is F007's; `ViewerScope`, `ReportRow` and the report
`column_ref` string are F021's; `dashboard_widgets` and `widget_cache` are F023's; `ActorContext` is
F038's.

**Which filter this feature carries, stated not reconciled.** `ExportOptions.filter` is F021's report
filter tree — F013's `FilterNode` shape with F021's own operator list — and F025 passes it straight
through to the report query without interpreting it. That list already diverges from F013's
`FilterOp`, and F021's Interface section records the divergence deliberately rather than merging the
two. F025 adopts F021's list unchanged and adds nothing: a filter legal on `GET /reports/{id}/rows`
is legal here and no other. This is a **third** shape in the product, and it is worth naming the
other one so nobody assumes they are the same: F010's `export_job_filters` is a flat conjunction of
`ExportFilterClause` rows with its own nine-operator set and no branch node, and that ticket's
Interface section says so explicitly. F010 exports a sheet or a view; F025 exports a report snapshot.
Neither is reconciled here — collapsing the three onto one vocabulary is a change to F013's contract
and belongs in a ticket against F013, not a quiet widening on the export side.

**`DrillTarget`.** `GET /api/v1/reports/{id}/drill/{row_id}` addresses one of two things through the
same path segment. A plain uuid is a snapshot row (FR-F025-01). The literal prefix `group:` followed
by base64url is a **`DrillKey`** (FR-F025-02): the canonical JSON of
`{ widget_id, dimension_values, filters, snapshot_id }` plus a truncated SHA-256 tag. The key is
user-visible, so it is verified and then **re-authorized server side** — a valid tag proves the key
was minted here, never that this caller may read what it names. A bad tag or unparsable body is
`400 invalid`; a `snapshot_id` no longer retained is `409 conflict` with `reason: "snapshot_expired"`
and the current `snapshot_id` in the body.

Query parameters: `snapshot_id` (uuid, optional, pins an older retained snapshot), and for a group
target `cursor` and `limit` (1–200, default 50).

**`DrillResponse`** — row target

| Field | Type | Notes |
|---|---|---|
| `target` | `{ kind: "row", row_id, snapshot_id }` | |
| `sources` | DrillSource[] | one per report source alias contributing to the row |
| `hidden_columns` | string[] | F021 `column_ref` strings removed from every `cells` map for this viewer |
| `restricted_sources` | string[] | aliases whose sheet the viewer cannot read |
| `meta` | `{ computed_at, scope: "viewer", correlation_id, aggregate_scope?, hidden_row_count? }` | `scope` is always `viewer`: an export or a drill is never produced under the report owner's authority. `aggregate_scope` and `hidden_row_count` appear only when the report's F021 `aggregate_policy` is `owner`, and they exist so the UI can say plainly that the aggregate counts rows this viewer cannot open (FR-F025-03) |

**`DrillSource`** `{ alias, sheet_id, sheet_name, source_row_id, access: "allowed" | "denied",
deep_link, cells }` — on `denied` the `cells` key is absent (not an empty object) and `deep_link` is
`null`; on `allowed` `deep_link` is
`/w/{workspace_id}/sheets/{sheet_id}?row={source_row_id}` and `cells` is a map of `column_ref` to
`{ raw, display }`, F007's `CellValue` pair. `source_row_id` is `null` for the unmatched right side
of a `left` join.

**`DrillRowsPage`** — group target: `{ target: { kind: "group", widget_id, dimensions, snapshot_id },
rows, meta }` where `dimensions` is an array of `{ field, value }`, `rows` is an array of
`{ row_id, sources }` using the same `DrillSource` shape, and `meta` is
`{ total, returned, truncated, next_cursor, computed_at, scope, correlation_id, aggregate_scope?,
hidden_row_count? }`. `total` counts only rows this viewer can see and is capped at 5,000, with
`truncated: true` beyond it; that cap is why this route returns its own envelope rather than F028's
`Page<T>`, whose `total` carries no such ceiling.

**`CreateReportExportRequest`** — `POST /api/v1/reports/{id}/exports`

| Field | Type | Required | Constraint |
|---|---|---|---|
| `format` | `"csv" \| "xlsx" \| "pdf"` | yes | `png` is dashboard-only, matching the `source_kind`/`format` checks |
| `snapshot_id` | uuid? | no | a retained snapshot; absent means the latest succeeded one |
| `columns` | string[]? | no | 0–200 F021 `column_ref` strings, distinct, ordered, all visible to the caller; an unreadable column → `400 invalid` with `field_errors.columns`. Absent means every column the caller may read |
| `filter` | FilterNode? | no | F021's tree as above; applied on top of the report's own filters |
| `include_group_headers` | bool | no | default `false` |
| `include_aggregates` | bool | no | default `false`; `true` with no group-by on the report is `400 invalid` |
| `timezone` | string | yes | IANA name; every date and datetime in the file is rendered in it |
| `locale` | string? | no | BCP 47; defaults to the caller's; drives F049 number and date formatting |
| `page` | `{ size: "a4" \| "letter", orientation: "portrait" \| "landscape" }`? | conditional | **required** for `pdf` and **rejected** for `csv` and `xlsx`, both `400 invalid` with `field_errors.page` (FR-F025-05) |

**`CreateDashboardExportRequest`** — `POST /api/v1/dashboards/{id}/exports`

| Field | Type | Required | Constraint |
|---|---|---|---|
| `format` | `"pdf" \| "png"` | yes | `csv` and `xlsx` are report-only |
| `widget_ids` | uuid[]? | no | a subset of the dashboard's live widgets, ordered as they should appear; absent means every widget in grid order; an id of another dashboard → `400 invalid` |
| `timezone` | string | yes | as above |
| `page` | PageSetup? | conditional | required for `pdf`, rejected for `png`, which renders at 1440×1024 CSS px at DPR 2 |
| `refresh` | bool | no | default `false`; `true` enqueues an F023 refresh first and waits up to 120 s (FR-F025-06) |

Both creators require `resource-exporter` plus `read` on the source and an `Idempotency-Key` of
16–128 characters. Both return `202` **`{ export_id, status: "queued", expires_at }`** in under
500 ms. A repeated `Idempotency-Key` with the same body returns the existing `export_id`; with a
different body it is `409 conflict`.

**`ExportJobResponse`** — `GET /api/v1/report-exports/{id}`

| Field | Type | Notes |
|---|---|---|
| `export_id` | uuid | |
| `source_kind` | `"report" \| "dashboard"` | |
| `source_id` | uuid | |
| `format` | `"csv" \| "xlsx" \| "pdf" \| "png"` | |
| `status` | `"queued" \| "running" \| "completed" \| "failed" \| "expired"` | `expired` is a listed status, not a disappearance: the nightly sweep produces it and the export centre shows it with `Re-run` (FR-F025-16) |
| `progress_pct` | integer | 0–100, updated every 5 s or 10,000 rows |
| `row_count` | integer? | on `completed`, for `csv`, `xlsx` and report `pdf` |
| `page_count` | integer? | on `completed`, for `pdf` |
| `byte_size` | integer? | on `completed` |
| `partial` | bool? | `true` when a dashboard export rendered a widget as "Not available" after the refresh wait (FR-F025-06) |
| `requested_by` | uuid | |
| `requested_at` | timestamp | |
| `completed_at` | timestamp? | |
| `expires_at` | timestamp | 7 days after completion |
| `error` | `{ code, message, correlation_id }`? | present only on `failed`; composed from the `error_code`, `error_message` and `error_correlation_id` columns |

`error.code` is exactly `source_unavailable`, `limit_exceeded`, `render_timeout`,
`storage_unavailable`, `internal` — the same closed list as the column check, so a client branches on
it and never on `message`. `storage_key` and `checksum` are never returned: the file is reached only
through the download route.

**Download.** `GET /api/v1/report-exports/{id}/download` returns no body. On `completed` it is `302`
with `Location` set to a signed object-storage URL valid 15 minutes, and the redirect writes the
`report-export.download` audit row.

**Status codes**

| Status | `code` | Produced by |
|---|---|---|
| `202` | — | an export accepted and queued |
| `302` | — | a download of a `completed` export by the requester or a `tenant-admin` |
| `400` | `invalid` | any constraint above — a malformed or tampered drill key, `page` missing on `pdf` or present on `csv`/`xlsx`/`png`, a format illegal for the source kind, 201 columns, an unreadable column or a widget of another dashboard, an invalid IANA `timezone`, an out-of-range `limit` |
| `403` | `denied` | a caller without `resource-exporter` on either export creator; a download by anyone but the requester or a `tenant-admin`; an F036 share-link actor creating an export — such an actor may drill but never export |
| `404` | `not_found` | unknown, foreign-tenant or invisible report, dashboard or export; a `row_id` absent from the snapshot; a download after `expires_at` or of a `failed` export, so an expiry is never distinguishable from an id that never existed |
| `409` | `conflict` | a download while `queued` or `running`, carrying the current `status`; a drill key whose snapshot is no longer retained, carrying `reason: "snapshot_expired"` and the current `snapshot_id`; `Idempotency-Key` replayed with a different body |
| `429` | `rate_limited` | more than 20 export requests per actor per hour or 3 concurrently `running` per tenant; carries `Retry-After` (FR-F025-11) |
| `503` | `unavailable` | object storage or the render queue is unreachable at request time |

A row or size cap breached **during** the render is not an HTTP status at all: the export finishes
`failed` with `error.code = "limit_exceeded"` and a message naming the cap, because by then the
`202` has long been returned.

### Use case signatures

In `crates/domain/src/report_exports/`. Every one takes `ctx: &ActorContext`, takes a `UnitOfWork`
for writes or a repository trait for reads, never a pool or a connection, and returns the shared
`DomainError`.

```rust
fn drill_row(ctx: &ActorContext, snapshots: &dyn ReportSnapshotRepository, rows: &dyn RowRepository, scope: &ViewerScope, report: ReportId, target: RowTarget) -> Result<DrillResult, DomainError>;
fn drill_group(ctx: &ActorContext, snapshots: &dyn ReportSnapshotRepository, rows: &dyn RowRepository, scope: &ViewerScope, report: ReportId, key: DrillKey, page: Cursor) -> Result<DrillRows, DomainError>;
fn encode_drill_key(target: &DrillTarget, secret: &SigningKey) -> DrillKey;
fn decode_drill_key(key: &str, secret: &SigningKey) -> Result<DrillTarget, DomainError>;
fn create_report_export(ctx: &ActorContext, uow: &mut UnitOfWork, report: ReportId, req: CreateReportExport) -> Result<ExportJob, DomainError>;
fn create_dashboard_export(ctx: &ActorContext, uow: &mut UnitOfWork, dashboard: DashboardId, req: CreateDashboardExport) -> Result<ExportJob, DomainError>;
fn get_export(ctx: &ActorContext, repo: &dyn ReportExportRepository, id: ExportId) -> Result<ExportJob, DomainError>;
fn sign_download(ctx: &ActorContext, repo: &dyn ReportExportRepository, store: &dyn ObjectStore, id: ExportId) -> Result<SignedUrl, DomainError>;
fn claim_render(ctx: &ActorContext, uow: &mut UnitOfWork, run_id: RunId) -> Result<Option<ExportJob>, DomainError>;
fn run_render(ctx: &ActorContext, uow: &mut UnitOfWork, renderer: &dyn ExportRenderer, store: &dyn ObjectStore, id: ExportId) -> Result<RenderSummary, DomainError>;
fn fail_render(ctx: &ActorContext, uow: &mut UnitOfWork, id: ExportId, error: ExportFailure) -> Result<ExportJob, DomainError>;
fn expire_exports(ctx: &ActorContext, uow: &mut UnitOfWork, store: &dyn ObjectStore, cutoff: Timestamp, limit: usize) -> Result<usize, DomainError>;
```

`encode_drill_key` and `decode_drill_key` take no `ctx` and no repository: they are pure over the
signing key, which is what keeps authorization out of them — a decoded key is a request, and
`drill_group` re-authorizes it against the caller's scope before touching a row.

**Transaction boundaries.** `create_report_export` and `create_dashboard_export` each take one
`UnitOfWork` covering `create_if_absent` on `(tenant_id, requested_by, idempotency_key)`, the ordered
`report_export_columns` or `report_export_widgets` rows, the audit row and the
`report-export.requested.v1` entry. The invariant is that a `queued` row is never claimable with half
its selection: the worker reads those child rows to decide the header order and the tile order, so an
export whose columns committed separately would render a different file from the one that was
requested. `claim_render` is its own boundary — the status move to `running` with `run_id` and
`started_at` under the row lock — so two workers never claim one export. `run_render` streams to a
temporary object key outside any transaction, then `complete(export_id, artifact)` takes one
`UnitOfWork` for `storage_key`, `checksum`, `byte_size`, `row_count`, `page_count`, `expires_at`, the
`completed` status and the `report-export.completed.v1` entry, after the object has been moved into
place; bytes before the row means a re-claimed job publishes no partial file. `update_progress` is
deliberately outside that boundary, a single-row write per tick, so progress reporting never holds a
transaction open across a 120-second render. `fail_render` and `expire_exports` each take one
boundary over their status move, their event, and — for expiry — the object deletion that precedes
it.

### PostgreSQL/SQLx

- Migration `*_report_exports_*.sql` creates `report_exports(id uuid pk, tenant_id uuid not null, source_kind text not null check (source_kind in ('report','dashboard')), source_id uuid not null, snapshot_id uuid null, format text not null check (format in ('csv','xlsx','pdf','png')), timezone text not null, locale text null, include_group_headers boolean not null default false, include_aggregates boolean not null default false, page_size text null check (page_size in ('a4','letter')), page_orientation text null check (page_orientation in ('portrait','landscape')), refresh_requested boolean not null default false, filter jsonb null, scope_key text not null, status text not null default 'queued' check (status in ('queued','running','completed','failed','expired')), progress_pct smallint not null default 0 check (progress_pct between 0 and 100), storage_key text, checksum text, byte_size bigint, row_count int, page_count int, partial bool not null default false, requested_by uuid not null, idempotency_key text not null, run_id uuid, attempts smallint not null default 0 check (attempts <= 4), error_code text null check (error_code in ('source_unavailable','limit_exceeded','render_timeout','storage_unavailable','internal')), error_message text null, error_correlation_id uuid null, started_at timestamptz, completed_at timestamptz, expires_at timestamptz, version bigint not null default 1, created_at, updated_at)`.
- The request options are typed columns rather than one `jsonb` options blob because FR-F025-05 and FR-F025-06 fix their shape, validate every member, and constrain `page` against `format`: `check ((format = 'pdf') = (page_size is not null))` and `check ((format = 'pdf') = (page_orientation is not null))` make FR-F025-05's "`page` is required for `pdf` and rejected for `csv` and `xlsx`" declarative in the schema; the request validator still returns the same `400 invalid` body with the same `field_errors`, so the response is unchanged and the database is the second line of defence.
- `report_export_columns(export_id uuid not null references report_exports(id) on delete cascade, tenant_id uuid not null, column_ref text not null, position smallint not null, created_by uuid not null, created_at timestamptz not null default now(), primary key (export_id, column_ref))` with `unique (export_id, position)` holds the ordered `columns` selection; FR-F025-11's cap of at most 200 columns stays a request validation because it bounds the submitted list, and the header row and column order in the CSV, XLSX, and PDF renderers are unchanged — renderers read the rows ordered by `position`.
- `report_export_widgets(export_id uuid not null references report_exports(id) on delete cascade, tenant_id uuid not null, widget_id uuid not null references dashboard_widgets(id) on delete restrict, position smallint not null, created_by uuid not null, created_at timestamptz not null default now(), primary key (export_id, widget_id))` with `unique (export_id, position)` holds the dashboard `widget_ids` selection in tile order. Unlike `source_id`, `widget_id` is not polymorphic, so its foreign key to `dashboard_widgets` is declared with `on delete restrict`.
- `filter jsonb null` is kept: it is the same user-authored F021 filter AST this feature passes straight through to the report query, never read by key, filtered, joined, or constrained here.
- The failure detail is typed columns rather than one `jsonb` error blob because FR-F025-12 branches on a fixed `error.code` list: `error_code`, `error_message`, and `error_correlation_id` with `check (status <> 'failed' or error_code is not null)`. FR-F025-07's `error: { code, message, correlation_id }` response object is unchanged, composed by the repository from those three columns.
- Invariants: unique `(tenant_id, requested_by, idempotency_key)`; `check (status <> 'completed' or (storage_key is not null and checksum is not null and expires_at is not null))`; `check (source_kind <> 'dashboard' or format in ('pdf','png'))`; `check (source_kind <> 'report' or format in ('csv','xlsx','pdf'))`; `check (attempts <= 4)`; `check (progress_pct between 0 and 100)`; the two `page_size`/`page_orientation` format checks; the failed-export `error_code` check; `unique (export_id, position)` on both child tables; foreign keys to `reports` and `dashboards` are not declared because `source_id` is polymorphic, so deletion is handled by the expiry sweep, while `report_export_columns` and `report_export_widgets` cascade from their parent export.
- Indexes: `report_exports(tenant_id, requested_by, created_at desc)`, `report_exports(status, created_at) where status in ('queued','running')` for the claim scan, `report_exports(expires_at) where status = 'completed'` for the sweep, `report_exports(tenant_id, error_code) where error_code is not null` for failure reporting, `report_export_columns(tenant_id, export_id, position)`, `report_export_widgets(tenant_id, export_id, position)`, `report_export_widgets(tenant_id, widget_id)`.
- Reads from other features are query-only and go through that feature's repository: `report_snapshot_rows` and `reports` (F021), `dashboard_widgets` and `widget_cache` (F023), `sheets` and `rows` for drill deep links; this feature issues no SQL of its own against another feature's tables.
- Audit events: `report.drill-through`, `report-export.request`, `report-export.download`, `report-export.expire`.
- Retention/deletion: completed exports expire 7 days after completion, the nightly sweep deletes the object and sets `expired` keeping the row 90 days for audit; failed rows kept 30 days; rollback drops `report_export_widgets`, `report_export_columns`, and `report_exports`.

### React/TypeScript

- Components in `apps/web/src/features/report-exports/`: `DrillPanel`, `DrillSourceList`, `DrillDeniedRow`, `DrillFooter`, `ExportDialog`, `ExportFormatPicker`, `ExportColumnPicker`, `PageSetupFields`, `ExportCenterPage`, `ExportRow`, `ExportProgressBar`, `useDrillTarget.ts`, `api.ts`, `routes.ts`.
- Routes `/exports` and `/exports/:exportId`; the drill panel mounts over report and dashboard routes without changing the URL path and records the target in the `drill` query parameter so the panel survives a reload.
- State: TanStack Query keys `['drill', reportId, targetKey, cursor]` (staleTime 30 s), `['exports', filter, cursor]`, `['export', id]` polling every 2 s while `queued` or `running` and stopping at `completed`, `failed`, or `expired`.
- API client: generated `ReportExportsApi` with `drill`, `createReportExport`, `createDashboardExport`, `getExport`, `downloadExport`.
- Telemetry: `drill_opened` (with `target_kind`, `denied_count`), `drill_row_opened`, `export_requested` (with `source_kind`, `format`), `export_completed`, `export_downloaded`, `export_retried`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F025-01 through FR-F025-13 in `testing/features/F025/requirements/cases.md`
- [ ] Failure/edge-case tests: unknown row id, expired snapshot key, tampered drill key tag, 201 columns, PDF over 200 pages, 250,001 rows, render timeout, storage outage mid-stream, worker killed mid-render, download before completion, download after expiry, duplicate idempotency key
- [ ] Permission-negative and tenant-isolation tests: restricted source sheet marked denied, hidden column absent from CSV and PDF bytes, viewer without `resource-exporter` denied, share-link actor may drill but not export, non-requester download denied, foreign-tenant export and drill return `not_found`
- [ ] Rust unit tests: `crates/domain/src/report_exports/` drill key encode/decode and tag check, source alias mapping, CSV escaping, XLSX typing, page break arithmetic, limit checks; `crates/persistence/src/report_exports/` repository tests for `create_if_absent`, ordered column and widget rows, `claim_next_queued`, `complete`, `fail`, and the two limit counters
- [ ] API contract/integration tests: every route above with success and each mapped error code
- [ ] Database migration/constraint tests: idempotency uniqueness, completed-row invariant, format-per-source checks, `page_size`/`page_orientation` required for `pdf` and rejected otherwise, `error_code` required on a `failed` row and restricted to the five codes, `report_export_columns` and `report_export_widgets` position uniqueness and cascade from the parent export, `dashboard_widgets` restrict on a widget still referenced, claim, sweep, and `error_code` index usage, rollback dropping all three tables
- [ ] React component tests: `DrillPanel` allowed, denied, empty, and owner-aggregate states; `ExportDialog` validation; `ExportRow` progress, failure, and retry
- [ ] Browser E2E tests: drill from a chart point to source rows, export a report to CSV and download it, export a dashboard to PDF with refresh, retry a failed export
- [ ] Accessibility tests: axe on panel, dialog, and export center, focus return, progress announcement, tagged PDF structure
- [ ] Performance/load tests: group drill p95 under 900 ms on a 100,000-row snapshot, 250,000-row CSV under 120 s, 12-widget dashboard PDF under 45 s

### Fast fanout configuration

- Test harness path: `testing/features/F025/`
- Feature flag: `F025_FEATURE`
- Fixture/seed factory: `testing/fixtures/report_exports.rs` reuses the F021 and F023 fixtures and adds report "Portfolio status" with a 100,000-row snapshot over sheets "Projects" and "Risks", a 250,000-row generator, dashboard "Weekly review" with 12 widgets including one the viewer cannot read, actors `exporter` (report-viewer plus resource-exporter), `viewer` (no export role), `tenant-admin`, and a share-link guest
- Deterministic test data: fixed clock `2026-09-03T00:00:00Z`, timezone `America/New_York`, locale `en-US`, seed `0x0F25`, fixed export UUIDv7s and idempotency keys
- Mock/stub contracts: in-memory outbox recorder; JetStream stub for `report-exports.render`; MinIO bucket per worker with an injectable failing sink; headless Chromium pool replaced by a deterministic PDF and PNG stub asserting the print route URL and service token scope
- Parallel isolation: one schema and one object-storage prefix per test worker, tenant ID per test
- Targeted command: `cargo xtask test-feature F025`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F025/`

## 6. Acceptance criteria

```gherkin
Feature: Export and drill-through

Scenario: Drill from a chart point to source rows
  Given the bar "Dana" on the Weekly review dashboard counts 7 risks for viewer Dana
  When Dana drills through with the group key for that point
  Then 7 rows are returned with their Projects and Risks sources and Open row links
  And drill-through.opened.v1 records source_count 7 and denied_count 0

Scenario: Drill hides rows the viewer cannot open
  Given viewer Lee cannot read sheet "Risks" and the report aggregate policy is owner
  When Lee drills through the same point
  Then every source for Risks has access denied with no cells and no deep link
  And meta.aggregate_scope is owner and meta.hidden_row_count states how many rows are counted but not visible

Scenario: Report CSV export excludes hidden columns
  Given exporter Dana cannot read the column Budget.margin
  When Dana exports report "Portfolio status" to CSV and downloads it
  Then the file has no Budget.margin header or values, report-export.completed.v1 is published, and an export.download audit event exists

Scenario: Download is refused before completion and after expiry
  Given an export in status running
  When the requester calls download
  Then the response is 409 conflict with status running
  And after completion plus 7 days the same call returns 404 not_found

Scenario: Viewer without the exporter role cannot export
  Given viewer Lee holds report-viewer but not resource-exporter
  When Lee posts an export for the dashboard
  Then the response is 403 denied and no report_exports, report_export_columns, or report_export_widgets row is created
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F023 (dashboards, widgets, `widget_cache`, refresh, and through it F021 `read_rows`, snapshots, and `ViewerScope`), F010 (object storage conventions, signed expiring downloads, export audit pattern); decisions sections 2, 3, 4, 6, 7, 9; contracts row F025
- Blocks: none
- Conflicts with: none (disjoint owned paths; `export_jobs` stays F010's table and `report_exports` is created here)
- External dependencies: S3-compatible object storage (MinIO locally); headless Chromium for PDF and PNG rendering; NATS JetStream for `report-exports.render`
- Risks and mitigations: a browser-rendered dashboard could authenticate as the wrong actor, so the print route accepts only a short-lived service token that carries the requester's `scope_key` and the render aborts on mismatch; a large PDF can exhaust worker memory, so pages are streamed and capped at 200 pages and 200 MB; a re-claimed job could publish a partial object, so bytes are written to a temporary key and moved on success; drill keys are user-visible, so they carry a truncated SHA-256 tag and are re-authorized server side rather than trusted; snapshot retention of 3 in F021 can expire a key mid-review, so `409 snapshot_expired` returns the current snapshot for a one-click reload.
- Open questions: none

## 7.1 Amendments

Every change made to this ticket after it was first accepted, newest first.

| Date | Caused by | What changed | Why |
|---|---|---|---|
| 2026-09-04 | Filter vocabulary unification (F013) | Subset of `docs/filter-vocabulary.md` declared in section 4 and the operator names aligned to it | the drill and export filters are the F021 definition's, which are now the shared vocabulary |

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F023 and F010 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F025/`
- [ ] Migration file name and owned paths claimed
- [ ] Fixture factory `testing/fixtures/report_exports.rs`, per-worker object-storage prefix, and the deterministic PDF/PNG render stub available

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit and outbox events verified for every drill, export request, completion, failure, and download
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F025_FEATURE` (drill entry points and export buttons hidden), stop the render consumer, run down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Report groups, KPI tiles, and chart points now drill through to the source records the viewer is allowed to open, stating plainly when an aggregate counts rows a viewer cannot see.
- Reports export to CSV, XLSX, and PDF and dashboards export to PDF and PNG asynchronously under the requester's own permissions, with progress, a 15-minute signed download that expires after 7 days, and an audit record of every request and download.
- Migration adds `report_exports` with its ordered `report_export_columns` and `report_export_widgets` child tables; rollback drops all three. Feature is off by default behind `F025_FEATURE`.
