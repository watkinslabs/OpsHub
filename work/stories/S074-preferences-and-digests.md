---
id: S074
type: story
status: planned
parent_epic: E004
parent_feature: F037
depends_on: [S073]
owned_paths: [crates/domain/src/notifications/**, services/api/src/notifications/**, services/worker/src/notifications/**, apps/web/src/features/notifications/**, services/api/migrations/*_notifications_*.sql, testing/features/F037/**]
feature_flag: F037_FEATURE
branch: s074-preferences-and-digests
started_at: null
finished_at: null
---

# S074 — Preferences and digests

## Identity

- Parent feature: `F037` Notification service
- Owner: platform
- Branch: `s074-preferences-and-digests`
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 7; `docs/capability-contracts.md` row F037

## Vertical slice

As a workspace member, I want one settings page where I choose which categories reach me in-app, by email, and by push, silence email overnight, and collapse routine traffic into an hourly or daily digest, so that I keep the notifications I act on and stop being interrupted by the rest.

## Requirements

- **SR-S074-01:** `GET /api/v1/notification-preferences` returns the effective `{ channels: { <category>: { in_app, email, push } }, digest: { cadence, send_at_local, timezone }, quiet_hours: { start_local, end_local, timezone, enabled }, version }` resolved from the user row, tenant defaults, and built-in defaults, and `PUT` replaces it under `If-Match`, returning `409 conflict` on a stale `version` (covers FR-F037-08).
- **SR-S074-02:** `in_app` for `approval` and `system` cannot be turned off; the attempt returns `400 invalid` with `field_errors.channels`, and a `PUT` with `scope = tenant` writes tenant defaults only for a `tenant-admin`, with every other caller denied (FR-F037-08, FR-F037-14).
- **SR-S074-03:** When quiet hours are enabled and creation falls inside the window in the recipient's IANA timezone, email and push deliveries are queued with `next_attempt_at` at the end of the window and the `quiet_hours_release` job re-queues them; in-app is never delayed and `system` ignores quiet hours, including across the Europe/Berlin and America/New_York DST transitions (FR-F037-09).
- **SR-S074-04:** With cadence `hourly` or `daily`, email deliveries outside `approval` and `system` are stored `digested` and `send_digest` sends one email per recipient at `digest_schedules.next_run_at` listing up to 200 items grouped by category, marks them `sent`, publishes `digest.sent.v1 { recipient_id, item_count }`, and advances `next_run_at`; an empty window sends nothing and still advances (FR-F037-10).
- **SR-S074-05:** `send_digest` claims each schedule row with `for update skip locked`, so two workers never send the same digest and a re-run of the same window sends nothing further (FR-F037-10, FR-F037-12).
- **SR-S074-06:** `/settings/notifications` renders the channel matrix, digest cadence and local send time, quiet-hours window, and `Enable push on this device`, and the header `NotificationBell` badge polls every 30 s while the tab is visible, with mark-read on drawer open and `Mark all read` updating the cached `unread_count` optimistically (FR-F037-13).
- **SR-S074-07:** Preference and subscription mutations require `Idempotency-Key`, write `audit_events` rows `preferences.update`, `preferences.tenant-default.update`, `push-subscription.add`, and `push-subscription.remove`, publish no domain event, and return `404 not_found` for cross-tenant IDs (FR-F037-14, NFR-F037-02).
- **SR-S074-08:** The bell, drawer, and settings page report zero serious axe violations, the badge count is announced through `aria-label`, the drawer is a labelled keyboard-reachable region with `Alt+N`, arrow, `Enter`, `R`, and `Escape` handling, and the channel matrix is a table with row and column headers and labelled checkboxes (NFR-F037-03).
- **SR-S074-09:** The digest run processes 10,000 recipients within 10 minutes and inbox reads stay under 500 ms p95 at 10,000 notifications per user while digest rows accumulate (NFR-F037-01, NFR-F037-04).

## Surfaces

- Infrastructure/container: `digest_schedules` scanning job on the F004 worker scheduler; Mailpit for digest assertions; timezone database pinned in the worker image
- Rust service/API: `crates/domain/src/notifications/{preferences.rs, quiet_hours.rs, digest.rs}`; `services/api/src/notifications/{handlers_preferences.rs, dto.rs}`; `services/worker/src/notifications/{send_digest.rs, quiet_hours_release.rs}`
- Data/migration: `services/api/migrations/<ts>_notifications_preferences.sql` creating `notification_preferences` and `digest_schedules` with the cadence check, the `(tenant_id, coalesce(user_id, ...))` uniqueness, and the `digest_schedules(next_run_at)` index
- React/UI: `apps/web/src/features/notifications/{PreferencesPage.tsx, ChannelMatrix.tsx, DigestSettings.tsx, QuietHoursSettings.tsx, PushEnableButton.tsx, routes.ts}`
- Mocks/fixtures: `testing/fixtures/notifications.rs` users `quiet` (20:00–07:00 Europe/Berlin) and `digest` (daily 08:00 America/New_York); fixed clock with timezone advance helpers; fixed VAPID key pair; recording email adapter capturing digest bodies

## TDD harness

- Test path: `testing/features/F037/{requirements,api,frontend,e2e,accessibility,performance}/`
- Feature flag: `F037_FEATURE`
- Targeted command: `cargo xtask test-feature F037`
- Full command: `cargo xtask test-all`
- First failing tests: `preferences_resolve_user_then_tenant_then_default`, `protected_in_app_channel_cannot_be_disabled`, `tenant_scope_put_requires_admin`, `stale_version_put_returns_conflict`, `quiet_hours_defer_email_not_in_app`, `quiet_hours_boundary_survives_dst_shift`, `digest_bundles_items_and_publishes_sent`, `empty_digest_window_sends_nothing`, `concurrent_digest_workers_send_once`, `settings_page_has_no_serious_axe_violations`

## Exit criteria

- [ ] Requirement tests SR-S074-01 through SR-S074-09 written first and failing
- [ ] Tasks T147 and T148 complete and wired through the API router, the worker scheduler, and the web route table
- [ ] Unit, API, database, React, E2E, accessibility, and performance gates pass in targeted and full modes
- [ ] Production call path named: `services/api/src/notifications/handlers_preferences.rs` mounted through `services/api/src/notifications/routes.rs` (`/api/v1/notification-preferences`); `services/worker/src/notifications/{send_digest.rs, quiet_hours_release.rs}` registered in `services/worker/src/registry.rs`; `/settings/notifications` registered in `apps/web/src/routes.tsx`
- [ ] Handoff evidence recorded in the F037 ticket
