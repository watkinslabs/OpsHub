---
id: F071
type: feature
status: planned
priority: P1
owner: platform
estimate: 8
target_milestone: M2
parent_epic: E003
depends_on: [F007, F010, F013]
blocks: []
conflicts_with: []
parallel_safe: true
owned_paths: [crates/persistence/src/migration/**, crates/domain/src/migration/**, services/api/src/migration/**, services/worker/src/migration/**, apps/web/src/features/migration/**, services/api/migrations/*_migration_*.sql, testing/features/F071/**]
feature_flag: F071_FEATURE
flag_default: off
branch: f071-migration-import
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 5, 7, 9
- Capability contract: `docs/capability-contracts.md` row F071

# F071 — Migration import

## 1. Identity and dates

- Branch: `f071-migration-import`
- Capability area: planning and intake (spec 5.2 structural import bullets; 5.1 typed columns and hierarchy; section 6 async job and reliability targets)
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 5, 7, 9; `docs/capability-contracts.md` row F071
- Aggregate: `migration`
- Module slug: `migration`

## 2. Requirement specification

### Problem and user outcome

A team evaluating OpsHub already holds its work in an Excel or Google Sheets workbook, a Smartsheet, or an Airtable base — many tabs, typed columns, filtered views, and references between tabs. F010 imports one file into one sheet that already exists, which is the wrong shape for arriving: it asks the newcomer to hand-build every sheet and column first. Nobody switches products if their structure has to be rebuilt by hand, so the workbook has to come in **as structure**.

As a sheet editor, I want to upload my workbook, see exactly what OpsHub would create — every sheet, every column with the type it inferred, every row count, every view, every link, and every thing it cannot bring over and why — correct the types I disagree with, and only then commit, so that adopting OpsHub costs an afternoon instead of a quarter and nothing is created behind my back.

### Functional requirements

- **FR-F071-01:** `POST /api/v1/migrations` with `{ file_id, source_kind: excel|google-sheets|smartsheet|airtable, target_folder_id, name? }` creates a `migrations` row in status `analyzing`, is acknowledged with `202 { id, status }` in under 2 s, and enqueues the analysis job; the actor needs `sheet-editor` on `target_folder_id` and a `file_id` already scanned by F017. The route creates no sheet, column, row, view, or link — analysis only stages the plan.
- **FR-F071-02:** Only the export formats the source products themselves document are accepted, and OpsHub never authenticates to, scrapes, or reverse-engineers a private API of any of them: `excel` and `google-sheets` are one `.xlsx` OOXML workbook (Google Sheets is reached through its own `File → Download → Microsoft Excel`), `smartsheet` is one or more sheet-level Excel exports bundled in a `.zip`, `airtable` is one `.csv` per table bundled in a `.zip` from Airtable's own per-table CSV download. A container that is neither `.xlsx` nor `.zip`, or whose entries do not match the declared `source_kind`, returns `400 invalid` with `field_errors.file_id = "unsupported_source"`. An `.xlsm` macro project is accepted, never executed, and recorded as one `macro_dropped` issue.
- **FR-F071-03:** Limits are enforced at analysis and reported before commit: container ≤ 200 MB and ≤ 500 MB uncompressed (`field_errors.file_id = "expansion_limit"`), ≤ 50 tabs (`"tab_limit"`), ≤ 400 columns per tab, ≤ 100,000 rows per tab, ≤ 500,000 rows per migration, and at most 3 migrations per tenant in `analyzing` or `committing` at once (`429 rate_limited` with `Retry-After`). A tab past the row cap is staged truncated at the cap with a `blocking` `row_cap_exceeded` issue; columns past the column cap are staged with `state = excluded` and a `blocking` `column_cap_exceeded` issue; a `blocking` issue makes commit return `400 invalid` until it is waived per issue or the source is fixed.
- **FR-F071-04:** One source tab becomes one `migration_sheets` row: `source_name`, `ordinal`, the proposed sheet name (deduplicated against the destination folder with a ` (2)` suffix), `row_count`, `column_count`, and `header_row_number`. A header row is the first row where at least 60 % of cells are non-empty and distinct and the row beneath it infers to different types; when no row qualifies, columns are named `Column 1` upward and a `no_header_row` issue is written. The primary column is the first column inferred `text`, otherwise the first column.
- **FR-F071-05:** Every source column becomes one `migration_column_maps` row carrying `source_header`, `source_index`, `inferred_type` drawn from exactly the twelve F007 types (`text, number, currency, date, datetime, boolean, person, link, file, select, formula, duration`), `confidence` (0.000–1.000), `state` in `inferred|ambiguous|overridden|excluded`, and the type settings the column would be created with. Inference samples up to 2,000 non-empty cells per column — the first 500 plus a deterministic stride over the remainder seeded by `source_index` — so re-analysing the same file yields the same plan.
- **FR-F071-06:** `confidence` is matched samples over sampled cells for the winning candidate. At or above 0.95 with every rival below 0.80 the column is `inferred`. At or above 0.95 with a rival also at or above 0.80 the column is `ambiguous`, the winner is taken from the fixed precedence `boolean, datetime, date, duration, currency, number, person, link, file, select, text`, and an `ambiguous_type` issue names both candidates. Below 0.95 the column falls back to `text`, is `ambiguous`, and the issue lists up to 5 sample values that failed. An entirely empty column is `text`, `inferred`, confidence 0. `formula` is never inferred from values.
- **FR-F071-07:** Per-type inference rules: `select` needs distinct non-empty values ≤ 50 and ≤ 20 % of `row_count` with each ≤ 60 chars, and stages one option per distinct value with colours assigned round-robin from the token palette; `person` needs ≥ 0.90 of samples to be an email resolving to an active tenant user, and every unresolved address raises `unresolved_person` and stays text; `currency` needs one ISO 4217 code or symbol across ≥ 0.95 of samples and stages it as the column's `currency_code`; `duration` accepts `1d 4h`, `1:30`, and ISO 8601 durations; `date` and `datetime` come from the cell's OOXML serial and number format, and a day/month order the workbook locale cannot settle raises `ambiguous_date_order` and defaults to ISO order.
- **FR-F071-08:** `GET /api/v1/migrations/{id}` returns the complete dry run: `status`, `source_kind`, counts, every `migration_sheets` row with its `migration_column_maps` rows (header, inferred type, confidence, state, settings, up to 5 sample values), up to 20 sample rows per tab parsed on demand from the stored source file, the proposed views and links, every `migration_issues` row, and `version`. `GET /api/v1/migrations` pages by cursor and filters by `status` and `source_kind`. Nothing in the destination folder exists yet at this point, and the response says so through `committed_sheet_count: 0`.
- **FR-F071-09:** `POST /api/v1/migrations/{id}/commit` carries `{ column_overrides: [{ column_map_id, target_type, settings? }], sheet_overrides: [{ sheet_map_id, name?, included }], accept_ambiguous: bool, waived_issue_ids: [] }` with `Idempotency-Key` and `If-Match`. Every override replaces its `migration_column_maps` row with `state = overridden` and is re-validated against the F007 create-column contract before any write; an invalid type, setting, or select option returns `400 invalid` with `field_errors.column_overrides` and creates nothing. A column still `ambiguous` at commit without an override is refused with `field_errors.column_overrides` unless `accept_ambiguous` is true. Commit on a migration already `committing` or `completed` returns `409 conflict`.
- **FR-F071-10:** Commit is acknowledged with `202 { id, status: committing }`, emits `migration.started.v1`, and provisions tab by tab in `ordinal` order. Each tab's structure — the sheet through `POST /api/v1/sheets`, its columns and options through `POST /api/v1/sheets/{sheet_id}/columns`, and its views through `POST /api/v1/views` — is written in one `UnitOfWork`, so a structure failure leaves nothing. Rows then stream from the stored source file in 1,000-row chunks through `POST /api/v1/sheets/{sheet_id}/rows/bulk` with `Idempotency-Key = <migration_id>:<sheet_ordinal>:<chunk_index>`, advancing `migration_sheets.cursor_row_number` and `committed_rows` after each chunk.
- **FR-F071-11:** The plan is resumable and never leaves a half-created sheet. `migration_sheets.state` moves `pending → committing → committed|failed|skipped`; a worker that claims a `committing` sheet resumes at `cursor_row_number`, and the stable idempotency key makes the replayed chunk a no-op rather than a duplicate. A tab that fails terminally after three attempts has its sheet and rows soft-deleted in one transaction, is marked `failed`, and the migration continues with the next tab; `DELETE /api/v1/migrations/{id}` on a non-`completed` migration soft-deletes every sheet it created, soft-deletes the migration, and leaves the destination folder as it was.
- **FR-F071-12:** A source view becomes an F013 view where the concepts map and is reported where they do not. An Excel AutoFilter or table filter becomes a `grid` view whose filter AST carries `eq`, `contains`, and `between` conditions; a saved sort state becomes `view_sorts` truncated at 5 with a `view_sorts_truncated` issue; hidden columns and column order become `view_columns`. Pivot tables, slicers, and Smartsheet card, calendar, and Gantt view definitions are absent from or unrepresentable in the documented exports and raise `unsupported_view_kind` or `unsupported_view_export` naming the tab and the source view. Airtable's CSV export carries only the exported view's column order and row order, which becomes one `grid` view per table with that order and an `informational` `unsupported_view_export` issue.
- **FR-F071-13:** A cross-tab reference becomes an F009 link when it resolves: the source cell's formula is a single-cell or single-column reference into another tab in the same migration, and that tab has a key column whose values are unique and non-empty. The column is staged as `link` with the target tab and key column recorded, and after every tab is committed a second pass creates one link per row through `POST /api/v1/links`. Multi-cell ranges, cross-workbook references such as another workbook's file name in brackets, and `INDIRECT` do not resolve: the last computed value is written as static text and a `cross_workbook_reference` or `unresolved_reference` issue records the cell. A link that fails to create marks its issue and never rolls back a committed sheet.
- **FR-F071-14:** Source outline levels — Excel row grouping and Smartsheet indentation — become F009 hierarchy through `POST /api/v1/rows/{id}/indent` up to depth 20; anything deeper is flattened at 20 with a `hierarchy_depth_exceeded` issue. A source formula whose functions are all supported by F035 becomes an F007 `formula` column with the translated expression; any other formula is written as its last computed value with an `unsupported_formula_function` issue naming the function and the cell.
- **FR-F071-15:** `migration_issues` is the visible record of everything that could not come over, written in the user's terms with `kind`, `severity` in `blocking|warning|informational`, the tab, the source column or cell reference, and a message. `kind` is one of `unsupported_formula_function`, `conditional_format_dropped`, `cross_workbook_reference`, `attachment_over_size_cap`, `unresolved_reference`, `ambiguous_type`, `ambiguous_date_order`, `unresolved_person`, `no_header_row`, `unsupported_view_kind`, `unsupported_view_export`, `view_sorts_truncated`, `hierarchy_depth_exceeded`, `row_cap_exceeded`, `column_cap_exceeded`, `merged_cells_split`, `data_validation_dropped`, `protected_range_dropped`, `chart_dropped`, `macro_dropped`. Attachments bundled in a Smartsheet or Excel export are uploaded through F017 into a `file` column when they are 25 MB or smaller; a larger one is skipped with `attachment_over_size_cap` naming the file and its size, and an Airtable attachment cell keeps its exported URL in a `link` column with an `informational` issue, because the CSV export carries a URL rather than the bytes.
- **FR-F071-16:** The web app provides `/w/:workspaceId/migrations` and `/w/:workspaceId/migrations/:migrationId` with an upload step, a per-tab review table of inferred types with confidence and inline type override, an issues panel grouped by severity with per-issue waive, a `Create everything` action that is disabled while a blocking issue is unwaived, and a commit progress panel showing per-tab state and row counts; `migration.completed.v1` links straight to the first created sheet. A viewer or commenter on the destination folder never sees the entry point and receives `denied` on every route.

### Non-functional requirements

- **NFR-F071-01 Performance:** analysis of a 20-tab, 200,000-cell workbook completes in under 90 s; `GET /api/v1/migrations/{id}` returns the full preview in under 800 ms p95 for 50 tabs and 2,000 column maps; commit of 100,000 rows across 10 tabs completes in under 15 minutes; both mutations are acknowledged in under 2 s; parsing holds peak resident memory under 512 MB by streaming rows rather than materialising the workbook.
- **NFR-F071-02 Security/privacy:** every query carries the `tenant_id` predicate; the source file is read only from the tenant's own object-storage prefix and no code path on this feature opens a network socket to Microsoft, Google, Smartsheet, or Airtable; zip entries are rejected when a path escapes the extraction root or the uncompressed total exceeds the expansion limit; the source file and its extracted entries are deleted 7 days after the migration reaches a terminal status or immediately on `DELETE`; a foreign-tenant `file_id`, `target_folder_id`, or migration id returns `not_found`.
- **NFR-F071-03 Accessibility:** the review table is a real table with column headers, per-row type selects labelled by their source header, and confidence conveyed by text and a labelled icon rather than colour alone; the issues panel groups under headings with counts; commit progress announces per-tab completion through a polite live region; keyboard reaches upload, override, waive, and commit; no serious or critical axe violations in both themes.
- **NFR-F071-04 Reliability/observability:** analysis and commit jobs are idempotent per tab and chunk, retried three times with exponential backoff, then dead-lettered into `job_runs`; metrics `migration_analysis_duration_ms`, `migration_rows_committed_total`, `migration_issues_total` by `kind`, and `migration_failed_total`; spans carry `tenant_id`, `migration_id`, `sheet_map_id`, and `correlation_id`.
- **NFR-F071-05 Determinism:** two analyses of the same file under the same tenant produce identical `migration_sheets`, `migration_column_maps`, and `migration_issues` content, because sampling strides are seeded by `source_index`, option and issue ordering is by source position, and no wall-clock or random input reaches inference.

### Scope

Included: the four documented export sources and their container handling, structural analysis staging sheets, column maps and issues, type inference with confidence and ambiguity, the dry-run preview, reviewed and overridden commit, per-tab transactional provisioning through F006/F007/F008/F013, the cross-tab link and hierarchy passes through F009, the issue ledger, limits and quotas, deletion and cleanup, worker handlers, and the migration UI.

Excluded: importing a CSV or xlsx into a sheet that already exists, with preview, duplicate strategy, and dry run (F010 owns that end to end, and F071 never writes an `import_jobs` row); continuous or scheduled movement of data between OpsHub and an external system (F052 and F053); connector authentication and OAuth token storage (F029, F030); file upload and virus scanning (F017); the formula language and its function set (F035); conditional formatting rules (F060); sheet, column, cell, view, link, and hierarchy tables, all of which stay with their owning features and are reached only through their services.

## 3. UX specification

- Entry points: workspace tree action `Bring in a workbook`, the empty-workspace panel's `Import a workbook` card, and route `/w/:workspaceId/migrations`; a running migration also appears in the workspace header as a progress chip.
- Primary flow: drop `Q3 delivery.xlsx`, watch `Analysing 12 tabs`, land on the review screen. The left column lists tabs with row counts and issue badges; the centre is the column review table for the selected tab — source header, sample values, inferred type, confidence, and a type select; the right is the issues panel grouped `Blocking`, `Warning`, `Information`. Change `Owner` from `text` to `person`, waive `Conditional formatting on Milestones was not brought over`, then press `Create everything`. The commit panel shows each tab moving `pending → committing → committed` with row counts, and on completion a link opens the first new sheet.
- Loading: skeleton tab list and review rows during analysis with the elapsed time. Empty: a workbook with no data tabs explains that every tab was empty and offers to delete the migration. Error: banner with `correlation_id` and retry; a failed tab shows its dead-letter reason inline and states that its sheet was removed. Denied: the entry point is hidden for viewers and commenters and the route renders the denied surface. Stale: a preview whose `version` moved shows the stale banner and refetches. Conflict: a second commit shows that this migration is already being created. Offline: upload and commit are disabled with the offline badge and the preview stays readable.
- Confidence is shown as a labelled `High`, `Medium`, or `Low` chip with the numeric value in monospace, never colour alone; an `ambiguous` column carries a warning icon with a title and cannot be committed until it is overridden or ambiguity is explicitly accepted.
- Responsive: under 1,100 px the issues panel collapses to a bottom sheet with a count button; under 640 px the review table scrolls horizontally in its own container and the tab list becomes a select.
- Keyboard: `Tab` moves through tabs, review rows, and issue actions; the type select is a native combobox; `Enter` waives a focused issue; `Escape` closes the issues sheet; motion respects `prefers-reduced-motion`.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for counts and confidence (F062); Lucide icons `FileSpreadsheet`, `Upload`, `Wand2`, `AlertTriangle`, `CheckCircle2`, `Link2`, `Table`; spacing and colour from `apps/web/src/design/tokens.css`.

- Design: `design/artboards/Migration.dc.html`, generated by `design/generator/migration.py`, drawing the preview-and-issues review step at 1440×900. The ticket is the contract and the artboard is the picture; when they disagree the ticket wins.

## 4. Technical specification

Canonical contract: `docs/capability-contracts.md` row F071.

### Rust backend

- Domain entities in `crates/domain/src/migration/`: `Migration { id, tenant_id, file_id, source_kind: SourceKind, target_folder_id, name, status: MigrationStatus, tab_count, total_rows, committed_sheet_count, blocking_issue_count, attempt, version, audit }`, `MigrationSheet { id, migration_id, ordinal, source_name, proposed_name, header_row_number, row_count, column_count, state: SheetState, target_sheet_id, cursor_row_number, committed_rows, included }`, `MigrationColumnMap { id, sheet_map_id, source_index, source_header, inferred_type: ColumnType, confidence, state: MapState, target_type, settings, link_target_sheet_map_id, link_key_source_index }`, `MigrationIssue { id, migration_id, sheet_map_id, kind: IssueKind, severity: Severity, source_ref, message, waived_by, waived_at }`.
- Modules: `sources/{xlsx_reader.rs, zip_container.rs, airtable_csv.rs, smartsheet_export.rs, detect.rs}`, `infer/{sampler.rs, candidates.rs, confidence.rs, options.rs}`, `plan/{structure.rs, views.rs, links.rs, hierarchy.rs, formulas.rs}`, `commit/{provisioner.rs, chunker.rs, rollback.rs}`, `issues.rs`, `limits.rs`, `service.rs`, `errors.rs`; worker handlers in `services/worker/src/migration/{analyze_job.rs, commit_job.rs, cleanup_job.rs}`.
- Data access (decision 2.1): `MigrationRepository` (`migrations`), `MigrationSheetRepository` (`migration_sheets`), `MigrationColumnMapRepository` (`migration_column_maps`), and `MigrationIssueRepository` (`migration_issues`) in `crates/persistence/src/migration/`, with named queries `claim_analyzable`, `claim_committing_sheet`, `advance_sheet_cursor`, `replace_column_maps`, `count_blocking_issues`, and `list_preview_page`. Sheets, columns, options, rows, cells, views, links, and hierarchy are created only through the F006, F007, F008, F013, and F009 domain services, so this feature adds no second writer to their tables and owns no repository over them. The parsers, inference, planning, commit code, handlers, and worker jobs contain no SQL, `sqlx::query*` call, or pool; the per-tab structure write and the per-tab rollback each run in one `UnitOfWork`.
- Use cases: `create_migration`, `analyze_migration`, `get_migration`, `list_migrations`, `apply_overrides`, `commit_migration`, `resume_commit`, `rollback_sheet`, `waive_issue`, `delete_migration`, `cleanup_expired`.
- API endpoints (`services/api/src/migration/`): `POST /api/v1/migrations`, `GET /api/v1/migrations`, `GET /api/v1/migrations/{id}`, `POST /api/v1/migrations/{id}/commit`, `DELETE /api/v1/migrations/{id}`. DTOs `CreateMigrationRequest`, `MigrationSummary`, `MigrationPreviewResponse { migration, sheets, issues, sample_rows }`, `SheetPlanDto`, `ColumnMapDto`, `IssueDto`, `CommitMigrationRequest`, `CommitAcceptedResponse`.
- Events: `migration.started.v1` (`tab_count`, `total_rows`), `migration.completed.v1` (`committed_sheet_count`, `committed_rows`, `issue_count`, `first_sheet_id`), `migration.failed.v1` (`reason: invalid_source|blocking_issues|dead_letter|cancelled`); all through the outbox with the contract envelope.
- Authorization: `sheet-editor` on `target_folder_id` for create, commit, and delete, and on the migration's folder for read; `viewer` and `commenter` receive `denied` on every route; every provisioning call runs under the requesting actor's context so a folder the actor cannot write is refused before the first sheet is created; foreign-tenant ids map to `not_found`.
- Validation: `source_kind` in the four values, `name` 1–120 chars, `file_id` present and scanned, container and limits per FR-F071-03, `column_overrides` target types within the twelve F007 types with settings valid for that type, `sheet_overrides` naming sheet maps of this migration, `waived_issue_ids` naming issues of this migration.
- Error mapping: `MigrationError::UnsupportedSource | LimitExceeded | InvalidOverride | UnresolvedAmbiguity | BlockingIssues → 400 invalid`, `AlreadyCommitting | TerminalStatus → 409 conflict`, `NotFound | Expired → 404 not_found`, `AuthzError::Denied → 403 denied`, `ConcurrentMigrationQuota → 429 rate_limited`, `SourceUnreadable → 503 unavailable`.

### Interface

Exact shapes. `T?` is nullable; a missing optional field and an explicit `null` are the same thing.
Timestamps are RFC 3339 UTC, ids are UUIDv7 strings, `version` increments by one per write. Unlisted
request fields are rejected with `400 invalid`. `Page<T>` and the error body (including its optional
`reason`) are F028's; `ColumnType` is F007's twelve-member enum and is not redefined here;
`ActorContext` is F038's; the permission vocabulary is `docs/authorization-model.md`.

- Filter operators: `docs/filter-vocabulary.md`, subset `eq`, `contains`, `between` — two narrow uses and no more: `GET /api/v1/migrations` filters by `status` and `source_kind` with equality only, and a translated Excel AutoFilter stages an F013 filter AST holding exactly these three operators (FR-F071-12); every richer source predicate becomes an issue rather than a fourth operator, because a filter this feature cannot express faithfully must be visible, not approximated.

**`CreateMigrationRequest`** — `POST /api/v1/migrations`

| Field | Type | Required | Constraint |
|---|---|---|---|
| `file_id` | uuid | yes | an F017 file already scanned `clean`; unscanned, foreign-tenant or absent → `404 not_found`; a container that is neither `.xlsx` nor `.zip`, or whose entries do not match `source_kind` → `400 invalid` with `field_errors.file_id = "unsupported_source"`; past the size or expansion caps → `field_errors.file_id = "expansion_limit"` |
| `source_kind` | `"excel" \| "google-sheets" \| "smartsheet" \| "airtable"` | yes | outside the four → `400 invalid` |
| `target_folder_id` | uuid | yes | caller holds `sheet-editor` on it, else `403 denied`; another tenant's folder → `404 not_found` |
| `name` | string? | no | 1–120 characters after trim; defaults to the container's file name |

**`CommitMigrationRequest`** — `POST /api/v1/migrations/{id}/commit`

| Field | Type | Required | Constraint |
|---|---|---|---|
| `column_overrides` | ColumnOverride[] | no | default empty; each `column_map_id` must belong to this migration, else `400 invalid` with `field_errors.column_overrides` |
| `sheet_overrides` | SheetOverride[] | no | default empty; each `sheet_map_id` must belong to this migration |
| `accept_ambiguous` | bool | no | default `false`; while `false`, any column still `ambiguous` with no override is `400 invalid` with `field_errors.column_overrides` naming it |
| `waived_issue_ids` | uuid[] | no | default empty; each must name an issue of this migration; an unwaived `blocking` issue leaves commit `400 invalid` with `field_errors.waived_issue_ids` |

**`ColumnOverride`**

| Field | Type | Required | Constraint |
|---|---|---|---|
| `column_map_id` | uuid | yes | a `migration_column_maps` row of this migration |
| `target_type` | ColumnType | yes | one of F007's twelve; re-validated against F007's create-column contract before any write |
| `settings` | object? | no | the F007 settings payload for `target_type`; invalid for that type → `400 invalid` with `field_errors.column_overrides` and nothing is created |

**`SheetOverride`**

| Field | Type | Required | Constraint |
|---|---|---|---|
| `sheet_map_id` | uuid | yes | a `migration_sheets` row of this migration |
| `name` | string? | no | 1–200 characters; deduplicated against the destination folder with a ` (2)` suffix, as the proposed name already is |
| `included` | bool | yes | `false` marks the tab `skipped` and creates no sheet for it |

**`MigrationSummary`** — the list item, and the `migration` member of the preview

| Field | Type | Notes |
|---|---|---|
| `id` | uuid | |
| `source_kind` | `"excel" \| "google-sheets" \| "smartsheet" \| "airtable"` | |
| `target_folder_id` | uuid | |
| `name` | string | |
| `status` | `"analyzing" \| "ready" \| "committing" \| "completed" \| "failed" \| "cancelled"` | |
| `failure_reason` | `"invalid_source" \| "blocking_issues" \| "dead_letter" \| "cancelled"`? | present only when `status` is `failed` or `cancelled` |
| `tab_count` | integer | |
| `total_rows` | integer | staged rows across every included tab |
| `committed_sheet_count` | integer | `0` until the first tab commits, which is how the dry run says nothing exists yet |
| `blocking_issue_count` | integer | unwaived `blocking` issues; commit is refused while it is non-zero |
| `expires_at` | timestamp | 7 days after a terminal status; the cleanup job's key |
| `version` | integer | pass as `If-Match` on commit and delete |
| `created_at` / `updated_at` | timestamp | |
| `created_by` / `updated_by` | uuid | |

**`MigrationPreviewResponse`** — `GET /api/v1/migrations/{id}`

| Field | Type | Notes |
|---|---|---|
| `migration` | MigrationSummary | |
| `sheets` | SheetPlanDto[] | in `ordinal` order |
| `issues` | IssueDto[] | in `ordinal` order, which is source position — the ordering NFR-F071-05 makes deterministic |
| `sample_rows` | map<uuid, (string?)[][]> | keyed by `sheet_map_id`, up to 20 rows per tab, each row an array of raw source strings in `source_index` order; parsed on demand from the stored file and never persisted |

**`SheetPlanDto`**

| Field | Type | Notes |
|---|---|---|
| `id` | uuid | the `sheet_map_id` overrides name |
| `ordinal` | integer | source tab order; also the commit order |
| `source_name` | string | |
| `proposed_name` | string | deduplicated against the destination folder |
| `header_row_number` | integer? | `null` when no row qualified, which also raises `no_header_row` |
| `row_count` | integer | staged rows, already truncated at the 100,000 cap when `row_cap_exceeded` was raised |
| `column_count` | integer | |
| `included` | bool | |
| `state` | `"pending" \| "committing" \| "committed" \| "failed" \| "skipped"` | |
| `target_sheet_id` | uuid? | non-null exactly when `state` is `committing` or `committed` |
| `cursor_row_number` | integer | the resume point; `≤ row_count` |
| `committed_rows` | integer | |
| `failure_reason` | string? | present only when `state` is `failed`; the dead-letter reason the UI shows inline |
| `columns` | ColumnMapDto[] | in `source_index` order |

**`ColumnMapDto`**

| Field | Type | Notes |
|---|---|---|
| `id` | uuid | the `column_map_id` an override names |
| `source_index` | integer | 0-based position in the source tab |
| `source_header` | string? | `null` when the tab had no header row |
| `inferred_type` | ColumnType | one of F007's twelve; `formula` is never inferred from values |
| `confidence` | decimal string | `0.000`–`1.000`, three decimals, sent as a string so no client does float arithmetic on it |
| `state` | `"inferred" \| "ambiguous" \| "overridden" \| "excluded"` | |
| `target_type` | ColumnType? | non-null exactly when `state` is `overridden`, matching the table's own check constraint |
| `settings` | object | the proposed F007 column settings, moved whole to the create-column call; `{}` when the type needs none |
| `sample_values` | string[] | up to 5 raw values; for an `ambiguous` column below 0.95 these are the values that failed |
| `link_target_sheet_map_id` | uuid? | present when the column resolved to a cross-tab link |
| `link_key_source_index` | integer? | present exactly when `link_target_sheet_map_id` is |
| `target_column_id` | uuid? | the created F007 column, present only after its tab commits |

**`IssueDto`**

| Field | Type | Notes |
|---|---|---|
| `id` | uuid | the id a `waived_issue_ids` entry names |
| `sheet_map_id` | uuid? | `null` for a migration-wide issue |
| `kind` | one of the twenty `kind` values of FR-F071-15 | |
| `severity` | `"blocking" \| "warning" \| "informational"` | |
| `source_ref` | string? | the source column or cell reference, e.g. `Milestones!D14` |
| `message` | string | written in the user's terms, not the parser's |
| `ordinal` | integer | source position; the stable sort key |
| `waived_by` | uuid? | non-null exactly when `waived_at` is |
| `waived_at` | timestamp? | |

**`CommitAcceptedResponse`** — the `202` body of both mutations that enqueue work

| Field | Type | Notes |
|---|---|---|
| `id` | uuid | the migration |
| `status` | `"analyzing" \| "committing"` | `analyzing` from `POST /api/v1/migrations`, `committing` from the commit route |
| `version` | integer | the row's version, per the catalog's "mutations return `version`" convention, so the client can `If-Match` the next call without a second read |

**List parameters** — `GET /api/v1/migrations`

| Parameter | Type | Constraint |
|---|---|---|
| `status` | string? | equality on one of the six status values; anything else → `400 invalid` |
| `source_kind` | string? | equality on one of the four source kinds |
| `cursor` | string? | F028's opaque signed cursor |
| `limit` | integer? | 1–100, default 20 |

The response is F028's `Page<MigrationSummary>`, sorted `created_at` descending then `id`, which is
the `migrations(tenant_id, status, created_at desc)` index.

**Status codes**

| Status | Produced by |
|---|---|
| `200` | `GET /api/v1/migrations`, `GET /api/v1/migrations/{id}` |
| `202` | `POST /api/v1/migrations` and `POST /api/v1/migrations/{id}/commit`, both acknowledged in under 2 s |
| `204` | `DELETE /api/v1/migrations/{id}` |
| `400 invalid` | `unsupported_source`, `expansion_limit`, `tab_limit`, an override naming a foreign map id, an invalid `target_type` or `settings`, an unwaived `blocking` issue, and an `ambiguous` column with neither an override nor `accept_ambiguous` |
| `403 denied` | a viewer or commenter on `target_folder_id`, or an actor without `sheet-editor` on the migration's folder |
| `404 not_found` | a `file_id`, `target_folder_id` or migration id from another tenant, and a migration past `expires_at` |
| `409 conflict` | committing a migration already `committing` or `completed`, a stale `If-Match`, and an `Idempotency-Key` replayed with a different body |
| `429 rate_limited` | a fourth concurrent migration in `analyzing` or `committing` for the tenant, with `Retry-After` |
| `503 unavailable` | `SourceUnreadable` — object storage will not serve the staged file; nothing is written |

### Use case signatures

In `crates/domain/src/migration/service.rs`; worker handlers in `services/worker/src/migration/`.
`Ctx` is F038's `ActorContext`; `JobCtx` is the worker's actor-less job context carrying tenant and
correlation id.

```rust
fn create_migration(ctx: &Ctx, uow: &mut UnitOfWork, req: CreateMigration) -> Result<Migration, DomainError>;
fn analyze_migration(ctx: &JobCtx, uow: &mut UnitOfWork, id: MigrationId, source: &dyn SourceReader) -> Result<Migration, DomainError>;
fn get_migration(ctx: &Ctx, repo: &dyn MigrationRepository, sheets: &dyn MigrationSheetRepository, maps: &dyn MigrationColumnMapRepository, issues: &dyn MigrationIssueRepository, source: &dyn SourceReader, id: MigrationId) -> Result<MigrationPreview, DomainError>;
fn list_migrations(ctx: &Ctx, repo: &dyn MigrationRepository, filter: MigrationFilter, page: Cursor) -> Result<Page<Migration>, DomainError>;
fn apply_overrides(ctx: &Ctx, uow: &mut UnitOfWork, id: MigrationId, expected: Version, req: CommitMigration) -> Result<Migration, DomainError>;
fn waive_issue(ctx: &Ctx, uow: &mut UnitOfWork, id: IssueId) -> Result<MigrationIssue, DomainError>;
fn commit_migration(ctx: &Ctx, uow: &mut UnitOfWork, id: MigrationId, expected: Version, req: CommitMigration) -> Result<Migration, DomainError>;
fn resume_commit(ctx: &JobCtx, uow: &mut UnitOfWork, sheet: SheetMapId, source: &dyn SourceReader) -> Result<MigrationSheet, DomainError>;
fn rollback_sheet(ctx: &JobCtx, uow: &mut UnitOfWork, sheet: SheetMapId, reason: FailureReason) -> Result<MigrationSheet, DomainError>;
fn delete_migration(ctx: &Ctx, uow: &mut UnitOfWork, id: MigrationId, expected: Version) -> Result<(), DomainError>;
fn cleanup_expired(ctx: &JobCtx, uow: &mut UnitOfWork, batch: usize) -> Result<CleanupReport, DomainError>;
```

`MigrationFilter` is `{ status: Option<MigrationStatus>, source_kind: Option<SourceKind> }` — the
whole of this route's filter surface. `CommitMigration` is the deserialized `CommitMigrationRequest`;
`apply_overrides` is the validation half of `commit_migration` and is called by it, not by a route of
its own, which is why the overrides are submitted whole with the commit. `waive_issue` is likewise
reached through `commit_migration`'s `waived_issue_ids` and has no route. A use case never takes a
pool or a connection and never returns a database row type.

Transaction boundaries:

- `create_migration` writes the `migrations` row, its audit row and the analysis job's outbox message
  in **one `UnitOfWork`**, so a migration that exists is always one a worker will pick up.
- `analyze_migration` writes every `migration_sheets`, `migration_column_maps` and `migration_issues`
  row plus the status flip to `ready` and the recomputed `blocking_issue_count` in **one
  `UnitOfWork`**. A half-staged plan would be a preview that lies about what commit will create;
  re-analysis replaces the whole plan through `replace_column_maps`, which is only atomic here.
- `commit_migration` validates and applies every override, waives the named issues, flips the status
  to `committing` and enqueues the commit job in **one `UnitOfWork`**, so the plan a worker reads is
  exactly the plan the user approved.
- Provisioning is **one `UnitOfWork` per tab**: that tab's sheet, its columns and options, and its
  views. A structure failure therefore leaves nothing of that tab, which is the invariant behind "a
  failed tab leaves nothing half-created". Rows are *not* in that boundary — they stream afterwards in
  1,000-row chunks, each chunk its own transaction advancing `cursor_row_number` and
  `committed_rows`, because one transaction over 100,000 rows would hold locks for minutes and lose
  the resume point.
- `rollback_sheet` soft-deletes that tab's sheet and rows and marks the map `failed` in **one
  `UnitOfWork`**; the migration continues with the next tab in its own boundaries.
- The link pass and the hierarchy pass run **one `UnitOfWork` per row batch** after every tab is
  committed; a link that fails marks its issue and never rolls back a committed sheet.
- `delete_migration` soft-deletes the migration and every sheet it created in one `UnitOfWork`, and
  the source file removal follows the commit, since an object-store delete cannot be rolled back.

### PostgreSQL/SQLx

- Migration `*_migration_*.sql` creates `migrations(id uuid pk, tenant_id uuid not null, file_id uuid not null, source_kind text not null check (source_kind in ('excel','google-sheets','smartsheet','airtable')), target_folder_id uuid not null references folders(id) on delete restrict, name text not null, status text not null check (status in ('analyzing','ready','committing','completed','failed','cancelled')), tab_count int not null default 0, total_rows bigint not null default 0, committed_sheet_count int not null default 0, blocking_issue_count int not null default 0, attempt smallint not null default 0 check (attempt between 0 and 3), failure_reason text, expires_at timestamptz not null, version bigint not null default 1, created_by, created_at, updated_by, updated_at, deleted_at)`.
- `migration_sheets(id uuid pk, tenant_id uuid not null, migration_id uuid not null references migrations(id) on delete cascade, ordinal smallint not null, source_name text not null, proposed_name text not null, header_row_number int, row_count int not null default 0, column_count smallint not null default 0, included bool not null default true, state text not null check (state in ('pending','committing','committed','failed','skipped')), target_sheet_id uuid, cursor_row_number int not null default 0, committed_rows int not null default 0, failure_reason text, unique (migration_id, ordinal), unique (migration_id, source_name))`.
- `migration_column_maps(id uuid pk, tenant_id uuid not null, sheet_map_id uuid not null references migration_sheets(id) on delete cascade, source_index smallint not null, source_header text, inferred_type text not null check (inferred_type in ('text','number','currency','date','datetime','boolean','person','link','file','select','formula','duration')), confidence numeric(4,3) not null check (confidence between 0 and 1), state text not null check (state in ('inferred','ambiguous','overridden','excluded')), target_type text check (target_type in ('text','number','currency','date','datetime','boolean','person','link','file','select','formula','duration')), settings jsonb not null default '{}', link_target_sheet_map_id uuid references migration_sheets(id) on delete set null, link_key_source_index smallint, target_column_id uuid, unique (sheet_map_id, source_index), check (state <> 'overridden' or target_type is not null))`.
- `migration_issues(id uuid pk, tenant_id uuid not null, migration_id uuid not null references migrations(id) on delete cascade, sheet_map_id uuid references migration_sheets(id) on delete cascade, kind text not null check (kind in ('unsupported_formula_function','conditional_format_dropped','cross_workbook_reference','attachment_over_size_cap','unresolved_reference','ambiguous_type','ambiguous_date_order','unresolved_person','no_header_row','unsupported_view_kind','unsupported_view_export','view_sorts_truncated','hierarchy_depth_exceeded','row_cap_exceeded','column_cap_exceeded','merged_cells_split','data_validation_dropped','protected_range_dropped','chart_dropped','macro_dropped')), severity text not null check (severity in ('blocking','warning','informational')), source_ref text, message text not null, ordinal int not null, waived_by uuid, waived_at timestamptz, unique (migration_id, ordinal))`.
- One `jsonb` column survives: `migration_column_maps.settings` is the proposed F007 column settings payload — precision, currency code, display format, timezone, and the staged select options — a user-defined block this feature only ever moves whole from inference to the F007 create-column call. It is never filtered, joined, sorted, or constrained on; every attribute the product does query is a typed column beside it. Staged issue kinds, sheet state, and column state are typed columns with check constraints rather than a status blob, and staged row values are not stored at all: the preview and the commit stream them from the source file in object storage, which is why there is no fifth table and why a 500,000-row migration costs four small tables.
- Invariants: `migration_sheets.target_sheet_id` is non-null exactly when `state` is `committed` or `committing`; `cursor_row_number <= row_count`; `migrations.committed_sheet_count` equals the count of `committed` sheet rows and is recomputed in the same transaction that flips a sheet; `blocking_issue_count` equals the count of unwaived `blocking` issues and is recomputed on issue write and waive; a migration in `completed` has no `pending` sheet row.
- Indexes: `migrations(tenant_id, status, created_at desc)` for the list route, `migrations(expires_at) where status in ('completed','failed','cancelled')` for the cleanup sweep, `migrations(tenant_id) where status in ('analyzing','committing')` for the concurrency quota, `migration_sheets(migration_id, ordinal)`, `migration_sheets(state) where state = 'committing'` for the resume claim, `migration_column_maps(sheet_map_id, source_index)`, `migration_issues(migration_id, severity, ordinal)` for the grouped panel, and `migration_issues(migration_id, kind)` for the counts.
- Audit events: `migration.create`, `migration.analyze`, `migration.override`, `migration.waive`, `migration.commit`, `migration.rollback`, `migration.delete` with actor, migration id, tab counts, and row counts.
- Retention/deletion: `DELETE` soft-deletes the migration, soft-deletes every sheet it created, and removes the source file and extracted entries immediately; a terminal migration expires after 7 days and the cleanup job removes its file and purges its four rows by cascade; rollback drops the four tables.

### React/TypeScript

- Routes: `/w/:workspaceId/migrations` and `/w/:workspaceId/migrations/:migrationId` in `apps/web/src/features/migration/`; components `MigrationListPage`, `MigrationUploadPanel`, `MigrationReviewPage`, `TabPlanList`, `ColumnReviewTable`, `TypeOverrideSelect`, `ConfidenceChip`, `SampleValueList`, `IssuePanel`, `IssueGroup`, `CommitProgressPanel`, `CommitConfirmDialog`.
- State: TanStack Query keys `['migration', id]` (polls every 3 s while `analyzing` or `committing`), `['migrations', filters, cursor]`; overrides are held in a local reducer keyed by `column_map_id` and submitted whole with the commit mutation, so a half-edited review never reaches the server; success invalidates `['workspace-tree', workspaceId]`.
- API client: generated `MigrationApi` with `createMigration`, `listMigrations`, `getMigration`, `commitMigration`, `deleteMigration`.
- Optimistic updates: none; type overrides are local until commit and commit progress is polled and reconciled with the server `version`.
- Telemetry: `migration_created`, `migration_analyzed`, `migration_type_overridden`, `migration_issue_waived`, `migration_committed`, `migration_deleted` with `source_kind`, `tab_count`, `total_rows`, `override_count`, and `blocking_issue_count`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F071-01 through FR-F071-16 in `testing/features/F071/requirements/cases.md`
- [ ] Failure/edge-case tests: unsupported container, zip expanding past the limit, zip entry escaping the root, 51 tabs, a tab past the row cap, a column past the column cap, no header row, an entirely empty workbook, a macro workbook, a commit while committing, a worker killed mid-chunk, a tab failing three times, an unresolvable cross-tab reference
- [ ] Permission-negative and tenant-isolation tests: viewer create denied, commenter commit denied, foreign-tenant file, folder, and migration id, and a destination folder the actor cannot write
- [ ] Rust unit tests: `crates/domain/src/migration/` sampler determinism, confidence and precedence, select and person and currency detection, header detection, view mapping, link resolution, formula translation, limit checks
- [ ] API contract/integration tests: every route above with success and each error code
- [ ] Database migration/constraint tests: check constraints, uniqueness, cascade, resume index usage, counter invariants, rollback
- [ ] React component tests: `ColumnReviewTable`, `TypeOverrideSelect`, `IssuePanel`, `CommitProgressPanel` states
- [ ] Browser E2E tests: upload, review, override a type, waive an issue, commit, open the created sheet, and delete an abandoned migration
- [ ] Accessibility tests: axe on list, review, and progress; keyboard override and waive; progress announcements
- [ ] Performance/load tests: 20-tab analysis, preview response, 100,000-row commit, parser memory ceiling

### Fast fanout configuration

- Test harness path: `testing/features/F071/`
- Feature flag: `F071_FEATURE`
- Fixture/seed factory: `testing/fixtures/migration.rs` builds tenant A and B, a sheet-editor, a viewer, a destination folder, and generators for `q3-delivery.xlsx` (12 tabs, typed columns, an AutoFilter, a sort state, grouped rows, a cross-tab reference, a conditional format, a 30 MB embedded attachment), `smartsheet-export.zip`, `airtable-base.zip`, a 50-tab workbook, a 120,000-row tab, and a zip whose entries expand past the limit
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, UTC, one object-storage prefix per worker
- Mock/stub contracts: F017 file API stubbed with pre-scanned fixtures; F006, F007, F008, F009, and F013 services exercised in-process against the real schema; in-memory outbox recorder; worker handlers invoked directly with a kill switch between tabs and between chunks; no test opens a socket to an external product
- Parallel isolation: one schema and one object-storage prefix per test worker, tenant id per test
- Targeted command: `cargo xtask test-feature F071`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F071/`

## 6. Acceptance criteria

```gherkin
Feature: Migration import

Scenario: The dry run creates nothing
  Given a sheet editor uploads a 12-tab workbook to folder "Delivery"
  When analysis finishes and they open the migration
  Then the preview lists 12 tabs with inferred column types, row counts, and issues
  And folder "Delivery" contains no new sheet

Scenario: An ambiguous column blocks commit until it is decided
  Given a column whose values parse as both number and duration above 0.80
  When the editor commits without an override and without accepting ambiguity
  Then the response is 400 invalid with field_errors.column_overrides naming that column map
  And no sheet is created

Scenario: A failed tab leaves nothing half-created
  Given a 5-tab migration whose third tab fails three times during row streaming
  When the commit job finishes
  Then the third tab is marked failed and its sheet and rows are soft-deleted
  And the other four tabs are committed with their full row counts

Scenario: Commit resumes after a worker crash without duplicate rows
  Given a committing tab of 5,000 rows whose worker is killed after chunk 2
  When another worker claims the migration
  Then it resumes from cursor row 2000 and the sheet holds exactly 5,000 rows
  And migration.completed.v1 is in the outbox

Scenario: What could not come over is visible rather than silent
  Given a tab using a formula function OpsHub does not support and a conditional format
  When the editor opens the issues panel
  Then it lists unsupported_formula_function naming the function and the cell
  And it lists conditional_format_dropped for that tab

Scenario: A viewer cannot start a migration
  Given a viewer on folder "Delivery"
  When they POST /api/v1/migrations targeting it
  Then the response is 403 denied and no migration is created
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F007 (the twelve column types, settings, options, and validation that inference targets), F010 (the xlsx and CSV parsing primitives, object-storage job conventions, and the chunked resumable commit pattern this feature reuses rather than reinvents), F013 (the view kinds, filter AST, sorts, and column visibility a source view maps onto); decisions sections 2, 2.1, 3, 4, 5, 7, 9; contracts row F071
- Blocks: none
- Conflicts with: none (disjoint owned paths)
- External dependencies: S3-compatible object storage for the source file and extracted entries; F017 for upload and scanning; F004 worker runtime, quotas, and dead letters; no network call to any external product on any code path
- Risks and mitigations: inference is confidently wrong on sparse columns, so confidence is surfaced per column and ambiguity blocks commit rather than defaulting silently; a large workbook can exhaust memory, so both parsing and commit stream and the memory ceiling is asserted in the performance lane; source products change their export shapes, so each reader validates the parts it depends on and fails with `unsupported_source` rather than mis-parsing; a partially committed migration is the worst outcome, so a failed tab is rolled back and `DELETE` removes every sheet the migration created; zip handling is an attack surface, so entry paths and expansion size are checked before extraction
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F007, F010, and F013 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F071/`
- [ ] Migration file name and owned paths claimed
- [ ] Fixture factory `testing/fixtures/migration.rs`, workbook and archive generators, per-worker object-storage prefix, and schema-per-worker isolation available in `testing/harness/`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit and outbox events verified for create, analyze, override, waive, commit, rollback, and delete
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets`, `check-contracts`, `check-persistence`, and `check-design` pass
- [ ] Rollback verified: disable `F071_FEATURE`, run down migration on an empty tenant, worker handlers unregistered
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Teams can bring an entire Excel or Google Sheets workbook, Smartsheet export, or Airtable export into OpsHub as structure: one sheet per tab with typed columns, views, hierarchy, and cross-tab links, reviewed in a full dry run with per-column confidence and an explicit list of what could not be brought over, and created only after the review is committed.
- Migration adds `migrations`, `migration_sheets`, `migration_column_maps`, and `migration_issues`; rollback drops them. Feature is off by default behind `F071_FEATURE`.
