---
id: S073
type: story
status: planned
parent_epic: E004
parent_feature: F037
depends_on: [F004, F002]
owned_paths: [crates/domain/src/notifications/**, crates/persistence/src/notifications/**, services/api/src/notifications/**, services/worker/src/notifications/**, apps/web/src/features/notifications/**, services/api/migrations/*_notifications_*.sql, testing/features/F037/**]
feature_flag: F037_FEATURE
branch: s073-channels-and-delivery
started_at: null
finished_at: null
---

# S073 — Channels and delivery

## Identity

- Parent feature: `F037` Notification service
- Owner: platform
- Branch: `s073-channels-and-delivery`
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 7; `docs/capability-contracts.md` row F037

## Vertical slice

As a workspace member, I want mentions, assignments, approvals, shares, reviews, update requests, and workflow failures to arrive in one in-app inbox and, where my channels allow it, by email and Web Push, with a delivery record I can inspect, so that producers stop building their own mail code and no message is silently lost or duplicated.

## Requirements

- **SR-S073-01:** `NotificationService::create(NotificationRequest { tenant_id, recipient_id, category, title, body, link, source, dedupe_key?, actor_id? })` writes one `notifications` row through `NotificationRepository::create_if_absent` inside the producer's `UnitOfWork` and publishes `notification.created.v1`; `title` over 200 chars or `body` over 2,000 chars is rejected before any write (covers FR-F037-01).
- **SR-S073-02:** The JetStream consumer maps `mention.created.v1` to `mention`, `approval.requested.v1` and `approval.escalated.v1` to `approval`, `share.granted.v1` and `guest.invited.v1` to `share`, `proof.decided.v1` to `review`, `update-request.sent.v1` and `update-request.reminded.v1` to `update_request`, and `workflow-run.failed.v1` to `workflow`, deduplicating on `source_event_id` inside `create_if_absent` so a replayed event creates no second notification (FR-F037-01, FR-F037-12).
- **SR-S073-03:** Only the eight categories `mention`, `assignment`, `approval`, `share`, `review`, `update_request`, `workflow`, `system` are accepted; any other value raises `NotificationError::InvalidCategory` with no row written, and a `dedupe_key` repeated for the same `(tenant_id, recipient_id)` inside 24 hours returns the existing notification, serialized by the advisory lock `create_if_absent` takes over that window and backed by the partial unique index (FR-F037-02).
- **SR-S073-04:** `NotificationPreferenceRepository::resolve_effective_preferences(tenant_id, user_id)` resolves the user's `notification_preferences` row and its `notification_channel_preferences` rows, then the tenant-default row (`user_id is null`) and its rows, then built-in defaults, and routing inserts one `notification_deliveries` row per enabled channel with `status = queued` in the same `UnitOfWork` as the notification; a channel whose row has `enabled = false` is written as `suppressed` with `reason = preference` rather than skipped (FR-F037-03).
- **SR-S073-05:** `GET /api/v1/notifications` pages newest-first through `NotificationRepository::page_for_recipient` with `limit` 1–100 and the `unread` and `category` filters and returns `unread_count` from `unread_count(recipient_id)`; `POST /api/v1/notifications/{id}/read` calls `mark_read(id)` idempotently and `POST /api/v1/notifications/read-all` with `{ before? }` calls `mark_all_read(recipient_id)` and returns `{ updated_count }` (FR-F037-04, FR-F037-05).
- **SR-S073-06:** The worker job `deliver_email` renders the category template and sends through the SMTP adapter, recording the outcome with `NotificationDeliveryRepository::record_delivery_attempt` to set `sent`, `provider_message_id`, and `sent_at` and publishing `notification.delivered.v1`; transient failures retry at 30 s, 2 min, 10 min, 30 min, 2 h and then set `failed` with `error` and publish `notification.failed.v1`, while an invalid address fails immediately (FR-F037-06, NFR-F037-04).
- **SR-S073-07:** `POST /api/v1/push-subscriptions` stores `{ endpoint, keys.p256dh, keys.auth, user_agent? }` unique per `endpoint`, `DELETE /api/v1/push-subscriptions/{id}` removes it, and `deliver_push` sends a VAPID-signed `{ title, body, link, notification_id }` payload; a `404` or `410` deletes the subscription through `PushSubscriptionRepository::delete_subscription_by_endpoint` and marks the delivery `failed` with `reason = subscription_gone` (FR-F037-07, NFR-F037-02).
- **SR-S073-08:** `GET /api/v1/notification-deliveries/{id}` returns channel, status, attempts, `next_attempt_at`, `sent_at`, `provider_message_id`, `error`, and `reason` to the recipient or a tenant-admin; every other caller and every cross-tenant ID receives `404 not_found`, and no route lets one user read another user's inbox (FR-F037-11, FR-F037-14).
- **SR-S073-09:** Jobs are safe to re-run and hold no SQL: `deliver_email` and `deliver_push` take work only from `NotificationDeliveryRepository::claim_due_deliveries(now, limit)`, which returns rows still in `queued`, and `deliver_push` reads endpoints through `list_subscriptions_for_user`, subscription mutations require `Idempotency-Key` and write `audit_events` without publishing a domain event, and metrics `notifications_created_total{category}`, `notification_deliveries_total{channel,status}`, and `notification_delivery_latency_seconds{channel}` are exported with `tenant_id`, `recipient_id`, `notification_id`, and `correlation_id` on the span (FR-F037-12, FR-F037-14, NFR-F037-01, NFR-F037-04).

## Surfaces

- Infrastructure/container: Mailpit SMTP service from the F004 compose stack; secret manager keys `notifications/smtp/username|password` and `notifications/vapid/public|private`; JetStream durable consumer `notifications-events`
- Rust service/API: `crates/domain/src/notifications/{notification.rs, delivery.rs, category.rs, router.rs, errors.rs, service.rs, templates/}` (repository traits only, no SQLx); `crates/persistence/src/notifications/{mod.rs, notification_repository.rs, notification_delivery_repository.rs, push_subscription_repository.rs}` holding every SQL statement these surfaces issue; `services/api/src/notifications/{routes.rs, handlers_inbox.rs, handlers_delivery.rs, handlers_subscription.rs, dto.rs}`; `services/worker/src/notifications/{mod.rs, event_consumer.rs, deliver_email.rs, deliver_push.rs}`
- Data/migration: `services/api/migrations/<ts>_notifications_create_tables.sql` creating `notifications`, `notification_deliveries`, and `push_subscriptions` with the category, channel, and status checks and the indexes from ticket section 4
- React/UI: `apps/web/src/features/notifications/{NotificationBell.tsx, NotificationDrawer.tsx, NotificationItem.tsx, CategoryIcon.tsx, DeliveryStatusChip.tsx, api.ts, hooks.ts}` and the `push` and `notificationclick` handlers in `sw.ts`
- Mocks/fixtures: `testing/fixtures/notifications.rs` seeding tenant, `dana`, a tenant-admin, a foreign tenant, and 300 notifications across categories; `RecordingAdapter` for email and push with scripted transient, permanent, and `410` failures; embedded JetStream; fixed clock `2026-09-03T00:00:00Z`

## TDD harness

- Test path: `testing/features/F037/{requirements,api,database,frontend}/`
- Feature flag: `F037_FEATURE`
- Targeted command: `cargo xtask test-feature F037`
- Full command: `cargo xtask test-all`
- First failing tests: `create_writes_notification_and_publishes_created`, `invalid_category_is_rejected_without_write`, `dedupe_key_within_24h_returns_existing`, `routing_uses_user_then_tenant_then_default_preferences`, `disabled_channel_is_recorded_suppressed`, `inbox_pages_newest_first_with_unread_count`, `mark_read_is_idempotent`, `deliver_email_retries_transient_then_fails`, `push_gone_deletes_subscription`, `replayed_source_event_creates_one_notification`, `other_users_delivery_returns_not_found`

## Exit criteria

- [ ] Requirement tests SR-S073-01 through SR-S073-09 written first and failing
- [ ] Tasks T145 and T146 complete and wired through the API router and the worker job registry
- [ ] Unit, API, database, React, and permission-negative tests pass in targeted and full modes
- [ ] `cargo xtask check-persistence` passes: no SQL string, `sqlx::query*` call, or connection outside `crates/persistence/src/notifications/`
- [ ] Production call path named: `services/api/src/notifications/routes.rs` mounted in `services/api/src/router.rs` (`/api/v1/notifications`, `/api/v1/notification-deliveries`, `/api/v1/push-subscriptions`); `services/worker/src/notifications/{event_consumer.rs, deliver_email.rs, deliver_push.rs}` registered in `services/worker/src/registry.rs`
- [ ] Handoff evidence recorded in the F037 ticket
