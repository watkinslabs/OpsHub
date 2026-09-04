---
id: F008
type: feature
status: planned
priority: P0
owner: platform
estimate: 8
target_milestone: M1
parent_epic: E002
depends_on: [F007]
blocks: [F010, F013, F021, F058, F060, F061]
conflicts_with: []
parallel_safe: true
owned_paths: [crates/persistence/src/grid/**, crates/domain/src/grid/**, services/api/src/grid/**, apps/web/src/features/grid/**, services/api/migrations/*_grid_*.sql, testing/features/F008/**]
feature_flag: F008_FEATURE
flag_default: off
branch: f008-grid-editing
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 6, 9
- Capability contract: `docs/capability-contracts.md` row F008

# F008 — Grid editing

## 1. Identity and dates

- Branch: `f008-grid-editing`
- Capability area: core work record engine (spec 5.1 WORK-01, WORK-02, grid low-level bullet; 5.2 DATA-01 change events; section 4 record rules; section 6 scale targets)
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 6; `docs/capability-contracts.md` row F008
- Aggregate: `cell-edit`
- Module slug: `grid`; aggregate: `cell-edit`

## 2. Requirement specification

### Problem and user outcome

F006 gives a team rows and F007 gives them typed columns, but editing is still one row at a time through a form-like patch. Teams work in a grid: they type into cells, paste blocks from spreadsheets, drag a fill handle, select ranges, undo mistakes, resize and freeze columns, and fix hundreds of cells at once. Every one of those edits must respect column validation, optimistic concurrency, idempotency, audit, and the change events that views, formulas, search, and automation consume.

As a sheet editor, I want to edit cells directly in a virtualized grid with paste, fill, multi-select, undo/redo, per-user column layout, bulk edit, and cell history, so that maintaining a 100,000-row sheet feels like a spreadsheet while every change stays typed, versioned, and auditable.

### Functional requirements

- **FR-F008-01:** `PATCH /api/v1/sheets/{sheet_id}/cells` accepts `{ edits: [{ row_id, column_id, value, expected_row_version }] }` with 1 to 200 edits; each edit is normalized and validated by the F007 column type, and the response lists a per-cell result of `applied` with the new `row_version` and `display`, `invalid` with the F007 validation code, or `conflict` with `current_row_version`; applied cells are committed even when other cells in the same request fail, and the summary counts `applied`, `invalid`, `conflict` are returned.
- **FR-F008-02:** Every applied cell edit increments the row `version`, writes one `cell_history` row with previous and new raw values, writes one `audit_events` row, and publishes `cell.updated.v1` carrying `row_id`, `column_id`, `version`, `changed_fields`, and `correlation_id`.
- **FR-F008-03:** `POST /api/v1/sheets/{sheet_id}/cells/bulk` accepts `{ mode: set|fill|clear, selection: { row_ids | filter }, column_ids, value?, source_cell? }` for up to 5,000 target cells; requests of 5,000 cells or fewer apply synchronously and return the batch result, larger selections return `invalid` with `field_errors.selection = "too_large"`.
- **FR-F008-04:** `POST /api/v1/sheets/{sheet_id}/rows/bulk` accepts `{ mode: set|clear, selection, cells: { column_id: value } }` for up to 1,000 rows, applies the same values to every selected row in one transaction, emits one `rows.bulk-updated.v1` event with the affected `row_ids`, and returns per-row versions.
- **FR-F008-05:** Every `PATCH cells`, `cells/bulk`, and `rows/bulk` call creates one `edit_batches` row for the actor plus one `cell_history` row per changed cell carrying `previous_raw`, `new_raw`, and the row version, which together are the batch's inverse; each actor keeps at most 50 undoable batches per sheet and the oldest batch is trimmed when a 51st is created.
- **FR-F008-06:** `POST /api/v1/sheets/{sheet_id}/undo` applies the inverse of the actor's most recent not-undone batch, read as that batch's `cell_history` rows, only when every affected cell still carries the row version recorded on its history row; a mismatch returns `conflict` listing the changed cells and leaves the batch on the stack; success sets `undone_at`, publishes `edit.undone.v1`, and returns the restored cells.
- **FR-F008-07:** `POST /api/v1/sheets/{sheet_id}/redo` re-applies the most recently undone batch under the same version check, clears `undone_at` and sets `redone_at`; any new edit by the actor after an undo discards the redo stack.
- **FR-F008-08:** `GET /api/v1/sheets/{sheet_id}/changes?since=<sheet_change_version>&limit=` returns the ordered change feed `{ changes: [{ row_id, column_id, row_version, actor_id, occurred_at, raw, display }], next_since, layout }` with `limit` up to 1,000, so an open grid can refresh without reloading the sheet.
- **FR-F008-09:** `GET /api/v1/cells/{row_id}/{column_id}/history` returns the cell's `cell_history` entries newest first with cursor paging, each carrying `version`, `previous_raw`, `new_raw`, `actor_id`, `batch_id`, and `occurred_at`; the actor needs read access to the row.
- **FR-F008-10:** The `layout` object `{ column_widths, column_order, hidden_columns, frozen_column_count }` sent as an optional top-level field of `PATCH /api/v1/sheets/{sheet_id}/cells` upserts the actor's `sheet_user_layouts` row and replaces its per-column `sheet_user_column_layouts` rows in the same request and transaction (an `edits` array may be empty when only `layout` is sent), and `GET /api/v1/sheets/{sheet_id}/changes` returns the actor's current `layout`; the primary column cannot be hidden and `frozen_column_count` is 0 to 5.
- **FR-F008-11:** Pasting a tab-separated block into the grid maps each column of the block to the target columns in visible order, converts values through the F007 normalizer, submits one `PATCH cells` request per 200 cells, and marks cells that failed validation with the returned code without blocking the rest of the paste.
- **FR-F008-12:** The fill handle extends the selected cell across a range using `mode: fill`; numeric and date sequences are continued from the source cell, text is repeated.
- **FR-F008-13:** The grid virtualizes rows and columns so that a 100,000-row, 500-column sheet mounts with at most 60 rendered rows and 40 rendered columns, and supports range selection with Shift+Arrow and Shift+Click plus non-contiguous selection with Ctrl+Click.
- **FR-F008-14:** Column resize, reorder, hide, and freeze are available to every tenant on every plan and are never gated by an entitlement; they are implemented on the F062 grid wrapper against this feature's `layout` field, backed by `sheet_user_column_layouts`, which remains the single store for them. They are applied immediately in the grid and persisted through the `layout` field within 1 s of the last change, so the layout is restored for that user on the next visit and is never shared with other users.
- **FR-F008-15:** An actor without `sheet-editor` on the sheet receives `denied` for every mutation route, commenters and viewers see read-only cells with the denied state on edit affordances, and a foreign-tenant actor receives `not_found` for every route.
- **FR-F008-16:** Every mutation route requires `Idempotency-Key`; a replay with the same body returns the stored response and performs no second write, a replay with a different body returns `conflict`.

### Non-functional requirements

- **NFR-F008-01 Performance:** single-cell `PATCH cells` responds in under 800 ms p95; a 5,000-cell bulk request completes in under 5 s; `GET changes` for 1,000 changes responds in under 500 ms p95; the grid scrolls a 100,000-row sheet at 60 fps with no frame over 32 ms (spec section 6).
- **NFR-F008-02 Security/privacy:** 1,000 concurrent editors in one tenant produce no lost updates (every write is version-checked inside the transaction); tenant isolation is enforced by a `tenant_id` predicate on every query; viewer, commenter, cross-tenant, and guest-link negatives are in the harness; server-side F007 validation cannot be bypassed by the client.
- **NFR-F008-03 Accessibility:** the grid uses `role="grid"` with `aria-rowindex` and `aria-colindex` on virtualized cells, is fully keyboard operable (arrows, Tab, Enter, Escape, Shift+Arrow, Ctrl+Z, Ctrl+Y), announces undo/redo and paste results through a live region, and passes axe with no serious violations (WCAG 2.2 AA).
- **NFR-F008-04 Reliability/observability:** each request has a tracing span with `tenant_id`, `sheet_id`, `batch_id`, `cell_count`, and `correlation_id`; metrics `grid_cells_applied_total`, `grid_cells_conflict_total`, `grid_undo_conflict_total`; outbox failures roll back the write and surface in `outbox_events` metrics.

### Scope

Included: cell patch with per-cell results, bulk cell and row edits, undo/redo stack, change feed, cell history, per-user layout persistence, virtualized grid with inline editors, paste, fill, multi-select, column resize/reorder/hide, frozen columns, bulk edit dialog, cell history popover, audit, idempotency, outbox events.

Excluded: column definitions and validation rules (F007), row hierarchy and links (F009), formula evaluation (F035), saved views and filters (F013), live patches over WebSocket (F046), offline queued edits (F058), conditional formatting (F060), comments on cells (F016).

## 3. UX specification

- Entry points: sheet page route `/w/{workspace_id}/sheets/{sheet_id}?mode=grid` from F006 replaces the read-only `GridView` with the editable `VirtualGrid` when `F008_FEATURE` is on; row context menu `Bulk edit`; cell context menu `History`.
- Primary flow: open a sheet, click a cell, type, press Enter, the cell shows the new display value and the row version updates; select A2:C40, paste from a spreadsheet, cells fill in and any invalid cell shows a red corner with the validation code; drag the fill handle down 20 rows, values continue; press Ctrl+Z, the paste reverts with a live announcement "Undid 117 cells"; drag a column edge to resize, drag a header to reorder, choose `Freeze up to here`, reload, layout persists.
- Loading: skeleton rows in the viewport; Empty: `Add row` call to action; Error: inline banner with `correlation_id` and retry; Success: no toast for single edits, toast for bulk results "412 cells updated, 3 invalid"; Stale/conflict: the conflicting cell gets a red outline with tooltip "Changed by Ada Lovelace, reload to edit" and a `Reload` action that fetches the change feed; Denied: cells are read-only with a lock badge on hover; Offline: editing disabled with the offline badge, no queueing in this feature.
- Bulk edit dialog: choose target column(s), mode set/clear, value editor matching the column type, preview count "Will update 812 rows", confirm; results toast with counts and a `Show invalid` filter.
- Responsive: the primary column and frozen columns stay pinned horizontally; under 768 px only the primary column is frozen and the bulk dialog is full screen.
- Keyboard: arrows move focus, Enter or F2 edits, Escape cancels, Tab moves right, Shift+Arrow extends selection, Ctrl+A selects all, Ctrl+C/Ctrl+V copy and paste, Ctrl+D fills down, Ctrl+Z/Ctrl+Y undo and redo, Delete clears the selection, Alt+Shift+H hides the focused column; focus ring uses the shared token; motion respects `prefers-reduced-motion`.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062), Lucide icons `Pencil`, `Undo2`, `Redo2`, `History`, `Columns3`, `Snowflake`, `EyeOff`, `ListChecks`; spacing and color from `apps/web/src/design/tokens.css`.

- Design: `design/artboards/Main.dc.html` on the canvas indexed by `design/canvas.json`. The ticket is the contract and the artboard is the picture; when they disagree the ticket wins.

## 4. Technical specification

Canonical contract: `docs/capability-contracts.md` row F008; every route and event below is reproduced from that row.

### Rust backend

- Domain entities in `crates/domain/src/grid/`: `CellEdit { row_id, column_id, value: Value, expected_row_version }`, `CellEditResult { row_id, column_id, outcome: Applied { row_version, display } | Invalid { code } | Conflict { current_row_version } }`, `EditBatch { id, tenant_id, sheet_id, actor_id, kind: Patch|BulkCells|BulkRows|Undo|Redo, cell_count, undone_at, redone_at, version }` whose inverse is loaded as `Vec<CellHistoryEntry>` for the batch, `CellHistoryEntry { row_id, column_id, version, previous_raw, new_raw, actor_id, batch_id, occurred_at }`, `UserLayout { frozen_column_count: u8, columns: Vec<UserColumnLayout { column_id, width, position, hidden }> }` projected to and from the same `{ column_widths, column_order, hidden_columns, frozen_column_count }` API shape, `ChangeFeedEntry`.
- Data access (decision 2.1): `CellHistoryRepository` (`cell_history`), `EditBatchRepository` (`edit_batches`), and `SheetUserLayoutRepository` (`sheet_user_layouts`, `sheet_user_column_layouts`) in `crates/persistence/src/grid/`; cells, rows, and `sheets.change_version` are written through the F006 `CellRepository`, `RowRepository`, and `SheetRepository`, so no table has two writers. The use cases below depend on those repository traits and one shared `UnitOfWork` per request; `crates/domain/src/grid/` and `services/api/src/grid/` contain no SQL, and the locking read, the change feed, and the undo lookup are named repository queries (`lock_rows_for_edit`, `changes_since`, `inverse_for_batch`).
- Use cases: `patch_cells`, `bulk_edit_cells`, `bulk_edit_rows`, `undo_batch`, `redo_batch`, `list_changes`, `list_cell_history`, `save_user_layout`, `resolve_selection` (row IDs or F013-compatible filter to row set, capped at 1,000 rows or 5,000 cells).
- API endpoints (`services/api/src/grid/`): `PATCH /api/v1/sheets/{sheet_id}/cells`, `POST /api/v1/sheets/{sheet_id}/cells/bulk`, `POST /api/v1/sheets/{sheet_id}/rows/bulk`, `GET /api/v1/sheets/{sheet_id}/changes`, `POST /api/v1/sheets/{sheet_id}/undo`, `POST /api/v1/sheets/{sheet_id}/redo`, `GET /api/v1/cells/{row_id}/{column_id}/history`. DTOs `PatchCellsRequest { edits, layout? }`, `PatchCellsResponse { results, summary, batch_id }`, `BulkCellsRequest`, `BulkRowsRequest`, `BulkResponse { batch_id, applied, invalid, conflict, row_versions }`, `UndoRedoResponse { batch_id, restored: Vec<CellEditResult> }`, `ChangesResponse { changes, next_since, layout }`, `Page<CellHistoryEntry>`.
- Events: `cell.updated.v1` (one per applied cell in `patch_cells`), `cells.bulk-updated.v1` (one per bulk cell batch with `row_ids`, `column_ids`, `cell_count`), `rows.bulk-updated.v1` (one per bulk row batch), `edit.undone.v1` (undo and redo, with `kind`). Payload per contract conventions with `changed_fields`.
- Authorization: `sheet-editor` on the sheet for every mutation; `sheet-viewer` for `changes` and `history`; resource ACL inherits from the sheet, workspace, and folder; explicit deny wins; no access maps to `not_found`.
- Validation: each edit value passes `columns::normalize(column, raw)` from F007 before write; `edits` 0–200 (0 only with `layout`), bulk cells ≤ 5,000, bulk rows ≤ 1,000, `limit` for changes 1–1,000, `frozen_column_count` 0–5, hidden columns cannot include `is_primary`. Idempotency reuses `idempotency_keys(tenant_id, key, request_hash, response)` for 24 hours. Concurrency: `expected_row_version` is compared inside `RowRepository::lock_rows_for_edit`, whose `SELECT ... FOR UPDATE` lives in `crates/persistence`; a whole bulk request uses one transaction and per-row version checks.
- Error mapping: `GridError::VersionMismatch → per-cell conflict (200 with results)` for `patch_cells`, `GridError::UndoStale → 409 conflict`, `GridError::NothingToUndo → 409 conflict` with `code: conflict` and `reason: "empty_stack"`, `GridError::SelectionTooLarge → 400 invalid`, `ColumnError::Validation → per-cell invalid`, `AuthzError::Denied → 403 denied`, unknown sheet, row, or foreign tenant → `404 not_found`.

### Interface

Exact shapes. Every field gives its JSON name, type, whether it is required, and the constraint that
makes it invalid. `T?` is nullable; an absent optional field and an explicit `null` mean the same
thing. Ids are UUIDv7 strings, timestamps are RFC 3339 UTC. Unlisted fields are rejected with
`400 invalid`. `CellValue` and its `RawValue`, `ValidationCode` and per-type null semantics are
F007's; `Page<T>` and the opaque cursor are F028's `{ items, next_cursor, has_more, total? }`; the
error codes are the shared six. Every mutation requires `Idempotency-Key`.

**`PatchCellsRequest`** — `PATCH /api/v1/sheets/{sheet_id}/cells`

| Field | Type | Required | Constraint |
|---|---|---|---|
| `edits` | CellEdit[] | yes | 0–200; 0 only when `layout` is present, 201 is `400 invalid` with `field_errors.edits = "too_many"`; the same `(row_id, column_id)` twice is `400 invalid` with `field_errors.edits = "duplicate_cell"` |
| `layout` | UserLayout? | no | upserts the actor's layout in the same transaction (FR-F008-10) |

**`CellEdit`**

| Field | Type | Required | Constraint |
|---|---|---|---|
| `row_id` | uuid | yes | a live row of `sheet_id`; unknown or foreign-tenant → the edit result is `invalid` with code `not_found` and no row is disclosed |
| `column_id` | uuid | yes | a live column of `sheet_id`; a `formula` or `link` column is `invalid` with code `read_only` (F007 FR-F007-15), a rolled-up parent cell is `invalid` with code `rolled_up` (F009 FR-F009-08) |
| `value` | RawValue? | yes | F007's raw form for that column type; `null` clears the cell; the field must be present, so a cleared cell is explicit |
| `expected_row_version` | integer | yes | compared inside `lock_rows_for_edit`; a mismatch is a per-cell `conflict`, not a request failure |

**`CellEditResult`** — one per submitted edit, in request order

| Field | Type | Notes |
|---|---|---|
| `row_id` / `column_id` | uuid | echoes the edit |
| `outcome` | `"applied" \| "invalid" \| "conflict"` | the discriminator; the fields below are conditional on it |
| `row_version` | integer | `applied` only: the row's new version, which the client sends as the next `expected_row_version` |
| `value` | CellValue | `applied` only: the stored cell with its `normalized`, `display` and `validation` |
| `code` | ValidationCode | `invalid` only: F007's code, or `read_only`, `rolled_up`, `not_found` |
| `message` | string? | `invalid` only: the rule message when the column defines one |
| `current_row_version` | integer | `conflict` only: the version the row actually holds, so the client can refetch and retry |

A partial failure is the normal case, not an error: applied cells commit even when others in the same
request fail (FR-F008-01), so the HTTP status stays `200` and the caller branches on `outcome` per
cell. An `invalid` or `conflict` cell leaves the stored cell untouched and writes no `cell_history`
row, so the batch inverse covers exactly the applied cells.

**`PatchCellsResponse`**

| Field | Type | Notes |
|---|---|---|
| `batch_id` | uuid? | the `edit_batches` row; `null` when nothing applied, since an empty batch is not pushed onto the undo stack |
| `results` | CellEditResult[] | one per submitted edit, request order |
| `summary` | `{ applied: integer, invalid: integer, conflict: integer }` | counts over `results` |
| `sheet_change_version` | integer | the sheet's `change_version` after the write; pass it as `since` to the change feed |
| `layout` | UserLayout? | present only when the request carried `layout` |

**`Selection`** — exactly one of the two fields, else `400 invalid` with `field_errors.selection`

| Field | Type | Required | Constraint |
|---|---|---|---|
| `row_ids` | uuid[] | one of | 1–1,000 live rows of the sheet |
| `filter` | string | one of | F028's filter grammar, resolved by `resolve_selection`; a resolved set over the route cap is `400 invalid` with `field_errors.selection = "too_large"` |

**`BulkCellsRequest`** — `POST /api/v1/sheets/{sheet_id}/cells/bulk`

| Field | Type | Required | Constraint |
|---|---|---|---|
| `mode` | `"set" \| "fill" \| "clear"` | yes | `set` needs `value`, `fill` needs `source_cell`, `clear` takes neither |
| `selection` | Selection | yes | `row_ids.len() * column_ids.len()` ≤ 5,000 |
| `column_ids` | uuid[] | yes | 1–500 live, cell-writable columns of the sheet |
| `value` | RawValue? | with `set` | one raw value normalized per target column; a value invalid for a column marks those cells `invalid` rather than failing the request |
| `source_cell` | `{ row_id, column_id }`? | with `fill` | the cell the sequence continues from (FR-F008-12); its column must be in `column_ids` |

**`BulkRowsRequest`** — `POST /api/v1/sheets/{sheet_id}/rows/bulk`: `{ mode: "set" | "clear",
selection, cells: map<uuid, RawValue?> }` where the map is keyed by column id, 1–500 entries, and the
selection resolves to at most 1,000 rows; every selected row gets the same values in one transaction.

**`BulkResponse`** — both bulk routes

| Field | Type | Notes |
|---|---|---|
| `batch_id` | uuid? | `null` when nothing applied |
| `applied` / `invalid` / `conflict` | integer | counts, not per-cell rows, because a 5,000-cell response would be unusable |
| `results` | CellEditResult[] | only the cells whose `outcome` is not `applied`, so a client can show what failed |
| `row_versions` | map<uuid, integer> | new version per touched row |
| `sheet_change_version` | integer | |

**`UserLayout`** — the actor's `sheet_user_layouts` row plus its `sheet_user_column_layouts` rows,
assembled in column `position` order; it is per user and never shared (FR-F008-14)

| Field | Type | Required | Constraint |
|---|---|---|---|
| `column_widths` | map<uuid, integer> | no | 40–1,000 px per column of this sheet |
| `column_order` | uuid[] | no | column ids of this sheet, no duplicates; columns absent from the list keep their sheet order after the listed ones |
| `hidden_columns` | uuid[] | no | may not contain the primary column, else `400 invalid` with `field_errors.layout = "primary_hidden"` |
| `frozen_column_count` | integer | no | 0–5, default 0 |

**`ChangesResponse`** — `GET /api/v1/sheets/{sheet_id}/changes?since=&limit=`, `since` an integer
`sheet_change_version` (omitted means from the sheet's oldest retained change), `limit` 1–1,000
default 200

| Field | Type | Notes |
|---|---|---|
| `changes` | ChangeEntry[] | ascending by `row_version` then `occurred_at`; this feed is not `Page<T>` because it is versioned, not cursored |
| `next_since` | integer | pass as the next `since`; equal to `since` when nothing changed |
| `layout` | UserLayout | the actor's current layout, so a reconnecting grid needs one call |

**`ChangeEntry`** `{ row_id: uuid, column_id: uuid, row_version: integer, actor_id: uuid,
occurred_at: timestamp, value: CellValue }`. A row deleted since `since` appears once with
`column_id` null and `value.raw` null.

**`CellHistoryEntry`** — `GET /api/v1/cells/{row_id}/{column_id}/history`, `Page<CellHistoryEntry>`
newest first by `occurred_at`, `limit` 1–100 default 50

| Field | Type | Notes |
|---|---|---|
| `version` | integer | the row version this change produced |
| `previous_raw` / `new_raw` | RawValue? | F007 raw forms; `previous_raw` is `null` for the first write |
| `actor_id` | uuid | |
| `batch_id` | uuid | groups every cell of one request |
| `occurred_at` | timestamp | |

**Undo and redo.** `POST /api/v1/sheets/{sheet_id}/undo` and `.../redo` take an empty body `{}`; any
field is `400 invalid`. There is no batch id parameter: the target is the actor's most recent
not-undone batch for undo and most recently undone batch for redo, so two clients cannot disagree
about the stack. `UndoRedoResponse`

| Field | Type | Notes |
|---|---|---|
| `batch_id` | uuid | the batch that was inverted |
| `kind` | `"patch" \| "bulk_cells" \| "bulk_rows"` | the kind of the original batch |
| `restored` | CellEditResult[] | one per cell of the inverse, all with outcome `applied` |
| `sheet_change_version` | integer | |

**The inverse.** `edit_batches` stores no payload. A batch's inverse is its `cell_history` rows read
by `batch_id`: applying `previous_raw` to each `(row_id, column_id)` undoes the batch, applying
`new_raw` redoes it, and each row's recorded `version` is the version the cell must still hold. Undo
is all-or-nothing: if any affected cell has moved past its recorded version, the response is
`409 conflict` with `{ code: "conflict", reason: "stale_cells", cells: [{ row_id, column_id,
expected_version, current_row_version }] }`, nothing is written, and the batch stays on the stack
(FR-F008-06). An empty stack is `409 conflict` with `reason: "empty_stack"`. Undo and redo each
create their own `edit_batches` row of kind `undo` or `redo` and their own `cell_history` rows, so
the audit trail is append-only and an undo is itself undoable.

**Status codes**

| Code | Produced by |
|---|---|
| `200` | every route, including a patch where every cell was `invalid` or `conflict` — per-cell outcomes are results, not statuses |
| `400 invalid` | over 200 edits, a duplicate cell in one request, a selection over 5,000 cells or 1,000 rows, a malformed filter, `frozen_column_count` outside 0–5, a width outside 40–1,000, hiding the primary column, a bulk request whose `mode` and payload disagree, an unlisted field |
| `403 denied` | a viewer or commenter on any mutation route |
| `404 not_found` | unknown or soft-deleted sheet, unknown row or column on the history route, and every foreign-tenant id on every route |
| `409 conflict` | `stale_cells` on undo or redo, `empty_stack`, `Idempotency-Key` replayed with a different body |
| `429 rate_limited` | tenant write quota on bulk routes |
| `502 unavailable` | outbox publish failed; the whole transaction is rolled back and no cell is applied |

### Use case signatures

In `crates/domain/src/grid/`. Each takes `ctx` carrying tenant, actor and correlation id, takes a
`UnitOfWork` to write or a repository to read, never a pool or a connection, and returns the shared
`DomainError`.

```rust
fn patch_cells(ctx: &Ctx, uow: &mut UnitOfWork, sheet: SheetId, req: PatchCells) -> Result<PatchCellsOutcome, DomainError>;
fn bulk_edit_cells(ctx: &Ctx, uow: &mut UnitOfWork, sheet: SheetId, req: BulkCells) -> Result<BulkOutcome, DomainError>;
fn bulk_edit_rows(ctx: &Ctx, uow: &mut UnitOfWork, sheet: SheetId, req: BulkRows) -> Result<BulkOutcome, DomainError>;
fn undo_batch(ctx: &Ctx, uow: &mut UnitOfWork, sheet: SheetId) -> Result<UndoOutcome, DomainError>;
fn redo_batch(ctx: &Ctx, uow: &mut UnitOfWork, sheet: SheetId) -> Result<UndoOutcome, DomainError>;
fn list_changes(ctx: &Ctx, repo: &dyn CellHistoryRepository, sheet: SheetId, since: ChangeVersion, limit: u16) -> Result<Changes, DomainError>;
fn list_cell_history(ctx: &Ctx, repo: &dyn CellHistoryRepository, row: RowId, column: ColumnId, page: Cursor) -> Result<Page<CellHistoryEntry>, DomainError>;
fn save_user_layout(ctx: &Ctx, uow: &mut UnitOfWork, sheet: SheetId, layout: UserLayout) -> Result<UserLayout, DomainError>;
fn resolve_selection(ctx: &Ctx, repo: &dyn RowRepository, sheet: SheetId, sel: Selection, cap: SelectionCap) -> Result<Vec<RowId>, DomainError>;
```

**Transaction boundaries.** One `UnitOfWork` per request, whatever the cell count. `patch_cells`
takes `lock_rows_for_edit` over the distinct `row_id` set in ascending id order — a fixed order, so
two concurrent batches over overlapping rows cannot deadlock — then within that boundary writes
`cells`, one `cell_history` row and one `sheets.change_version` increment per applied cell, the
`edit_batches` row, the `audit_events` row, the outbox enqueue, and the layout upsert when `layout`
was sent. That boundary is what makes the change feed monotonic: a reader polling `since` can never
observe a cell whose `change_version` increment has not committed. `bulk_edit_cells` and
`bulk_edit_rows` use the same single boundary for the whole selection, so a bulk edit is never half
applied even though individual cells may be reported `invalid`. `undo_batch` and `redo_batch` read
`inverse_for_batch` and re-check every recorded version inside the same transaction that writes the
reverted cells, which is what stops an undo from overwriting another editor's later change.

### PostgreSQL/SQLx

- Migration `*_grid_*.sql` creates `cell_history(id uuid pk, tenant_id uuid not null, row_id uuid not null, column_id uuid not null, version bigint not null, previous_raw jsonb, new_raw jsonb, actor_id uuid not null, batch_id uuid not null, occurred_at timestamptz not null)`, `edit_batches(id uuid pk, tenant_id, sheet_id, actor_id, kind text check (kind in ('patch','bulk_cells','bulk_rows','undo','redo')), cell_count int not null, undone_at timestamptz, redone_at timestamptz, version bigint not null default 1, created_at, created_by, updated_at, updated_by)`, `sheet_user_layouts(tenant_id, sheet_id, user_id, frozen_column_count smallint not null default 0 check (frozen_column_count between 0 and 5), version bigint not null default 1, updated_at, primary key (tenant_id, sheet_id, user_id))`, `sheet_user_column_layouts(tenant_id uuid not null, sheet_id uuid not null, user_id uuid not null, column_id uuid not null references columns(id) on delete cascade, width smallint check (width between 40 and 1000), position text collate "C", hidden bool not null default false, primary key (tenant_id, sheet_id, user_id, column_id), foreign key (tenant_id, sheet_id, user_id) references sheet_user_layouts(tenant_id, sheet_id, user_id) on delete cascade)`, and adds `sheets.change_version bigint not null default 0` through an additive `alter table`.
- Invariants: the per-user layout is rows, not three parallel `jsonb` structures: `column_widths`, `column_order`, and `hidden_columns` were a repeating group keyed by column id, so they become one `sheet_user_column_layouts` row per column with a real foreign key that disappears with the column, while `frozen_column_count` stays on the parent row; the API keeps the same `layout` object, assembled from those rows in column `position` order, so nothing externally visible changes. `edit_batches` no longer stores an `inverse` blob: the batch's `cell_history` rows already hold `previous_raw`, `new_raw`, and the row version per cell, so undo reads them by `batch_id` and there is one source of truth for a batch's effect instead of two. `cell_history.previous_raw` and `new_raw` stay `jsonb` because each is one user-defined typed cell value, never queried by key (decision 2). `cell_history(row_id, column_id, version)` unique; `edit_batches` foreign key to `sheets` with `on delete restrict`; at most 50 non-trimmed batches per `(sheet_id, actor_id)` enforced by the service, verified by a test; `sheets.change_version` increments once per applied cell inside the write transaction.
- Indexes: `cell_history(row_id, column_id, occurred_at desc)`, `cell_history(tenant_id, row_id)`, `cell_history(batch_id)` for the undo read, `sheet_user_column_layouts(tenant_id, sheet_id, user_id)` for the layout read and `sheet_user_column_layouts(column_id)` for column deletion, `edit_batches(sheet_id, actor_id, created_at desc) where undone_at is null`, `edit_batches(sheet_id, actor_id, undone_at desc) where undone_at is not null and redone_at is null`, `cells(sheet_change_version)` via a new column `cells.change_version bigint` for the feed query.
- Audit events: `cell.patch`, `cells.bulk`, `rows.bulk`, `edit.undo`, `edit.redo`, `layout.save` with field-level diffs; bulk audits store counts plus the batch ID instead of every cell.
- Retention/deletion: `cell_history` older than the tenant history retention (default 365 days) is purged by the F027 job; `edit_batches` older than 30 days are trimmed nightly; deleting a row soft-deletes it in F006 and leaves history readable until purge; migration rollback drops the four tables and the two added columns.

### React/TypeScript

- Routes: none new; `apps/web/src/features/grid/` exports `VirtualGrid` which the F006 `SheetPage` mounts in place of `GridView` when the flag is on. Components `VirtualGrid`, `GridHeaderRow`, `GridRow`, `GridCell`, `CellEditor` (per column type: text, number, currency, date, datetime, boolean, person, select, duration), `SelectionModel`, `ClipboardController`, `FillHandle`, `UndoRedoController`, `ColumnResizeHandle`, `ColumnHeaderMenu`, `FrozenColumnsPane`, `BulkEditDialog`, `CellHistoryPopover`, `ConflictOutline`.
- State: TanStack Query keys `['grid-rows', sheetId, cursor]`, `['grid-changes', sheetId, since]`, `['cell-history', rowId, columnId]`, `['grid-layout', sheetId]`; mutations `patchCells`, `bulkCells`, `bulkRows`, `undo`, `redo` update the cached rows and `version` from the response; the change feed polls every 15 s while the tab is visible and merges by row version.
- API client: generated `GridApi` from OpenAPI with `patchCells`, `bulkEditCells`, `bulkEditRows`, `undo`, `redo`, `listChanges`, `listCellHistory`.
- Optimistic updates: single-cell edits apply locally and reconcile with the per-cell result; `conflict` restores the server value and shows `ConflictOutline`; `invalid` keeps the typed raw value with the code badge; layout changes debounce 1 s then send `layout` with an empty `edits` array.
- Telemetry: `cell_edited`, `cells_pasted`, `fill_applied`, `edit_undone`, `edit_redone`, `bulk_edit_applied`, `layout_changed` with `sheet_id`, `cell_count`, and `outcome`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F008-01 through FR-F008-16 in `testing/features/F008/requirements/cases.md`
- [ ] Failure/edge-case tests: mixed applied/invalid/conflict patch, 201-edit request, 5,001-cell bulk, undo after another user changed a cell, redo stack discarded by a new edit, layout hiding the primary column, replay with mismatched body
- [ ] Permission-negative and tenant-isolation tests: viewer and commenter mutations `denied`, cross-tenant sheet, row, and history `not_found`, guest link cannot patch
- [ ] Rust unit tests: `crates/domain/src/grid/` inverse computation, stack trimming, selection resolution caps, fill sequence generation
- [ ] API contract/integration tests: every route above with success and each error code
- [ ] Database migration/constraint tests: history uniqueness, batch foreign key, layout check constraint, change_version increment, rollback
- [ ] React component tests: `VirtualGrid`, `CellEditor`, `ClipboardController`, `UndoRedoController`, `BulkEditDialog`, `CellHistoryPopover` states
- [ ] Browser E2E tests: type into cell, paste block, fill down, undo, resize and freeze persisted, bulk edit, conflict outline
- [ ] Accessibility tests: axe on the grid, keyboard-only editing and selection, live region announcements
- [ ] Performance/load tests: single-cell p95 under 800 ms, 5,000-cell bulk under 5 s, 1,000 concurrent editors lose no updates, 100,000-row scroll frame budget

### Fast fanout configuration

- Test harness path: `testing/features/F008/`
- Feature flag: `F008_FEATURE`
- Fixture/seed factory: `testing/fixtures/grid.rs` builds tenant, sheet with 12 typed columns (text, number, currency, date, datetime, boolean, person, select, duration, plus primary), 500 rows, editor, commenter, viewer, foreign tenant, and a second editor for conflicts
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, UTC
- Mock/stub contracts: outbox publisher recorded in memory; authz uses the real F003 engine with fixture bindings; F007 normalizer real
- Parallel isolation: one schema per test worker, tenant ID per test
- Targeted command: `cargo xtask test-feature F008`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F008/`

## 6. Acceptance criteria

```gherkin
Feature: Grid editing

Scenario: Patch cells with mixed outcomes
  Given a sheet with a number column "Budget" and rows at version 2
  When an editor patches three cells with values 10, "abc", and 30 where the third row is now at version 3
  Then the response reports one applied, one invalid with code type_mismatch, one conflict with current_row_version 3
  And exactly one cell.updated.v1 event and one cell_history row exist

Scenario: Undo respects other users' changes
  Given editor A pasted 100 cells creating one edit batch
  And editor B then changed one of those cells
  When editor A calls undo
  Then the response is 409 conflict listing the changed cell and no cell is reverted

Scenario: Viewer cannot edit
  Given a viewer on the sheet
  When they PATCH cells or POST cells/bulk
  Then the response is 403 denied and the grid shows read-only cells

Scenario: Layout persists per user
  Given editor A resized "Budget" to 240 px, hid "Notes", and froze 2 columns
  When editor A reloads and editor B opens the same sheet
  Then editor A sees the saved layout and editor B sees the default layout
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F007 (typed columns, normalizer, validation codes); decisions sections 2–4, 6; contracts row F008
- Blocks: F010, F013, F021, F058, F060, F061
- Conflicts with: none (disjoint owned paths)
- External dependencies: none
- Risks and mitigations: per-cell events on a 5,000-cell bulk would flood the outbox, so bulk routes emit one aggregate event and rely on the change feed for detail; an undo inverse for a large paste can be large, so a batch is capped at 5,000 cells and its `cell_history` rows are read in one indexed query by `batch_id`, and batches beyond 30 days are trimmed; the change feed depends on `sheets.change_version` being incremented in every F006 and F008 write path, verified by the database lane.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F007 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F008/`
- [ ] Migration file name and owned paths claimed
- [ ] Fixture factory and schema-per-worker isolation available in `testing/harness/`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for every mutation
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F008_FEATURE`, run down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Users can edit cells inline, paste and fill ranges, multi-select, undo and redo, bulk edit, view cell history, and keep a personal column layout with frozen columns.
- Migration adds `cell_history`, `edit_batches`, `sheet_user_layouts`, `sheet_user_column_layouts`, and change-version columns on `sheets` and `cells`; rollback drops them. Feature is off by default behind `F008_FEATURE`.
