---
id: T145
type: task
status: planned
parent_epic: E004
parent_feature: F037
parent_story: S073
depends_on: [S073]
owned_paths: [services/api/migrations/*_notifications_*.sql, crates/domain/src/notifications/**, services/api/src/notifications/**, services/worker/src/notifications/**, testing/features/F037/api/**, testing/features/F037/database/**]
feature_flag: F037_FEATURE
branch: t145-notification-outbox
started_at: null
finished_at: null
---

# T145 — Notification outbox

## Identity

- Parent story: `S073` Channels and delivery
- Owner: platform
- Branch: `t145-notification-outbox`
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 7; `docs/capability-contracts.md` row F037

## Objective

Create the notifications schema and implement creation, category validation, dedupe, preference-driven routing into delivery rows, the JetStream event consumer, and the in-app inbox routes, so that every producer has one call path and one durable delivery record.

## Specification

- Owned paths: `services/api/migrations/<ts>_notifications_create_tables.sql` and `.down.sql`, `crates/domain/src/notifications/{mod.rs, notification.rs, delivery.rs, category.rs, router.rs, errors.rs, service.rs}`, `services/api/src/notifications/{mod.rs, routes.rs, handlers_inbox.rs, dto.rs}`, `services/worker/src/notifications/{mod.rs, event_consumer.rs}`
- Contract/input: `NotificationRequest { tenant_id, recipient_id, category, title (≤ 200), body (≤ 2,000), link (relative, ≤ 1,000), source: { kind, id }, dedupe_key?, actor_id? }`; inbox query `{ cursor?, limit? (1–100), unread?, category? }`; `ReadAllRequest { before? }`; consumed subjects `mention.created.v1`, `approval.requested.v1`, `approval.escalated.v1`, `share.granted.v1`, `guest.invited.v1`, `proof.decided.v1`, `update-request.sent.v1`, `update-request.reminded.v1`, `workflow-run.failed.v1`.
- Output/behavior: routes `GET /api/v1/notifications`, `POST /api/v1/notifications/{id}/read`, `POST /api/v1/notifications/read-all`; DTOs `NotificationResponse`, `InboxPage { items, next_cursor, unread_count }`, `ReadAllResponse { updated_count }`; `service.rs` writes the `notifications` row inside the caller's transaction, rejects unknown categories with `NotificationError::InvalidCategory`, and returns the existing row for a `dedupe_key` repeated within 24 hours under an advisory lock plus the partial unique index; `router.rs` resolves preferences user row → tenant defaults → built-in defaults (in-app on for all categories, email on for `approval`, `assignment`, `mention`, `update_request`, push off) and inserts one `notification_deliveries` row per channel, `queued` when enabled and `suppressed` with `reason = preference` when not; `event_consumer.rs` maps the subjects above to categories and deduplicates on `source_event_id` through the unique `(tenant_id, source_event_id, recipient_id)`; publishes `notification.created.v1`; DDL for `notifications`, `notification_deliveries`, and `push_subscriptions` with the category, channel, and status checks and the indexes `notifications(tenant_id, recipient_id, created_at desc)`, `notifications(tenant_id, recipient_id) where read_at is null`, and `notification_deliveries(status, next_attempt_at) where status in ('queued','digested')`; inbox is strictly `self` scoped and cross-tenant IDs return `404 not_found`.
- Dependencies: F004 JetStream consumer runtime, retry policy, and outbox publisher; F002 users, tenants, timezones, and the `tenant-admin` role; F028 correlation IDs and error envelope.
- Feature flag: `F037_FEATURE` gates the routes and the consumer registration; the migration runs regardless.

## TDD

- Failing test first: `testing/features/F037/api/create_tests.rs::create_writes_notification_and_publishes_created`, `::title_over_200_chars_rejected`, `::invalid_category_is_rejected_without_write`, `::dedupe_key_within_24h_returns_existing`, `::rolled_back_producer_transaction_leaves_no_rows`; `testing/features/F037/api/routing_tests.rs::routing_uses_user_then_tenant_then_default_preferences`, `::disabled_channel_is_recorded_suppressed`; `testing/features/F037/api/inbox_tests.rs::inbox_pages_newest_first_with_unread_count`, `::inbox_limit_out_of_bounds_rejected`, `::mark_read_is_idempotent`, `::read_all_before_leaves_newer_unread`, `::other_users_inbox_returns_not_found`; `testing/features/F037/api/consumer_tests.rs::replayed_source_event_creates_one_notification`, `::each_subject_maps_to_expected_category`; `testing/features/F037/database/migration_tests.rs::notifications_tables_exist_with_checks`, `::deliveries_cascade_on_notification_delete`, `::dedupe_partial_index_blocks_same_day_duplicate`
- Targeted command: `cargo xtask test-feature F037`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/notifications.rs` tenant, `dana`, tenant-admin, foreign tenant, 300 seeded notifications; embedded JetStream publisher; in-memory outbox recorder; fixed clock `2026-09-03T00:00:00Z`

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; routes and consumer registered behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S073
- [ ] `finished_at` recorded
