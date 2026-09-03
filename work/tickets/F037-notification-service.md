---
id: F037
type: feature
status: planned
priority: P0
owner: platform
estimate: 8
target_milestone: M3
parent_epic: E004
depends_on: [F004, F002]
blocks: [F020, F029, F058, F061]
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/notifications/**, services/api/src/notifications/**, services/worker/src/notifications/**, apps/web/src/features/notifications/**, services/api/migrations/*_notifications_*.sql, testing/features/F037/**]
feature_flag: F037_FEATURE
flag_default: off
branch: f037-notification-service
started_at: null
finished_at: null
---

# F037 — Notification service

## 1. Identity and dates

- Branch: `f037-notification-service`
- Capability area: automation and notifications (spec 5.5 AUTO-02 send email/in-app/push, notification preferences bullet; section 3 Notification service; section 8 notification verification)
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 7; `docs/capability-contracts.md` row F037
- Aggregate: `notification`
- Module slug: `notifications`

## 2. Requirement specification

### Problem and user outcome

Comments, approvals, workflows, and update requests all need to tell people something, and each would otherwise build its own email code with its own failures and no user control. Users need one inbox, one place to choose channels, digests, and quiet hours, and administrators need to see whether a message was delivered.

As a workspace member, I want to be notified in the app, by email, or by push when I am mentioned, assigned, or asked to approve, on the schedule and channels I choose, so that I act on work without being interrupted by messages I did not ask for.

### Functional requirements

- **FR-F037-01:** Producers create notifications through the in-process `NotificationService::create(NotificationRequest { tenant_id, recipient_id, category, title (≤ 200 chars), body (≤ 2,000 chars), link, source: { kind, id }, dedupe_key?, actor_id? })` or through the JetStream consumer that maps `mention.created.v1` to `mention`, `approval.requested.v1` and `approval.escalated.v1` to `approval`, `share.granted.v1` and `guest.invited.v1` to `share`, `proof.decided.v1` to `review`, `update-request.sent.v1` and `update-request.reminded.v1` to `update_request`, and `workflow-run.failed.v1` to `workflow`; F019 `assign` and `send` actions call `create` with `assignment` or `workflow`; each creation inserts a `notifications` row and publishes `notification.created.v1`.
- **FR-F037-02:** Categories are `mention`, `assignment`, `approval`, `share`, `review`, `update_request`, `workflow`, and `system`; a request with another value is rejected with `NotificationError::InvalidCategory`; a `dedupe_key` repeated for the same `(tenant_id, recipient_id)` within 24 hours returns the existing notification and creates no second row or delivery.
- **FR-F037-03:** On creation the router reads the recipient's effective preferences (user row, else tenant defaults, else built-in defaults: in-app on for all categories, email on for `approval`, `assignment`, `mention`, `update_request`, push off, no digest, no quiet hours) and inserts one `notification_deliveries` row per enabled channel with `status = queued`; a disabled channel produces a `suppressed` row with `reason = preference`.
- **FR-F037-04:** In-app delivery is immediate: `GET /api/v1/notifications` returns the recipient's notifications newest first with cursor paging, `limit` 1–100, filters `unread=true|false` and `category`, and `unread_count` in the response body; a recipient never sees another user's notifications and a tenant-admin never reads another user's inbox through this route.
- **FR-F037-05:** `POST /api/v1/notifications/{id}/read` sets `read_at` (idempotent, returns 200 on repeat) and `POST /api/v1/notifications/read-all` with `{ before?: timestamp }` marks all unread notifications up to `before` and returns `{ updated_count }`; both require the recipient identity.
- **FR-F037-06:** The worker job `deliver_email` renders the category template (subject, text, HTML with the `link`) and sends through the SMTP adapter (Mailpit locally); success sets `status = sent`, `provider_message_id`, `sent_at`, and publishes `notification.delivered.v1`; a transient failure retries with backoff 30 s, 2 min, 10 min, 30 min, 2 h and then sets `failed` with `error` and publishes `notification.failed.v1`; a permanent failure (invalid address, 5xx policy rejection) fails immediately.
- **FR-F037-07:** `POST /api/v1/push-subscriptions` with `{ endpoint, keys: { p256dh, auth }, user_agent? }` stores a Web Push subscription for the actor (unique per `endpoint`), `DELETE /api/v1/push-subscriptions/{id}` removes it, and the worker job `deliver_push` sends a VAPID-signed payload `{ title, body, link, notification_id }` to every subscription of the recipient; a `404` or `410` from the push service deletes that subscription and marks the delivery `failed` with `reason = subscription_gone`.
- **FR-F037-08:** `GET /api/v1/notification-preferences` returns the effective preferences `{ channels: { <category>: { in_app, email, push } }, digest: { cadence: none|hourly|daily, send_at_local, timezone }, quiet_hours: { start_local, end_local, timezone, enabled }, version }` and `PUT /api/v1/notification-preferences` replaces them with `If-Match`; a tenant-admin may `PUT` with `scope = tenant` to change tenant defaults, and `in_app` for `approval` and `system` cannot be disabled (`400 invalid` with `field_errors.channels`).
- **FR-F037-09:** When the recipient's quiet hours are enabled and the creation time falls inside them in the recipient's timezone, email and push deliveries are queued with `next_attempt_at` at the end of the window; in-app delivery is never delayed; `system` category ignores quiet hours.
- **FR-F037-10:** When digest cadence is `hourly` or `daily`, email deliveries for categories other than `approval` and `system` are stored with `status = digested` and the worker job `send_digest` sends one email per recipient at the next `digest_schedules.next_run_at`, listing up to 200 items grouped by category, marks them `sent`, publishes `digest.sent.v1 { recipient_id, item_count }`, and advances `next_run_at`; an empty window sends nothing.
- **FR-F037-11:** `GET /api/v1/notification-deliveries/{id}` returns `{ id, notification_id, channel, status, attempts, next_attempt_at, sent_at, provider_message_id, error, reason }` to the recipient of the notification or a tenant-admin; anyone else receives `404 not_found`.
- **FR-F037-12:** Every consumer and job is idempotent: the event consumer deduplicates by `source_event_id`, `deliver_email` and `deliver_push` skip deliveries not in `queued` state, and `send_digest` uses a `for update skip locked` claim on the schedule row so two workers never send the same digest.
- **FR-F037-13:** The web app renders a `NotificationBell` with an unread badge polled every 30 s, a `NotificationDrawer` listing items with category icons, relative times, mark-read on open, `Mark all read`, and a `/settings/notifications` page with the channel matrix, digest, quiet hours, and a `Enable push on this device` button that registers the service-worker subscription.
- **FR-F037-14:** Every preference and subscription mutation requires `Idempotency-Key`, writes an `audit_events` row, and publishes no domain event (preferences are private); notification, delivery, and preference reads for another tenant's IDs return `404 not_found`.

### Non-functional requirements

- **NFR-F037-01 Performance:** in-app list and unread count respond under 500 ms p95 with 10,000 notifications per user; creation plus routing completes under 50 ms p95 inside the producer's transaction; email delivery is attempted within 5 s p95 of creation outside quiet hours; digest job handles 10,000 recipients per run within 10 minutes (spec section 6 async consistency).
- **NFR-F037-02 Security/privacy:** notification bodies never include cell values the recipient cannot read (producers pass permission-filtered text and the router stores only what it receives); push payloads carry title, body, link, and ID only; SMTP credentials and VAPID keys live in the secret manager; email addresses and push endpoints are redacted from logs; inbox and preference routes are strictly `self` scoped.
- **NFR-F037-03 Accessibility:** bell, drawer, and settings page pass axe with zero serious violations; the badge count is announced through `aria-label`; the drawer is a labelled region reachable by keyboard; the channel matrix uses labelled checkboxes in a table with row and column headers.
- **NFR-F037-04 Reliability/observability:** deliveries dead-letter after the retry schedule with the row left `failed`; metrics `notifications_created_total{category}`, `notification_deliveries_total{channel,status}`, `notification_delivery_latency_seconds{channel}`, `digest_items_total`, and `push_subscriptions_gone_total` are exported; spans carry `tenant_id`, `recipient_id`, `notification_id`, `channel`, and `correlation_id`.

### Scope

Included: notification creation API and event consumer, category model, dedupe, preference resolution and routing, in-app inbox routes, email and Web Push adapters, delivery log and retry, preferences with quiet hours and digest, digest schedules and sender, push subscriptions, bell, drawer, settings page, audit.

Excluded: producers' content decisions (F016, F017, F020, F036, F061 own their event payloads), workflow action definitions (F018, F019 call `create`), Slack and Microsoft Teams channels (F029 adds adapters behind the same delivery table), mobile device registration and deep links (F058 registers push subscriptions through this route), localization of templates beyond English (F049 supplies catalogs later), SMS.

## 3. UX specification

- Entry points: bell icon in the global header; `/settings/notifications`; notification item links open the source (row drawer, approval, file proof, update request); browser push click opens the same link.
- Primary flow: Dana is mentioned; within a second the bell badge shows `1`; she opens the drawer, sees `Ana mentioned you in Launch plan · Kickoff`, clicks it, the row drawer opens and the item is marked read; in settings she enables daily digest at 08:00 and quiet hours 20:00–07:00; the next mention outside approvals arrives in-app immediately and by email in the morning digest.
- Loading: skeleton list in the drawer; Empty: `You are all caught up`; Error: banner with `correlation_id` and retry; Success: settings toast `Preferences saved`, push toast `Push enabled on this device`; Stale/conflict: settings saved with a stale version shows `Preferences changed elsewhere` with reload; Offline: drawer shows cached items with an offline badge and disables mark-read.
- Permission-denied: the bell is hidden for link principals and shown for guests; a delivery detail for another user renders not-found; push button shows `Blocked in browser settings` when permission is denied.
- Responsive: drawer becomes a full-screen sheet under 640 px; the channel matrix becomes stacked cards per category under 768 px.
- Keyboard: `Alt+N` opens the drawer, arrow keys move between items, `Enter` opens, `R` marks read, `Escape` closes and returns focus to the bell; matrix checkboxes are in Tab order with row headers; motion respects `prefers-reduced-motion`.
- Font/icon/design tokens: Inter variable; Lucide `Bell`, `BellOff`, `AtSign`, `UserCheck`, `CheckSquare`, `Share2`, `FileCheck`, `Workflow`, `Moon`, `Mail`, `Smartphone`; tokens from `apps/web/src/design/tokens.css`.

## 4. Technical specification

### Rust backend

- Domain entities in `crates/domain/src/notifications/`: `Notification { id, tenant_id, recipient_id, category: Category, title, body, link, source: SourceRef, actor_id, dedupe_key, read_at, created_at }`, `Delivery { id, tenant_id, notification_id, channel: Channel { InApp, Email, Push }, status: DeliveryStatus { Queued, Sent, Failed, Suppressed, Digested }, attempts, next_attempt_at, sent_at, provider_message_id, error, reason }`, `Preferences { tenant_id, user_id (null for tenant defaults), channels: BTreeMap<Category, ChannelSet>, digest: DigestSetting, quiet_hours: QuietHours, version }`, `PushSubscription { id, tenant_id, user_id, endpoint, p256dh, auth, user_agent, created_at, last_used_at }`, `DigestSchedule { tenant_id, user_id, cadence, send_at_local, timezone, next_run_at, last_run_at }`.
- Use cases: `create_notification`, `route_deliveries`, `resolve_preferences`, `list_inbox`, `mark_read`, `mark_all_read`, `get_preferences`, `put_preferences`, `add_push_subscription`, `remove_push_subscription`, `get_delivery`; worker jobs in `services/worker/src/notifications/`: `event_consumer`, `deliver_email`, `deliver_push`, `send_digest`, `quiet_hours_release`.
- API endpoints (`services/api/src/notifications/`): `GET /api/v1/notifications`, `POST /api/v1/notifications/{id}/read`, `POST /api/v1/notifications/read-all`, `GET /api/v1/notification-preferences`, `PUT /api/v1/notification-preferences`, `POST /api/v1/push-subscriptions`, `DELETE /api/v1/push-subscriptions/{id}`, `GET /api/v1/notification-deliveries/{id}`. DTOs `NotificationResponse`, `InboxPage { items, next_cursor, unread_count }`, `ReadAllRequest`, `ReadAllResponse`, `PreferencesResponse`, `PutPreferencesRequest { scope?: user|tenant, channels, digest, quiet_hours }`, `PushSubscriptionRequest`, `PushSubscriptionResponse`, `DeliveryResponse`.
- Events: `notification.created.v1`, `notification.delivered.v1`, `notification.failed.v1`, `digest.sent.v1`; payloads carry `notification_id`, `recipient_id`, `category`, `channel`, and for digests `item_count`.
- Adapters: `EmailAdapter` trait with `SmtpAdapter` (lettre, STARTTLS, credentials from the secret manager, Mailpit in compose) and `RecordingAdapter` for tests; `PushAdapter` trait with `WebPushAdapter` (VAPID keys from the secret manager, `aes128gcm` encryption) and a recording stub; templates in `crates/domain/src/notifications/templates/` as typed Rust builders per category.
- Authorization: inbox, read, preferences, and subscriptions are `self` scoped by `actor_id`; tenant defaults require `tenant-admin`; delivery detail requires recipient or `tenant-admin`; the event consumer runs with a system actor.
- Validation: `title` ≤ 200, `body` ≤ 2,000, `link` relative path ≤ 1,000 chars, `endpoint` https URL ≤ 2,000 chars, `timezone` IANA name, `send_at_local` and quiet hours `HH:MM`, `limit` bounds; idempotency for 24 hours; `If-Match` on preferences.
- Error mapping: `NotificationError::InvalidCategory → 400 invalid`, `NotificationError::ProtectedChannel → 400 invalid`, `NotificationError::StaleVersion → 409 conflict`, `NotificationError::NotFound → 404 not_found`, `AuthzError::Denied → 403 denied`, `AdapterError::Unavailable → retry` (never surfaced to HTTP).

### PostgreSQL/SQLx

- Migration `*_notifications_*.sql` creates `notifications(id uuid pk, tenant_id uuid not null, recipient_id uuid not null, category text not null, title text not null, body text not null, link text, source_kind text, source_id uuid, actor_id uuid, dedupe_key text, source_event_id uuid, read_at timestamptz, created_at timestamptz not null)`, `notification_deliveries(id uuid pk, tenant_id, notification_id uuid not null references notifications(id) on delete cascade, channel text not null, status text not null default 'queued', attempts int not null default 0, next_attempt_at timestamptz, sent_at timestamptz, provider_message_id text, error text, reason text, updated_at)`, `notification_preferences(id uuid pk, tenant_id, user_id uuid null, channels jsonb not null, digest jsonb not null, quiet_hours jsonb not null, version bigint not null default 1, audit fields)`, `push_subscriptions(id uuid pk, tenant_id, user_id uuid not null, endpoint text not null, p256dh text not null, auth text not null, user_agent text, created_at, last_used_at)`, `digest_schedules(id uuid pk, tenant_id, user_id uuid not null, cadence text not null, send_at_local time not null, timezone text not null, next_run_at timestamptz not null, last_run_at timestamptz)`.
- Invariants: `check (category in ('mention','assignment','approval','share','review','update_request','workflow','system'))`; `check (channel in ('in_app','email','push'))`; `check (status in ('queued','sent','failed','suppressed','digested'))`; `check (cadence in ('hourly','daily'))`; unique `notifications(tenant_id, recipient_id, dedupe_key) where dedupe_key is not null and created_at > now() - interval '24 hours'` enforced by the service with an advisory lock plus a partial unique index on `(tenant_id, recipient_id, dedupe_key, date_trunc('day', created_at))`; unique `notifications(tenant_id, source_event_id, recipient_id)`; unique `notification_preferences(tenant_id, coalesce(user_id, '00000000-0000-0000-0000-000000000000'))`; unique `push_subscriptions(endpoint)`; unique `digest_schedules(tenant_id, user_id)`.
- Indexes: `notifications(tenant_id, recipient_id, created_at desc)`, `notifications(tenant_id, recipient_id) where read_at is null`, `notification_deliveries(status, next_attempt_at) where status in ('queued','digested')`, `notification_deliveries(notification_id)`, `digest_schedules(next_run_at)`, `push_subscriptions(tenant_id, user_id)`.
- Audit events: `notification.read`, `notification.read-all`, `preferences.update`, `preferences.tenant-default.update`, `push-subscription.add`, `push-subscription.remove`.
- Retention/deletion: notifications older than 180 days and deliveries older than 90 days are purged by the F027 retention job; subscriptions removed on `410` or on user deactivation (`user.deactivated.v1` consumer); migration rollback drops the five tables.

### React/TypeScript

- Routes: `/settings/notifications` in `apps/web/src/features/notifications/`; components `NotificationBell`, `NotificationDrawer`, `NotificationItem`, `CategoryIcon`, `PreferencesPage`, `ChannelMatrix`, `DigestSettings`, `QuietHoursSettings`, `PushEnableButton`, `DeliveryStatusChip`.
- State: TanStack Query keys `['notifications', { unread, category, cursor }]` (30 s `refetchInterval` while the tab is visible), `['notification-preferences']`, `['push-subscriptions']`; mark-read updates the cached `unread_count` optimistically.
- API client: generated `NotificationsApi` with `listNotifications`, `markRead`, `markAllRead`, `getPreferences`, `putPreferences`, `addPushSubscription`, `removePushSubscription`, `getDelivery`; service worker `sw.ts` handles `push` and `notificationclick` events.
- Optimistic updates: mark-read and mark-all-read apply locally and roll back on error; preferences save is not optimistic and shows the stale banner on `conflict`.
- Telemetry: `notification_drawer_opened`, `notification_opened`, `notification_marked_read`, `notifications_all_read`, `preferences_saved`, `push_enabled`, `push_blocked` with `category` and `channel`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F037-01 through FR-F037-14 in `testing/features/F037/requirements/cases.md`
- [ ] Failure/edge-case tests: invalid category, dedupe within 24 h, protected in-app channel, quiet-hours boundary at midnight across DST, empty digest window, push `410`, SMTP transient then permanent failure
- [ ] Permission-negative and tenant-isolation tests: reading another user's inbox or delivery returns `not_found`, tenant defaults by non-admin returns `denied`, cross-tenant IDs return `not_found`
- [ ] Rust unit tests: `crates/domain/src/notifications/` preference resolution order, quiet-hours math, digest scheduling, template rendering
- [ ] API contract/integration tests: every route above with success and each error code
- [ ] Database migration/constraint tests: category and status checks, dedupe index, preference uniqueness, delivery index, rollback
- [ ] React component tests: `NotificationBell`, `NotificationDrawer`, `PreferencesPage` states
- [ ] Browser E2E tests: mention to bell, open and read, preferences save, digest email in Mailpit, push enable
- [ ] Accessibility tests: axe on drawer and settings, keyboard drawer, matrix headers
- [ ] Performance/load tests: 10,000-item inbox p95, routing latency, digest run of 10,000 recipients

### Fast fanout configuration

- Test harness path: `testing/features/F037/`
- Feature flag: `F037_FEATURE`
- Fixture/seed factory: `testing/fixtures/notifications.rs` builds tenant, users `dana` (default preferences), `quiet` (quiet hours 20:00–07:00 Europe/Berlin), `digest` (daily 08:00 America/New_York), tenant-admin, foreign tenant, and 300 seeded notifications across categories
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z` with timezone advance helpers, fixed VAPID key pair
- Mock/stub contracts: `RecordingAdapter` for email and push with scripted failures; Mailpit for E2E; embedded JetStream for the event consumer; outbox recorder in memory
- Parallel isolation: one schema per test worker, tenant ID per test
- Targeted command: `cargo xtask test-feature F037`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F037/`

## 6. Acceptance criteria

```gherkin
Feature: Notification creation, routing, delivery, and preferences

Scenario: Mention becomes an in-app and email notification
  Given Dana has default preferences
  When mention.created.v1 for Dana is consumed
  Then a mention notification exists with in_app and email deliveries queued
  And after deliver_email runs the email delivery is sent and notification.delivered.v1 is published

Scenario: Quiet hours defer email but not in-app
  Given Quinn has quiet hours 20:00 to 07:00 Europe/Berlin
  When an assignment notification is created at 22:00 Berlin time
  Then the in-app delivery is visible immediately and the email delivery has next_attempt_at 07:00

Scenario: Digest bundles items
  Given Dee has a daily digest at 08:00 America/New_York and three mention notifications since yesterday
  When send_digest runs at 08:00 New York time
  Then one email lists three items, the deliveries are sent, and digest.sent.v1 has item_count 3

Scenario: Another user's delivery is not readable
  Given a delivery for Dana's notification
  When Eli requests GET /api/v1/notification-deliveries/{id}
  Then the response is 404 not_found

Scenario: Replayed event creates no duplicate
  Given mention.created.v1 with event_id E1 was consumed
  When the same event is delivered again
  Then Dana still has one notification for E1 and one email delivery
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F004 (worker runtime, JetStream consumers, retry and dead-letter policy, secret manager, Mailpit compose service), F002 (users, timezones, deactivation events, tenant-admin role); decisions sections 2–4, 7; contracts row F037
- Blocks: F020 (approval notifications), F029 (Slack and Teams adapters), F058 (mobile push registration), F061 (update-request reminders)
- Conflicts with: none (disjoint owned paths)
- External dependencies: SMTP relay (Mailpit locally), browser push services reachable from the worker
- Risks and mitigations: producers might leak unauthorized cell values into bodies, so the `NotificationRequest` contract documents that text must already be permission-filtered and the F016 and F020 harnesses assert it; digest and quiet-hours math around DST transitions is error-prone, so tests cover the Europe/Berlin and America/New_York transitions with the fixed clock; a stuck SMTP relay would back up the queue, so `deliver_email` uses a 10 s send timeout and per-tenant concurrency of 8; push endpoints churn, so `410` handling deletes subscriptions and the UI re-registers on next visit.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F004 and F002 accepted and archived; Mailpit present in `infra/compose.yml`; VAPID key pair provisioned in the secret manager
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F037/`
- [ ] Migration file name and owned paths claimed
- [ ] Fixture factory, recording adapters, and schema-per-worker isolation available in `testing/harness/`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/worker/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events verified for every preference and subscription mutation; outbox events verified for creation, delivery, failure, and digest
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F037_FEATURE` (producers' `create` becomes a no-op logging call), run down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Users receive in-app, email, and push notifications for mentions, assignments, approvals, shares, reviews, update requests, and workflow failures, and control channels, daily or hourly digests, and quiet hours from one settings page; administrators can inspect delivery status.
- Migration adds `notifications`, `notification_deliveries`, `notification_preferences`, `push_subscriptions`, and `digest_schedules`; rollback drops them. Requires SMTP and VAPID secrets. Feature is off by default behind `F037_FEATURE`.
