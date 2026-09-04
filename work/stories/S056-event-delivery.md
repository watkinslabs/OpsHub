---
id: S056
type: story
status: planned
parent_epic: E006
parent_feature: F028
depends_on: [S055]
owned_paths: [crates/domain/src/public-api/**, crates/persistence/src/public-api/**, services/api/src/public-api/**, services/worker/src/public-api/**, apps/web/src/features/public-api/**, testing/features/F028/**]
feature_flag: F028_FEATURE
branch: s056-event-delivery
started_at: null
finished_at: null
---

# S056 — Event delivery

## Identity

- Parent feature: `F028` API/webhooks
- Owner: platform
- Branch: `s056-event-delivery`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 7; `docs/capability-contracts.md` row F028

## Vertical slice

As a tenant administrator, I want to subscribe an HTTPS endpoint to OpsHub events and receive signed deliveries with automatic retry, a delivery log, replay, and automatic disable after repeated failures, so that my integration reacts to changes reliably and I can see why a delivery failed.

## Requirements

- **SR-S056-01:** `POST /api/v1/webhooks` validates an https public URL, 1–50 event patterns, and filters, writes one `webhook_events` row per pattern and one `webhook_filters(filter_key, filter_value)` row per filter through `WebhookRepository` in the webhook's `UnitOfWork`, generates a 32-byte secret returned once and stored encrypted, and publishes `webhook.updated.v1`; the DTO keeps `events` as an array and `filters` as an object (covers FR-F028-08, NFR-F028-02).
- **SR-S056-02:** The dispatcher consumes outbox events, selects active webhooks with `WebhookRepository::list_active_webhooks_for_event` joining `webhook_events` on exact or `row.*` prefix match and requiring every `webhook_filters` row to be satisfied, writes one delivery per `(webhook_id, event_id)`, and POSTs the envelope with `X-OpsHub-Delivery-Id`, `X-OpsHub-Event`, `X-OpsHub-Timestamp`, and `X-OpsHub-Signature` within 10 s (FR-F028-09, NFR-F028-04).
- **SR-S056-03:** Each attempt is appended as one `webhook_delivery_attempts` row by `WebhookDeliveryRepository::append_attempt` in the same transaction as the delivery status change; failed attempts retry at 1 min, 5 min, 30 min, 2 h, 12 h with jitter; the fifth failure marks `exhausted` and publishes `webhook.failed.v1`; a 2xx publishes `webhook.delivered.v1` (FR-F028-10).
- **SR-S056-04:** Ten consecutive exhausted deliveries disable the webhook with `disabled_reason: consecutive_failures` and publish `webhook.disabled.v1`; a success resets the counter; `PATCH { status: active }` re-enables (FR-F028-11).
- **SR-S056-05:** `GET /api/v1/webhooks/{id}/deliveries` lists deliveries with their `webhook_delivery_attempts` rows reassembled into the `attempts` array in `attempt_no` order and filters by `status` and `event`; `POST /api/v1/webhook-deliveries/{id}/replay` re-sends within 30 days with a new delivery ID and rejects disabled webhooks with `409` (FR-F028-12).
- **SR-S056-06:** `rotate_secret` returns a new secret once and signs with both secrets for 24 hours; `DELETE` cancels pending deliveries (FR-F028-13).
- **SR-S056-07:** Delivery payloads pass the F003 field-level filter for the bound application's current `api_application_scopes` rows; private, loopback, link-local, and metadata addresses are rejected at creation and at every attempt (FR-F028-14, NFR-F028-02).
- **SR-S056-08:** The `Webhooks` pages show the delivery log, attempt drawer, `Replay`, `Re-enable`, and one-time secret reveal, and the full F028 harness including 1,000 deliveries per minute passes (FR-F028-15, NFR-F028-01, NFR-F028-03).

## Surfaces

- Infrastructure/container: JetStream consumer `public-api-dispatcher` on `outbox.>` with per-tenant quota from F004
- Data access: `crates/persistence/src/public-api/{webhook_repository.rs, delivery_repository.rs}` hold every SQL statement for this slice — `WebhookRepository` owns `webhooks`, `webhook_events`, and `webhook_filters`; `WebhookDeliveryRepository` owns `webhook_deliveries` and `webhook_delivery_attempts` — and `services/worker/src/public-api/{dispatcher.rs, sender.rs}` plus the delivery handlers call those traits with no `sqlx::query*` call and no connection of their own (decision section 2.1)
- Rust service/API: `crates/domain/src/public-api/{webhook.rs, delivery.rs, signature.rs, matcher.rs, retry.rs, service_webhook.rs}`; `services/api/src/public-api/{handlers_webhook.rs, handlers_delivery.rs}`; `services/worker/src/public-api/{dispatcher.rs, sender.rs, url_guard.rs}`
- Data/migration: none new; uses `webhooks`, `webhook_events`, `webhook_filters`, `webhook_deliveries`, and `webhook_delivery_attempts` from S055
- React/UI: `apps/web/src/features/public-api/{WebhookTable.tsx, WebhookForm.tsx, SecretRevealDialog.tsx, DeliveryLog.tsx, DeliveryDrawer.tsx, AttemptTable.tsx}`
- Mocks/fixtures: harness HTTP receiver (`testing/harness/receiver.rs`) returning 200, 500, or hanging; fixed secret for signature vectors; real JetStream from compose for dispatcher tests

## TDD harness

- Test path: `testing/features/F028/{api,database,frontend,e2e,accessibility,performance}/`
- Feature flag: `F028_FEATURE`
- Targeted command: `cargo xtask test-feature F028`
- Full command: `cargo xtask test-all`
- First failing tests: `webhook_create_rejects_private_url`, `delivery_signature_matches_vector`, `delivery_retry_schedule_and_exhausted`, `delivery_attempt_rows_appended_in_order`, `webhook_event_pattern_row_unique`, `webhook_disabled_after_ten_exhausted`, `delivery_replay_new_id_within_30_days`, `dispatcher_idempotent_after_restart`, `delivery_payload_filtered_by_scopes`, `dispatch_1000_per_minute_p95`

## Exit criteria

- [ ] Requirement tests SR-S056-01 through SR-S056-08 written first and failing
- [ ] Tasks T111 and T112 complete; dispatcher registered in `services/worker/src/registry.rs`; UI wired to the real API through the generated client
- [ ] Unit, API, database, React, E2E, permission, accessibility, and performance tests pass
- [ ] Production call path named: `services/worker/src/public-api/dispatcher.rs` registered in `services/worker/src/registry.rs`; `apps/web/src/features/public-api/DeliveryLog.tsx` mounted at `/admin/developer/webhooks/:webhookId`
- [ ] Handoff evidence recorded in the F028 ticket
