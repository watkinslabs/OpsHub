---
id: F013
type: feature
status: planned
priority: P1
owner: platform
estimate: 8
target_milestone: M2
parent_epic: E003
depends_on: [F008, F011]
blocks: [F015, F050, F051, F055, F059]
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/views/**, crates/persistence/src/views/**, services/api/src/views/**, apps/web/src/features/views/**, services/api/migrations/*_views_*.sql, testing/features/F013/**]
feature_flag: F013_FEATURE
flag_default: off
branch: f013-views
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 6
- Capability contract: `docs/capability-contracts.md` row F013

# F013 — Views

## 1. Identity and dates

- Branch: `f013-views`
- Capability area: planning and visualization (spec 5.1 WORK-03, WORK-05, Card and Calendar/timeline bullets; section 4 View entity)
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 6; `docs/capability-contracts.md` row F013
- Aggregate: `view`
- Module slug: `views`

## 2. Requirement specification

### Problem and user outcome

A sheet holds the canonical rows, but a team needs to look at the same rows as a Kanban board, a calendar, or a timeline, with their own filters, sorts, and groupings, and share that arrangement with others without copying data. Today only the grid and the default board lanes exist (F006), and nothing is saved per user.

As a sheet member, I want to save named views of a sheet with filters, sorts, grouping, visible columns, and card, calendar, or timeline settings, and share them with people and groups, so that everyone plans from one record set through the presentation that fits their work.

### Functional requirements

- **FR-F013-01:** An actor with `sheet-viewer` on a sheet can create a view with `sheet_id`, `name` (1–120 chars), `kind` in `grid|card|calendar|timeline`, `visibility` in `private|sheet`, and typed `settings`; the response returns a UUIDv7 `id`, `version` 1, and `owner_id` equal to the actor; a sheet with 100 non-deleted views returns `invalid` with `field_errors.sheet_id = "view_limit"`. The wire `settings` object is unchanged: the repository decomposes it into `views` columns and the `view_sorts`, `view_columns`, `view_card_fields`, and `view_filter_columns` child tables on write, and composes it back on read.
- **FR-F013-02:** The request member `settings.filter` is a typed AST of `and`/`or` groups whose leaf conditions reference a column ID and an operator valid for that column type (`eq`, `neq`, `contains`, `in`, `is_empty`, `gt`, `lt`, `between`, `before`, `after`, `is_me`); an unknown column, a type-mismatched operator, or more than 50 leaf conditions returns `invalid` with `field_errors.settings.filter`. It is stored in `views.filter jsonb`: the AST is a user-authored tree of arbitrary shape and depth, it is never read by key in SQL, and every column it references is projected into `view_filter_columns` in the same transaction, so no query ever reaches into the JSON.
- **FR-F013-03:** Sorts are at most 5 ordered `{ column_id, direction }` rows in `view_sorts` (`position` 1–5, unique per column), `group_by` is `views.group_by_column_id` (one column or null), and the ordered visible column list is `view_columns` rows keyed by `position` and unique per column; unknown column IDs return `invalid`. The 5-sort limit is declarative: `position smallint check (position between 1 and 5)` with `primary key (view_id, position)`.
- **FR-F013-04:** Per-kind settings are typed columns on `views` with check constraints, so FR-F013-04's validation is declarative rather than service-only: a `card` view requires `lane_column_id`, accepts up to 8 ordered `view_card_fields` rows (`position smallint check (position between 1 and 8)`) and an optional `swimlane_column_id`; a `calendar` view requires either `date_column_id` or the pair `start_column_id`/`end_column_id` plus `calendar_mode` in `month|week|day`; a `timeline` view requires `start_column_id`, `end_column_id`, `timeline_zoom` in `day|week|month|quarter`, and an optional `color_by_column_id`. The service still validates what a check cannot express — the lane column must be `select` and the date columns `date|datetime` per `columns.type` — and returns the same `400 invalid` with `field_errors.settings.card.lane_column_id`, `.calendar`, or `.timeline`. A `gantt` settings block is stored opaquely in `views.gantt_settings jsonb null`: it is an F012-owned payload this feature never reads, queries, or constrains.
- **FR-F013-05:** `GET /api/v1/views/{id}/rows` applies the view's `filter` AST, its `view_sorts` rows, and `group_by_column_id` server-side over the F008 row query, returns cursor pages with `limit` 1–500 in `group` then `sort` order, includes only the `view_columns` visible columns plus the primary column, and never returns rows or cells the actor cannot read.
- **FR-F013-06:** Calendar rendering resolves the display timezone from `sheet_schedule_settings.timezone` (F011) and falls back to the user locale timezone (F049); rows with a recurrence rule render every occurrence in range read-only, and the row list for calendar and timeline kinds accepts `range_start` and `range_end` (≤ 366 days apart).
- **FR-F013-07:** Dragging a card between lanes calls `PATCH /api/v1/sheets/{sheet_id}/cells` (F008) for the lane column with `If-Match`, and dragging a bar or event on calendar or timeline calls `POST /api/v1/rows/{id}/reschedule` (F011); a `conflict` response rolls the item back and shows the stale banner.
- **FR-F013-08:** `PATCH /api/v1/views/{id}` updates `name`, `visibility`, `is_default`, and `settings` with `If-Match`; only the view owner or a `sheet-editor` may update a `sheet` view, only the owner may update a `private` view, and marking `is_default` clears the previous default in the same transaction. A `settings` patch is a full replace of the view's projection rows — `view_sorts`, `view_columns`, `view_card_fields`, `view_filter_columns` — plus the typed columns and `filter`, written with the version bump in one transaction.
- **FR-F013-09:** `DELETE /api/v1/views/{id}` soft-deletes the view and its shares; the default view cannot be deleted (`invalid` with `field_errors.is_default`); a deleted view returns `not_found` on every route.
- **FR-F013-10:** `POST /api/v1/views/{id}/share` by the owner creates a `view_shares` row with `principal_kind` in `user|group`, a non-null `principal_id`, `role` in `viewer|editor`, and an optional `expires_at`; the response contains the share ID and publishes `view.shared.v1`; a non-owner receives `denied`. F013 mints no tokens and serves no unauthenticated route: public link sharing of a view is F036 `POST /api/v1/share-links` with `target_kind: view`, served by `GET /public/share/{token}`, and arrives with F036 in M3. F013's obligation to that actor is FR-F013-05: the row read filters by the actor's permissions however that actor authenticated.
- **FR-F013-11:** `GET /api/v1/sheets/{sheet_id}/views` lists views the actor may see: their own `private` views, all `sheet` views, and views shared to them or their groups, with cursor pagination, `filter` by `kind`, and `sort` by `name` or `updated_at`; foreign-tenant or unshared private views return `not_found`.
- **FR-F013-12:** Every mutation requires `Idempotency-Key`, writes an `audit_events` row, and publishes `view.created.v1`, `view.updated.v1`, `view.deleted.v1`, or `view.shared.v1` through the outbox with `changed_fields`.
- **FR-F013-13:** The web app renders `CardView`, `CalendarView`, and `TimelineView` from the saved view, a `ViewSwitcher` listing accessible views with the default first, a `ViewSettingsPanel` with `FilterBuilder`, and a `ShareViewDialog`; the route is `/w/:workspaceId/sheets/:sheetId/views/:viewId`.
- **FR-F013-14:** Exporting a view calls `POST /api/v1/exports` (F010) with `view_id`, and the export job applies the same filter, sort, visible columns, and permission filtering as the row list.

### Non-functional requirements

- **NFR-F013-01 Performance:** `GET /views/{id}/rows` with a 3-condition filter and 2 sorts over a 100,000-row sheet responds in under 500 ms p95 for a 500-row page; a card lane move (cell patch) responds in under 800 ms p95; calendar month range over 5,000 dated rows renders in under 500 ms p95.
- **NFR-F013-02 Security/privacy:** row and cell permission filtering runs in the service layer on every view row read; an F036 scoped-token actor reading a shared view is filtered by the same service-layer path as a session actor and can never write; cross-tenant view IDs return `not_found`.
- **NFR-F013-03 Accessibility:** card, calendar, and timeline pass axe with zero serious violations; lane moves, calendar day changes, and timeline bar moves are keyboard operable and announced through a live region; motion respects `prefers-reduced-motion`.
- **NFR-F013-04 Reliability/observability:** every view read carries a span with `tenant_id`, `sheet_id`, `view_id`, and `correlation_id`; filter compile errors are counted in `views_filter_compile_errors_total`; outbox publish failure never loses the write.

### Scope

Included: saved view CRUD, typed filter AST, sorts, grouping, visible columns, card/calendar/timeline settings and rendering, default view, personal versus sheet visibility, user and group shares, row filtering for F036 scoped-token actors, server-side filtered row list, drag interactions delegated to F008 and F011, view export handoff, audit and events.

Excluded: share links, guest invitations, and every unauthenticated token route for views (F036 owns the single share-link system; F013 duplicates none of it), Gantt rendering and dependency arrows (F012), restricted field-level dynamic views (F050), embed and public publication rendering beyond the link token (F059), conditional formatting (F060), multi-source calendar app (F055), report views (F021), the grid editor itself (F008).

## 3. UX specification

- Entry points: sheet header `ViewSwitcher` dropdown with `New view`; route `/w/{workspace_id}/sheets/{sheet_id}/views/{view_id}`; `Share` button in the view header; `Export` in the view overflow menu.
- Primary flow: open a sheet, choose `New view`, pick `Card`, select the `Status` lane column, save — the panel sends one `settings` object and the server stores the lane column as `views.lane_column_id` and each sort, visible column, and card field as its own ordered row, so the panel refuses a 6th sort or a 9th card field with the same inline message it shows today; cards appear in lanes per status; drag a card from `Backlog` to `Doing`, the API confirms and the card stays; switch to a `Calendar` view keyed on `Due`, drag an event to the next week, the row is rescheduled; open `Share`, add a group as viewer, and see the group's members gain access.
- Loading: lane, month grid, and timeline skeletons; Empty: `No rows match this view` with `Clear filters`; Error: banner with `correlation_id` and retry; Success: toast on save and share; Stale/conflict: dragged item snaps back with `This row changed` banner and `Reload`; Offline: drag disabled with offline badge.
- Permission-denied: viewers see cards, events, and bars without drag handles; share button hidden for non-owners; unshared private view URL renders the not-found page.
- Responsive: lanes scroll horizontally with snap under 768 px; calendar switches to agenda list under 640 px; timeline shows a day zoom with a pinned row label column under 640 px.
- Keyboard: `Tab` reaches switcher, settings, share, then each lane, event, or bar; `Space` picks up, arrows move by lane, day, or zoom unit, `Enter` drops, `Escape` cancels; `FilterBuilder` rows are reachable and deletable by keyboard; focus returns to the trigger after dialogs close.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062), Lucide icons `LayoutGrid`, `Kanban`, `CalendarDays`, `GanttChart`, `Filter`, `Share2`, `Download`, `Star`; tokens from `apps/web/src/design/tokens.css`.

- Design: `design/artboards/Board.dc.html` on the canvas indexed by `design/canvas.json`. The ticket is the contract and the artboard is the picture; when they disagree the ticket wins.

## 4. Technical specification

### Rust backend

- Domain entities: `View { id, tenant_id, sheet_id, owner_id, name, kind: ViewKind, visibility: Visibility, is_default, settings: ViewSettings, version, created/updated actor+time, deleted_at }`, `ViewSettings { filter: Option<FilterNode>, sorts: Vec<SortSpec>, group_by: Option<ColumnId>, columns: Vec<ColumnId>, card: Option<CardSettings>, calendar: Option<CalendarSettings>, timeline: Option<TimelineSettings>, gantt: Option<serde_json::Value> }` — one wire and domain shape composed by the repository from the `views` typed columns and the projection tables, `FilterNode::{And(Vec<FilterNode>), Or(Vec<FilterNode>), Leaf { column_id, op: FilterOp, value: FilterValue }}` where `FilterOp` and `FilterValue` are `docs/filter-vocabulary.md`, `ViewShare { id, tenant_id, view_id, principal_kind: PrincipalKind, principal_id, role: ShareRole, expires_at, revoked_at }`.
- Use cases in `crates/domain/src/views/`: `create_view`, `update_view`, `delete_view`, `get_view`, `list_views`, `list_view_rows`, `share_view`, `revoke_share`, `compile_filter` (AST to a filter specification over the F008 row query with the column type table), `validate_settings` (column types and the checks the database cannot express), `project_filter_columns` (AST walk producing the `view_filter_columns` set).
- Persistence (`crates/persistence/src/views/`): `ViewRepository` owns `views`, `view_sorts`, `view_columns`, `view_card_fields`, `view_filter_columns`; `ViewShareRepository` owns `view_shares`. Each implements the shared `Repository` contract (`get`, `list` with cursor pagination, `insert`, `update` under an expected version, `soft_delete`, `restore`, `purge`) and adds named queries `list_visible_to(actor, sheet_id, cursor)`, `find_default(sheet_id)`, `clear_default(sheet_id)`, `replace_projection(view_id, sorts, columns, card_fields, filter_columns)`, `list_views_using_column(column_id)`, `list_active_shares(view_id)`, `revoke_shares_for_view(view_id)`; the tenant predicate, soft-delete filter, version check, audit row, and outbox enqueue come from the base contract. Multi-table writes — the default swap (`clear_default` then the `views` update) and the settings replace (`views` update plus `replace_projection`) — run in one `UnitOfWork` that owns the transaction. `GET /api/v1/views/{id}/rows` composes a row query executed by F008's row repository under the view's filter, sorts, and visible columns; this feature contributes the filter and sort specification, not SQL. Per decision 2.1 the use cases above depend on these repository traits and contain no SQL: no SQL string, `sqlx::query*` call, or connection exists in `crates/domain/src/views` or `services/api/src/views`.
- Filter operators: `docs/filter-vocabulary.md`, subset all — this feature owns the vocabulary and the `FilterNode` AST that carries it.
- API endpoints (`services/api/src/views/`): `GET /api/v1/sheets/{sheet_id}/views`, `POST /api/v1/views`, `GET /api/v1/views/{id}`, `PATCH /api/v1/views/{id}`, `DELETE /api/v1/views/{id}`, `GET /api/v1/views/{id}/rows`, `POST /api/v1/views/{id}/share`. DTOs `CreateViewRequest`, `UpdateViewRequest`, `ShareViewRequest`, `ViewResponse`, `ViewShareResponse`, `Page<ViewRowResponse>`; row query `{ cursor?, limit?, range_start?, range_end? }`.
- Events: `view.created.v1`, `view.updated.v1`, `view.deleted.v1`, `view.shared.v1` with contract payload and `changed_fields`.
- Authorization: `sheet-viewer` on the sheet to create and read; owner or `sheet-editor` to update `sheet` views; owner only for `private` views and for `share`; an F036 scoped-token actor whose target is this view reads it read-only through the same filtering path; sheet ACL and explicit deny win over any share.
- Validation: name 1–120, ≤ 100 views per sheet, ≤ 50 filter leaves, ≤ 5 sorts, ≤ 8 card fields, range ≤ 366 days, `limit` 1–500. Idempotency keys stored 24 hours. `If-Match` compared inside the update transaction.
- Error mapping: `ViewError::Limit → 400 invalid`, `ViewError::BadFilter → 400 invalid` with `field_errors.settings.filter`, `ViewError::DefaultDelete → 400 invalid`, `ViewError::StaleVersion → 409 conflict`, `ViewError::NotFound → 404 not_found`, `AuthzError::Denied → 403 denied`, expired or revoked share → `404 not_found`.

### Interface

Exact shapes. Every field lists its JSON name, type, whether it is required, and the constraint that
makes it invalid. `T?` is nullable, and a missing optional field and an explicit `null` mean the same
thing. Ids are UUIDv7 strings, timestamps are RFC 3339 UTC, `version` increments by one per write.
Unlisted fields are rejected with `400 invalid`. `Page<T>` and its opaque cursor are F028's; the
error envelope `{ code, message, field_errors, correlation_id }` and the six codes are the shared
ones; `CellValue` is F007's.

**`FilterNode`** — the filter AST. F013 owns it; F021 reports, F025 exports, F050 dynamic views and
F060 formatting reuse this definition rather than restating one. A node is one of three shapes,
discriminated by `type`. Any other `type` value is `400 invalid` with `field_errors.settings.filter`.

Branch node — `type` is `"and"` or `"or"`:

| Field | Type | Required | Constraint |
|---|---|---|---|
| `type` | `"and" \| "or"` | yes | no other discriminator is accepted |
| `children` | FilterNode[] | yes | 1–20 entries; an empty array is invalid, and a one-child branch is legal and evaluates as its child |

Leaf node — `type` is `"leaf"`:

| Field | Type | Required | Constraint |
|---|---|---|---|
| `type` | `"leaf"` | yes | |
| `column_id` | uuid | yes | a live, non-deleted column of the view's `sheet_id`; unknown or foreign column → `invalid` with `field_errors.settings.filter` |
| `op` | FilterOp | yes | a member of `docs/filter-vocabulary.md` that appears in the operator row for that column's `columns.type`; otherwise `invalid` |
| `value` | FilterValue | conditional | required for every operator except `is_empty`, `is_not_empty` and `is_me`, which reject a present `value` |

Tree constraints, all checked before any evaluation and all returning `400 invalid` with
`field_errors.settings.filter`: the root is depth 1, maximum nesting depth is 8, and the whole tree
holds at most 50 leaf nodes (FR-F013-02). A `filter` that is absent or `null` means no filter; it is
not the same as an empty branch, which is invalid. Every `column_id` appearing anywhere in the tree
is projected into `view_filter_columns` in the same transaction as the view write.

**`FilterOp`** and **`FilterValue`** are `docs/filter-vocabulary.md`: the product's one closed
predicate vocabulary, the operator row for each `columns.type`, the value each operator takes, and
the relative-date tokens. This ticket owns that file and accepts the whole vocabulary; F009, F010,
F018, F021, F022, F025, F050, F056 and F060 accept subsets and name theirs in their own section 4.
The operators are not restated here, because a second copy is how the product ended up with five
spellings of one operator.

An operator outside the row for the column's type, a value whose JSON type does not match the
column, or an unresolvable relative token is `400 invalid` with `field_errors.settings.filter` — the
one key every filter failure in this feature reports under.

**`ViewSettings`** — one wire shape for create, update and read. The repository decomposes it into
`views` columns and the four projection tables on write and composes it back on read (FR-F013-01).

| Field | Type | Required | Constraint |
|---|---|---|---|
| `filter` | FilterNode? | no | null means no filter |
| `sorts` | SortSpec[] | no | 0–5 entries, precedence is array order, `column_id` distinct; a 6th entry → `invalid` with `field_errors.settings.sorts` |
| `group_by` | uuid? | no | one live column of the sheet |
| `columns` | uuid[] | no | ordered visible columns, distinct, all live columns of the sheet; empty or absent means every column the actor may read |
| `card` | CardSettings? | conditional | required when `kind` is `card`, rejected for any other kind |
| `calendar` | CalendarSettings? | conditional | required when `kind` is `calendar`, rejected otherwise |
| `timeline` | TimelineSettings? | conditional | required when `kind` is `timeline`, rejected otherwise |
| `gantt` | object? | no | opaque F012-owned payload stored and returned verbatim; F013 never reads inside it |

**`SortSpec`**

| Field | Type | Required | Constraint |
|---|---|---|---|
| `column_id` | uuid | yes | live column of the sheet, not repeated within `sorts` |
| `direction` | `"asc" \| "desc"` | no | defaults to `"asc"` |

**`CardSettings`**

| Field | Type | Required | Constraint |
|---|---|---|---|
| `lane_column_id` | uuid | yes | column type must be `select`, else `invalid` with `field_errors.settings.card.lane_column_id` |
| `swimlane_column_id` | uuid? | no | column type `select`; must differ from `lane_column_id` |
| `fields` | uuid[] | no | 0–8 ordered card fields, distinct; a 9th → `invalid` with `field_errors.settings.card.fields` |

**`CalendarSettings`**

| Field | Type | Required | Constraint |
|---|---|---|---|
| `date_column_id` | uuid? | conditional | column type `date` or `datetime`; present exactly when `start_column_id`/`end_column_id` are absent |
| `start_column_id` | uuid? | conditional | `date`/`datetime`; present with `end_column_id` and only when `date_column_id` is absent |
| `end_column_id` | uuid? | conditional | `date`/`datetime`; must differ from `start_column_id` |
| `mode` | `"month" \| "week" \| "day"` | yes | any other member → `invalid` with `field_errors.settings.calendar` |

Supplying both `date_column_id` and the pair, or neither, is `400 invalid` with
`field_errors.settings.calendar`.

**`TimelineSettings`**

| Field | Type | Required | Constraint |
|---|---|---|---|
| `start_column_id` | uuid | yes | column type `date` or `datetime` |
| `end_column_id` | uuid | yes | `date`/`datetime`, distinct from `start_column_id` |
| `zoom` | `"day" \| "week" \| "month" \| "quarter"` | yes | else `invalid` with `field_errors.settings.timeline` |
| `color_by_column_id` | uuid? | no | column type `select` |

**`CreateViewRequest`** — `POST /api/v1/views`

| Field | Type | Required | Constraint |
|---|---|---|---|
| `sheet_id` | uuid | yes | caller holds `sheet-viewer` on it, else `404 not_found`; a sheet already holding 100 live views → `invalid` with `field_errors.sheet_id = "view_limit"` |
| `name` | string | yes | 1–120 chars after trim, unique per `(sheet_id, owner_id)` among live views, else `409 conflict` |
| `kind` | `"grid" \| "card" \| "calendar" \| "timeline"` | yes | closed set |
| `visibility` | `"private" \| "sheet"` | yes | closed set |
| `is_default` | bool | no | defaults `false`; `true` clears the sheet's previous default in the same transaction |
| `settings` | ViewSettings | yes | per-kind sub-object must match `kind` |

**`UpdateViewRequest`** — `PATCH /api/v1/views/{id}`, `If-Match: <version>` required, all fields
optional, at least one present, unlisted fields rejected.

| Field | Type | Constraint |
|---|---|---|
| `name` | string | as above |
| `visibility` | `"private" \| "sheet"` | owner only; a `sheet` view may also be updated by a `sheet-editor` |
| `is_default` | bool | `true` clears the previous default in the same transaction; a `private` view cannot be the sheet default |
| `settings` | ViewSettings | full replace of the typed columns, `filter` and all four projection tables — never a merge; `kind` is immutable, so the per-kind sub-object must match the stored `kind` |

**`ShareViewRequest`** — `POST /api/v1/views/{id}/share`

| Field | Type | Required | Constraint |
|---|---|---|---|
| `principal_kind` | `"user" \| "group"` | yes | closed set |
| `principal_id` | uuid | yes | a live user or group of this tenant; unknown → `invalid`; a second live share for the same `(view_id, principal_kind, principal_id)` → `409 conflict` |
| `role` | `"viewer" \| "editor"` | yes | closed set |
| `expires_at` | timestamp? | no | must be in the future |

**`ViewResponse`**

| Field | Type | Notes |
|---|---|---|
| `id` | uuid | |
| `sheet_id` | uuid | |
| `owner_id` | uuid | actor who created it |
| `name` | string | |
| `kind` | ViewKind | |
| `visibility` | `"private" \| "sheet"` | |
| `is_default` | bool | at most one `true` per sheet |
| `settings` | ViewSettings | composed from the typed columns and projection rows; defaults materialised |
| `can_update` / `can_share` | bool | this actor's rights, so the client hides affordances instead of guessing |
| `version` | integer | pass as `If-Match` on the next write |
| `created_at` / `updated_at` | timestamp | |
| `created_by` / `updated_by` | uuid | |
| `deleted_at` | timestamp? | never present on a normal read; a soft-deleted view is `404 not_found` |

**`ViewShareResponse`**: `{ id, view_id, principal_kind, principal_id, role, expires_at?, revoked_at?, created_at, created_by }`.

**`ViewRowResponse`** — one row as this view presents it.

| Field | Type | Notes |
|---|---|---|
| `row_id` | uuid | F006's row id, unchanged by the view |
| `group_key` | string? | present only when `settings.group_by` is set: the normalized value of the grouping column, `null` for the empty group |
| `position` | string | F006's fractional index as a string |
| `cells` | map<uuid, CellValue> | only the `settings.columns` visible columns the actor may read, plus the sheet's primary column |
| `occurrence_start` / `occurrence_end` | timestamp? | present only for `calendar` and `timeline` kinds; a recurring row yields one read-only entry per occurrence in range (FR-F013-06) |
| `version` | integer | the row's version, for the `If-Match` a card or bar drag sends to F008 or F011 |

**List routes.** `GET /api/v1/sheets/{sheet_id}/views` returns `Page<ViewResponse>` with query
`{ kind?: ViewKind, sort?: "name" \| "updated_at" (default "updated_at" descending), cursor?: string, limit?: 1–100 (default 25) }`; the page holds only views the actor may see per FR-F013-11.
`GET /api/v1/views/{id}/rows` returns `Page<ViewRowResponse>` sorted by `group_key` then the
`view_sorts` order then `position`, with query `{ cursor?: string, limit?: 1–500 (default 100), range_start?: timestamp, range_end?: timestamp }`; `range_start`/`range_end` are required together
for `calendar` and `timeline`, rejected for `grid` and `card`, and a span over 366 days is
`400 invalid` with `field_errors.range_end`. Permission filtering runs inside the query that pages,
so a page is never short because hidden rows were dropped after paging.

**Status codes**

| Code | Produced by |
|---|---|
| `200` | reads and `PATCH`; `201` on create and share |
| `400 invalid` | any constraint above: filter depth, leaf count, operator/column-type mismatch, value shape, sort or card-field limit, per-kind settings, range over 366 days, deleting the default view (`field_errors.is_default`), view limit |
| `403 denied` | a visible view the actor may read but not update or share — non-owner on a `private` view, non-editor on a `sheet` view, non-owner on `share` |
| `404 not_found` | unknown, soft-deleted, foreign-tenant, or invisible view or sheet; an expired or revoked share; never `denied` for something the actor cannot see |
| `409 conflict` | stale `If-Match`, duplicate view name for that owner, duplicate live share for a principal |
| `429 rate_limited` | the shared per-actor request limit |
| `502` | never returned by this feature; it calls no external service |

### Use case signatures

In `crates/domain/src/views/`. Each takes `ctx` carrying tenant, actor and correlation id, takes a
`UnitOfWork` for writes or a repository for reads — never a pool or a connection — and returns the
shared `DomainError` mapped by the table above. None returns a database row type.

```rust
fn create_view(ctx: &Ctx, uow: &mut UnitOfWork, req: CreateView) -> Result<View, DomainError>;
fn update_view(ctx: &Ctx, uow: &mut UnitOfWork, id: ViewId, expected: Version, req: UpdateView) -> Result<View, DomainError>;
fn delete_view(ctx: &Ctx, uow: &mut UnitOfWork, id: ViewId, expected: Version) -> Result<(), DomainError>;
fn get_view(ctx: &Ctx, repo: &ViewRepository, id: ViewId) -> Result<View, DomainError>;
fn list_views(ctx: &Ctx, repo: &ViewRepository, sheet: SheetId, filter: ViewFilter, page: Cursor) -> Result<Page<View>, DomainError>;
fn list_view_rows(ctx: &Ctx, views: &ViewRepository, rows: &RowReader, id: ViewId, range: Option<DateRange>, page: Cursor) -> Result<Page<ViewRow>, DomainError>;
fn share_view(ctx: &Ctx, uow: &mut UnitOfWork, id: ViewId, req: ShareView) -> Result<ViewShare, DomainError>;
fn revoke_share(ctx: &Ctx, uow: &mut UnitOfWork, share: ViewShareId) -> Result<(), DomainError>;
fn compile_filter(ctx: &Ctx, columns: &ColumnTypeMap, filter: &FilterNode) -> Result<RowPredicate, DomainError>;
fn validate_settings(ctx: &Ctx, columns: &ColumnTypeMap, kind: ViewKind, settings: &ViewSettings) -> Result<(), DomainError>;
fn project_filter_columns(filter: &FilterNode) -> BTreeSet<ColumnId>;
```

`compile_filter` returns a `RowPredicate` that the F008 row query ANDs *inside* its own
permission-filtered query; it never produces SQL and never sees a connection.
`project_filter_columns` is pure and total — it walks the AST and cannot fail, because
`validate_settings` has already rejected an unknown column.

**Transaction boundaries.** `create_view` and `update_view` each run in one `UnitOfWork` covering the
`views` row, the `filter` value, and a full replace of `view_sorts`, `view_columns`,
`view_card_fields` and `view_filter_columns`, plus `clear_default` when `is_default` is set. That
single boundary protects three invariants that concurrent writes would otherwise break: at most one
default view per sheet, a projection set that always matches the stored `filter` (so
`list_views_using_column` can never miss a reference and let F007 drop a column a live view uses),
and the version bump landing with the rows it describes. `delete_view` soft-deletes the view and
revokes its shares in one `UnitOfWork` so no share outlives its view. `share_view` writes one
`view_shares` row plus its audit and outbox entries in the base contract's boundary.

### PostgreSQL/SQLx

- Migration `*_views_*.sql` creates `views(id uuid pk, tenant_id uuid not null, sheet_id uuid not null references sheets(id) on delete restrict, owner_id uuid not null, name text not null, kind text not null check (kind in ('grid','card','calendar','timeline')), visibility text not null check (visibility in ('private','sheet')), is_default bool not null default false, filter jsonb not null default '{}', group_by_column_id uuid null references columns(id) on delete restrict, lane_column_id uuid null references columns(id) on delete restrict, swimlane_column_id uuid null references columns(id) on delete restrict, date_column_id uuid null references columns(id) on delete restrict, start_column_id uuid null references columns(id) on delete restrict, end_column_id uuid null references columns(id) on delete restrict, color_by_column_id uuid null references columns(id) on delete restrict, calendar_mode text null check (calendar_mode in ('month','week','day')), timeline_zoom text null check (timeline_zoom in ('day','week','month','quarter')), gantt_settings jsonb null, version bigint not null default 1, created_by, created_at, updated_by, updated_at, deleted_at)` and `view_shares(id uuid pk, tenant_id uuid not null, view_id uuid not null references views(id) on delete restrict, principal_kind text not null check (principal_kind in ('user','group')), principal_id uuid not null, role text not null check (role in ('viewer','editor')), expires_at timestamptz null, revoked_at timestamptz null, version bigint not null default 1, audit fields)`.
- Two `jsonb` columns survive the audit and both are payloads, not queried structures: `views.filter` holds the FR-F013-02 AST, a user-authored tree of arbitrary shape and depth that is never read by key in SQL because the column references inside it are projected into `view_filter_columns`; `views.gantt_settings` is an opaque F012-owned block this feature never reads, queries, or constrains.
- Projection tables, each with `tenant_id uuid not null` and the sibling `created_by`/`created_at`/`updated_by`/`updated_at` audit columns, written in the same transaction as the view: `view_filter_columns(tenant_id, view_id uuid not null references views(id) on delete cascade, column_id uuid not null references columns(id) on delete restrict, primary key (view_id, column_id))`; `view_sorts(tenant_id, view_id uuid not null references views(id) on delete cascade, position smallint not null check (position between 1 and 5), column_id uuid not null references columns(id) on delete cascade, direction text not null check (direction in ('asc','desc')), primary key (view_id, position), unique (view_id, column_id))`; `view_columns(tenant_id, view_id uuid not null references views(id) on delete cascade, position smallint not null, column_id uuid not null references columns(id) on delete cascade, primary key (view_id, position), unique (view_id, column_id))`; `view_card_fields(tenant_id, view_id uuid not null references views(id) on delete cascade, position smallint not null check (position between 1 and 8), column_id uuid not null references columns(id) on delete cascade, primary key (view_id, position))`.
- Per-kind check constraints on `views` make FR-F013-04 declarative: `views_card_lane_ck` requires `lane_column_id is not null` when `kind = 'card'`; `views_calendar_ck` requires `calendar_mode is not null` and either `date_column_id is not null` or both `start_column_id` and `end_column_id` when `kind = 'calendar'`; `views_timeline_ck` requires `start_column_id`, `end_column_id`, and `timeline_zoom` when `kind = 'timeline'`. The column-type rules a check cannot express (lane column `select`, date columns `date|datetime`) stay in the service against `columns.type` and keep the same `400 invalid` `field_errors` response.
- Invariants: partial unique index `views_default_per_sheet_idx on (sheet_id) where is_default and deleted_at is null`; unique `views_sheet_owner_name_idx on (sheet_id, owner_id, lower(name)) where deleted_at is null`; unique `view_shares_principal_idx on (view_id, principal_kind, principal_id) where revoked_at is null`; the ≤ 5 sorts and ≤ 8 card fields limits are the `position` checks with `primary key (view_id, position)`, and no column repeats in a view's sorts or visible columns.
- Indexes: `views(tenant_id, sheet_id, updated_at desc) where deleted_at is null`, `views(tenant_id, owner_id)`, `view_shares(view_id) where revoked_at is null`, b-tree `view_filter_columns(column_id)`, `view_sorts(column_id)`, `view_columns(column_id)`, `view_card_fields(column_id)`. The F007 column-delete lookup keeps its behaviour unchanged and is now backed by real foreign keys and the b-tree `view_filter_columns(column_id)` index instead of a GIN scan of JSON.
- Audit events: `view.create`, `view.update`, `view.delete`, `view.share`, `view.share-revoke` with field-level diffs; share tokens are hashed and never logged.
- Retention/deletion: soft delete sets `deleted_at` on the view and `revoked_at` on its shares; purge follows the F027 retention job; rollback drops `view_card_fields`, `view_columns`, `view_sorts`, `view_filter_columns`, `view_shares`, and `views`.

### React/TypeScript

- Routes: `/w/:workspaceId/sheets/:sheetId/views/:viewId` and `/w/:workspaceId/sheets/:sheetId/views/new` in `apps/web/src/features/views/`; components `ViewPage`, `ViewSwitcher`, `ViewSettingsPanel`, `FilterBuilder`, `SortEditor`, `CardView`, `CardLane`, `ViewCard`, `CalendarView`, `CalendarEvent`, `TimelineView`, `TimelineBar`, `ShareViewDialog`, `ExportViewButton`.
- State: TanStack Query keys `['views', sheetId]`, `['view', viewId]`, `['view-rows', viewId, cursor, rangeStart, rangeEnd]`; mutations invalidate by key and update cached `version`; lane and date drags are optimistic with rollback on `conflict`.
- API client: generated `ViewsApi` with `listViews`, `createView`, `getView`, `updateView`, `deleteView`, `listViewRows`, `shareView`; reuses `GridApi.patchCells` (F008) and `SchedulesApi.rescheduleRow` (F011).
- Date formatting: calendar and timeline labels use the F049 locale formatter with the resolved timezone.
- Telemetry: `view_created`, `view_opened`, `view_kind_changed`, `card_lane_moved`, `calendar_event_rescheduled`, `timeline_bar_moved`, `view_shared`, `view_exported` with `sheet_id`, `view_id`, `kind`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F013-01 through FR-F013-14 in `testing/features/F013/requirements/cases.md`
- [ ] Failure/edge-case tests: 51-leaf filter, operator mismatched to column type, lane column not select, deleting the default view, duplicate share for one principal, expired share, range over 366 days
- [ ] Permission-negative and tenant-isolation tests: cross-tenant view returns `not_found`, non-owner share returns `denied`, unshared private view hidden from list, link actor cannot patch cells, hidden rows excluded from view rows
- [ ] Rust unit tests: `crates/domain/src/views/` filter compile per operator, settings validation per kind, share token hashing and expiry
- [ ] API contract/integration tests: every route above with success and each error code
- [ ] Database migration/constraint tests: default-per-sheet index, name uniqueness per owner, share check constraints, per-kind check constraints, sort and card-field position bounds, `view_filter_columns` foreign key blocking a column delete, rollback
- [ ] React component tests: `CardView`, `CalendarView`, `TimelineView`, `FilterBuilder`, `ShareViewDialog` states
- [ ] Browser E2E tests: create card view, move card, calendar drag reschedule, timeline zoom and drag, share link and open as guest
- [ ] Accessibility tests: axe on three kinds, keyboard lane and date moves, live-region announcements
- [ ] Performance/load tests: filtered view rows p95 under 500 ms on 100,000 rows, lane move p95 under 800 ms, calendar month over 5,000 rows

### Fast fanout configuration

- Test harness path: `testing/features/F013/`
- Feature flag: `F013_FEATURE`
- Fixture/seed factory: `testing/fixtures/views.rs` builds tenant, sheet with `Status` select, `Due` date, `Start`/`End` datetime columns, 200 rows, owner, editor, viewer, foreign tenant, and one view per kind
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, UTC with sheet timezone `America/New_York`
- Mock/stub contracts: outbox recorded in memory; F008 cell patch and F011 reschedule called through the real handlers in the same test schema; MSW handlers mirror seeded views
- Parallel isolation: one schema per test worker, tenant ID per test
- Targeted command: `cargo xtask test-feature F013`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F013/`

## 6. Acceptance criteria

```gherkin
Feature: Saved views

Scenario: Create a card view and move a card
  Given a sheet "Launch plan" with select column "Status" and rows in "Backlog"
  When an editor creates card view "Board by status" on "Status" and drags "Kickoff" to "Doing"
  Then the row's Status cell is "Doing" with a new version
  And events view.created.v1 and cell.updated.v1 are in the outbox

Scenario: Filtered rows respect permissions
  Given view "Mine" with filter Owner is_me and a viewer who cannot read rows in group "Restricted"
  When the viewer requests the view rows
  Then only their own rows outside "Restricted" are returned in sort order

Scenario: Non-owner cannot share
  Given a private view owned by user A
  When user B posts a share for the view
  Then the response is 403 denied and no view_shares row exists

Scenario: Share to a group is visible to its members
  Given view "Q3 plan" shared to group "Delivery" as viewer
  When a member of Delivery lists views for the sheet
  Then the view appears and its rows are filtered by that member's permissions

Scenario: Calendar drag reschedules
  Given calendar view "Due dates" keyed on "Due" in timezone America/New_York
  When a keyboard user moves "Kickoff" forward one week
  Then POST /api/v1/rows/{id}/reschedule is called and the event renders on the new day
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F008 (row query, cell patch, bulk edits), F011 (schedule settings timezone, reschedule route); decisions sections 2, 3, 4, 6; contracts row F013
- Blocks: F015, F050, F051, F055, F059
- Conflicts with: none (disjoint owned paths)
- External dependencies: none
- Risks and mitigations: a filter compiled to SQL could bypass the permission predicate, so `compile_filter` produces a predicate that is always ANDed inside the F008 permission-filtered query and a test asserts hidden rows never appear; a deleted column can no longer strand a view — `list_views_using_column` reads `view_filter_columns` by foreign key, sort and visible-column rows cascade, and the `on delete restrict` references make F007 resolve the view before the column goes; large calendars are bounded by the 366-day range and 5,000-row page test.
- Open questions: none

## 7.1 Amendments

Every change made to this ticket after it was first accepted, newest first.

| Date | Caused by | What changed | Why |
|---|---|---|---|
| 2026-09-04 | Filter vocabulary unification | `FilterOp` and `FilterValue` moved out of this ticket into `docs/filter-vocabulary.md`, which this ticket owns; `is_not_empty` added to the value-absent operators; `before`/`after` removed in favour of `lt`/`gt`; `neq` renamed `ne`; `gte`, `lte`, `not_in`, `starts_with`, `is_not_empty` added; relative-date tokens defined | Five features had each written their own operator list — `ne` against `neq`, `before` beside `lt`, `gte` present in one and missing from the next — so a filter saved in one could not be read by another. `cargo xtask check-filters` now refuses a sixth spelling |

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F008 and F011 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F013/`
- [ ] Migration file name and owned paths claimed
- [ ] Fixture factory with select, date, and datetime columns available in `testing/fixtures/views.rs`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for every mutation
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F013_FEATURE`, run down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Users can save card, calendar, timeline, and grid views with filters, sorts, grouping, and visible columns, set a default view, and share views with users, groups, or a 30-day link.
- Migration adds `views`, `view_shares`, `view_sorts`, `view_columns`, `view_card_fields`, and `view_filter_columns`; rollback drops them. Feature is off by default behind `F013_FEATURE`.
