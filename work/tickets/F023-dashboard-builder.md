---
id: F023
type: feature
status: planned
priority: P1
owner: platform
estimate: 8
target_milestone: M4
parent_epic: E005
depends_on: [F021, F036]
blocks: [F024, F025, F051, F059]
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/dashboards/**, crates/persistence/src/dashboards/**, services/api/src/dashboards/**, services/worker/src/dashboards/**, apps/web/src/features/dashboards/**, services/api/migrations/*_dashboards_*.sql, testing/features/F023/**]
feature_flag: F023_FEATURE
flag_default: off
branch: f023-dashboard-builder
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 6, 7, 9
- Capability contract: `docs/capability-contracts.md` row F023
- Product spec: `docs/product-capability-spec.md` section 5.6 REPORT-02, REPORT-03, section 4 Dashboard entity, section 10 (link expiry)

# F023 — Dashboard builder

## 1. Identity and dates

- Branch: `f023-dashboard-builder`
- Capability area: reporting (spec 5.6 REPORT-02 executive dashboards with KPI cards, tables, charts, images, links; REPORT-03 real-time or scheduled refresh, sharing; low-level bullets: widget types KPI, metric comparison, table, bar/line/pie, burndown, timeline, workload, text, image, report embed; refresh jobs cached with last-success, duration, source versions, stale state)
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 6, 7; `docs/capability-contracts.md` row F023
- Aggregate: `dashboard`
- Module slug: `dashboards`

## 2. Requirement specification

### Problem and user outcome

A PMO lead wants one page for the Monday leadership meeting: three KPI cards, a risk table, a status chart, a burndown, a note, and the company logo. Today that page is a slide deck rebuilt weekly. They need a dashboard whose widgets point at governed reports and metrics, refresh on a schedule with visible freshness, and can be shared with the leadership group or an expiring link while every widget still honors the viewer's permissions.

As a dashboard editor, I want to place typed widgets on a grid, bind them to reports and metrics, set a refresh policy, and share the dashboard, so that leaders open one live page instead of a rebuilt deck.

### Functional requirements

- **FR-F023-01:** An actor with the `dashboard-editor` role on a workspace can `POST /api/v1/dashboards` with `{ name, workspace_id, folder_id?, description?, refresh_policy: { mode: manual|interval|on_open, interval_minutes? }, layout: { columns: 12, row_height_px: 80 } }`; `layout` and `refresh_policy` are fixed-shape objects stored as typed columns (`grid_columns` fixed at 12, `row_height_px` 40..200, `refresh_mode`, `refresh_interval_minutes` 5..1440) and recomposed into the same wire objects on read; the response returns a UUIDv7 `id`, `version` 1, and `widgets: []`; `name` is unique per folder (case-insensitive) or the call returns `409 conflict` with `field_errors.name`.
- **FR-F023-02:** `PUT /api/v1/dashboards/{id}/widgets` replaces the full widget set with `If-Match` and a list of 0 to 40 `{ id?, kind, title, position: { x, y, w, h }, config, refresh_override? }`; positions use a 12-column grid with `w` 1..12, `h` 1..12, no overlaps, and `x + w ≤ 12`; an overlap or out-of-range position returns `400 invalid` with `field_errors["widgets[i].position"]`; widgets with an existing `id` keep their `widget_cache`, new widgets receive new IDs, omitted widgets are deleted, and each widget's `dashboard_widget_sources` and `dashboard_widget_columns` rows are rewritten from its `config` in the same transaction.
- **FR-F023-03:** `kind` is one of `kpi`, `metric_comparison`, `table`, `bar`, `line`, `pie`, `burndown`, `timeline`, `workload`, `text`, `image`, `report_embed`; the widget registry validates `config` per kind: `table` and `report_embed` require `report_id` and optional `column_refs[]`, `limit ≤ 200`; `text` requires `markdown` ≤ 8,000 chars; `image` requires `file_id` from F017 plus `alt` ≤ 200 chars; `kpi` and `metric_comparison` require `metric_id` (and `compare_metric_id` for comparison); chart kinds require `chart_id` or an inline `chart_spec`; an unknown kind or invalid config returns `400 invalid` with `field_errors["widgets[i].config"]`; the ids the config names are persisted as `dashboard_widget_sources` rows (`report`, `metric`, `sheet`, `file`, `chart` with role `primary` or `comparison`) and `column_refs[]` is persisted as ordered `dashboard_widget_columns` rows, while the per-kind presentation settings stay in `config`.
- **FR-F023-04:** The registry maps each `kind` to a `WidgetResolver`; F023 ships resolvers for `table`, `report_embed`, `text`, and `image`; `kpi`, `metric_comparison`, `bar`, `line`, `pie`, `burndown`, `timeline`, and `workload` are registered by F024 and, until registered, `GET /api/v1/widgets/{id}/data` returns `status: "unavailable"` with `reason: "resolver_not_registered"` and the widget renders the unavailable state.
- **FR-F023-05:** `GET /api/v1/widgets/{id}/data` returns `{ status: fresh|stale|computing|error|unavailable|denied, payload, computed_at, duration_ms, source_versions, error?, scope: viewer|owner }` from `widget_cache` keyed by `(widget_id, scope_key)` using the viewer's F021 `ViewerScope`; a miss enqueues a `dashboards.refresh-widget` job and returns `computing`; `stale` is set when any `widget_cache_sources` row is behind the current source version or the source report has a newer snapshot, compared by joining that table to the live sources; `denied` is returned with no payload when the viewer lacks `read` on any `dashboard_widget_sources` row for the widget (report, metric, sheet, file, or chart); the response field `source_versions` is unchanged and is composed from `widget_cache_sources`.
- **FR-F023-06:** `POST /api/v1/dashboards/{id}/refresh` enqueues a refresh of every widget for the caller's `scope_key`, returns `202 { run_id, status: "queued", widget_count }` within 2 seconds, and returns `409 conflict` while a refresh for that scope is active; the worker records per-widget `duration_ms`, `computed_at`, `status`, and `error` on the cache entry and one `widget_cache_sources` row per source version, then publishes `dashboard.refreshed.v1` with `succeeded_count` and `failed_count`.
- **FR-F023-07:** `refresh_mode = 'interval'` with `refresh_interval_minutes` 5..1440 enqueues refreshes for scopes read in the last 24 hours, the scheduler selecting due dashboards on the `dashboards(refresh_mode, refresh_interval_minutes)` index instead of scanning a JSON policy; `on_open` enqueues when `GET /api/v1/dashboards/{id}` is called and the newest cache entry for the scope is older than 60 seconds; `manual` refreshes only through the endpoint; per-widget `refresh_override` may shorten but never lengthen the dashboard interval.
- **FR-F023-08:** `GET /api/v1/dashboards/{id}` returns `name`, `description`, `layout` and `refresh_policy` recomposed from their typed columns, `widgets[]` with `position`, `kind`, `title`, `config` recomposed from the stored settings plus the widget's source and column rows, and `cache_summary { status, computed_at, stale }` per widget for the caller's scope, `share_summary { shared_with_count, link_active }`, and `version`; `GET /api/v1/dashboards` pages by cursor with `limit` 1..100, filters by `workspace_id`, `folder_id`, `name` prefix, `deleted`, and returns dashboards the actor can read directly or through an F036 share.
- **FR-F023-09:** Dashboards are F036 share targets of `target_kind = dashboard`: `POST /api/v1/shares` grants `viewer` or `editor`, and `POST /api/v1/share-links` issues a read-only link expiring within 30 days; a share-link viewer receives every widget through the same `ViewerScope` rules, so widgets whose sources the guest cannot read return `denied` and the page shows the denied tile; share links never allow `PUT widgets`, `PATCH`, or `refresh`.
- **FR-F023-10:** `PATCH /api/v1/dashboards/{id}` updates `name`, `description`, `folder_id`, `refresh_policy` (`refresh_mode`, `refresh_interval_minutes`), `layout` (`grid_columns`, `row_height_px`), and `audience` (`workspace|shared_only`) with `If-Match`; a stale version returns `409 conflict` with `current_version`; `DELETE` soft-deletes the dashboard, its widgets, and its cache, and revokes its share links; deleting a widget cascades its `dashboard_widget_sources` and `dashboard_widget_columns` rows, and deleting a cache entry cascades its `widget_cache_sources` rows; a foreign-tenant actor receives `404 not_found` on every route including `GET /api/v1/widgets/{id}/data`.
- **FR-F023-11:** Every mutation requires `Idempotency-Key`, writes an `audit_events` row with the widget diff (added, removed, moved, reconfigured IDs), and publishes `dashboard.created.v1`, `dashboard.updated.v1`, or `dashboard.deleted.v1` through the outbox; the refresh worker is idempotent by `run_id`, retries 3 times, and dead-letters on the fourth failure.
- **FR-F023-12:** The web builder renders the 12-column grid with drag, resize, and keyboard placement, a widget palette listing the twelve kinds, per-kind config forms, a share dialog reusing F036 components, a refresh policy form, and a viewer mode that shows each widget's freshness badge, `Refresh` action, and the states loading, empty, error, denied, stale, computing, unavailable, and offline.
- **FR-F023-13:** Widget titles, positions, and config are validated client-side with the same limits as the server, and unsaved layout changes prompt before navigation; saving emits a single `PUT widgets` call with the full set.

### Non-functional requirements

- **NFR-F023-01 Performance:** `GET /api/v1/dashboards/{id}` responds under 500 ms p95 with 40 widgets; `GET /widgets/{id}/data` from cache responds under 300 ms p95; a full 40-widget refresh for one scope completes under 60 s with widgets resolved in parallel (8 at a time); the builder keeps 60 fps during drag with 40 widgets.
- **NFR-F023-02 Security/privacy:** cache entries are keyed by `scope_key` and never served across scopes; share-link actors are read-only and tested for mutation, refresh, and cross-tenant negatives; `image` widgets serve files through F017 signed downloads only after scan success.
- **NFR-F023-03 Accessibility:** the grid is keyboard operable (select widget, move with arrows, resize with Shift+arrows, announce position); every widget is a labeled region; axe reports zero serious violations in builder and viewer; reduced motion disables drag animations.
- **NFR-F023-04 Reliability/observability:** spans carry `tenant_id`, `dashboard_id`, `widget_id`, `run_id`, `scope_key`; metrics `dashboard_refresh_duration_seconds`, `widget_resolve_failures_total`, `widget_cache_hits_total`; failed widgets never block other widgets in the same run.

### Scope

Included: dashboard CRUD, widget set replacement with grid validation, widget registry and config schemas for the twelve kinds, resolvers for table, report embed, text, and image, per-scope widget cache with refresh state, refresh policies and worker, sharing through F036, builder and viewer UI.

Excluded: KPI, metric comparison, chart, burndown, timeline, and workload resolvers and renderers (F024), export and drill-through (F025), anonymous published embeds (F059), WorkApps composition (F051), metric definitions (F022), report definitions (F021).

## 3. UX specification

- Entry points: workspace tree item `New dashboard`; route `/w/{workspace_id}/dashboards/{dashboard_id}` (viewer) and `/w/{workspace_id}/dashboards/{dashboard_id}/edit` (builder); share button in the header; `/public/share/{token}` renders the viewer for links.
- Primary flow: click `New dashboard`, name "Weekly review", open the palette, drag `Table` onto the grid, pick report "Portfolio status" and four columns, add `Text` with the agenda, add `Image` with the logo, set refresh every 30 minutes, save, click `Share`, add group "Leadership" as viewer, copy an expiring link; the viewer shows each widget with `Updated 2 min ago`.
- Loading: grid skeleton with widget outlines; Empty: "Add your first widget" with the palette open; Error: widget tile shows `correlation_id` and retry without affecting other tiles; Denied: tile "You do not have access to this source"; Unavailable: tile "Widget type not enabled"; Stale: badge with `Refresh`; Computing: badge with spinner; Conflict: banner "Dashboard changed" with reload; Offline: editing disabled.
- Responsive: 12 columns above 1024 px, 6 columns 640..1024 px (widths halved, rounded up), single column under 640 px in saved `y` order.
- Keyboard: `Tab` between widgets, `Enter` selects, arrows move by one cell, `Shift+Arrow` resizes, `Escape` deselects, `Delete` removes with confirm; live region announces "Table moved to column 4 row 2"; focus ring tokens; reduced motion respected.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062); Lucide `LayoutDashboard`, `Plus`, `Move`, `Share2`, `RefreshCw`, `Image`, `Type`, `Table`; tokens from `apps/web/src/design/tokens.css`.

- Design: `design/artboards/Dashboard.dc.html` on the canvas indexed by `design/canvas.json`. The ticket is the contract and the artboard is the picture; when they disagree the ticket wins.

## 4. Technical specification

### Rust backend

- Domain entities in `crates/domain/src/dashboards/`: `Dashboard { id, tenant_id, workspace_id, folder_id, name, description, layout: GridLayout, refresh_policy: DashboardRefreshPolicy, audience, version, audit fields, deleted_at }`, `DashboardWidget { id, dashboard_id, kind: WidgetKind, title, position: GridPosition, config: WidgetConfig, refresh_override, position_index }`, `WidgetKind` enum with the twelve variants, `WidgetConfig` enum validated per kind, `WidgetCacheEntry { widget_id, scope_key, status, payload, computed_at, duration_ms, source_versions: Vec<SourceVersion>, error }`, `WidgetData { status, payload, computed_at, duration_ms, source_versions, error, scope }`; `GridLayout` and `DashboardRefreshPolicy` map to the typed `dashboards` columns, `WidgetConfig` carries only the per-kind presentation settings, and `SourceRef`/`SourceVersion` map to `dashboard_widget_sources` and `widget_cache_sources`.
- Registry `crates/domain/src/dashboards/registry.rs`: `trait WidgetResolver { fn kind(&self) -> WidgetKind; fn validate(&self, config: &Json) -> Result<WidgetConfig, FieldErrors>; async fn resolve(&self, ctx: ResolveContext, config: &WidgetConfig) -> Result<Payload, ResolveError>; fn source_versions(&self, config) -> Vec<SourceRef>; }` and `WidgetRegistry::register(Box<dyn WidgetResolver>)`; resolvers `TableResolver`, `ReportEmbedResolver` (both call F021 `read_rows` with the viewer scope), `TextResolver`, `ImageResolver` (F017 signed URL).
- Use cases: `create_dashboard`, `update_dashboard`, `delete_dashboard`, `list_dashboards`, `get_dashboard`, `replace_widgets` (grid validation, diff, cache retention), `read_widget_data`, `request_refresh`, `execute_refresh` (worker), `compute_widget_stale`.
- Persistence (`crates/persistence/src/dashboards/`): `DashboardRepository` owns `dashboards`; `DashboardWidgetRepository` owns `dashboard_widgets`, `dashboard_widget_sources`, `dashboard_widget_columns`; `WidgetCacheRepository` owns `widget_cache` and `widget_cache_sources`. Each implements the shared `Repository` contract (`get`, `list` with cursor pagination, `insert`, `update` under an expected version, `soft_delete`, `restore`, `purge`) and adds named queries `page_dashboards(filter, cursor)`, `load_with_widgets(dashboard_id, scope_key)`, `replace_widgets(dashboard_id, widgets)`, `list_widgets_using_source(source_kind, source_id)`, `get_cache(widget_id, scope_key)`, `put_cache(widget_id, scope_key, entry)`, `list_scopes_read_since(dashboard_id, cutoff)`, `find_active_refresh(dashboard_id, scope_key)`, `prune_cache_unread_since(cutoff)`, `delete_cache_for_dashboard(dashboard_id)`; the tenant predicate, soft-delete filter, version check, audit row, and outbox enqueue come from the base contract. `PUT /api/v1/dashboards/{id}/widgets` — the full-set replace that keeps existing widgets' cache, inserts new IDs, deletes omitted ones, and rewrites the source and column rows — runs in one `UnitOfWork`, and so does a refresh run (cache entries, source versions, outbox). Widget data is resolved by calling F021, F022, F024, and F017 through their own repositories; this feature issues no SQL against another feature's tables, and F036 shares are read through `ShareRepository`. Per decision 2.1 the use cases above depend on these repository traits and contain no SQL: no SQL string, `sqlx::query*` call, or connection exists in `crates/domain/src/dashboards` or `services/api/src/dashboards`.
- Worker `services/worker/src/dashboards/{refresh_job.rs, scheduler.rs}`: consumes `dashboards.refresh` and `dashboards.refresh-widget`, resolves widgets 8 at a time with a 20 s per-widget timeout, writes cache entries through `WidgetCacheRepository::put_cache`, publishes `dashboard.refreshed.v1`; the scheduler enqueues interval and `on_open` refreshes using `page_dashboards` and `list_scopes_read_since`, and the nightly prune calls `prune_cache_unread_since`. The worker holds no SQL string, `sqlx::query*` call, or connection.
- API endpoints (`services/api/src/dashboards/`): `GET /api/v1/dashboards`, `POST /api/v1/dashboards`, `GET /api/v1/dashboards/{id}`, `PATCH /api/v1/dashboards/{id}`, `DELETE /api/v1/dashboards/{id}`, `PUT /api/v1/dashboards/{id}/widgets`, `POST /api/v1/dashboards/{id}/refresh`, `GET /api/v1/widgets/{id}/data`; DTOs `CreateDashboardRequest`, `UpdateDashboardRequest`, `ReplaceWidgetsRequest { widgets }`, `DashboardResponse`, `WidgetResponse`, `WidgetDataResponse`, `RefreshResponse { run_id, status, widget_count }`.
- Events: `dashboard.created.v1`, `dashboard.updated.v1` (with `changed_fields` including `widgets`), `dashboard.deleted.v1`, `dashboard.refreshed.v1` (payload adds `run_id`, `scope_key`, `succeeded_count`, `failed_count`, `duration_ms`).
- Authorization: `dashboard-editor` on the workspace or F036 `editor` share for mutations; direct ACL, F036 `viewer` share, or valid share link for reads; explicit deny wins; share links are read-only; missing access maps to `not_found`.
- Validation limits: name 1..200, description ≤ 4,000, widgets ≤ 40, title ≤ 120, markdown ≤ 8,000, `limit` ≤ 200 rows for table widgets, `column_refs` ≤ 50 per widget, config settings object ≤ 32 KB per widget.
- Error mapping: `DashboardError::NameTaken → 409 conflict`, `DashboardError::StaleVersion → 409 conflict`, `DashboardError::RefreshActive → 409 conflict`, `DashboardError::LayoutOverlap → 400 invalid`, `DashboardError::InvalidWidgetConfig → 400 invalid`, `DashboardError::NotFound → 404 not_found`, `AuthzError::Denied → 403 denied`, `ResolveError::Denied → data status denied`, queue unavailable → `503 unavailable`.

### Interface

Exact shapes. Every field gives its JSON name, its type, whether it is required, and the constraint
that makes it invalid. `T?` is nullable; an absent optional field and an explicit `null` mean the
same thing. Ids are UUIDv7 strings, timestamps are RFC 3339 UTC, `version` increments by one per
write. Unlisted fields are rejected with `400 invalid`. `Page<T>`, the opaque cursor and `ListQuery`
are F028's; the error body and the six codes are the shared ones; `ViewerScope`, `ReportRow` and
`RowsMeta` are F021's; `MetricValuesResponse` is F022's; `ChartSpec` is F024's; `ActorContext` is
F038's. Shares and share links are F036's and this feature declares only that a dashboard is a
`target_kind = dashboard` for them.

**`GridLayout`** `{ columns: 12, row_height_px }` — `columns` is fixed at 12 and any other value is
`400 invalid`; `row_height_px` is 40–200, default 80. **`DashboardRefreshPolicy`**
`{ mode: "manual" | "interval" | "on_open", interval_minutes? }` — `interval_minutes` is required
when `mode` is `interval` and must be 5–1,440, rejected otherwise. Both are fixed-shape objects on
the wire and typed columns in storage (FR-F023-01).

**`CreateDashboardRequest`** — `POST /api/v1/dashboards`

| Field | Type | Required | Constraint |
|---|---|---|---|
| `name` | string | yes | 1–200 chars after trim, unique per folder case-insensitively among live dashboards, else `409 conflict` with `field_errors.name` |
| `workspace_id` | uuid | yes | the caller holds `dashboard-editor` on it, else `403 denied` |
| `folder_id` | uuid? | no | a folder of that workspace; `null` means workspace root |
| `description` | string? | no | ≤ 4,000 chars |
| `refresh_policy` | DashboardRefreshPolicy | yes | as above |
| `layout` | GridLayout | yes | as above |

The response is a `DashboardResponse` with `version` 1 and `widgets: []`; widgets are never created
in this call.

**`UpdateDashboardRequest`** — `PATCH /api/v1/dashboards/{id}`, `If-Match` required, every field
optional and at least one present: `name`, `description`, `folder_id`, `refresh_policy`, `layout`,
and `audience` (`"workspace" | "shared_only"`). `refresh_policy` and `layout` replace their object
whole. Widgets are not editable here — they move only through `PUT /widgets`.

**`ReplaceWidgetsRequest`** — `PUT /api/v1/dashboards/{id}/widgets`, `If-Match` required.
`{ widgets: WidgetInput[] }`, 0–40 entries, the **complete** set: an existing `id` that is present
keeps its `widget_cache` rows, an entry with no `id` is created, and an id omitted from the array is
deleted with its cache (FR-F023-02). A `widgets` key that is absent, rather than an empty array, is
`400 invalid` — clearing a dashboard is `[]`, said explicitly.

**`WidgetInput`**

| Field | Type | Required | Constraint |
|---|---|---|---|
| `id` | uuid? | no | an existing widget of this dashboard; an id of another dashboard → `400 invalid` with `field_errors["widgets[i].id"]` |
| `kind` | WidgetKind | yes | one of the twelve below; on an existing id the `kind` may not change, which is `400 invalid` |
| `title` | string | yes | 1–120 chars after trim |
| `position` | GridPosition | yes | below |
| `config` | object | yes | validated per `kind` by the registry; ≤ 32 KB of presentation settings after the ids are projected out |
| `refresh_override` | integer? | no | minutes, 5–1,440, and never longer than the dashboard's `interval_minutes` — a longer override is `400 invalid` (FR-F023-07) |

**`GridPosition`** `{ x, y, w, h }` — all integers; `x` 0–11, `y` ≥ 0, `w` 1–12, `h` 1–12, and
`x + w ≤ 12`. Two widgets whose rectangles intersect are `400 invalid` with
`field_errors["widgets[i].position"]` naming the later entry, and no widget, source, or column row is
written for the whole request.

**`WidgetKind` and its `config`** (FR-F023-03). The ids named in `config` are projected into
`dashboard_widget_sources` rows and `column_refs` into ordered `dashboard_widget_columns` rows in the
same transaction; the response recomposes the same object, so the wire shape is unchanged.

| `kind` | `config` fields | Constraint |
|---|---|---|
| `table` | `report_id` (uuid, required), `column_refs` (string[], optional), `limit` (integer, optional) | `report_id` a live F021 report; `column_refs` ≤ 50 F021 `column_ref` strings of that report, distinct and ordered; `limit` 1–200, default 50 |
| `report_embed` | the same three | same rules; the resolver returns F021 rows with their group headers rather than a flat table |
| `text` | `markdown` (string, required) | ≤ 8,000 chars; rendered sanitised, never as raw HTML |
| `image` | `file_id` (uuid, required), `alt` (string, required) | `file_id` an F017 file that passed its scan, served through a signed download; `alt` ≤ 200 chars, and an empty `alt` is `invalid` rather than a decorative image |
| `kpi` | `metric_id` (uuid, required) | a live F022 metric |
| `metric_comparison` | `metric_id` (uuid, required), `compare_metric_id` (uuid, required) | two distinct live metrics; the second is written with `role = 'comparison'` |
| `bar`, `line`, `pie`, `burndown`, `timeline`, `workload` | exactly one of `chart_id` (uuid) or `chart_spec` (object) | `chart_spec` is F024's `ChartSpec`, validated by F024's resolver; both or neither present is `400 invalid` |

An unknown `kind`, or a `config` failing its per-kind rules, is `400 invalid` with
`field_errors["widgets[i].config"]`. The eight kinds F023 does not resolve are still storable and
still validated structurally; their **data** is `unavailable` until F024 registers a resolver
(FR-F023-04), which is a widget state and not a save-time error.

**`DashboardResponse`** — `GET /api/v1/dashboards/{id}`

| Field | Type | Notes |
|---|---|---|
| `id`, `workspace_id` | uuid | |
| `folder_id` | uuid? | |
| `name`, `description` | string, string? | |
| `layout` | GridLayout | recomposed from `grid_columns` and `row_height_px` |
| `refresh_policy` | DashboardRefreshPolicy | recomposed from `refresh_mode` and `refresh_interval_minutes` |
| `audience` | `"workspace" \| "shared_only"` | |
| `widgets` | WidgetResponse[] | in `position_index` order |
| `share_summary` | `{ shared_with_count, link_active }` | F036 data, read through `ShareRepository`; counts principals, not people |
| `version` | integer | pass as `If-Match` on the next write |
| `created_at` / `updated_at`, `created_by` / `updated_by` | timestamp, uuid | |
| `deleted_at` | timestamp? | present only when reading a soft-deleted dashboard |

**`WidgetResponse`** `{ id, kind, title, position, config, refresh_override?, cache_summary }` —
`cache_summary` is `{ status, computed_at?, stale }` for the **caller's** `scope_key`, so two viewers
of one dashboard legitimately see different summaries; `computed_at` is absent when no cache entry
exists for that scope.

**`WidgetDataResponse`** — `GET /api/v1/widgets/{id}/data` (FR-F023-05)

| Field | Type | Notes |
|---|---|---|
| `status` | `"fresh" \| "stale" \| "computing" \| "error" \| "unavailable" \| "denied"` | the closed set matching the `widget_cache.status` check |
| `payload` | object? | the per-kind rendered result; absent for `computing`, `unavailable`, `denied`, and for `error` |
| `computed_at` | timestamp? | absent while `computing` |
| `duration_ms` | integer? | of the run that produced the payload |
| `source_versions` | map<source_id, integer> | composed from `widget_cache_sources`; `stale` is `true` when any is behind the live source |
| `error` | `{ message, correlation_id }`? | present only with `status: "error"` |
| `reason` | string? | present with `unavailable` (`"resolver_not_registered"`) and with `denied` |
| `scope` | `"viewer" \| "owner"` | which scope produced the payload |

`denied` is a `200` body, not a `403`: a widget the viewer may not read is a tile state on a page the
viewer may read, and returning a status code would fail the whole dashboard for one tile. A
**dashboard** the caller may not read is still `404 not_found` on this route, so a widget id never
confirms a dashboard exists.

**`RefreshResponse`** `{ run_id, status: "queued", widget_count }`, returned `202`. A refresh while
one is active for the caller's `scope_key` is `409 conflict` carrying that `run_id`.

**List route.** `GET /api/v1/dashboards` returns `Page<DashboardResponse>` in F028's envelope
`{ items, next_cursor, has_more, total? }` with `widgets` omitted from list items, `sort` = `name` or
`updated_at` (default `-updated_at`), `limit` 1–100, filters `workspace_id`, `folder_id`, `name`
(prefix) and `deleted` (bool, default `false`); it returns dashboards the actor can read directly or
through an F036 share.

**Status codes**

| Status | `code` | Produced by |
|---|---|---|
| `202` | — | a refresh accepted and queued |
| `400` | `invalid` | any constraint above — overlapping or out-of-range positions, a 41st widget, an unknown `kind`, a `config` failing its per-kind rules, a `refresh_override` longer than the dashboard interval, a `kind` change on an existing widget, an out-of-range `limit` or a cursor from a different query |
| `403` | `denied` | a viewer or a share-link actor calling `PATCH`, `PUT /widgets`, `DELETE` or `refresh`; share links are read-only on every route (FR-F023-09) |
| `404` | `not_found` | unknown, foreign-tenant or invisible dashboard, folder or widget id, including on `GET /widgets/{id}/data` |
| `409` | `conflict` | duplicate `name` in the folder, stale `If-Match` with `current_version`, a refresh while one is active for the scope, `Idempotency-Key` replayed with a different body |
| `429` | `rate_limited` | the calling application's F028 token bucket is exhausted |
| `503` | `unavailable` | the refresh queue or the outbox is unreachable. A widget whose resolver fails does **not** produce this: it is `status: "error"` on that tile alone (NFR-F023-04) |

### Use case signatures

In `crates/domain/src/dashboards/`. Every one takes `ctx: &ActorContext`, takes a `UnitOfWork` for
writes or a repository trait for reads, never a pool or a connection, and returns the shared
`DomainError`.

```rust
fn create_dashboard(ctx: &ActorContext, uow: &mut UnitOfWork, req: CreateDashboard) -> Result<Dashboard, DomainError>;
fn update_dashboard(ctx: &ActorContext, uow: &mut UnitOfWork, id: DashboardId, expected: Version, req: UpdateDashboard) -> Result<Dashboard, DomainError>;
fn delete_dashboard(ctx: &ActorContext, uow: &mut UnitOfWork, id: DashboardId, expected: Version) -> Result<(), DomainError>;
fn get_dashboard(ctx: &ActorContext, repo: &dyn DashboardRepository, scope: &ViewerScope, id: DashboardId) -> Result<Dashboard, DomainError>;
fn list_dashboards(ctx: &ActorContext, repo: &dyn DashboardRepository, filter: DashboardFilter, page: Cursor) -> Result<Page<Dashboard>, DomainError>;
fn replace_widgets(ctx: &ActorContext, uow: &mut UnitOfWork, registry: &WidgetRegistry, id: DashboardId, expected: Version, widgets: Vec<WidgetInput>) -> Result<Vec<DashboardWidget>, DomainError>;
fn read_widget_data(ctx: &ActorContext, repo: &dyn WidgetCacheRepository, registry: &WidgetRegistry, scope: &ViewerScope, id: WidgetId) -> Result<WidgetData, DomainError>;
fn request_refresh(ctx: &ActorContext, uow: &mut UnitOfWork, id: DashboardId, scope: &ScopeKey) -> Result<RefreshHandle, DomainError>;
fn execute_refresh(ctx: &ActorContext, uow: &mut UnitOfWork, registry: &WidgetRegistry, id: DashboardId, scope: &ScopeKey, run_id: RunId) -> Result<RefreshSummary, DomainError>;
fn compute_widget_stale(repo: &dyn WidgetCacheRepository, id: WidgetId, scope: &ScopeKey) -> Result<bool, DomainError>;
```

**Transaction boundaries.** `replace_widgets` is one `UnitOfWork` covering the grid validation's
accepted set, the inserts, the updates, the deletes of omitted widgets with their cache rows, the
full rewrite of every surviving widget's `dashboard_widget_sources` and `dashboard_widget_columns`
rows, the audit row with the added/removed/moved diff, and the `dashboard.updated.v1` entry. The
invariant is that the layout is never partially applied: overlap is a property of the whole set, so
committing widget 3 before widget 7 is rejected would leave a grid that violates the rule the
endpoint exists to enforce, and a widget whose source rows were rewritten separately would be
permission-checked in FR-F023-05 against sources its `config` no longer names. `execute_refresh`
takes one `UnitOfWork` per widget — the `widget_cache` entry, its `widget_cache_sources` rows and the
per-widget outcome — so a failing widget cannot roll back the widgets that already succeeded, and one
final boundary for the run summary and the `dashboard.refreshed.v1` entry. `read_widget_data` writes
nothing; a cache miss enqueues a `dashboards.refresh-widget` job in its own boundary.

### PostgreSQL/SQLx

- Migration `*_dashboards_*.sql` creates `dashboards(id uuid pk, tenant_id, workspace_id, folder_id null, name text, description text, grid_columns smallint not null default 12 check (grid_columns = 12), row_height_px smallint not null default 80 check (row_height_px between 40 and 200), refresh_mode text not null check (refresh_mode in ('manual','interval','on_open')), refresh_interval_minutes int null check (refresh_interval_minutes between 5 and 1440), audience text default 'workspace', version bigint default 1, audit fields, deleted_at)` and `dashboard_widgets(id uuid pk, tenant_id, dashboard_id, kind text, title text, pos_x smallint, pos_y smallint, pos_w smallint, pos_h smallint, config jsonb, refresh_override int null, position_index int, created_at, updated_at, deleted_at)`.
- Widget references are rows, not JSON: `dashboard_widget_sources(id uuid pk, tenant_id uuid not null, widget_id uuid not null references dashboard_widgets(id) on delete cascade, source_kind text not null check (source_kind in ('report','metric','sheet','file','chart')), source_id uuid not null, role text not null check (role in ('primary','comparison')), created_at)` with `unique (widget_id, source_kind, source_id, role)`; `kpi` and `metric_comparison` write a `primary` metric row plus a `comparison` row when `compare_metric_id` is set, `table` and `report_embed` write a `report` row, `image` writes a `file` row, and chart kinds write a `chart` row when `chart_id` is set. `dashboard_widget_columns(widget_id uuid not null references dashboard_widgets(id) on delete cascade, tenant_id uuid not null, column_ref text not null, position smallint not null, primary key (widget_id, column_ref))` with `unique (widget_id, position)` holds FR-F023-03's ordered `column_refs[]`.
- `dashboard_widgets.config` stays `jsonb`: it holds only the per-kind presentation settings (`markdown`, `alt`, `limit`, inline `chart_spec`, styling), which decision section 2 allows as widget settings — the registry validates them in memory per kind and the database never filters inside them. Preserved on the wire: the `PUT widgets` request and the `GET` response carry the same `config` object, composed by `DashboardWidgetRepository` from the settings column plus the source and column rows; the `limit ≤ 200`, `markdown ≤ 8,000`, `alt ≤ 200`, and per-kind required-field validations stay in the registry with the same `field_errors["widgets[i].config"]` responses; the `unavailable` behaviour for an unregistered resolver is unchanged.
- `widget_cache(tenant_id, widget_id, scope_key text, status text, payload jsonb, computed_at timestamptz, duration_ms int, error text, run_id uuid, primary key (widget_id, scope_key))`. `payload` stays `jsonb`: it is the opaque per-kind rendered result for one `(widget_id, scope_key)` that the database never queries; it is a derived, rebuildable cache serving `GET /api/v1/widgets/{id}/data` and rebuilt by the `dashboards.refresh-widget` job, as decision section 2 requires. Source versions become `widget_cache_sources(widget_id uuid not null, scope_key text not null, tenant_id uuid not null, source_kind text not null, source_id uuid not null, source_version bigint not null, primary key (widget_id, scope_key, source_kind, source_id), foreign key (widget_id, scope_key) references widget_cache(widget_id, scope_key) on delete cascade)`, so FR-F023-05's `stale` comparison against the current source version is a join; the `source_versions` response field is unchanged.
- Invariants: unique partial index on `(tenant_id, workspace_id, coalesce(folder_id, zero uuid), lower(name)) where deleted_at is null`; `check (kind in (twelve kinds))`; `check (pos_w between 1 and 12 and pos_h between 1 and 12 and pos_x + pos_w <= 12)`; overlap prevented in service code inside the replace transaction; `check (refresh_mode <> 'interval' or refresh_interval_minutes is not null)`; `widget_cache.widget_id` foreign key `on delete cascade`; `dashboard_widget_sources.widget_id`, `dashboard_widget_columns.widget_id`, and `widget_cache_sources.(widget_id, scope_key)` foreign keys `on delete cascade`; `check (status in ('fresh','stale','computing','error','denied','unavailable'))`.
- Indexes: `dashboard_widgets(dashboard_id, position_index) where deleted_at is null`, `widget_cache(scope_key, computed_at)` for scheduler scans, `dashboards(tenant_id, workspace_id, updated_at desc)`, `dashboards(refresh_mode, refresh_interval_minutes) where deleted_at is null` for the FR-F023-07 scheduler, `dashboard_widget_sources(source_kind, source_id)` so "which widgets break when this report is deleted" and the per-widget `denied` check are joins.
- Audit events: `dashboard.create`, `dashboard.update`, `dashboard.delete`, `dashboard.widgets.replace` (with added/removed/moved IDs), `dashboard.refresh.request`, `dashboard.refresh.complete`.
- Retention/deletion: cache entries for scopes unread for 7 days are pruned nightly through `prune_cache_unread_since`, taking their `widget_cache_sources` rows with them; soft delete cascades `deleted_at` to widgets and deletes cache; rollback drops the six tables `dashboards`, `dashboard_widgets`, `dashboard_widget_sources`, `dashboard_widget_columns`, `widget_cache`, and `widget_cache_sources`.

### React/TypeScript

- Routes: `/w/:workspaceId/dashboards/new`, `/w/:workspaceId/dashboards/:dashboardId`, `/w/:workspaceId/dashboards/:dashboardId/edit` in `apps/web/src/features/dashboards/`; components `DashboardPage`, `DashboardViewer`, `DashboardBuilder`, `GridCanvas`, `WidgetFrame`, `WidgetPalette`, `WidgetConfigPanel`, `TableWidget`, `ReportEmbedWidget`, `TextWidget`, `ImageWidget`, `UnavailableWidget`, `DeniedWidget`, `FreshnessBadge`, `RefreshPolicyForm`, `ShareDashboardDialog`, `NewDashboardDialog`.
- Widget renderer registry `apps/web/src/features/dashboards/widgetRegistry.ts`: `registerWidgetRenderer(kind, Component)`; F024 registers chart and KPI renderers; unknown kinds render `UnavailableWidget`.
- State: TanStack Query keys `['dashboard', id]`, `['widget-data', widgetId, scopeKey]` (refetch every 3 s while `computing`), `['dashboard-list', workspaceId, filters]`; layout draft in a reducer with undo of the last 20 moves.
- API client: generated `DashboardsApi` with `listDashboards`, `createDashboard`, `getDashboard`, `updateDashboard`, `deleteDashboard`, `replaceWidgets`, `refreshDashboard`, `getWidgetData`.
- Telemetry: `dashboard_created`, `dashboard_opened`, `widget_added` (with `kind`), `widgets_saved` (with `count`), `dashboard_refresh_requested`, `dashboard_shared`, `widget_denied_shown`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F023-01 through FR-F023-13 in `testing/features/F023/requirements/cases.md`
- [ ] Failure/edge-case tests: overlapping widgets, `x + w > 12`, 41 widgets, unknown kind, invalid config per kind, refresh while active, override longer than interval, resolver timeout
- [ ] Permission-negative and tenant-isolation tests: cross-tenant `not_found`, viewer mutation `denied`, share-link mutation and refresh `denied`, denied widget for a restricted source, cache never crosses scopes
- [ ] Rust unit tests: `crates/domain/src/dashboards/` grid validator, registry dispatch, stale computation from `widget_cache_sources`, widget diff; `crates/persistence/src/dashboards/` repository named queries against a real schema
- [ ] API contract/integration tests: every route above with success and each error code
- [ ] Database migration/constraint tests: position checks, kind check, `grid_columns`/`row_height_px` and `refresh_mode`/`refresh_interval_minutes` checks, source-kind and role checks, `dashboard_widget_columns` position uniqueness, cache primary key, every cascade, rollback of all six tables
- [ ] React component tests: `GridCanvas`, `WidgetPalette`, `WidgetConfigPanel`, `DashboardViewer` states
- [ ] Browser E2E tests: build the review dashboard, save, share, open as viewer and as link guest, refresh, stale badge
- [ ] Accessibility tests: axe on builder and viewer, keyboard move and resize, announcements
- [ ] Performance/load tests: 40-widget get p95 under 500 ms, cache hit p95 under 300 ms, full refresh under 60 s

### Fast fanout configuration

- Test harness path: `testing/features/F023/`
- Feature flag: `F023_FEATURE`
- Fixture/seed factory: `testing/fixtures/dashboards.rs` reuses the F021 fixture and adds dashboard "Weekly review" with a table, a report embed, a text, an image, and one `kpi` widget without a resolver; users editor, viewer, restricted viewer, share-link guest, foreign tenant
- Deterministic test data: fixed clock `2026-09-03T00:00:00Z`, fixed UUIDv7 seeds, scanned image file fixture from F017
- Mock/stub contracts: in-memory outbox recorder; JetStream stub for `dashboards.refresh` and `dashboards.refresh-widget`; real F003 and F036 engines; F017 signed URL stub
- Parallel isolation: one schema per test worker, tenant ID per test
- Targeted command: `cargo xtask test-feature F023`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F023/`

## 6. Acceptance criteria

```gherkin
Feature: Dashboard builder

Scenario: Build and share the weekly review
  Given editor Dana has report "Portfolio status" and a scanned logo file
  When she creates dashboard "Weekly review", places a table, a report embed, a text, and an image widget, sets refresh every 30 minutes, saves, and shares with group "Leadership"
  Then GET returns four widgets with positions and cache_summary, dashboard.created.v1 and dashboard.updated.v1 are in the outbox, and share.granted.v1 names the dashboard

Scenario: Overlapping widgets rejected
  Given a table widget at x 0 y 0 w 6 h 4
  When Dana saves a text widget at x 3 y 2 w 6 h 2
  Then the response is 400 invalid with field_errors["widgets[1].position"] and no widget, source, or column row is written

Scenario: Share-link guest sees denied tile and cannot refresh
  Given a share link for "Weekly review" and the table widget's report includes sheet "Risks"
  When a guest without Risks access opens the link
  Then the table widget data has status denied with no payload, other widgets render, and POST refresh returns 403 denied

Scenario: Stale widget refreshed for the viewer's scope
  Given the table widget cache for Lee has a widget_cache_sources row recording report snapshot 12
  When the report refreshes to snapshot 13 and Lee opens the dashboard
  Then the widget shows stale, a refresh-widget job runs for Lee's scope_key, and status returns to fresh with computed_at updated
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F021 (reports, `read_rows`, `ViewerScope`, snapshot versions), F036 (shares, share links, guest identity); decisions sections 2, 3, 4, 6, 7; contracts row F023
- Blocks: F024, F025, F051, F059
- Conflicts with: none (disjoint owned paths)
- External dependencies: NATS JetStream for refresh subjects; F017 signed downloads for image widgets
- Risks and mitigations: per-scope caches multiply with shared dashboards, so scopes unread for 7 days are pruned and interval refresh only targets scopes read in 24 hours; a slow resolver could stall a run, so widgets resolve in parallel with a 20 s timeout and failures are isolated per widget; chart kinds ship without resolvers until F024, so the unavailable state is explicit rather than an error.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F021 and F036 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F023/`
- [ ] Migration file name and owned paths claimed
- [ ] Fixture factory `testing/fixtures/dashboards.rs` and F017 signed URL stub available

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for every mutation and refresh
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F023_FEATURE`, stop refresh consumers, run down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Users can build dashboards on a 12-column grid with table, report embed, text, and image widgets, schedule refreshes with visible freshness per widget, and share them with groups or expiring links; chart and KPI widgets activate with F024.
- Every widget honors the viewer's permissions; sources a viewer cannot read show a denied tile and never leak through the cache.
- Migration adds `dashboards`, `dashboard_widgets`, `dashboard_widget_sources`, `dashboard_widget_columns`, `widget_cache`, and `widget_cache_sources`; rollback drops all six. Feature is off by default behind `F023_FEATURE`.
