---
id: F055
type: feature
status: planned
priority: P2
owner: platform
estimate: 5
target_milestone: M7
parent_epic: E008
depends_on: [F013, F011, F048]
blocks: []
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/calendar-app/**, crates/persistence/src/calendar-app/**, services/api/src/calendar-app/**, apps/web/src/features/calendar-app/**, services/api/migrations/*_calendar-app_*.sql, testing/features/F055/**]
feature_flag: F055_FEATURE
flag_default: off
branch: f055-calendar-app
started_at: null
finished_at: null
---

# F055 — Calendar App

## 1. Identity and dates

- Branch: `f055-calendar-app`
- Capability area: advanced modules (spec 5.11 Calendar App "multi-source calendar aggregation and publishing"; 5.1 WORK-03, WORK-05 and the calendar/timeline bullet "date or date-range mapping, timezone-aware rendering, drag-to-reschedule, recurrence display"; section 6 internationalization "locale-aware dates/numbers, timezones"; section 10 external sharing decision)
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 6, 9, 10; `docs/capability-contracts.md` row F055
- Module slug: `calendar-app`

## 2. Requirement specification

### Problem and user outcome

An F013 calendar view shows one sheet. Operations leads need one calendar that overlays launches from a marketing sheet, maintenance windows from an IT sheet, and leave from a resource sheet, respecting what each viewer may see, rendered correctly across timezones and daylight-saving changes, and subscribable from Outlook or Google Calendar without granting tenant access.

As a calendar editor, I want to aggregate up to 20 sheet or view sources into one calendar with per-source date, title, and color mapping, share it inside the tenant, publish an ICS feed with an expiring revocable token, and reschedule events by dragging, so that teams coordinate across sheets from one permission-aware surface.

### Functional requirements

- **FR-F055-01:** `POST /api/v1/calendars` by a `calendar-editor` creates a calendar with `name` (1–120 chars), `workspace_id`, `default_timezone` (valid IANA zone, defaults to the tenant zone from F049), `week_start` (`monday`|`sunday`), and returns a UUIDv7 `id` with `version` 1; a tenant beyond `max_calendars` receives `409 conflict` with `field_errors.limit`.
- **FR-F055-02:** `PUT /api/v1/calendars/{id}/sources` replaces the source list (1–20 items) where each source names a `sheet_id` or F013 `view_id`, `start_column_id` (date or datetime column), optional `end_column_id` or `duration_column_id`, `title_column_id`, optional `color_column_id` (select column) or fixed `color`, `all_day_rule` (`column_type`|`always`|`never`), and `timezone_source` (`tenant`|`column:<column_id>`|`fixed:<zone>`); a 21st source, a column that is not a date type, or a sheet the editor cannot read returns `400 invalid` with `field_errors.sources[i].<field>`; more than `max_sources_per_calendar` returns `409 conflict`. The request and response keep the flat per-source object with those field names, so the API shape is unchanged; each source is one `calendar_sources` row and each mapped column is one `calendar_source_column_maps(source_id, role, column_id)` row with `role` in `start`, `end`, `duration`, `title`, `color`, and `timezone_source` is stored decomposed as `timezone_source_kind` plus `timezone_column_id` or `timezone_fixed_zone` instead of a delimited string.
- **FR-F055-03:** `GET /api/v1/calendars/{id}/events?from&to&tz` returns events within the window (max 366 days, otherwise `400 invalid`) as `{ id, source_id, row_id, start, end, all_day, title, color, can_edit }` with `start`/`end` as RFC 3339 strings carrying the offset of `tz` (default the calendar zone), computed from stored cell values through the F011 date and working-calendar rules; the aggregator resolves each source's `start`, `end`, `duration`, `title`, and `color` columns by joining `calendar_source_column_maps` on `role`, never by reading a mapping document.
- **FR-F055-04:** Events are filtered per source by the viewer's row-level permission on the source sheet or view (F013 view filters and F003 ACL); sources the viewer cannot read at all are omitted and reported in `hidden_sources` as a count, never by name or ID.
- **FR-F055-05:** Date-only columns produce all-day events with no offset; datetime columns convert from the source zone to `tz` including daylight-saving transitions (an event at 2026-03-29 01:30 Europe/London renders as 02:30 after the switch, and a 2026-10-25 event does not duplicate); a `duration_column_id` in hours produces `end = start + duration`.
- **FR-F055-06:** Dragging an event to a new date calls the F011 route `POST /api/v1/rows/{id}/reschedule` with the row's `If-Match` version and the new start (and end when mapped); the calendar never writes cells through another path, and `can_edit` is false when the viewer lacks `sheet-editor` on the source.
- **FR-F055-07:** `POST /api/v1/calendars/{id}/publish` by the owner or a `calendar-editor` creates a `calendar_publications` row with a 32-byte random token, `expires_at` at most 30 days ahead (default 30, `400 invalid` beyond), `include_details` (`true` sends titles, `false` sends `Busy`), and returns the feed URL; publishing again with `{ revoke: true }` sets `revoked_at` on the current token and emits `calendar.published.v1` with `revoked: true`.
- **FR-F055-08:** `GET /public/calendars/{token}.ics` requires no session, streams an RFC 5545 `VCALENDAR` with `X-WR-CALNAME`, one `VTIMEZONE` per zone used, `VEVENT` with `UID` `<row_id>@<calendar_id>`, `DTSTART`/`DTEND` (or `DTSTART;VALUE=DATE` for all-day), `SUMMARY`, `LAST-MODIFIED`, and an `ETag` derived from the newest source row version; an expired, revoked, or unknown token returns `404 not_found`, and more than 60 requests per minute per token returns `429 rate_limited`.
- **FR-F055-09:** The ICS feed applies the publisher's permissions at request time, never widens them, and includes no attachments, comments, or column values other than the mapped title and dates; a source deleted or un-shared after publication disappears from the feed on the next request.
- **FR-F055-10:** `GET /api/v1/calendars` lists calendars the viewer may read with cursor pagination and filters `workspace_id`, `name` prefix; `PATCH /api/v1/calendars/{id}` updates `name`, `default_timezone`, `week_start`, and `description` with `If-Match`; stale versions return `409 conflict`.
- **FR-F055-11:** Every mutation requires `Idempotency-Key`, writes an `audit_events` row, and publishes `calendar.updated.v1` (create, patch, sources) or `calendar.published.v1` (publish, revoke) through the outbox; cross-tenant access by ID returns `404 not_found`.
- **FR-F055-12:** Every `/api/v1/calendars*` route sits behind `RequireModule(ModuleSlug::CalendarApp)`; a tenant without an active `calendar-app` entitlement receives `403 denied` with `field_errors.module`; the public ICS route checks the publication's tenant entitlement and returns `404 not_found` when the module is not allowed.
- **FR-F055-13:** The web app renders month, week, and agenda layouts with a timezone switcher, a per-source color legend with toggles whose entries come from the source's fixed `color` or, when the source has a `color` role mapping, from the mapped select column's options, a hidden-sources notice, drag-to-reschedule with keyboard equivalent, a source editor dialog, and a publish dialog showing the feed URL, expiry, and revoke action.
- **FR-F055-14:** A viewer with read access sees the calendar without source editing, publish, or drag; a user without access to the calendar sees the not-found state; a viewer whose access covers only some sources sees those sources and the hidden-sources count.

### Non-functional requirements

- **NFR-F055-01 Performance:** `GET /events` for a 31-day window over 20 sources totalling 100,000 rows responds in under 500 ms p95 using indexed date columns; the ICS feed for 5,000 events streams in under 2 seconds; reschedule round-trip under 800 ms p95 (spec section 6).
- **NFR-F055-02 Security/privacy:** publication tokens are 256-bit random, stored hashed (SHA-256), expire within 30 days, are revocable, rate-limited per token, never grant tenant discovery, and the feed contains only mapped fields; permission filtering is applied in the service layer per source with cross-tenant, guest, and field-level negatives in the harness.
- **NFR-F055-03 Accessibility:** month, week, and agenda layouts pass axe with zero serious violations; events are reachable in a roving-tabindex grid, rescheduling has a keyboard path (`Space`, arrows, `Enter`) with live-region announcements, colors carry text labels, and the agenda layout is the screen-reader default.
- **NFR-F055-04 Reliability/observability:** event spans carry `tenant_id`, `calendar_id`, `source_count`, `hidden_sources`, `correlation_id`; metrics `calendar_events_duration_seconds`, `calendar_ics_requests_total{result}`, `calendar_reschedule_total{result}`; stale sources (source sheet missing) render an explicit stale state rather than an empty calendar.

### Scope

Included: calendar CRUD, sources with date/title/color mapping, event aggregation with permission filtering, timezone and DST-correct rendering, drag and keyboard reschedule through F011, ICS publication with expiring revocable tokens, entitlement gating, audit, events, month/week/agenda UI.

Excluded: recurring-event authoring (recurrence display comes from F011 row recurrence fields and is rendered read-only); two-way sync from external calendars (F029 Google/Microsoft adapters); embedding calendars in dashboards or WorkApps (F023, F051 embed the calendar route); notifications for upcoming events (F037 with F018 workflows).

## 3. UX specification

- Entry points: workspace navigation `Calendars` (shown when `useModuleAllowed('calendar-app')`) → `/w/{workspace_id}/calendars`; `New calendar`; calendar page `/w/{workspace_id}/calendars/{calendar_id}?layout=month|week|agenda&tz=<zone>`; `Publish` in the header.
- Primary flow: editor creates `Ops overview`, adds sources `Launches` (start/end date, title, color by `Team`) and `Maintenance` (datetime start, duration hours, fixed color), sees both on the month grid, switches the timezone to `America/Los_Angeles` and watches a maintenance window shift, drags a launch to next week and confirms the reschedule, opens `Publish`, sets 14-day expiry with details, copies the ICS URL, subscribes in an external client.
- Loading: skeleton grid; Empty: `No sources yet` with `Add source`; Error: inline banner with `correlation_id` and retry; Success: toast on save, reschedule, publish; Stale/conflict: reschedule 409 reverts the event and shows `This row changed`; Offline: drag disabled with offline badge; Stale source: source chip shows `Source unavailable`; Not entitled: `ModuleNotEntitled` panel.
- Permission-denied: viewers see no `Add source`, `Publish`, or drag handles; hidden sources show `2 sources hidden by permissions`; no-access renders not-found.
- Responsive: month grid becomes a stacked agenda under 768 px; week view scrolls horizontally with the time gutter frozen; publish dialog full-screen under 640 px.
- Keyboard: arrows move between days and events, `Enter` opens event details, `Space` picks up an event, arrows move by day (week/month) or 15 minutes (week), `Enter` drops, `Escape` cancels; `T` jumps to today; `1/2/3` switch layouts; focus ring from shared tokens; `prefers-reduced-motion` disables drag animation.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062), Lucide icons `CalendarDays`, `CalendarRange`, `List`, `Globe`, `Share2`, `Link`, `EyeOff`; tokens from `apps/web/src/design/tokens.css`.

## 4. Technical specification

Canonical contract: `docs/capability-contracts.md` row F055 (aggregate `calendar`, module `calendar-app`, roles `calendar-editor`; reads via resource ACL and F036 shares).

### Rust backend

- Data access (decision section 2.1): `crates/persistence/src/calendar-app/` holds `CalendarRepository` (owns `calendars`), `CalendarSourceRepository` (owns `calendar_sources` and its child `calendar_source_column_maps`), and `CalendarPublicationRepository` (owns `calendar_publications`). A child table is owned by the repository of its parent object type, so no two classes write the same table. Named queries: `list_calendars_for_viewer`, `find_calendar_by_id`, `count_active_calendars` (the `max_calendars` limit), `load_sources_with_column_map`, `replace_sources`, `count_sources`, `list_sources_referencing_sheet` (stale-source detection), `insert_publication`, `find_active_publication_by_token_hash`, `revoke_active_publication`, `list_publications_for_calendar`, `delete_publications_expired_before`; no generic query escape hatch exists. Source rows are read through the owning features' repositories — F013 `ViewRepository::list_view_rows_in_window` and F006 `RowRepository::list_rows_by_date_column(sheet_id, column_id, from, to, cap)` — and the ICS rate limit through the F038 `RateLimitRepository`. The use cases below depend on these traits and contain no SQL: `aggregate.rs`, the events handler, the public `.ics` handler, and the nightly prune compose named queries and never build SQL in a handler, service, job, or test. Multi-table writes run in one `UnitOfWork`: `replace_sources` deletes and reinserts `calendar_sources` plus their `calendar_source_column_maps` rows, publish inserts a `calendar_publications` row and revokes the previous one, and every audit row and outbox enqueue joins the same transaction.
- Domain entities in `crates/domain/src/calendar-app/`: `Calendar { id, tenant_id, workspace_id, name, description, default_timezone: Tz, week_start: WeekStart, owner_id, version, audit fields, deleted_at }`, `CalendarSource { id, calendar_id, kind: SourceKind (Sheet|View), sheet_id, view_id, columns: ColumnMap (role → column_id for Start, End, Duration, Title, Color, hydrated from `calendar_source_column_maps`), color, all_day_rule, timezone_source: TimezoneSource (Tenant | Column(column_id) | Fixed(zone)), position }`, `CalendarPublication { id, calendar_id, token_hash, expires_at, include_details, revoked_at, created_by, created_at }`, `CalendarEvent { id, source_id, row_id, start: DateTime<FixedOffset>, end, all_day, title, color, can_edit }`.
- Use cases: `create_calendar`, `update_calendar`, `list_calendars`, `replace_sources`, `list_events(calendar, viewer, window, tz)`, `publish_calendar`, `revoke_publication`, `render_ics(publication, now)`; pure functions `normalize_event(cell_values, source, tz) -> Option<CalendarEvent>` and `ics::encode(events, zones, name) -> String` are unit tested against DST fixtures.
- Aggregation: `list_events` calls `CalendarSourceRepository::load_sources_with_column_map` once, then loads rows per source through the F013 `ViewRepository` named query or the F006 `RowRepository` named query with F003 row ACL, restricted to rows whose start column falls in the window (index on `cells` typed date values from F007), then normalizes with `chrono-tz`; it composes those named queries and builds no SQL of its own. Sources failing the read check are counted into `hidden_sources`.
- API endpoints (`services/api/src/calendar-app/`): `GET /api/v1/calendars`, `POST /api/v1/calendars`, `PATCH /api/v1/calendars/{id}`, `PUT /api/v1/calendars/{id}/sources`, `GET /api/v1/calendars/{id}/events`, `POST /api/v1/calendars/{id}/publish`, `GET /public/calendars/{token}.ics`. DTOs: `CreateCalendarRequest`, `UpdateCalendarRequest`, `ReplaceSourcesRequest { sources[] }`, `EventsQuery { from, to, tz? }`, `EventsResponse { events, hidden_sources, tz }`, `PublishRequest { expires_in_days?, include_details, revoke? }`, `PublishResponse { feed_url, expires_at }`, `CalendarResponse`, `Page<CalendarResponse>`. Reschedule reuses the F011 route and DTO.
- Events: `calendar.updated.v1` (create, patch, sources with `changed_fields`), `calendar.published.v1` (`publication_id`, `expires_at`, `revoked: bool`).
- Authorization: `RequireModule(ModuleSlug::CalendarApp)` on the API router; `calendar-editor` on the workspace or calendar owner for mutations; reads via calendar ACL and F036 shares; per-source row filtering via F013/F003; ICS route authenticates by token hash, then evaluates the publisher's permissions; explicit deny wins; foreign tenant → `not_found`.
- Validation: name 1–120; sources 1–20; window ≤ 366 days; `tz` valid IANA; `expires_in_days` 1–30; token lookup constant-time on the hash; rate limit 60/min/token in `rate_limit_buckets` (F038).
- Error mapping: `CalendarError::TooManySources → 400 invalid`, `CalendarError::LimitExceeded → 409 conflict` with `field_errors.limit`, `CalendarError::WindowTooLarge → 400 invalid`, `CalendarError::BadTimezone → 400 invalid`, `PublicationError::Expired|Revoked|Unknown → 404 not_found`, `PublicationError::RateLimited → 429 rate_limited`, `StaleVersion → 409 conflict`, `AuthzError::Denied → 403 denied`, `NotFound → 404`.

### PostgreSQL/SQLx

- Migration `*_calendar-app_*.sql` creates `calendars(id uuid pk, tenant_id uuid not null references tenants(id) on delete restrict, workspace_id uuid not null references workspaces(id) on delete restrict, name text not null, description text, default_timezone text not null, week_start text not null check (week_start in ('monday','sunday')), owner_id uuid not null references users(id) on delete restrict, version bigint not null default 1, created_by uuid not null references users(id) on delete restrict, created_at timestamptz not null, updated_by uuid references users(id) on delete restrict, updated_at timestamptz not null, deleted_at timestamptz)`, `calendar_sources(id uuid pk, tenant_id uuid not null, calendar_id uuid not null references calendars(id) on delete cascade, kind text not null check (kind in ('sheet','view')), sheet_id uuid references sheets(id) on delete restrict, view_id uuid references views(id) on delete restrict, color text, all_day_rule text not null check (all_day_rule in ('column_type','always','never')), timezone_source_kind text not null check (timezone_source_kind in ('tenant','column','fixed')), timezone_column_id uuid references columns(id) on delete restrict, timezone_fixed_zone text, position int not null, created_at, updated_at)`, `calendar_publications(id uuid pk, tenant_id uuid not null, calendar_id uuid not null references calendars(id) on delete cascade, token_hash bytea not null, expires_at timestamptz not null, include_details bool not null default true, revoked_at timestamptz, created_by uuid not null references users(id) on delete restrict, created_at timestamptz not null)`.
- Normalized sets (decision section 2, no repeated columns and no encoded compound values): `calendar_source_column_maps(tenant_id uuid not null, source_id uuid not null references calendar_sources(id) on delete cascade, role text not null check (role in ('start','end','duration','title','color')), column_id uuid not null references columns(id) on delete restrict, primary key (source_id, role))` replaces the repeated `start_column_id`, `end_column_id`, `duration_column_id`, `title_column_id`, and `color_column_id` columns, so the mapping the aggregator reads by key is joinable, constrained, and indexed, and a column deletion is blocked by a real foreign key instead of a dangling id. `timezone_source` is no longer the delimited string `column:<column_id>` / `fixed:<zone>`: it is stored as `timezone_source_kind` plus `timezone_column_id` or `timezone_fixed_zone`. The source list itself remains its own child table `calendar_sources` with `on delete cascade`, since a source cannot outlive its calendar. `ReplaceSourcesRequest`, `EventsResponse`, and the `CalendarResponse` source objects keep the flat `start_column_id`/`title_column_id`/`timezone_source` field names and array ordering by `position`, so no externally visible behaviour changes: `CalendarSourceRepository::replace_sources` fans a request array out to `calendar_sources` and `calendar_source_column_maps` rows and reassembles it on read inside one `UnitOfWork`.
- `jsonb` audit: this module stores no `jsonb` column. The two candidates were rejected or placed elsewhere — the per-source field mapping is queried by key by the aggregator and by the stale-column check, so it is a table (`calendar_source_column_maps`), not a document; the per-viewer layout and `tz` preference is a view setting, and it stays out of this schema entirely because it is carried in the URL (`?layout=&tz=`) and, when persisted, lives in the F013 view-settings row owned by that feature. Event payloads on the outbox and audit diffs keep their platform-wide `jsonb` shape in the F004 outbox and `audit_events` tables, which this feature does not own.
- Invariants: unique `calendars(tenant_id, workspace_id, lower(name)) where deleted_at is null`; check `(kind = 'sheet' and sheet_id is not null and view_id is null) or (kind = 'view' and view_id is not null and sheet_id is null)`; check `(timezone_source_kind = 'tenant' and timezone_column_id is null and timezone_fixed_zone is null) or (timezone_source_kind = 'column' and timezone_column_id is not null and timezone_fixed_zone is null) or (timezone_source_kind = 'fixed' and timezone_fixed_zone is not null and timezone_column_id is null)`; `calendar_source_column_maps` primary key blocks a duplicate role on a source, and every source carries exactly one `start` and one `title` row, enforced by `CalendarSourceRepository::replace_sources` and asserted by the constraint tests; a source has either a fixed `color` or a `color` role row, never both; check `expires_at <= created_at + interval '30 days'`; unique `calendar_publications(token_hash)`; at most one active publication per calendar via partial unique index `where revoked_at is null`; trigger enforcing ≤ 20 sources per calendar.
- Indexes: `calendars(tenant_id, workspace_id, updated_at desc)`, `calendar_sources(calendar_id, position)`, `calendar_sources(sheet_id)` and `calendar_sources(view_id)` for stale-source detection and `list_sources_referencing_sheet`, `calendar_source_column_maps(column_id)` for the reverse "which sources map this column" lookup on column delete, `calendar_publications(token_hash) where revoked_at is null`, `calendar_publications(expires_at)`; the `(source_id, role)` primary key serves the per-source map load and event windows rely on the F007 typed date index on `cells`.
- Audit events: `calendar.create`, `calendar.update`, `calendar.sources.replace`, `calendar.publish`, `calendar.revoke`, `calendar.ics.read` (token id, IP, result) with diffs where applicable.
- Retention/deletion: calendars soft-delete; publications are deleted with the calendar purge (F027); expired tokens are pruned by the nightly job after 90 days through `CalendarPublicationRepository::delete_publications_expired_before`; rollback drops the four tables, children before parents (`calendar_source_column_maps`, `calendar_sources`, `calendar_publications`, `calendars`).

### React/TypeScript

- Routes: `/w/:workspaceId/calendars`, `/w/:workspaceId/calendars/:calendarId` in `apps/web/src/features/calendar-app/`; components `CalendarListPage`, `CalendarPage`, `CalendarHeader`, `LayoutSwitch`, `TimezoneSwitcher`, `MonthGrid`, `WeekGrid`, `AgendaList`, `EventChip`, `EventDetailsPopover`, `SourceLegend`, `HiddenSourcesNotice`, `SourceEditorDialog`, `SourceRow`, `PublishDialog`, `NewCalendarDialog`.
- State: TanStack Query keys `['calendars', workspaceId]`, `['calendar', id]`, `['calendar-events', id, from, to, tz]`; reschedule mutation applies optimistically, rolls back on `conflict`, and invalidates the event window; layout and `tz` persisted in the URL.
- API client: generated `CalendarAppApi` with `listCalendars`, `createCalendar`, `updateCalendar`, `replaceSources`, `listEvents`, `publishCalendar`; reschedule through the F011 `SchedulesApi.rescheduleRow`.
- Gating: `useModuleAllowed('calendar-app')` from `apps/web/src/features/entitlements`; not allowed renders `ModuleNotEntitled`.
- Telemetry: `calendar_created`, `calendar_sources_saved`, `calendar_layout_changed`, `calendar_timezone_changed`, `calendar_event_rescheduled`, `calendar_published`, `calendar_publication_revoked` with `calendar_id`, `layout`, `tz`, `source_count`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F055-01 through FR-F055-14 in `testing/features/F055/requirements/cases.md`
- [ ] Failure/edge-case tests: 21 sources, non-date column, 367-day window, invalid zone, expired token, revoked token, 61st request per minute, reschedule with stale version, deleted source sheet
- [ ] Permission-negative and tenant-isolation tests: hidden sources counted not named, viewer cannot publish or reschedule, foreign tenant not found, ICS never shows unmapped fields, module guard denial
- [ ] Rust unit tests: `normalize_event` DST fixtures (spring forward, fall back, all-day, duration), `ics::encode` folding and escaping, token hashing
- [ ] API contract/integration tests: every route above with success and each error code
- [ ] Database migration/constraint tests: source kind check, timezone-source kind/payload check, duplicate `calendar_source_column_maps` role rejected, source missing its `start` or `title` role rejected, `column_id` foreign key blocks a deleted column, 30-day check, single active publication, 20-source trigger, rollback ordering
- [ ] React component tests: `MonthGrid`, `WeekGrid`, `AgendaList`, `SourceEditorDialog`, `PublishDialog`, `TimezoneSwitcher` states
- [ ] Browser E2E tests: create, add sources, switch zone, drag reschedule, publish and fetch ICS, viewer read-only
- [ ] Accessibility tests: axe on three layouts, keyboard reschedule with announcements, color labels
- [ ] Performance/load tests: events 31 days over 20 sources p95 < 500 ms, ICS 5,000 events < 2 s, reschedule p95 < 800 ms

### Fast fanout configuration

- Test harness path: `testing/features/F055/`
- Feature flag: `F055_FEATURE`
- Fixture/seed factory: `testing/fixtures/calendar_app.rs` builds tenant A (editor, viewer, partial viewer), tenant B, active `calendar-app` entitlement with `max_calendars 20`, `max_sources_per_calendar 20`, three source sheets (`Launches` date range, `Maintenance` datetime plus duration, `Leave` all-day) with DST-spanning rows, one restricted sheet, and a calendar with 20 sources totalling 100,000 rows for performance
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, UTC, fixture rows at 2026-03-29 and 2026-10-25 for Europe/London and 2026-03-08 and 2026-11-01 for America/Los_Angeles
- Mock/stub contracts: outbox recorded in memory; authz uses the real F003 engine; F011 reschedule service called in-process; rate limiter with injectable clock
- Parallel isolation: one schema per test worker, tenant ID per test
- Targeted command: `cargo xtask test-feature F055`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F055/`

## 6. Acceptance criteria

```gherkin
Feature: Calendar App aggregation and publishing

Scenario: Aggregate two sources with timezone conversion
  Given calendar "Ops overview" with sources Launches (date range) and Maintenance (datetime, Europe/London)
  When a viewer requests events for March 2026 with tz America/Los_Angeles
  Then Launches rows appear as all-day events and the 2026-03-29 01:30 London maintenance appears at 2026-03-28 18:30 -07:00
  And the response reports hidden_sources 0

Scenario: Hidden source is counted, not named
  Given the calendar also includes the restricted sheet the viewer cannot read
  When the viewer requests events
  Then the restricted rows are absent and hidden_sources is 1 with no sheet id in the body

Scenario: Viewer cannot publish
  Given a viewer with read access to the calendar
  When they POST publish
  Then the response is 403 denied and no calendar_publications row exists

Scenario: Published feed expires and revokes
  Given an editor publishes with expires_in_days 14 and include_details true
  When the feed is fetched, then revoked, then fetched again
  Then the first fetch returns a VCALENDAR with VTIMEZONE and 3 VEVENTs and the second returns 404 not_found
  And calendar.published.v1 is emitted twice, the second with revoked true

Scenario: Drag reschedule goes through the schedule route
  Given an editor drags a Launches event from 2026-09-10 to 2026-09-17
  When the client calls the row reschedule route with the current version
  Then the row start and end move by 7 days and the event window refetches with the new dates
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F013 (view row queries and calendar view semantics), F011 (date types, working calendars, reschedule route), F048 (`RequireModule`, entitlement limits); F068 (`Repository`/`UnitOfWork` contracts in `crates/persistence`); decisions sections 2, 2.1, 3, 4, 6, 9, 10; contracts row F055
- Blocks: none
- Conflicts with: none (disjoint owned paths)
- External dependencies: external calendar clients (Outlook, Google Calendar, Apple Calendar) validated manually against the ICS output; automated tests use an RFC 5545 parser
- Risks and mitigations: DST edge cases can double or drop events, so normalization uses `chrono-tz` with explicit ambiguous/nonexistent handling and fixture rows on every 2026 transition; a leaked feed token exposes titles, so tokens are hashed at rest, expire within 30 days, are revocable, rate-limited, and `include_details: false` publishes only busy blocks; aggregating 20 large sources could exceed the read budget, so the window is capped at 366 days and each source query uses the typed date index with a per-source row cap of 10,000 and a `truncated_sources` count.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F013, F011, and F048 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F055/`
- [ ] Migration file name and owned paths claimed
- [ ] DST fixture sheets and the RFC 5545 parser available in `testing/harness/`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for every mutation and ICS read
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F055_FEATURE` (routes unmounted, ICS route returns not-found, publications retained), run down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Calendar editors can aggregate up to 20 sheets or views into one permission-aware calendar with month, week, and agenda layouts, timezone switching, drag-to-reschedule, and expiring ICS feeds.
- Migration adds `calendars`, `calendar_sources`, `calendar_source_column_maps`, and `calendar_publications`; rollback drops them children first. Feature is off by default behind `F055_FEATURE` and requires the `calendar-app` entitlement.
