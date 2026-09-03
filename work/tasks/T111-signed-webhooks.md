---
id: T111
type: task
status: planned
parent_epic: E006
parent_feature: F028
parent_story: S056
depends_on: [S056]
owned_paths: [crates/domain/src/public-api/**, services/api/src/public-api/**, services/worker/src/public-api/**, apps/web/src/features/public-api/**, testing/features/F028/api/**, testing/features/F028/frontend/**]
feature_flag: F028_FEATURE
branch: t111-signed-webhooks
started_at: null
finished_at: null
---

# T111 — Signed webhooks

## Identity

- Parent story: `S056` Event delivery
- Owner: platform
- Branch: `t111-signed-webhooks`
- Decision references: `docs/architecture-decisions.md` sections 3, 7; `docs/capability-contracts.md` row F028

## Objective

Implement webhook CRUD with encrypted secrets and URL guarding, the JetStream dispatcher with HMAC-SHA256 signing, retry schedule, disable-after-failure, replay, delivery log routes, and the webhook admin pages.

## Specification

- Owned paths: `crates/domain/src/public-api/{webhook.rs, delivery.rs, signature.rs, matcher.rs, retry.rs, service_webhook.rs}`, `services/api/src/public-api/{handlers_webhook.rs, handlers_delivery.rs}`, `services/worker/src/public-api/{mod.rs, dispatcher.rs, sender.rs, url_guard.rs}`, `apps/web/src/features/public-api/{WebhookTable.tsx, WebhookForm.tsx, SecretRevealDialog.tsx, DeliveryLog.tsx, DeliveryDrawer.tsx, AttemptTable.tsx}`
- Contract/input: `CreateWebhookRequest { url, events, filters?, application_id? }`, `UpdateWebhookRequest { url?, events?, filters?, status?, rotate_secret? }`, delivery list query `{ cursor?, limit?, status?, event? }`; outbox envelope from F004 `{ tenant_id, actor_id, aggregate_id, version, changed_fields, correlation_id, occurred_at }`.
- Output/behavior: routes `GET/POST /api/v1/webhooks`, `PATCH/DELETE /api/v1/webhooks/{id}`, `GET /api/v1/webhooks/{id}/deliveries`, `POST /api/v1/webhook-deliveries/{id}/replay`; `url_guard.rs` resolves the host and rejects private, loopback, link-local, and metadata ranges at creation and before every attempt, redirects disabled; secrets envelope-encrypted with the F004 secret manager key, returned once, rotation keeps the previous secret 24 hours and signs `X-OpsHub-Signature: v1=<new>,v1=<old>`; `signature.rs` computes HMAC-SHA256 over `"<timestamp>.<body>"`; `dispatcher.rs` consumes `outbox.>` durable consumer `public-api-dispatcher`, matches by `matcher.rs` (patterns, wildcards, filters), inserts deliveries idempotently on `(webhook_id, event_id)`, applies the F003 field filter for the bound application's scopes, sends with 10 s timeout; `retry.rs` schedules `[60, 300, 1800, 7200, 43200]` s ±10 % and marks `exhausted` after 5 attempts; ten consecutive exhausted deliveries disable the webhook; events `webhook.updated.v1`, `webhook.delivered.v1`, `webhook.failed.v1`, `webhook.disabled.v1`; replay within 30 days creates a new delivery with `replay_of`; UI per ticket section 3.
- Dependencies: T110 conventions; F004 JetStream consumer runtime and secret manager; F003 field-level filter.
- Feature flag: `F028_FEATURE` gates routes, dispatcher registration, and pages.

## TDD

- Failing test first: `testing/features/F028/api/webhook_tests.rs::webhook_create_returns_secret_once`, `::webhook_create_rejects_private_url`, `::webhook_rotate_secret_dual_signature_24h`, `::webhook_delete_cancels_pending`; `testing/features/F028/api/delivery_tests.rs::delivery_signature_matches_vector`, `::delivery_retry_schedule_and_exhausted`, `::webhook_disabled_after_ten_exhausted`, `::delivery_success_resets_counter`, `::delivery_replay_new_id_within_30_days`, `::delivery_replay_disabled_webhook_conflicts`, `::delivery_payload_filtered_by_scopes`, `::dispatcher_rejects_dns_rebind_at_attempt`; `testing/features/F028/frontend/DeliveryLog.test.tsx::shows_attempts_and_replay`, `WebhookForm.test.tsx::rejects_http_url`
- Targeted command: `cargo xtask test-feature F028`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: harness receiver with 200/500/hang modes and a rebinding DNS stub; fixed secret and body for the signature vector; fixed clock for retry timing

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Dispatcher registered in `services/worker/src/registry.rs` behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S056
- [ ] `finished_at` recorded
