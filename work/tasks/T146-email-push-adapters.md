---
id: T146
type: task
status: planned
parent_epic: E004
parent_feature: F037
parent_story: S073
depends_on: [T145]
owned_paths: [crates/domain/src/notifications/**, crates/persistence/src/notifications/**, services/api/src/notifications/**, services/worker/src/notifications/**, apps/web/src/features/notifications/**, testing/features/F037/api/**, testing/features/F037/frontend/**]
feature_flag: F037_FEATURE
branch: t146-email-push-adapters
started_at: null
finished_at: null
---

# T146 — Email/push adapters

## Identity

- Parent story: `S073` Channels and delivery
- Owner: platform
- Branch: `t146-email-push-adapters`
- Decision references: `docs/architecture-decisions.md` sections 3, 7; `docs/capability-contracts.md` row F037

## Objective

Implement the email and Web Push delivery adapters, the category templates, the retry and dead-letter schedule, push-subscription registration and pruning, the delivery-detail route, and the bell and drawer surfaces that consume them.

## Specification

- Owned paths: `crates/domain/src/notifications/{adapters/{mod.rs, smtp.rs, web_push.rs, recording.rs}, templates/{mod.rs, mention.rs, assignment.rs, approval.rs, share.rs, review.rs, update_request.rs, workflow.rs, system.rs}, subscription.rs}`, `crates/persistence/src/notifications/{notification_delivery_repository.rs, push_subscription_repository.rs}`, `services/api/src/notifications/{handlers_delivery.rs, handlers_subscription.rs}`, `services/worker/src/notifications/{deliver_email.rs, deliver_push.rs}`, `apps/web/src/features/notifications/{NotificationBell.tsx, NotificationDrawer.tsx, NotificationItem.tsx, CategoryIcon.tsx, DeliveryStatusChip.tsx, api.ts, hooks.ts}`
- Contract/input: `EmailAdapter::send(EmailMessage { to, subject, text, html })` and `PushAdapter::send(PushMessage { endpoint, p256dh, auth, payload })`; `PushSubscriptionRequest { endpoint (https, ≤ 2,000 chars), keys: { p256dh, auth }, user_agent? }`; secret manager keys `notifications/smtp/username|password` and `notifications/vapid/public|private`; `Idempotency-Key` required on both subscription mutations.
- Output/behavior: routes `POST /api/v1/push-subscriptions`, `DELETE /api/v1/push-subscriptions/{id}`, `GET /api/v1/notification-deliveries/{id}` returning `DeliveryResponse { id, notification_id, channel, status, attempts, next_attempt_at, sent_at, provider_message_id, error, reason }` to the recipient or a `tenant-admin` and `404 not_found` to anyone else; `deliver_email.rs` takes work only from `NotificationDeliveryRepository::claim_due_deliveries(now, limit)`, which returns rows still `queued`, renders the category template with the `link`, sends through `SmtpAdapter` (lettre, STARTTLS, 10 s send timeout, per-tenant concurrency 8), and calls `record_delivery_attempt(delivery_id, outcome)` to set `sent`, `provider_message_id`, and `sent_at`, then publishes `notification.delivered.v1`; transient failures retry at 30 s, 2 min, 10 min, 30 min, 2 h, then set `failed` with `error` and publish `notification.failed.v1`; an invalid address or 5xx policy rejection fails on the first attempt; `deliver_push.rs` sends a VAPID-signed `aes128gcm` payload `{ title, body, link, notification_id }` to every subscription returned by `PushSubscriptionRepository::list_subscriptions_for_user(user_id)` and on `404` or `410` calls `delete_subscription_by_endpoint(endpoint)` and marks the delivery `failed` with `reason = subscription_gone`; neither job nor handler holds a SQL string, a `sqlx::query*` call, or a connection, and the `user.deactivated.v1` consumer prunes subscriptions through the same two repository methods; email addresses and push endpoints are redacted from logs; metrics `notification_deliveries_total{channel,status}`, `notification_delivery_latency_seconds{channel}`, and `push_subscriptions_gone_total` are exported; the bell polls `unread_count` every 30 s while visible and the drawer marks visible items read on open.
- Dependencies: T145 delivery rows, router, and inbox routes; F004 secret manager, job retry, and Mailpit compose service; F002 user email addresses and deactivation events.
- Feature flag: `F037_FEATURE` gates the routes, the two jobs, and the bell mount.

## TDD

- Failing test first: `testing/features/F037/api/email_tests.rs::deliver_email_sends_and_marks_sent`, `::deliver_email_retries_transient_then_fails`, `::invalid_address_fails_without_retry`, `::deliver_email_skips_non_queued_rows`, `::template_renders_link_for_each_category`; `testing/features/F037/api/push_tests.rs::push_subscription_is_unique_per_endpoint`, `::subscription_mutation_requires_idempotency_key_and_writes_audit`, `::push_gone_deletes_subscription_and_fails_delivery`, `::push_payload_contains_no_cell_values`; `testing/features/F037/api/delivery_tests.rs::recipient_reads_delivery_detail`, `::tenant_admin_reads_delivery_detail`, `::other_users_delivery_returns_not_found`, `::cross_tenant_delivery_returns_not_found`; `testing/features/F037/frontend/bell_tests.tsx::bell_badge_polls_unread_count`, `::drawer_marks_visible_items_read_on_open`, `::delivery_chip_renders_failed_reason`
- Targeted command: `cargo xtask test-feature F037`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `RecordingAdapter` for email and push with scripted transient, permanent, and `410` responses; Mailpit for the integration assertion; fixed VAPID key pair; fixed clock with manual retry-schedule advance

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Both jobs registered in `services/worker/src/registry.rs` behind the flag; routes mounted and OpenAPI regenerated without drift
- [ ] Redaction verified: no email address or push endpoint appears in captured logs
- [ ] `cargo xtask check-persistence` passes
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S073
- [ ] `finished_at` recorded
