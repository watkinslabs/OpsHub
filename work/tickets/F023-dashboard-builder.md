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
owned_paths: [crates/domain/src/dashboards/**, services/api/src/dashboards/**, services/worker/src/dashboards/**, apps/web/src/features/dashboards/**, services/api/migrations/*_dashboards_*.sql, testing/features/F023/**]
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

- **FR-F023-01:** An actor with the `dashboard-editor` role on a workspace can `POST /api/v1/dashboards` with `{ name, workspace_id, folder_id?, description?, refresh_policy: { mode: manual|interval|on_open, interval_minutes? }, layout: { columns: 12, row_height_px: 80 } }`; the response returns a UUIDv7 `id`, `version` 1, and `widgets: []`; `name` is unique per folder (case-insensitive) or the call returns `409 conflict` with `field_errors.name`.
- **FR-F023-02:** `PUT /api/v1/dashboards/{id}/widgets` replaces the full widget set with `If-Match` and a list of 0 to 40 `{ id?, kind, title, position: { x, y, w, h }, config, refresh_override? }`; positions use a 12-column grid with `w` 1..12, `h` 1..12, no overlaps, and `x + w ≤ 12`; an overlap or out-of-range position returns `400 invalid` with `field_errors["widgets[i].position"]`; widgets with an existing `id` keep their `widget_cache`, new widgets receive new IDs, and omitted widgets are deleted.
- **FR-F023-03:** `kind` is one of `kpi`, `metric_comparison`, `table`, `bar`, `line`, `pie`, `burndown`, `timeline`, `workload`, `text`, `image`, `report_embed`; the widget registry validates `config` per kind: `table` and `report_embed` require `report_id` and optional `column_refs[]`, `limit ≤ 200`; `text` requires `markdown` ≤ 8,000 chars; `image` requires `file_id` from F017 plus `alt` ≤ 200 chars; `kpi` and `metric_comparison` require `metric_id` (and `compare_metric_id` for comparison); chart kinds require `chart_id` or an inline `chart_spec`; an unknown kind or invalid config returns `400 invalid` with `field_errors["widgets[i].config"]`.
- **FR-F023-04:** The registry maps each `kind` to a `WidgetResolver`; F023 ships resolvers for `table`, `report_embed`, `text`, and `image`; `kpi`, `metric_comparison`, `bar`, `line`, `pie`, `burndown`, `timeline`, and `workload` are registered by F024 and, until registered, `GET /api/v1/widgets/{id}/data` returns `status: "unavailable"` with `reason: "resolver_not_registered"` and the widget renders the unavailable state.
- **FR-F023-05:** `GET /api/v1/widgets/{id}/data` returns `{ status: fresh|stale|computing|error|unavailable|denied, payload, computed_at, duration_ms, source_versions, error?, scope: viewer|owner }` from `widget_cache` keyed by `(widget_id, scope_key)` using the viewer's F021 `ViewerScope`; a miss enqueues a `dashboards.refresh-widget` job and returns `computing`; `stale` is set when any `source_versions` entry is behind the current source version or the source report has a newer snapshot; `denied` is returned with no payload when the viewer lacks `read` on the widget's report, metric, sheet, or file.
- **FR-F023-06:** `POST /api/v1/dashboards/{id}/refresh` enqueues a refresh of every widget for the caller's `scope_key`, returns `202 { run_id, status: "queued", widget_count }` within 2 seconds, and returns `409 conflict` while a refresh for that scope is active; the worker records per-widget `duration_ms`, `computed_at`, `source_versions`, `status`, and `error`, then publishes `dashboard.refreshed.v1` with `succeeded_count` and `failed_count`.
- **FR-F023-07:** `refresh_policy` `interval` (5..1440 minutes) enqueues refreshes for scopes read in the last 24 hours; `on_open` enqueues when `GET /api/v1/dashboards/{id}` is called and the newest cache entry for the scope is older than 60 seconds; `manual` refreshes only through the endpoint; per-widget `refresh_override` may shorten but never lengthen the dashboard interval.
- **FR-F023-08:** `GET /api/v1/dashboards/{id}` returns `name`, `description`, `layout`, `refresh_policy`, `widgets[]` with `position`, `kind`, `title`, `config`, and `cache_summary { status, computed_at, stale }` per widget for the caller's scope, `share_summary { shared_with_count, link_active }`, and `version`; `GET /api/v1/dashboards` pages by cursor with `limit` 1..100, filters by `workspace_id`, `folder_id`, `name` prefix, `deleted`, and returns dashboards the actor can read directly or through an F036 share.
- **FR-F023-09:** Dashboards are F036 share targets of `target_kind = dashboard`: `POST /api/v1/shares` grants `viewer` or `editor`, and `POST /api/v1/share-links` issues a read-only link expiring within 30 days; a share-link viewer receives every widget through the same `ViewerScope` rules, so widgets whose sources the guest cannot read return `denied` and the page shows the denied tile; share links never allow `PUT widgets`, `PATCH`, or `refresh`.
- **FR-F023-10:** `PATCH /api/v1/dashboards/{id}` updates `name`, `description`, `folder_id`, `refresh_policy`, `layout`, and `audience` (`workspace|shared_only`) with `If-Match`; a stale version returns `409 conflict` with `current_version`; `DELETE` soft-deletes the dashboard, its widgets, and its cache, and revokes its share links; a foreign-tenant actor receives `404 not_found` on every route including `GET /api/v1/widgets/{id}/data`.
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
- Font/icon/design tokens: Inter variable; Lucide `LayoutDashboard`, `Plus`, `Move`, `Share2`, `RefreshCw`, `Image`, `Type`, `Table`; tokens from `apps/web/src/design/tokens.css`.

## 4. Technical specification

### Rust backend

- Domain entities in `crates/domain/src/dashboards/`: `Dashboard { id, tenant_id, workspace_id, folder_id, name, description, layout: GridLayout, refresh_policy: DashboardRefreshPolicy, audience, version, audit fields, deleted_at }`, `DashboardWidget { id, dashboard_id, kind: WidgetKind, title, position: GridPosition, config: WidgetConfig, refresh_override, position_index }`, `WidgetKind` enum with the twelve variants, `WidgetConfig` enum validated per kind, `WidgetCacheEntry { widget_id, scope_key, status, payload, computed_at, duration_ms, source_versions, error }`, `WidgetData { status, payload, computed_at, duration_ms, source_versions, error, scope }`.
- Registry `crates/domain/src/dashboards/registry.rs`: `trait WidgetResolver { fn kind(&self) -> WidgetKind; fn validate(&self, config: &Json) -> Result<WidgetConfig, FieldErrors>; async fn resolve(&self, ctx: ResolveContext, config: &WidgetConfig) -> Result<Payload, ResolveError>; fn source_versions(&self, config) -> Vec<SourceRef>; }` and `WidgetRegistry::register(Box<dyn WidgetResolver>)`; resolvers `TableResolver`, `ReportEmbedResolver` (both call F021 `read_rows` with the viewer scope), `TextResolver`, `ImageResolver` (F017 signed URL).
- Use cases: `create_dashboard`, `update_dashboard`, `delete_dashboard`, `list_dashboards`, `get_dashboard`, `replace_widgets` (grid validation, diff, cache retention), `read_widget_data`, `request_refresh`, `execute_refresh` (worker), `compute_widget_stale`.
- Worker `services/worker/src/dashboards/{refresh_job.rs, scheduler.rs}`: consumes `dashboards.refresh` and `dashboards.refresh-widget`, resolves widgets 8 at a time with a 20 s per-widget timeout, writes cache entries, publishes `dashboard.refreshed.v1`; scheduler enqueues interval and `on_open` refreshes for scopes read in the last 24 hours.
- API endpoints (`services/api/src/dashboards/`): `GET /api/v1/dashboards`, `POST /api/v1/dashboards`, `GET /api/v1/dashboards/{id}`, `PATCH /api/v1/dashboards/{id}`, `DELETE /api/v1/dashboards/{id}`, `PUT /api/v1/dashboards/{id}/widgets`, `POST /api/v1/dashboards/{id}/refresh`, `GET /api/v1/widgets/{id}/data`; DTOs `CreateDashboardRequest`, `UpdateDashboardRequest`, `ReplaceWidgetsRequest { widgets }`, `DashboardResponse`, `WidgetResponse`, `WidgetDataResponse`, `RefreshResponse { run_id, status, widget_count }`.
- Events: `dashboard.created.v1`, `dashboard.updated.v1` (with `changed_fields` including `widgets`), `dashboard.deleted.v1`, `dashboard.refreshed.v1` (payload adds `run_id`, `scope_key`, `succeeded_count`, `failed_count`, `duration_ms`).
- Authorization: `dashboard-editor` on the workspace or F036 `editor` share for mutations; direct ACL, F036 `viewer` share, or valid share link for reads; explicit deny wins; share links are read-only; missing access maps to `not_found`.
- Validation limits: name 1..200, description ≤ 4,000, widgets ≤ 40, title ≤ 120, markdown ≤ 8,000, `limit` ≤ 200 rows for table widgets, config JSON ≤ 32 KB per widget.
- Error mapping: `DashboardError::NameTaken → 409 conflict`, `DashboardError::StaleVersion → 409 conflict`, `DashboardError::RefreshActive → 409 conflict`, `DashboardError::LayoutOverlap → 400 invalid`, `DashboardError::InvalidWidgetConfig → 400 invalid`, `DashboardError::NotFound → 404 not_found`, `AuthzError::Denied → 403 denied`, `ResolveError::Denied → data status denied`, queue unavailable → `503 unavailable`.

### PostgreSQL/SQLx

- Migration `*_dashboards_*.sql` creates `dashboards(id uuid pk, tenant_id, workspace_id, folder_id null, name text, description text, layout jsonb, refresh_policy jsonb, audience text default 'workspace', version bigint default 1, audit fields, deleted_at)`, `dashboard_widgets(id uuid pk, tenant_id, dashboard_id, kind text, title text, pos_x smallint, pos_y smallint, pos_w smallint, pos_h smallint, config jsonb, refresh_override int null, position_index int, created_at, updated_at, deleted_at)`, `widget_cache(tenant_id, widget_id, scope_key text, status text, payload jsonb, computed_at timestamptz, duration_ms int, source_versions jsonb, error text, run_id uuid, primary key (widget_id, scope_key))`.
- Invariants: unique partial index on `(tenant_id, workspace_id, coalesce(folder_id, zero uuid), lower(name)) where deleted_at is null`; `check (kind in (twelve kinds))`; `check (pos_w between 1 and 12 and pos_h between 1 and 12 and pos_x + pos_w <= 12)`; overlap prevented in service code inside the replace transaction; `widget_cache.widget_id` foreign key `on delete cascade`; `check (status in ('fresh','stale','computing','error','denied','unavailable'))`.
- Indexes: `dashboard_widgets(dashboard_id, position_index) where deleted_at is null`, `widget_cache(scope_key, computed_at)` for scheduler scans, `dashboards(tenant_id, workspace_id, updated_at desc)`.
- Audit events: `dashboard.create`, `dashboard.update`, `dashboard.delete`, `dashboard.widgets.replace` (with added/removed/moved IDs), `dashboard.refresh.request`, `dashboard.refresh.complete`.
- Retention/deletion: cache entries for scopes unread for 7 days are pruned nightly; soft delete cascades `deleted_at` to widgets and deletes cache; rollback drops the three tables.

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
- [ ] Rust unit tests: `crates/domain/src/dashboards/` grid validator, registry dispatch, stale computation, widget diff
- [ ] API contract/integration tests: every route above with success and each error code
- [ ] Database migration/constraint tests: position checks, kind check, cache primary key, cascade, rollback
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
  Then the response is 400 invalid with field_errors["widgets[1].position"] and no widget is written

Scenario: Share-link guest sees denied tile and cannot refresh
  Given a share link for "Weekly review" and the table widget's report includes sheet "Risks"
  When a guest without Risks access opens the link
  Then the table widget data has status denied with no payload, other widgets render, and POST refresh returns 403 denied

Scenario: Stale widget refreshed for the viewer's scope
  Given the table widget cache for Lee records report snapshot 12
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
- Migration adds `dashboards`, `dashboard_widgets`, and `widget_cache`; rollback drops them. Feature is off by default behind `F023_FEATURE`.
