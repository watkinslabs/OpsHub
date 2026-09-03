---
id: S110
type: story
status: planned
parent_epic: E008
parent_feature: F055
depends_on: [S109]
owned_paths: [crates/domain/src/calendar-app/**, services/api/src/calendar-app/**, apps/web/src/features/calendar-app/**, testing/features/F055/**]
feature_flag: F055_FEATURE
branch: s110-publishing
started_at: null
finished_at: null
---

# S110 — Publishing

## Identity

- Parent feature: `F055` Calendar App
- Owner: platform
- Branch: `s110-publishing`
- Decision references: `docs/architecture-decisions.md` sections 3, 4, 6, 9, 10; `docs/capability-contracts.md` row F055

## Vertical slice

As a calendar editor, I want to publish an expiring, revocable ICS feed and use month, week, and agenda layouts with a timezone switcher and drag-to-reschedule, so that teams and external calendar clients see the same permission-filtered events rendered correctly in their zone.

## Requirements

- **SR-S110-01:** `POST /api/v1/calendars/{id}/publish` creates a hashed 256-bit token with `expires_in_days` 1–30 and `include_details`, returns `feed_url`, and `{ revoke: true }` sets `revoked_at` and emits `calendar.published.v1` with `revoked: true` (covers FR-F055-07, FR-F055-11).
- **SR-S110-02:** `GET /public/calendars/{token}.ics` streams RFC 5545 output with `X-WR-CALNAME`, `VTIMEZONE` per zone, `UID <row_id>@<calendar_id>`, `DTSTART;VALUE=DATE` for all-day events, `ETag`; expired, revoked, or unknown tokens → `404`; 61st request per minute → `429 rate_limited` (FR-F055-08).
- **SR-S110-03:** The feed applies the publisher's permissions at request time, includes only mapped title and dates (`Busy` when `include_details` is false), drops un-shared or deleted sources, and returns `404` when the tenant's `calendar-app` entitlement is not allowed (FR-F055-09, FR-F055-12, NFR-F055-02).
- **SR-S110-04:** `CalendarPage` renders month, week, and agenda layouts, a timezone switcher persisted in the URL, source legend with toggles, hidden-sources notice, event details popover, and loading, empty, error, denied, stale, offline, and not-entitled states (FR-F055-13, FR-F055-14).
- **SR-S110-05:** Drag or keyboard reschedule calls the F011 `rescheduleRow` client with the row's version, applies optimistically, and reverts with a stale banner on `409 conflict` (FR-F055-06).
- **SR-S110-06:** `SourceEditorDialog` and `PublishDialog` let editors manage sources, publish with expiry and detail level, copy the feed URL, and revoke; viewers see none of these controls (FR-F055-13, FR-F055-14).
- **SR-S110-07:** All three layouts pass axe with zero serious violations, events are a roving-tabindex grid, keyboard reschedule announces moves, and color chips carry text labels (NFR-F055-03).
- **SR-S110-08:** Timezone tests prove DST spring-forward and fall-back rendering in Europe/London and America/Los_Angeles for API, ICS, and UI, and the ICS feed for 5,000 events streams under 2 seconds (FR-F055-05, NFR-F055-01).

## Surfaces

- Infrastructure/container: none new
- Rust service/API: `crates/domain/src/calendar-app/{publication.rs, ics.rs, token.rs, service_publish.rs}`; `services/api/src/calendar-app/{handlers_publish.rs, handlers_public_ics.rs, rate_limit.rs}`
- Data/migration: none new; uses `calendar_publications` from S109
- React/UI: `apps/web/src/features/calendar-app/{CalendarListPage.tsx, CalendarPage.tsx, CalendarHeader.tsx, LayoutSwitch.tsx, TimezoneSwitcher.tsx, MonthGrid.tsx, WeekGrid.tsx, AgendaList.tsx, EventChip.tsx, EventDetailsPopover.tsx, SourceLegend.tsx, HiddenSourcesNotice.tsx, SourceEditorDialog.tsx, SourceRow.tsx, PublishDialog.tsx, NewCalendarDialog.tsx, api.ts, hooks.ts, routes.ts}`
- Mocks/fixtures: DST fixture sheets; RFC 5545 parser helper in `testing/harness/ics.rs`; MSW handlers for component tests; Playwright against real API; rate limiter with injectable clock; 5,000-event generator

## TDD harness

- Test path: `testing/features/F055/{api,frontend,e2e,accessibility,performance}/`
- Feature flag: `F055_FEATURE`
- Targeted command: `cargo xtask test-feature F055`
- Full command: `cargo xtask test-all`
- First failing tests: `publish_creates_hashed_token_with_30_day_cap`, `ics_revoked_token_not_found`, `ics_busy_only_without_details`, `ics_rate_limited_after_60_requests`, `month_grid_renders_dst_shifted_event`, `keyboard_reschedule_calls_f011_route`, `ics_5000_events_under_2s`

## Exit criteria

- [ ] Requirement tests SR-S110-01 through SR-S110-08 written first and failing
- [ ] Tasks T219 and T220 complete; UI wired to real API through generated client
- [ ] Unit, API, React, E2E, accessibility, permission, and performance tests pass
- [ ] Production call path named: `apps/web/src/features/calendar-app/CalendarPage.tsx` mounted at `/w/:workspaceId/calendars/:calendarId`; `services/api/src/calendar-app/handlers_public_ics.rs` mounted at `/public/calendars/{token}.ics` in `services/api/src/router.rs`
- [ ] Handoff evidence recorded in the F055 ticket
