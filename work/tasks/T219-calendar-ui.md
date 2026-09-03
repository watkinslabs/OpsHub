---
id: T219
type: task
status: planned
parent_epic: E008
parent_feature: F055
parent_story: S110
depends_on: [S110]
owned_paths: [crates/domain/src/calendar-app/**, services/api/src/calendar-app/**, apps/web/src/features/calendar-app/**, testing/features/F055/api/**, testing/features/F055/frontend/**]
feature_flag: F055_FEATURE
branch: t219-calendar-ui
started_at: null
finished_at: null
---

# T219 — Calendar UI

## Identity

- Parent story: `S110` Publishing
- Owner: platform
- Branch: `t219-calendar-ui`
- Decision references: `docs/architecture-decisions.md` sections 3, 4, 6, 10; `docs/capability-contracts.md` row F055

## Objective

Implement ICS publication and the public feed route on the backend, and the calendar pages with month, week, and agenda layouts, timezone switcher, source editor, publish dialog, and drag or keyboard reschedule wired to the real API.

## Specification

- Owned paths: `crates/domain/src/calendar-app/{publication.rs, ics.rs, token.rs, service_publish.rs}`, `services/api/src/calendar-app/{handlers_publish.rs, handlers_public_ics.rs, rate_limit.rs}`, `apps/web/src/features/calendar-app/{CalendarListPage.tsx, CalendarPage.tsx, CalendarHeader.tsx, LayoutSwitch.tsx, TimezoneSwitcher.tsx, MonthGrid.tsx, WeekGrid.tsx, AgendaList.tsx, EventChip.tsx, EventDetailsPopover.tsx, SourceLegend.tsx, HiddenSourcesNotice.tsx, SourceEditorDialog.tsx, SourceRow.tsx, PublishDialog.tsx, NewCalendarDialog.tsx, api.ts, hooks.ts, routes.ts}`
- Contract/input: `POST /api/v1/calendars/{id}/publish` with `PublishRequest { expires_in_days? (1–30), include_details, revoke? }`, `Idempotency-Key`, `If-Match`; `GET /public/calendars/{token}.ics` with no session, `If-None-Match`; generated `CalendarAppApi` client plus F011 `SchedulesApi.rescheduleRow`; route params `workspaceId`, `calendarId`, query `layout`, `tz`.
- Output/behavior: publish stores SHA-256 of a 32-byte random token, returns `PublishResponse { feed_url, expires_at }`, revoke sets `revoked_at`, both emit `calendar.published.v1` and audit rows; the ICS handler resolves the token hash in constant time, checks expiry, revocation, and the tenant's `calendar-app` entitlement (`404` on any failure), enforces 60 requests per minute per token via `rate_limit_buckets` (`429`), renders RFC 5545 with `X-WR-CALNAME`, `VTIMEZONE` blocks, `UID <row_id>@<calendar_id>`, `DTSTART;VALUE=DATE` for all-day, `SUMMARY` or `Busy`, `LAST-MODIFIED`, `ETag` from the newest row version with `304` on match, and writes audit `calendar.ics.read`; pages render layouts, timezone switcher persisted in the URL, legend toggles, hidden-sources notice, details popover, source editor, publish dialog with copy and revoke; drag and keyboard reschedule call `rescheduleRow` optimistically and revert on `409` with the stale banner; states: loading skeleton, empty with `Add source`, error banner with correlation ID, denied affordances for viewers, not-found, stale source chip, offline badge, `ModuleNotEntitled` via `useModuleAllowed('calendar-app')`; telemetry `calendar_created`, `calendar_sources_saved`, `calendar_layout_changed`, `calendar_timezone_changed`, `calendar_event_rescheduled`, `calendar_published`, `calendar_publication_revoked`.
- Dependencies: T218 permissions; F011 reschedule route; F038 `rate_limit_buckets`; F048 hooks; F005 workspace shell navigation entry.
- Feature flag: `F055_FEATURE` read through the flag hook; routes not registered and ICS route returns not-found when off.

## TDD

- Failing test first: `testing/features/F055/api/publish_tests.rs::publish_creates_hashed_token_with_30_day_cap`, `::publish_viewer_denied`, `::ics_streams_vtimezone_and_events`, `::ics_revoked_token_not_found`, `::ics_busy_only_without_details`, `::ics_rate_limited_after_60_requests`, `::ics_etag_returns_304`, `::ics_not_found_when_module_not_allowed`; `testing/features/F055/frontend/MonthGrid.test.tsx::month_grid_renders_dst_shifted_event`, `::keyboard_reschedule_calls_f011_route`, `::rolls_back_on_conflict`, `AgendaList.test.tsx::agenda_lists_events_in_selected_zone`, `SourceEditorDialog.test.tsx::blocks_21st_source`, `PublishDialog.test.tsx::copy_url_and_revoke`, `CalendarPage.test.tsx::viewer_has_no_edit_controls`, `::shows_hidden_sources_notice`
- Targeted command: `cargo xtask test-feature F055`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: DST fixture sheets; RFC 5545 parser helper `testing/harness/ics.rs`; MSW handlers from the fixture; rate limiter with injectable clock; role-switching session helper

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] API and component lanes pass; pages mounted on their routes; ICS route mounted in `services/api/src/router.rs`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S110
- [ ] `finished_at` recorded
