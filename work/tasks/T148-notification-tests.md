---
id: T148
type: task
status: planned
parent_epic: E004
parent_feature: F037
parent_story: S074
depends_on: [T147]
owned_paths: [testing/features/F037/**]
feature_flag: F037_FEATURE
branch: t148-notification-tests
started_at: null
finished_at: null
---

# T148 — Notification tests

## Identity

- Parent story: `S074` Preferences and digests
- Owner: platform
- Branch: `t148-notification-tests`
- Decision references: `docs/architecture-decisions.md` sections 7, 9; `docs/capability-contracts.md` row F037

## Objective

Complete the F037 suite end to end: the fixture factory and recording adapters, the browser journeys from mention to read, digest and push enrolment, the accessibility gates on bell, drawer, and settings, and the performance gates for inbox, routing, and digest throughput.

## Specification

- Owned paths: `testing/features/F037/{requirements,api,database,frontend,e2e,accessibility,performance}/` and the fixture entry point `testing/fixtures/notifications.rs` consumed from them
- Contract/input: every FR-F037-01 through FR-F037-14 and NFR-F037-01 through NFR-F037-04 case listed in `testing/features/F037/requirements/cases.md` must have an executable test in the lane named on its row; seeds are the fixed UUIDv7 set, the fixed clock `2026-09-03T00:00:00Z`, and the fixed VAPID key pair.
- Output/behavior: E2E journeys drive mention to bell badge, drawer open and mark-read, `Mark all read`, preferences save with quiet hours and daily digest, a digest email asserted in Mailpit, and push enrolment with a stubbed service worker; accessibility runs axe on the drawer and `/settings/notifications` asserting zero serious violations, keyboard traversal `Alt+N`, arrows, `Enter`, `R`, `Escape`, the `aria-label` badge announcement, and the matrix row and column headers; performance asserts inbox list and unread count under 500 ms p95 at 10,000 notifications per user, creation plus routing under 50 ms p95 inside the producer transaction, email attempted within 5 s p95 outside quiet hours, and a 10,000-recipient digest run under 10 minutes, with metrics `notifications_created_total{category}`, `notification_deliveries_total{channel,status}`, `notification_delivery_latency_seconds{channel}`, `digest_items_total`, and `push_subscriptions_gone_total` asserted present; every lane runs schema-per-worker with a tenant ID per test and writes evidence to `testing/evidence/F037/`; each gate carries a positive control that reintroduces a known defect, observes RED, restores, and observes GREEN.
- Dependencies: T145, T146, and T147 for the routes, jobs, and UI under test; F004 embedded JetStream and Mailpit; F002 seeded users and timezones.
- Feature flag: `F037_FEATURE` enabled explicitly by both the targeted and the full command.

## TDD

- Failing test first: `testing/features/F037/e2e/inbox_journey.spec.ts::mention_reaches_bell_and_opens_source`, `::mark_all_read_clears_badge_without_reload`, `::preferences_save_persists_quiet_hours_and_digest`, `::daily_digest_email_lands_in_mailpit`, `::push_enrolment_registers_subscription`; `testing/features/F037/accessibility/a11y_tests.ts::drawer_has_no_serious_axe_violations`, `::settings_page_has_no_serious_axe_violations`, `::badge_count_is_announced`, `::drawer_keyboard_traversal_returns_focus_to_bell`, `::channel_matrix_has_row_and_column_headers`; `testing/features/F037/performance/load_tests.rs::inbox_p95_under_500ms_at_10k_notifications`, `::create_and_route_p95_under_50ms`, `::digest_run_of_10k_recipients_under_10_minutes`, `::delivery_metrics_are_exported`
- Targeted command: `cargo xtask test-feature F037`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/notifications.rs` seeding the tenant, `dana`, `quiet`, `digest`, a tenant-admin, a foreign tenant, and 300 notifications across categories; recording email and push adapters with scripted failures; Mailpit for E2E; embedded JetStream; stubbed service worker for push permission states

## Exit criteria

- [ ] Every FR and NFR row in `testing/features/F037/requirements/cases.md` maps to a named executable test
- [ ] Targeted and full modes both pass and are reproducible in parallel
- [ ] Positive control recorded for each gate: known defect RED, restore, GREEN
- [ ] Evidence artifacts written to `testing/evidence/F037/`
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S074
- [ ] `finished_at` recorded
