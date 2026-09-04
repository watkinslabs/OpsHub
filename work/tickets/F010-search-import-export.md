---
id: F010
type: feature
status: planned
priority: P1
owner: platform
estimate: 8
target_milestone: M1
parent_epic: E002
depends_on: [F008, F004]
blocks: [F025, F027, F052]
conflicts_with: []
parallel_safe: true
owned_paths: [crates/persistence/src/dataio/**, crates/domain/src/dataio/**, services/api/src/dataio/**, services/worker/src/dataio/**, apps/web/src/features/dataio/**, services/api/migrations/*_dataio_*.sql, testing/features/F010/**]
feature_flag: F010_FEATURE
flag_default: off
branch: f010-search-import-export
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 5, 6, 7, 9
- Capability contract: `docs/capability-contracts.md` row F010

# F010 — Search/import/export

## 1. Identity and dates

- Branch: `f010-search-import-export`
- Capability area: core work record engine (spec 5.1 search and import/export bullets; 5.2 DATA-04 and import bullets; 5.6 export attribution; section 6 async job, consistency, and reliability targets)
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 5, 6, 7, 9; `docs/capability-contracts.md` row F010
- Module slug: `dataio`; aggregate: `data-job`

## 2. Requirement specification

### Problem and user outcome

Teams already hold work in spreadsheets and cannot find rows across dozens of sheets once it is in OpsHub. They need one tenant-scoped search box that finds sheets, rows, comment metadata, and attachment metadata they are allowed to see, a CSV/XLSX import that shows what will happen before it writes anything and survives a worker crash, and CSV/XLSX/PDF exports that respect the same permissions as the grid.

As a sheet editor, I want to import a 100,000-row CSV with a preview, a dry run, and a duplicate strategy, then search for any row and export the sheet to XLSX or PDF, so that migration into OpsHub and reporting out of it never lose or leak data.

### Functional requirements

- **FR-F010-01:** `GET /api/v1/search?q=<text>&kind=sheet|row|comment|attachment&workspace_id=&sheet_id=&cursor=&limit=` returns hits ranked by `ts_rank_cd` with `kind`, `entity_id`, `sheet_id`, `workspace_id`, `title`, `snippet` (highlighted with `<mark>`), `updated_at`, and an opaque cursor; `q` is 1–256 chars, `limit` is 1–100 (default 25), and an empty `q` returns `400 invalid` with `field_errors.q`.
- **FR-F010-02:** Search results are tenant-scoped by the gateway context and prefiltered by joining the hit's `search_document_principals` rows against the actor and its groups, then re-checked against the actor's resource ACL per hit before return; a row on a sheet the actor cannot read is omitted, and a foreign-tenant `sheet_id` filter returns an empty page, never `denied`.
- **FR-F010-03:** The indexer consumes `sheet.created.v1`, `sheet.updated.v1`, `sheet.deleted.v1`, `sheet.restored.v1`, `row.created.v1`, `row.updated.v1`, `row.deleted.v1`, `row.restored.v1`, `cell.updated.v1`, `cells.bulk-updated.v1`, `comment.created.v1`, and `file.uploaded.v1`, upserts `search_documents` keyed by `(tenant_id, kind, entity_id)`, ignores events older than the stored `source_version`, and emits `search.indexed.v1` per upsert.
- **FR-F010-04:** Comment and attachment documents index metadata only (comment title/first 200 chars of body, author display name, attachment filename, MIME type, size); file bodies are never indexed, and soft-deleted sources are removed from `search_documents` in the same consumer transaction.
- **FR-F010-05:** `POST /api/v1/imports` with `{ sheet_id, file_id, format: csv|xlsx, has_header: bool }` creates an `import_jobs` row in status `created` for a file up to 50 MB and 100,000 rows uploaded through F017; a larger file or an unreadable format returns `400 invalid` with `field_errors.file_id`.
- **FR-F010-06:** `POST /api/v1/imports/{id}/preview` with `{ mapping?, key_column_id?, duplicate_strategy?: skip|update|append }` parses the file, returns the first 50 rows, detected column types (`text`, `number`, `currency`, `date`, `datetime`, `boolean`, `select`), a proposed mapping to existing or new columns with type coercion rules stored as one `import_column_mappings` row per source column, duplicate matches on `key_column_id`, and moves the job to `previewed`.
- **FR-F010-07:** `POST /api/v1/imports/{id}/commit` with `{ dry_run: true }` validates every row through the F007 validation engine, writes `import_rows` with `status` `valid|invalid` and one `import_row_errors` row per failure, records the counts in the typed `total_rows`, `valid_rows`, `invalid_rows`, and `duplicate_rows` columns of `import_jobs`, sets status `dry_run`, and writes no sheet rows; the report returned by the API is those counts plus the first 100 `import_row_errors` rows in `(row_number, ordinal)` order, so its content is unchanged.
- **FR-F010-08:** `POST /api/v1/imports/{id}/commit` with `{ dry_run: false }` is acknowledged with `202 { job_id, status: committing }` in under 2 s, then the worker writes rows in 1,000-row chunks through the F008 bulk row service with `Idempotency-Key = <import_id>:<chunk_index>`, advances `cursor_chunk_index` and `cursor_row_number` after each chunk, and emits `import.started.v1` at the first chunk and `import.completed.v1` with `report` at the end.
- **FR-F010-09:** A worker killed mid-commit leaves the job in `committing` with a valid cursor; the next worker claiming the job resumes from `cursor_chunk_index` and produces no duplicate rows, verified by `import_rows.target_row_id` being set exactly once per row.
- **FR-F010-10:** `duplicate_strategy` `skip` leaves existing rows untouched and marks incoming rows `skipped`; `update` patches matched rows' mapped cells with `If-Match` on their current version; `append` creates new rows regardless; a job without `key_column_id` accepts only `append`.
- **FR-F010-11:** `POST /api/v1/imports/{id}/cancel` on a `committing` job sets status `cancelled` after the current chunk finishes, keeps already-written rows, records `processed_rows`, and emits `import.failed.v1` with `reason = cancelled`; cancel on a terminal job returns `409 conflict`.
- **FR-F010-12:** `GET /api/v1/imports/{id}` returns `status`, `total_rows`, `processed_rows`, `error_count`, the cursor, the report assembled from the count columns and `import_row_errors`, `version`, and timestamps; a job whose worker fails three times moves to `failed` with the dead-letter reason and emits `import.failed.v1`.
- **FR-F010-13:** `POST /api/v1/exports` with `{ source_kind: sheet|view, source_id, format: csv|xlsx|pdf, filter?, columns? }` creates an `export_jobs` row in `queued` with its `columns` as `export_job_columns` rows and its `filter` as ordered `export_job_filters` rows, is acknowledged with `202 { job_id }` in under 2 s, and the worker writes the file to object storage, records `storage_key`, `checksum`, `row_count`, `requested_by`, and emits `export.completed.v1`.
- **FR-F010-14:** Exports apply the actor's permissions at generation time: hidden or denied columns and rows the actor cannot read are excluded, the PDF renders the visible grid as a paginated table with repeated header rows and a footer naming the sheet, exporter, and timestamp, and every export writes an `audit_events` row `export.download` on each download.
- **FR-F010-15:** `GET /api/v1/exports/{id}/download` returns `302` to a signed object-storage URL valid for 15 minutes when status is `completed`, `409 conflict` while `queued` or `running`, and `410` mapped to `not_found` after `expires_at` (7 days), and only the requester or a `tenant-admin` may download.
- **FR-F010-16:** The web app provides a `Ctrl+K` search palette and `/search` results page, an import wizard with upload, map, preview, dry run, and commit steps at `/w/:workspaceId/sheets/:sheetId/import`, a live import status panel, and an export dialog with a status toast that links to the download; viewers see search and export but the import entry point is hidden and the import routes return `denied`.

### Non-functional requirements

- **NFR-F010-01 Performance:** search p95 under 500 ms on 1,000,000 indexed documents per tenant; index lag from outbox event to searchable document under 5 s p95; import of 100,000 rows completes in under 10 minutes; CSV export of 100,000 rows completes in under 60 s; job acknowledgement under 2 s (spec section 6).
- **NFR-F010-02 Security/privacy:** every search, import, and export query carries the `tenant_id` predicate; export files are stored under `tenant_id/exports/<job_id>` with server-side encryption and expiring signed URLs; import files are scanned by F017 before parsing; search never returns file bodies or another tenant's documents.
- **NFR-F010-03 Accessibility:** the search palette uses the combobox pattern with announced result counts; the import wizard exposes step progress with `aria-current`, table previews with proper headers, and progress announcements through a polite live region; no serious axe violations.
- **NFR-F010-04 Reliability/observability:** jobs are idempotent per chunk, retried three times with exponential backoff, then dead-lettered with `job_runs` history; metrics `search_query_duration_ms`, `search_index_lag_ms`, `import_rows_processed_total`, `import_jobs_failed_total`, `export_duration_ms`; spans carry `tenant_id`, `job_id`, `sheet_id`, `correlation_id`.

### Scope

Included: search index and consumer, search route and UI, import job lifecycle with preview, dry run, duplicate strategy, chunked resumable commit, cancel, status; export jobs for sheet or view in CSV, XLSX, PDF with permission filtering, signed download, expiry; audit and outbox events; worker handlers.

Excluded: report and dashboard exports (F025), tenant-wide compliance exports and purge (F027), scheduled file ingestion (F052), file upload and virus scan (F017), comment bodies beyond metadata (F016), search over documents (F045), saved view definitions used as export sources (F013 owns the view; F010 only reads its filter).

## 3. UX specification

- Entry points: global header search field and `Ctrl+K` palette; sheet menu `Import from file` and `Export`; folder tree item `Imports` showing recent jobs; route `/search?q=` for full results.
- Primary flow: press `Ctrl+K`, type `kickoff`, see grouped results (Sheets, Rows, Comments, Attachments) with highlighted snippets, press `Enter` to open the row in its grid. From the sheet menu choose `Import from file`, drop `plan.csv`, see detected columns and types, adjust mapping, pick key column `Task ID` and strategy `update`, run `Dry run`, read the report (`980 valid, 20 invalid`), click `Commit`, watch the progress bar, land back on the grid with a toast `1,000 rows imported`. Choose `Export`, pick `PDF`, receive a toast with `Download` when ready.
- Loading: skeleton result rows; wizard step spinner; progress bar with `processed_rows/total_rows`. Empty: `No results for "…"` with filter hints; import preview of a file with zero data rows shows an explanation. Error: banner with `correlation_id` and retry; invalid rows listed with row number, column, and code. Success: toasts for import completed and export ready. Stale/conflict: `update` strategy rows that changed during import are reported as conflicts in the report. Offline: import and export actions disabled with the offline badge; search shows cached recent results.
- Permission-denied: import entry hidden for viewers and commenters; export dialog visible to viewers but only for columns they can read; download by a non-requester shows `denied` explanation.
- Responsive: palette becomes a full-screen sheet under 640 px; wizard steps stack vertically with a sticky action bar; preview table scrolls horizontally in its own container.
- Keyboard: `Ctrl+K` opens, arrows move, `Enter` opens, `Escape` closes; wizard steps are reachable with `Tab`, `Enter` advances, `Shift+Enter` goes back; mapping selects are native comboboxes; motion respects `prefers-reduced-motion`.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062); Lucide icons `Search`, `Upload`, `Download`, `FileSpreadsheet`, `FileText`, `AlertCircle`, `CheckCircle2`; spacing and color from `apps/web/src/design/tokens.css`.

- Design: `design/artboards/Search.dc.html` on the canvas indexed by `design/canvas.json`. The ticket is the contract and the artboard is the picture; when they disagree the ticket wins.

## 4. Technical specification

Canonical contract: `docs/capability-contracts.md` row F010.

### Rust backend

- Domain entities in `crates/domain/src/dataio/`: `SearchDocument { tenant_id, kind: DocKind, entity_id, sheet_id, workspace_id, title, body: String, principals: Vec<DocumentPrincipal { principal_kind, principal_id, effect }>, source_version, indexed_at }`, `ImportJob { id, tenant_id, sheet_id, file_id, format: ImportFormat, status: ImportStatus, mapping: ImportMapping, duplicate_strategy: DuplicateStrategy, key_column_id, dry_run, total_rows, processed_rows, error_count, cursor: Option<ChunkCursor>, report: Option<ImportReport>, version, audit }`, `ImportRow { import_id, row_number, raw, normalized, status: ImportRowStatus, errors: Vec<RowError>, target_row_id }` with the errors held as `import_row_errors` rows, `ExportJob { id, tenant_id, source_kind: ExportSource, source_id, format: ExportFormat, filter, columns, status: ExportStatus, storage_key, checksum, row_count, requested_by, expires_at, version }`.
- Modules: `search/{indexer.rs, query.rs, acl_filter.rs}`, `import/{parser_csv.rs, parser_xlsx.rs, type_detect.rs, mapping.rs, dedupe.rs, service.rs, chunker.rs}`, `export/{service.rs, csv_writer.rs, xlsx_writer.rs, pdf_writer.rs, permission_filter.rs}`, `errors.rs`; worker handlers in `services/worker/src/dataio/{index_consumer.rs, import_job.rs, export_job.rs}`.
- Data access (decision 2.1): `SearchDocumentRepository` (`search_documents`, `search_document_principals`), `ImportJobRepository` (`import_jobs`, `import_column_mappings`), `ImportRowRepository` (`import_rows`, `import_row_errors`), and `ExportJobRepository` (`export_jobs`, `export_job_columns`, `export_job_filters`) in `crates/persistence/src/dataio/`; sheet rows and cells are written only through the F008 bulk row service over the F006 repositories, so this feature adds no second writer to them. The use cases below, the worker handlers in `services/worker/src/dataio/`, and `search/query.rs` depend on those repository traits and the shared `UnitOfWork`; no SQL, `tsquery` string, or pool lives in `crates/domain/src/dataio/`, `services/api/src/dataio/`, or the worker — the ranked search, the ACL prefilter join, the resume claim, and the chunk advance are named repository queries (`search_ranked`, `claim_resumable_job`, `advance_cursor`, `upsert_document`).
- Filter operators: `docs/filter-vocabulary.md`, subset `eq`, `ne`, `lt`, `lte`, `gt`, `gte`, `contains`, `is_empty`, `is_not_empty` — `export_job_filters` is a flat conjunction, one row per predicate ANDed together, not F013's nested AST. An export **of a saved view** carries no filter of its own and inherits the view's, which is the full vocabulary; only an ad-hoc export uses this narrower flat form. The narrowing is deliberate: an export runs unattended, so it takes no `is_me`, and a flat list keeps the audit trail of what was exported readable as rows.
- Use cases: `search`, `create_import`, `preview_import`, `commit_import` (dry run and real), `resume_import`, `cancel_import`, `get_import`, `create_export`, `run_export`, `get_export`, `sign_download`, `index_event`.
- API endpoints (`services/api/src/dataio/`): `GET /api/v1/search`, `POST /api/v1/imports`, `GET /api/v1/imports/{id}`, `POST /api/v1/imports/{id}/preview`, `POST /api/v1/imports/{id}/commit`, `POST /api/v1/imports/{id}/cancel`, `POST /api/v1/exports`, `GET /api/v1/exports/{id}`, `GET /api/v1/exports/{id}/download`. DTOs `SearchQuery`, `SearchResponse { hits, next_cursor }`, `CreateImportRequest`, `PreviewImportRequest`, `PreviewImportResponse { sample_rows, detected_types, proposed_mapping, duplicates }`, `CommitImportRequest { dry_run }`, `ImportJobResponse`, `CreateExportRequest`, `ExportJobResponse`.
- Events: `search.indexed.v1` (aggregate `entity_id`, `kind`), `import.started.v1`, `import.completed.v1` (`report`), `import.failed.v1` (`reason: cancelled|dead_letter|invalid_file`), `export.completed.v1` (`format`, `row_count`); all through the outbox with the contract envelope.
- Authorization: `sheet-editor` on the target sheet for imports; `sheet-viewer` for search and exports of that sheet; download restricted to `requested_by` or `tenant-admin`; foreign-tenant IDs map to `not_found`.
- Validation: `q` 1–256 chars, `limit` 1–100, file ≤ 50 MB and ≤ 100,000 rows, mapping rows must target column IDs of the sheet or a new column of a named type, one row per source column, `key_column_id` required for `skip|update`, `export_job_columns` a subset of readable columns.
- Error mapping: `DataIoError::InvalidFile | InvalidMapping | EmptyQuery → 400 invalid`, `JobNotResumable | DownloadNotReady | CancelTerminal → 409 conflict`, `Expired | NotFound → 404 not_found`, `AuthzError::Denied → 403 denied`, `QuotaExceeded → 429 rate_limited`.

### Interface

Exact shapes. Every field lists its JSON name, type, whether it is required, and the constraint that
makes it invalid. `T?` is nullable; a missing optional field and an explicit `null` mean the same
thing. Ids are UUIDv7 strings, timestamps are RFC 3339 UTC, `version` increments by one per write.
Unlisted fields are rejected with `400 invalid`. `Page<T>` and its opaque cursor are F028's; the
error envelope and the six codes are the shared ones; `CellValue` is F007's.

**`SearchQuery`** — `GET /api/v1/search`, query string only, no body.

| Field | Type | Required | Constraint |
|---|---|---|---|
| `q` | string | yes | 1–256 chars after trim; empty or whitespace-only → `400 invalid` with `field_errors.q` |
| `kind` | `"sheet" \| "row" \| "comment" \| "attachment"` | no | repeatable; absent means all four |
| `workspace_id` | uuid? | no | narrows to one workspace; a foreign-tenant id yields an empty page, never `denied` |
| `sheet_id` | uuid? | no | narrows to one sheet; same rule for a foreign or unreadable id |
| `cursor` | string? | no | opaque, from a prior `next_cursor`; a cursor minted for a different `q` or filter set → `400 invalid` |
| `limit` | integer? | no | 1–100, default 25 |

**`SearchHit`**

| Field | Type | Notes |
|---|---|---|
| `kind` | `"sheet" \| "row" \| "comment" \| "attachment"` | |
| `entity_id` | uuid | the sheet, row, comment or file id; the client resolves the route from `kind` |
| `sheet_id` | uuid? | null for a `sheet` hit; the owning sheet otherwise |
| `workspace_id` | uuid | |
| `title` | string | the indexed display title: sheet name, primary-cell value, comment author and first line, or file name |
| `snippet` | string | see below |
| `score` | number | the `ts_rank_cd` value the ordering used, so a client can group by relevance band |
| `updated_at` | timestamp | the source's `updated_at`, not `indexed_at` |

`snippet` is produced by PostgreSQL `ts_headline` over the document's indexed `body` against the same
`tsquery` that matched, with `StartSel=<mark>`, `StopSel=</mark>`, `MaxWords=35`, `MinWords=15` and
`MaxFragments=1`. It therefore contains exactly those two tags and no other markup, and every other
character is HTML-escaped before the tags are inserted, so a client may render it as HTML without
sanitising user text itself. A hit whose `body` produced no fragment (a bare title match) returns the
first 140 characters of `title` with the matched terms wrapped by the same tags. For `comment` and
`attachment` kinds the snippet is drawn from metadata only — comment first 200 characters, file name,
MIME type and size — because no file body is ever indexed (FR-F010-04).

**`SearchResponse`**: `{ hits: SearchHit[], next_cursor: string? }`. It carries no `total`: counting
matches would require running the permission filter over the whole result set.

**Permission filtering happens before paging, never after.** The ranked query joins
`search_document_principals` against the actor and its group ids inside the same statement that
orders and limits, and each surviving hit is then re-checked against the authoritative resource ACL
before it is added to the page; a hit dropped by that re-check is backfilled from the same statement
so the page is full at `limit` whenever more visible matches exist. A client therefore never sees a
short page that secretly means "some results were hidden", and `next_cursor` is null only when no
further visible match exists. A row on a sheet the actor cannot read is simply absent (FR-F010-02).

**`CreateImportRequest`** — `POST /api/v1/imports`

| Field | Type | Required | Constraint |
|---|---|---|---|
| `sheet_id` | uuid | yes | caller holds `sheet-editor`, else `403 denied`; unreadable → `404 not_found` |
| `file_id` | uuid | yes | a scanned-clean F017 file in this tenant, ≤ 50 MB and ≤ 100,000 data rows; larger, unreadable or an unsupported encoding → `400 invalid` with `field_errors.file_id` |
| `format` | `"csv" \| "xlsx"` | yes | must match the file's detected format |
| `has_header` | bool | yes | when true, row 1 supplies `source_header` values |

**`ColumnMapping`** — one entry per source column, the wire form of an `import_column_mappings` row.

| Field | Type | Required | Constraint |
|---|---|---|---|
| `source_index` | integer | yes | 0-based position in the file, distinct, one entry per source column |
| `source_header` | string? | no | echoed from the header row; ignored on write |
| `target_column_id` | uuid? | conditional | a live column of the sheet; exactly one of this and `new_column_type` must be present |
| `new_column_type` | `"text" \| "number" \| "currency" \| "date" \| "datetime" \| "boolean" \| "select"` | conditional | creates a column on commit |
| `coercion` | string? | no | the named coercion rule applied before validation (for example a date input format); unknown name → `400 invalid` |
| `skip` | bool | no | `true` drops the source column; `target_column_id` and `new_column_type` must then be absent |

**`PreviewImportRequest`** — `POST /api/v1/imports/{id}/preview`

| Field | Type | Required | Constraint |
|---|---|---|---|
| `mapping` | ColumnMapping[]? | no | absent means accept the detected proposal; when present it replaces the mapping whole |
| `key_column_id` | uuid? | no | a mapped target column; required when `duplicate_strategy` is `skip` or `update`, else `400 invalid` with `field_errors.key_column_id` |
| `duplicate_strategy` | `"skip" \| "update" \| "append"` | no | defaults `append` |

**`PreviewImportResponse`**

| Field | Type | Notes |
|---|---|---|
| `sample_rows` | array of `{ row_number, values: string[] }` | first 50 data rows as parsed, before coercion |
| `detected_types` | array of `{ source_index, type, confidence }` | `type` from the same seven-member set as `new_column_type` |
| `proposed_mapping` | ColumnMapping[] | one entry per source column, echoed back so the client edits and re-posts it |
| `duplicates` | array of `{ row_number, existing_row_id }` | empty when `key_column_id` is absent |
| `status` | ImportStatus | `"previewed"` on success |

**`CommitImportRequest`**: `{ dry_run: bool }` — required, no other member. `true` validates and
reports; `false` is acknowledged `202` with `{ job_id, status: "committing" }` in under 2 s.

**`ImportReport`** — the same object on `GET /api/v1/imports/{id}` and in `import.completed.v1`,
assembled from the count columns and `import_row_errors`, never stored as a blob.

| Field | Type | Notes |
|---|---|---|
| `total_rows` / `valid_rows` / `invalid_rows` / `duplicate_rows` / `processed_rows` | integer | typed `import_jobs` columns |
| `errors` | array of `{ row_number, ordinal, column_id?, code, message }` | the first 100 `import_row_errors` rows in `(row_number, ordinal)` order |
| `errors_truncated` | bool | true when more than 100 error rows exist |

**`ImportJobResponse`**: `{ id, sheet_id, file_id, format, status, duplicate_strategy, key_column_id?, mapping: ColumnMapping[], report: ImportReport, cursor: { chunk_index, row_number }?, version, created_at, created_by, updated_at, updated_by }`. `cursor` is present only while `status` is
`"committing"` or `"paused"`, and `status` is one of `created`, `previewed`, `dry_run`, `committing`,
`paused`, `completed`, `failed`, `cancelled`.

**`ExportFilterClause`** — one `export_job_filters` row. The export filter is a flat conjunction, not
F013's `FilterNode`: every clause is ANDed in `ordinal` order, and the table carries no branch node.
An export whose `source_kind` is `view` instead inherits that view's full `FilterNode` from F013
server-side, and may add these clauses on top of it.

| Field | Type | Required | Constraint |
|---|---|---|---|
| `column_id` | uuid | yes | a live column of the source the actor may read; an unreadable column → `400 invalid` |
| `operator` | `"eq" \| "ne" \| "lt" \| "lte" \| "gt" \| "gte" \| "contains" \| "is_empty" \| "is_not_empty"` | yes | closed set, matching the table's `check`; `contains` is text-only, the four ordering operators are numeric, currency, duration, date and datetime only |
| `value` | scalar? | conditional | required for every operator but `is_empty` and `is_not_empty`; stored in exactly one of `value_text`, `value_number`, `value_datetime` chosen by the column's type, so a value whose JSON type does not match the column is `400 invalid` |

**`CreateExportRequest`** — `POST /api/v1/exports`

| Field | Type | Required | Constraint |
|---|---|---|---|
| `source_kind` | `"sheet" \| "view"` | yes | closed set |
| `source_id` | uuid | yes | the sheet or view id; caller holds `sheet-viewer` on the sheet, else `404 not_found` |
| `format` | `"csv" \| "xlsx" \| "pdf"` | yes | closed set |
| `filter` | ExportFilterClause[]? | no | 0–20 clauses, `ordinal` is array order |
| `columns` | uuid[]? | no | ordered, distinct, all readable columns of the source; absent means every column the actor may read; naming an unreadable column → `400 invalid` with `field_errors.columns` |

**`ExportJobResponse`**: `{ id, source_kind, source_id, format, status: "queued" \| "running" \| "completed" \| "failed", row_count?, checksum?, error?, requested_by, expires_at?, version, created_at, updated_at }`. `row_count` and `checksum` appear only when `status` is `"completed"`;
`storage_key` is internal and never returned — the file is reached only through the download route.
`GET /api/v1/exports/{id}/download` returns no body: `302` with a `Location` header holding a signed
object-storage URL valid for 15 minutes.

**List routes.** This feature exposes no list of jobs; `GET /api/v1/imports/{id}` and
`GET /api/v1/exports/{id}` are single reads polled by the client, and `GET /api/v1/search` is the
only paged route, returning `SearchResponse` rather than a `Page<T>` because it carries no total.

**Status codes**

| Code | Produced by |
|---|---|
| `200` | reads, preview, dry-run commit; `201` on job creation; `202` on a real commit and on export creation; `302` on a ready download |
| `400 invalid` | empty or over-long `q`, out-of-range `limit`, a cursor from a different query, oversize or unreadable file, a mapping with neither target nor new type, a duplicate `source_index`, `skip`/`update` without `key_column_id`, an unknown coercion, an operator not legal for the column type, a value whose JSON type does not match the column, an unreadable column in `columns` |
| `403 denied` | a `sheet-viewer` creating an import; a download requested by neither `requested_by` nor a `tenant-admin` |
| `404 not_found` | unknown, foreign-tenant or invisible sheet, view, file or job; a download after `expires_at` (the 7-day expiry maps `410` onto `not_found`) |
| `409 conflict` | download while `queued` or `running`; cancel of a job already in a terminal status; commit of a job not in `previewed` or `dry_run`; a replayed `Idempotency-Key` with a different body |
| `429 rate_limited` | tenant job quota exceeded (`DataIoError::QuotaExceeded`) |
| `502` | never returned; object-storage failure surfaces as `503 unavailable` |

### Use case signatures

In `crates/domain/src/dataio/`. Each takes `ctx` carrying tenant, actor and correlation id, takes a
`UnitOfWork` for writes or a repository for reads — never a pool or a connection — and returns the
shared `DomainError`. The worker handlers in `services/worker/src/dataio/` call these same functions.

```rust
fn search(ctx: &Ctx, repo: &SearchDocumentRepository, acl: &AclReader, q: SearchQuery) -> Result<SearchResponse, DomainError>;
fn create_import(ctx: &Ctx, uow: &mut UnitOfWork, req: CreateImport) -> Result<ImportJob, DomainError>;
fn preview_import(ctx: &Ctx, uow: &mut UnitOfWork, id: ImportId, req: PreviewImport) -> Result<ImportPreview, DomainError>;
fn commit_import(ctx: &Ctx, uow: &mut UnitOfWork, id: ImportId, dry_run: bool) -> Result<ImportJob, DomainError>;
fn resume_import(ctx: &Ctx, uow: &mut UnitOfWork, id: ImportId) -> Result<ImportJob, DomainError>;
fn cancel_import(ctx: &Ctx, uow: &mut UnitOfWork, id: ImportId, expected: Version) -> Result<ImportJob, DomainError>;
fn get_import(ctx: &Ctx, jobs: &ImportJobRepository, rows: &ImportRowRepository, id: ImportId) -> Result<ImportJob, DomainError>;
fn create_export(ctx: &Ctx, uow: &mut UnitOfWork, req: CreateExport) -> Result<ExportJob, DomainError>;
fn run_export(ctx: &Ctx, uow: &mut UnitOfWork, store: &dyn ObjectStore, id: ExportId) -> Result<ExportJob, DomainError>;
fn get_export(ctx: &Ctx, repo: &ExportJobRepository, id: ExportId) -> Result<ExportJob, DomainError>;
fn sign_download(ctx: &Ctx, repo: &ExportJobRepository, store: &dyn ObjectStore, id: ExportId) -> Result<SignedUrl, DomainError>;
fn index_event(ctx: &Ctx, uow: &mut UnitOfWork, event: &ChangeEvent) -> Result<(), DomainError>;
```

**Transaction boundaries.** `index_event` runs one `UnitOfWork` per consumed event covering the
`search_documents` upsert and the full replace of that document's `search_document_principals` rows,
so the ACL snapshot the search prefilter joins against can never describe a different version of the
document than the one it sits beside; the upsert's `where source_version < excluded.source_version`
guard makes a replayed or out-of-order event a no-op. A soft-delete event removes the document and
its principal rows in that same boundary (FR-F010-04). `commit_import` with `dry_run: true` writes
all `import_rows` and `import_row_errors` plus the four count columns in one `UnitOfWork` and touches
no sheet row. The real commit takes one `UnitOfWork` **per 1,000-row chunk**, not one for the job:
the chunk's F008 bulk row write, the `import_rows.target_row_id` stamps and the
`cursor_chunk_index`/`cursor_row_number` advance commit together, which is exactly what makes
FR-F010-09 hold — a worker killed mid-commit leaves a cursor that already accounts for every row
written, so the next claimant resumes without duplicating any. `cancel_import` finishes the current
chunk's boundary before flipping the status, so no partially-written chunk is ever left behind.
`create_export` writes the `export_jobs` row with its `export_job_columns` and `export_job_filters`
children in one `UnitOfWork`, so a queued job is never picked up with half its column list.

### PostgreSQL/SQLx

- Migration `*_dataio_*.sql` creates `search_documents(tenant_id uuid not null, kind text not null check (kind in ('sheet','row','comment','attachment')), entity_id uuid not null, sheet_id uuid, workspace_id uuid, title text not null, body tsvector not null, body_simple tsvector not null, source_version bigint not null, indexed_at timestamptz not null, primary key (tenant_id, kind, entity_id))`, `search_document_principals(tenant_id uuid not null, kind text not null, entity_id uuid not null, principal_kind text not null check (principal_kind in ('user','group')), principal_id uuid not null, effect text not null check (effect in ('allow','deny')), primary key (tenant_id, kind, entity_id, principal_kind, principal_id), foreign key (tenant_id, kind, entity_id) references search_documents(tenant_id, kind, entity_id) on delete cascade)`, `import_jobs(id uuid pk, tenant_id, sheet_id, file_id, format text, status text check (status in ('created','previewed','dry_run','committing','paused','completed','failed','cancelled')), duplicate_strategy text check (duplicate_strategy in ('skip','update','append')), key_column_id uuid, dry_run bool, total_rows int, processed_rows int default 0, error_count int default 0, valid_rows int default 0, invalid_rows int default 0, duplicate_rows int default 0, cursor_chunk_index int, cursor_row_number int, version bigint default 1, audit fields)`, `import_column_mappings(import_id uuid not null references import_jobs(id) on delete cascade, source_index smallint not null, source_header text, target_column_id uuid, new_column_type text check (new_column_type in ('text','number','currency','date','datetime','boolean','select')), coercion text, primary key (import_id, source_index), check (target_column_id is not null or new_column_type is not null))`, `import_rows(import_id uuid, row_number int, raw jsonb, normalized jsonb, status text check (status in ('pending','valid','invalid','skipped','committed')), target_row_id uuid, primary key (import_id, row_number))`, `import_row_errors(import_id uuid not null, row_number int not null, ordinal smallint not null, column_id uuid, code text not null, message text not null, primary key (import_id, row_number, ordinal), foreign key (import_id, row_number) references import_rows(import_id, row_number) on delete cascade)`, `export_jobs(id uuid pk, tenant_id, source_kind text, source_id uuid, format text check (format in ('csv','xlsx','pdf')), status text check (status in ('queued','running','completed','failed')), storage_key text, checksum text, row_count int, requested_by uuid, expires_at timestamptz, error text, version bigint default 1, audit fields)`, `export_job_columns(export_job_id uuid not null references export_jobs(id) on delete cascade, column_id uuid not null, position smallint not null, primary key (export_job_id, column_id), unique (export_job_id, position))`, `export_job_filters(export_job_id uuid not null references export_jobs(id) on delete cascade, ordinal smallint not null, column_id uuid not null, operator text not null check (operator in ('eq','ne','lt','lte','gt','gte','contains','is_empty','is_not_empty')), value_text text, value_number numeric, value_datetime timestamptz, primary key (export_job_id, ordinal))`.
- Four `jsonb` columns became tables because the product queries what was inside them: the ACL snapshot is joined against the actor on every search (`search_document_principals`, a derived cache the indexer rebuilds in the same upsert that writes the document and the only query it serves is the search prefilter), the import mapping is read and edited per source column (`import_column_mappings`), row errors are counted, paged, and shown per cell (`import_row_errors`), and the export column list and filter are ordered sets naming columns (`export_job_columns`, `export_job_filters`). The `report` blob is gone: its counts are the typed `valid_rows`, `invalid_rows`, and `duplicate_rows` columns and its error list is the first 100 `import_row_errors` rows, so the API response keeps the same fields with one source of truth. The resume cursor is two typed integer columns instead of a blob. `import_rows.raw` and `normalized` stay `jsonb`: each is one staged source record whose shape comes from the user's file, moved whole through the parser and the validator, and the product only ever filters staging by `status`, `row_number`, and `target_row_id` (decision 2).
- Invariants: `import_rows.target_row_id` unique per `import_id` where not null; `import_jobs.cursor_chunk_index` non-null while `committing`; `export_jobs.storage_key` non-null when `completed`; `source_version` monotonic per document enforced by the consumer's `where source_version < excluded.source_version` upsert.
- Indexes: GIN `search_documents_body_idx on (body)` and `search_documents_body_simple_idx on (body_simple)`, `search_documents(tenant_id, workspace_id, kind)`, `search_document_principals(tenant_id, principal_kind, principal_id)` for the ACL prefilter, `import_jobs(tenant_id, sheet_id, created_at desc)`, `import_rows(import_id, status)`, `import_row_errors(import_id, row_number)` for the report page and `import_row_errors(import_id, code)` for error counts, `export_jobs(tenant_id, requested_by, created_at desc)`, `export_jobs(expires_at) where status = 'completed'`.
- Audit events: `import.create`, `import.preview`, `import.dry_run`, `import.commit`, `import.cancel`, `export.request`, `export.download` with actor, job ID, and row counts.
- Retention/deletion: `search_documents` rows are deleted by the consumer on soft delete and re-created on restore; `import_rows` are purged 30 days after job completion; export files and rows expire after 7 days by a worker sweep, taking their column, filter, mapping, error, and principal rows with them by cascade; rollback drops the nine tables.

### React/TypeScript

- Routes: `/search`, `/w/:workspaceId/sheets/:sheetId/import` in `apps/web/src/features/dataio/`; components `SearchCommandPalette`, `SearchResultsPage`, `SearchResultGroup`, `ImportWizard`, `ImportUploadStep`, `ImportMappingStep`, `ImportPreviewTable`, `ImportReportPanel`, `ImportStatusPanel`, `ExportDialog`, `ExportStatusToast`.
- State: TanStack Query keys `['search', q, filters, cursor]`, `['import', id]` (polls every 2 s while `committing`), `['import-preview', id]`, `['export', id]` (polls every 2 s while `queued|running`); mutations invalidate `['grid-rows', sheetId]` after `import.completed`.
- API client: generated `DataIoApi` with `search`, `createImport`, `previewImport`, `commitImport`, `cancelImport`, `getImport`, `createExport`, `getExport`, `downloadExport`.
- Optimistic updates: none; job status is polled and reconciled with the server `version`.
- Telemetry: `search_performed`, `search_result_opened`, `import_started`, `import_dry_run`, `import_committed`, `export_requested`, `export_downloaded` with `sheet_id`, `format`, `row_count`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F010-01 through FR-F010-16 in `testing/features/F010/requirements/cases.md`
- [ ] Failure/edge-case tests: empty query, 51 MB file, malformed XLSX, `update` strategy without key column, worker kill mid-commit, cancel after chunk, download before completion, download after expiry, stale event ignored by indexer
- [ ] Permission-negative and tenant-isolation tests: foreign-tenant search returns nothing, unreadable sheet rows omitted, viewer import denied, non-requester download denied, hidden columns absent from export
- [ ] Rust unit tests: `crates/domain/src/dataio/` type detection, mapping coercion, dedupe matching, chunk cursor, permission filter, PDF pagination
- [ ] API contract/integration tests: every route above with success and each error code
- [ ] Database migration/constraint tests: status checks, GIN index usage, unique target row, expiry index, rollback
- [ ] React component tests: `SearchCommandPalette`, `ImportWizard`, `ImportStatusPanel`, `ExportDialog` states
- [ ] Browser E2E tests: search and open row, import with dry run and commit, cancel import, export PDF and download
- [ ] Accessibility tests: axe on palette, wizard, dialog; combobox keyboard flow; progress announcements
- [ ] Performance/load tests: 1M-document search p95, index lag, 100k-row import, 100k-row export

### Fast fanout configuration

- Test harness path: `testing/features/F010/`
- Feature flag: `F010_FEATURE`
- Fixture/seed factory: `testing/fixtures/dataio.rs` builds tenant A and B, editor, viewer, tenant-admin, a sheet `Plan` with 8 typed columns and 1,000 rows, a restricted sheet `Payroll`, seeded comments and attachment metadata, and generators for `plan.csv`, `plan.xlsx`, and a 100,000-row CSV
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, UTC, MinIO bucket per worker
- Mock/stub contracts: in-memory outbox recorder; worker handlers invoked directly by tests with a kill switch between chunks; F017 file API stubbed with a pre-scanned file fixture
- Parallel isolation: one schema and one object-storage prefix per test worker, tenant ID per test
- Targeted command: `cargo xtask test-feature F010`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F010/`

## 6. Acceptance criteria

```gherkin
Feature: Search, import, and export

Scenario: Search finds a row the actor can read and omits one they cannot
  Given row "Kickoff" on sheet "Plan" and row "Kickoff bonus" on restricted sheet "Payroll"
  When a viewer of "Plan" searches for "kickoff"
  Then the results contain the "Plan" row and not the "Payroll" row

Scenario: Import resumes after a worker crash without duplicates
  Given a committing import of 5,000 rows whose worker is killed after chunk 2
  When another worker claims the job
  Then it resumes from cursor chunk 3 and the sheet contains exactly 5,000 new rows
  And import.completed.v1 is in the outbox with total_rows 5000

Scenario: Dry run writes nothing
  Given a previewed import with 20 invalid rows
  When the editor commits with dry_run true
  Then the report lists 20 invalid rows with codes and the sheet row count is unchanged

Scenario: Viewer cannot import
  Given a viewer on sheet "Plan"
  When they POST /api/v1/imports for that sheet
  Then the response is 403 denied and no job is created

Scenario: Export respects hidden columns
  Given column "Salary" is denied to the exporter
  When they export "Plan" to XLSX and download it
  Then the workbook has no "Salary" column and an export.download audit event exists
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F008 (bulk row service used by import commit, grid refresh), F004 (worker runtime, outbox consumer registration, object storage, job runs and dead letters); decisions sections 2–7, 9; contracts row F010
- Blocks: F025, F027, F052
- Conflicts with: none (disjoint owned paths)
- External dependencies: S3-compatible object storage (MinIO locally) for import files and export outputs; F017 file upload path for `file_id`
- Risks and mitigations: PostgreSQL full-text search may rank poorly for short tokens, so the `simple` configuration is queried alongside `english` and prefix matching is enabled for the last term; XLSX parsing memory is bounded by streaming rows rather than loading the workbook; PDF rendering of 500 columns is paginated across pages horizontally with column groups; ACL snapshot staleness is bounded by the per-hit authoritative check.
- Open questions: none

## 7.1 Amendments

Every change made to this ticket after it was first accepted, newest first.

| Date | Caused by | What changed | Why |
|---|---|---|---|
| 2026-09-04 | Filter vocabulary unification (F013) | Subset of `docs/filter-vocabulary.md` declared in section 4 and the operator names aligned to it | `export_job_filters` is now a declared subset, and its flat-conjunction shape — which is *not* F013's nested AST — is stated rather than left for a reader to discover |

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F008 and F004 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F010/`
- [ ] Migration file name and owned paths claimed
- [ ] Fixture factory `testing/fixtures/dataio.rs`, per-worker object-storage prefix, and schema-per-worker isolation available in `testing/harness/`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for every mutation and download
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F010_FEATURE`, run down migration on an empty tenant, worker handlers unregistered
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Users can search sheets, rows, comment metadata, and attachment metadata across their tenant, import CSV/XLSX files with preview, dry run, duplicate handling, and resumable progress, and export sheets to CSV, XLSX, or PDF with permission filtering.
- Migration adds `search_documents`, `search_document_principals`, `import_jobs`, `import_column_mappings`, `import_rows`, `import_row_errors`, `export_jobs`, `export_job_columns`, and `export_job_filters`; rollback drops them. Feature is off by default behind `F010_FEATURE`.
