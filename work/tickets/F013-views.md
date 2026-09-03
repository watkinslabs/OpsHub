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
owned_paths: [crates/domain/src/views/**, services/api/src/views/**, apps/web/src/features/views/**, services/api/migrations/*_views_*.sql, testing/features/F013/**]
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

As a sheet member, I want to save named views of a sheet with filters, sorts, grouping, visible columns, and card, calendar, or timeline settings, and share them with people or a link, so that everyone plans from one record set through the presentation that fits their work.

### Functional requirements

- **FR-F013-01:** An actor with `sheet-viewer` on a sheet can create a view with `sheet_id`, `name` (1–120 chars), `kind` in `grid|card|calendar|timeline`, `visibility` in `private|sheet|link`, and typed `settings`; the response returns a UUIDv7 `id`, `version` 1, and `owner_id` equal to the actor; a sheet with 100 non-deleted views returns `invalid` with `field_errors.sheet_id = "view_limit"`.
- **FR-F013-02:** View `settings.filter` is a typed AST of `and`/`or` groups whose leaf conditions reference a column ID and an operator valid for that column type (`eq`, `neq`, `contains`, `in`, `is_empty`, `gt`, `lt`, `between`, `before`, `after`, `is_me`); an unknown column, a type-mismatched operator, or more than 50 leaf conditions returns `invalid` with `field_errors.settings.filter`.
- **FR-F013-03:** `settings.sorts` holds at most 5 `{ column_id, direction }` entries, `settings.group_by` is one column ID or null, and `settings.columns` is the ordered list of visible column IDs; unknown column IDs return `invalid`.
- **FR-F013-04:** A `card` view requires `settings.card.lane_column_id` to be a `select` column; it accepts `card_fields` (≤ 8 column IDs) and optional `swimlane_column_id`; a `calendar` view requires either `date_column_id` or the pair `start_column_id`/`end_column_id` of `date|datetime` type plus `mode` in `month|week|day`; a `timeline` view requires `start_column_id`, `end_column_id`, `zoom` in `day|week|month|quarter`, and optional `color_by_column_id`; a `gantt` settings block is stored opaquely for F012.
- **FR-F013-05:** `GET /api/v1/views/{id}/rows` applies the view filter, sorts, and grouping server-side over the F008 row query, returns cursor pages with `limit` 1–500 in `group` then `sort` order, includes only the view's visible columns plus the primary column, and never returns rows or cells the actor cannot read.
- **FR-F013-06:** Calendar rendering resolves the display timezone from `sheet_schedule_settings.timezone` (F011) and falls back to the user locale timezone (F049); rows with a recurrence rule render every occurrence in range read-only, and the row list for calendar and timeline kinds accepts `range_start` and `range_end` (≤ 366 days apart).
- **FR-F013-07:** Dragging a card between lanes calls `PATCH /api/v1/sheets/{sheet_id}/cells` (F008) for the lane column with `If-Match`, and dragging a bar or event on calendar or timeline calls `POST /api/v1/rows/{id}/reschedule` (F011); a `conflict` response rolls the item back and shows the stale banner.
- **FR-F013-08:** `PATCH /api/v1/views/{id}` updates `name`, `visibility`, `is_default`, and `settings` with `If-Match`; only the view owner or a `sheet-editor` may update a `sheet` view, only the owner may update a `private` view, and marking `is_default` clears the previous default in the same transaction.
- **FR-F013-09:** `DELETE /api/v1/views/{id}` soft-deletes the view and its shares; the default view cannot be deleted (`invalid` with `field_errors.is_default`); a deleted view returns `not_found` on every route.
- **FR-F013-10:** `POST /api/v1/views/{id}/share` by the owner creates a `view_shares` row with `principal_kind` in `user|group|link`, `principal_id`, `role` in `viewer|editor`, and for `link` an `expires_at` no more than 30 days out and a signed token; the response contains the share ID and, for links, the URL served by `GET /public/views/{token}`, which resolves the token to a read-only `ViewLinkActor`; a non-owner receives `denied`. This route is the view-specific link surface; general resource share links and guest invitations are F036 and are not duplicated here.
- **FR-F013-11:** `GET /api/v1/sheets/{sheet_id}/views` lists views the actor may see: their own `private` views, all `sheet` views, and views shared to them or their groups, with cursor pagination, `filter` by `kind`, and `sort` by `name` or `updated_at`; foreign-tenant or unshared private views return `not_found`.
- **FR-F013-12:** Every mutation requires `Idempotency-Key`, writes an `audit_events` row, and publishes `view.created.v1`, `view.updated.v1`, `view.deleted.v1`, or `view.shared.v1` through the outbox with `changed_fields`.
- **FR-F013-13:** The web app renders `CardView`, `CalendarView`, and `TimelineView` from the saved view, a `ViewSwitcher` listing accessible views with the default first, a `ViewSettingsPanel` with `FilterBuilder`, and a `ShareViewDialog`; the route is `/w/:workspaceId/sheets/:sheetId/views/:viewId`.
- **FR-F013-14:** Exporting a view calls `POST /api/v1/exports` (F010) with `view_id`, and the export job applies the same filter, sort, visible columns, and permission filtering as the row list.

### Non-functional requirements

- **NFR-F013-01 Performance:** `GET /views/{id}/rows` with a 3-condition filter and 2 sorts over a 100,000-row sheet responds in under 500 ms p95 for a 500-row page; a card lane move (cell patch) responds in under 800 ms p95; calendar month range over 5,000 dated rows renders in under 500 ms p95.
- **NFR-F013-02 Security/privacy:** row and cell permission filtering runs in the service layer on every view row read; link shares expire within 30 days, are revocable, grant no tenant discovery, and never permit writes; cross-tenant view IDs return `not_found`.
- **NFR-F013-03 Accessibility:** card, calendar, and timeline pass axe with zero serious violations; lane moves, calendar day changes, and timeline bar moves are keyboard operable and announced through a live region; motion respects `prefers-reduced-motion`.
- **NFR-F013-04 Reliability/observability:** every view read carries a span with `tenant_id`, `sheet_id`, `view_id`, and `correlation_id`; filter compile errors are counted in `views_filter_compile_errors_total`; outbox publish failure never loses the write.

### Scope

Included: saved view CRUD, typed filter AST, sorts, grouping, visible columns, card/calendar/timeline settings and rendering, default view, personal versus sheet visibility, user/group/link shares, server-side filtered row list, drag interactions delegated to F008 and F011, view export handoff, audit and events.

Excluded: Gantt rendering and dependency arrows (F012), restricted field-level dynamic views (F050), embed and public publication rendering beyond the link token (F059), conditional formatting (F060), multi-source calendar app (F055), report views (F021), the grid editor itself (F008).

## 3. UX specification

- Entry points: sheet header `ViewSwitcher` dropdown with `New view`; route `/w/{workspace_id}/sheets/{sheet_id}/views/{view_id}`; `Share` button in the view header; `Export` in the view overflow menu.
- Primary flow: open a sheet, choose `New view`, pick `Card`, select the `Status` lane column, save; cards appear in lanes per status; drag a card from `Backlog` to `Doing`, the API confirms and the card stays; switch to a `Calendar` view keyed on `Due`, drag an event to the next week, the row is rescheduled; open `Share`, add a group as viewer, copy the 30-day link.
- Loading: lane, month grid, and timeline skeletons; Empty: `No rows match this view` with `Clear filters`; Error: banner with `correlation_id` and retry; Success: toast on save and share; Stale/conflict: dragged item snaps back with `This row changed` banner and `Reload`; Offline: drag disabled with offline badge.
- Permission-denied: viewers see cards, events, and bars without drag handles; share button hidden for non-owners; unshared private view URL renders the not-found page.
- Responsive: lanes scroll horizontally with snap under 768 px; calendar switches to agenda list under 640 px; timeline shows a day zoom with a pinned row label column under 640 px.
- Keyboard: `Tab` reaches switcher, settings, share, then each lane, event, or bar; `Space` picks up, arrows move by lane, day, or zoom unit, `Enter` drops, `Escape` cancels; `FilterBuilder` rows are reachable and deletable by keyboard; focus returns to the trigger after dialogs close.
- Font/icon/design tokens: Inter variable, Lucide icons `LayoutGrid`, `Kanban`, `CalendarDays`, `GanttChart`, `Filter`, `Share2`, `Download`, `Star`; tokens from `apps/web/src/design/tokens.css`.

## 4. Technical specification

### Rust backend

- Domain entities: `View { id, tenant_id, sheet_id, owner_id, name, kind: ViewKind, visibility: Visibility, is_default, settings: ViewSettings, version, created/updated actor+time, deleted_at }`, `ViewSettings { filter: Option<FilterNode>, sorts: Vec<SortSpec>, group_by: Option<ColumnId>, columns: Vec<ColumnId>, card: Option<CardSettings>, calendar: Option<CalendarSettings>, timeline: Option<TimelineSettings>, gantt: Option<serde_json::Value> }`, `FilterNode::{And(Vec<FilterNode>), Or(Vec<FilterNode>), Leaf { column_id, op: FilterOp, value }}`, `ViewShare { id, tenant_id, view_id, principal_kind: PrincipalKind, principal_id, role: ShareRole, token_hash, expires_at, revoked_at }`.
- Use cases in `crates/domain/src/views/`: `create_view`, `update_view`, `delete_view`, `get_view`, `list_views`, `list_view_rows`, `share_view`, `revoke_share`, `compile_filter` (AST to SQL predicate over F008 row query with column type table), `validate_settings`.
- API endpoints (`services/api/src/views/`): `GET /api/v1/sheets/{sheet_id}/views`, `POST /api/v1/views`, `GET /api/v1/views/{id}`, `PATCH /api/v1/views/{id}`, `DELETE /api/v1/views/{id}`, `GET /api/v1/views/{id}/rows`, `POST /api/v1/views/{id}/share`. DTOs `CreateViewRequest`, `UpdateViewRequest`, `ShareViewRequest`, `ViewResponse`, `ViewShareResponse`, `Page<ViewRowResponse>`; row query `{ cursor?, limit?, range_start?, range_end? }`.
- Events: `view.created.v1`, `view.updated.v1`, `view.deleted.v1`, `view.shared.v1` with contract payload and `changed_fields`.
- Authorization: `sheet-viewer` on the sheet to create and read; owner or `sheet-editor` to update `sheet` views; owner only for `private` views and for `share`; link principals resolve to a `ViewLinkActor` with read-only scope; sheet ACL and explicit deny win over any share.
- Validation: name 1–120, ≤ 100 views per sheet, ≤ 50 filter leaves, ≤ 5 sorts, ≤ 8 card fields, range ≤ 366 days, `limit` 1–500, link `expires_at` ≤ now + 30 days. Idempotency keys stored 24 hours. `If-Match` compared inside the update transaction.
- Error mapping: `ViewError::Limit → 400 invalid`, `ViewError::BadFilter → 400 invalid` with `field_errors.settings.filter`, `ViewError::DefaultDelete → 400 invalid`, `ViewError::StaleVersion → 409 conflict`, `ViewError::NotFound → 404 not_found`, `AuthzError::Denied → 403 denied`, expired link → `404 not_found`.

### PostgreSQL/SQLx

- Migration `*_views_*.sql` creates `views(id uuid pk, tenant_id uuid not null, sheet_id uuid not null references sheets(id) on delete restrict, owner_id uuid not null, name text not null, kind text not null check (kind in ('grid','card','calendar','timeline')), visibility text not null check (visibility in ('private','sheet','link')), is_default bool not null default false, settings jsonb not null default '{}', version bigint not null default 1, created_by, created_at, updated_by, updated_at, deleted_at)` and `view_shares(id uuid pk, tenant_id uuid not null, view_id uuid not null references views(id) on delete restrict, principal_kind text not null check (principal_kind in ('user','group','link')), principal_id uuid null, role text not null check (role in ('viewer','editor')), token_hash bytea null, expires_at timestamptz null, revoked_at timestamptz null, version bigint not null default 1, audit fields)`.
- Invariants: partial unique index `views_default_per_sheet_idx on (sheet_id) where is_default and deleted_at is null`; unique `views_sheet_owner_name_idx on (sheet_id, owner_id, lower(name)) where deleted_at is null`; check `link shares have token_hash and expires_at not null and principal_id null`; check `user/group shares have principal_id not null`.
- Indexes: `views(tenant_id, sheet_id, updated_at desc) where deleted_at is null`, `views(tenant_id, owner_id)`, `view_shares(view_id) where revoked_at is null`, unique `view_shares(token_hash) where token_hash is not null`, GIN on `settings` for column-usage lookups when F007 deletes a column.
- Audit events: `view.create`, `view.update`, `view.delete`, `view.share`, `view.share-revoke` with field-level diffs; share tokens are hashed and never logged.
- Retention/deletion: soft delete sets `deleted_at` on the view and `revoked_at` on its shares; purge follows the F027 retention job; rollback drops both tables.

### React/TypeScript

- Routes: `/w/:workspaceId/sheets/:sheetId/views/:viewId` and `/w/:workspaceId/sheets/:sheetId/views/new` in `apps/web/src/features/views/`; components `ViewPage`, `ViewSwitcher`, `ViewSettingsPanel`, `FilterBuilder`, `SortEditor`, `CardView`, `CardLane`, `ViewCard`, `CalendarView`, `CalendarEvent`, `TimelineView`, `TimelineBar`, `ShareViewDialog`, `ExportViewButton`.
- State: TanStack Query keys `['views', sheetId]`, `['view', viewId]`, `['view-rows', viewId, cursor, rangeStart, rangeEnd]`; mutations invalidate by key and update cached `version`; lane and date drags are optimistic with rollback on `conflict`.
- API client: generated `ViewsApi` with `listViews`, `createView`, `getView`, `updateView`, `deleteView`, `listViewRows`, `shareView`; reuses `GridApi.patchCells` (F008) and `SchedulesApi.rescheduleRow` (F011).
- Date formatting: calendar and timeline labels use the F049 locale formatter with the resolved timezone.
- Telemetry: `view_created`, `view_opened`, `view_kind_changed`, `card_lane_moved`, `calendar_event_rescheduled`, `timeline_bar_moved`, `view_shared`, `view_exported` with `sheet_id`, `view_id`, `kind`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F013-01 through FR-F013-14 in `testing/features/F013/requirements/cases.md`
- [ ] Failure/edge-case tests: 51-leaf filter, operator mismatched to column type, lane column not select, deleting the default view, link share past 30 days, expired link, range over 366 days
- [ ] Permission-negative and tenant-isolation tests: cross-tenant view returns `not_found`, non-owner share returns `denied`, unshared private view hidden from list, link actor cannot patch cells, hidden rows excluded from view rows
- [ ] Rust unit tests: `crates/domain/src/views/` filter compile per operator, settings validation per kind, share token hashing and expiry
- [ ] API contract/integration tests: every route above with success and each error code
- [ ] Database migration/constraint tests: default-per-sheet index, name uniqueness per owner, share check constraints, token hash uniqueness, rollback
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

Scenario: Link share expires
  Given a link share created with expires_at 31 days out
  When the owner submits it
  Then the response is 400 invalid with field_errors.expires_at

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
- Risks and mitigations: a filter compiled to SQL could bypass the permission predicate, so `compile_filter` produces a predicate that is always ANDed inside the F008 permission-filtered query and a test asserts hidden rows never appear; jsonb settings referencing deleted columns are pruned by a listener on `column.deleted.v1` so views never fail to load; large calendars are bounded by the 366-day range and 5,000-row page test.
- Open questions: none

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
- Migration adds `views` and `view_shares`; rollback drops them. Feature is off by default behind `F013_FEATURE`.
