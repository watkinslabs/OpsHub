---
id: F028
type: feature
status: planned
priority: P1
owner: platform
estimate: 8
target_milestone: M5
parent_epic: E006
depends_on: [F003, F038, F004]
blocks: [F029, F047]
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/public-api/**, crates/contracts/src/public-api/**, services/api/src/public-api/**, services/worker/src/public-api/**, apps/web/src/features/public-api/**, services/api/migrations/*_public-api_*.sql, testing/features/F028/**]
feature_flag: F028_FEATURE
flag_default: off
branch: f028-api-webhooks
started_at: null
finished_at: null
---

# F028 — API/webhooks

## 1. Identity and dates

- Branch: `f028-api-webhooks`
- Capability area: integrations and APIs (spec 5.9 INT-01; section 4 record rules; section 6 observability)
- Decision references: `docs/architecture-decisions.md` sections 3, 4, 7; `docs/capability-contracts.md` row F028
- Aggregate: `api-application`
- Module slug: `public-api`

## 2. Requirement specification

### Problem and user outcome

Customers and partners need to read and write OpsHub records from their own systems and react to changes without polling. Today the API exists only as internal handlers with no published description, no consistent list conventions, and no way to subscribe to events.

As a tenant administrator, I want to register an API application with scoped credentials, read a generated OpenAPI 3.1 document that matches the running service, rely on one set of pagination, filtering, error, and rate-limit conventions, and subscribe HTTPS endpoints to signed events with retry and replay, so that integrations are buildable from the documentation alone and observable when they fail.

### Functional requirements

- **FR-F028-01:** `GET /api/v1/openapi.json` returns an OpenAPI 3.1 document generated at build time from the typed Rust contracts in `crates/contracts` covering every `/api/v1` route registered in the router; the document includes `info.version` equal to the service build, component schemas for every DTO, the shared `Error` schema, `Page<T>` schemas, and security schemes `sessionCookie` and `apiToken`; a route missing from the document fails the `check-contracts` CI gate.
- **FR-F028-02:** A `tenant-admin` can create an API application with `name`, `description`, `scopes` (subset of the F038 token scopes), `rate_limit_per_minute` (60–6,000, default 600), and `allowed_ips` (0–20 CIDRs); creation returns the application with `version` 1 and a `client_id`; credentials are issued as F038 API tokens bound to the application.
- **FR-F028-03:** `PATCH /api/v1/applications/{id}` updates name, description, scopes, rate limit, allowed IPs, and `status: active|suspended` with `If-Match`; suspending an application rejects its tokens with `401 denied` within 5 s; `DELETE` soft-deletes and revokes all bound tokens; both publish `application.updated.v1`.
- **FR-F028-04:** Every `/api/v1` list route accepts `cursor` (opaque, HMAC-signed, expires after 24 hours), `limit` (1–200 default 50 unless the route documents a higher cap), `filter` (grammar `field op value` joined by `and`, operators `eq`, `ne`, `lt`, `lte`, `gt`, `gte`, `in`, `contains`, `is_null`), `sort` (`field` or `-field`, at most 3 keys), and `fields` (comma-separated projection); an invalid cursor returns `400 invalid` with `field_errors.cursor`, an unknown filter field returns `400 invalid` with `field_errors.filter`.
- **FR-F028-05:** List responses are `{ items, next_cursor, has_more, total?: number }` where `total` is present only when `include_total=true` and the route allows it; `fields` projection removes non-requested attributes but always returns `id` and `version`.
- **FR-F028-06:** Every error response uses `{ code, message, field_errors, correlation_id }` with `code` in `invalid`, `denied`, `not_found`, `conflict`, `rate_limited`, `unavailable`; HTTP status maps `400`, `403`, `404`, `409`, `429`, `503`; `correlation_id` equals the request's `X-Correlation-Id` header when supplied (UUID) or a generated UUIDv7, and is echoed on every response.
- **FR-F028-07:** Requests authenticated by an application token are rate-limited per application with a token bucket of `rate_limit_per_minute` and burst 2x; every response carries `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` (epoch seconds); an exhausted bucket returns `429 rate_limited` with `Retry-After`.
- **FR-F028-08:** A `tenant-admin` can create a webhook with `url` (https, public IP only, ≤ 2,048 chars), `events` (1–50 names from the contract event catalog, wildcards `row.*`), `filters` (optional `{ workspace_id?, sheet_id? }`), `secret` (generated 32 bytes, returned once), `status: active`; creation returns `version` 1 and publishes `webhook.updated.v1`.
- **FR-F028-09:** For each outbox event matching an active webhook's events and filters, the dispatcher creates a `webhook_deliveries` row with a UUIDv7 `delivery_id` and POSTs the JSON envelope `{ id, event, occurred_at, tenant_id, data, correlation_id }` with headers `X-OpsHub-Delivery-Id`, `X-OpsHub-Event`, `X-OpsHub-Timestamp`, and `X-OpsHub-Signature: v1=<hex HMAC-SHA256 of "<timestamp>.<body>">` within 10 s timeout; any 2xx marks the delivery `succeeded`.
- **FR-F028-10:** A non-2xx response, timeout, or connection error marks the attempt `failed` and schedules retries at 1 min, 5 min, 30 min, 2 h, and 12 h (5 attempts total) with jitter; after the final failure the delivery is `exhausted` and `webhook.failed.v1` is published once per delivery.
- **FR-F028-11:** After 10 consecutive exhausted deliveries a webhook moves to `status: disabled` with `disabled_reason: consecutive_failures`, publishes `webhook.disabled.v1`, and stops receiving events until a `tenant-admin` sets `status: active` again; a successful delivery resets the consecutive counter.
- **FR-F028-12:** `GET /api/v1/webhooks/{id}/deliveries` lists deliveries with `status`, `attempts` (each with `status_code`, `duration_ms`, `error`, `attempted_at`), `event`, and `created_at`, filterable by `status` and `event`; `POST /api/v1/webhook-deliveries/{id}/replay` creates a new delivery with the same payload and a new delivery ID within 30 days of the original, returns `202`, and is rejected with `409 conflict` when the webhook is disabled.
- **FR-F028-13:** `PATCH /api/v1/webhooks/{id}` supports `rotate_secret: true` which returns a new secret once and honors the old secret for signatures during a 24-hour grace where both signatures are sent as `v1=<new>,v1=<old>`; `DELETE` soft-deletes and cancels pending deliveries.
- **FR-F028-14:** Every application and webhook mutation requires `Idempotency-Key` and writes an audit event; cross-tenant IDs return `not_found`; a non-admin receives `denied`; delivery payloads contain only fields the application's scopes allow to read.
- **FR-F028-15:** The web developer console lists applications and webhooks, shows the one-time secret and token, renders the delivery log with attempt details, offers `Replay` and `Re-enable`, and links the OpenAPI document and a rendered reference page.

### Non-functional requirements

- **NFR-F028-01 Performance:** OpenAPI document served from an in-memory build artifact in under 50 ms p95; list conventions add under 20 ms p95 over the underlying query; dispatcher latency from outbox commit to first delivery attempt under 5 s p95; 1,000 deliveries per minute per tenant sustained.
- **NFR-F028-02 Security/privacy:** webhook URLs are resolved and rejected when they point to private, loopback, link-local, or metadata ranges at creation and at each attempt; secrets stored encrypted with the deployment envelope key and never logged; signature uses constant-time comparison in the verification sample; application tokens honor `allowed_ips`.
- **NFR-F028-03 Accessibility:** the developer console passes axe with zero serious violations; delivery status uses text plus icon; one-time secret fields are labelled and copy actions are announced.
- **NFR-F028-04 Reliability/observability:** the dispatcher is an idempotent JetStream consumer keyed by `(webhook_id, event_id)`, survives worker restart without duplicate deliveries, dead-letters malformed payloads; metrics `webhook_delivery_total{status}`, `webhook_delivery_duration_seconds`, `api_rate_limited_total{application}` and per-delivery tracing spans exist.

### Scope

Included: OpenAPI generation and drift gate, list and error conventions as shared middleware and extractors, correlation IDs, application registry and per-application rate limits, webhook CRUD, signing, dispatch, retry, replay, disable-after-failure, delivery log, developer console.

Excluded: session login and API token issuance (F038); role and ACL evaluation (F003); outbox and JetStream transport (F004); inbound webhooks for workflows (F019); OAuth connections to providers (F029); MCP transport (F047); SDK generation for client languages (later increment).

## 3. UX specification

- Entry points: admin navigation `Developer`; routes `/admin/developer/applications`, `/admin/developer/applications/:appId`, `/admin/developer/webhooks`, `/admin/developer/webhooks/:webhookId`, `/admin/developer/reference` (rendered OpenAPI).
- Primary flow: administrator creates application `Finance sync` with scopes `rows:read`, `rows:write`, copies the token once; creates webhook `https://hooks.partner.example/opshub` for `row.updated.v1` filtered to sheet `Budget`, copies the secret once; edits a row and sees a `succeeded` delivery with 200 in 340 ms; partner endpoint goes down, deliveries show `failed` attempts with the retry schedule, the webhook becomes `disabled` after 10 exhausted deliveries, the administrator clicks `Re-enable` and `Replay` on the last delivery.
- Loading: table skeletons; Empty: cards with `New application` and `New webhook`; Error: banner with `correlation_id` and retry; Success: toasts; Stale/conflict: banner with reload; Denied: non-admins see the denied page; disabled webhooks show a warning row with the reason and `Re-enable`.
- Delivery detail drawer: envelope preview (payload redacted to the first 4 KB), attempts table, `Replay` button, curl sample for signature verification.
- Responsive: tables collapse to cards under 768 px; the delivery drawer becomes a full-screen sheet under 640 px.
- Keyboard: tab order follows tables and drawers; `Escape` closes; copy buttons announce; reduced motion disables drawer slide.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062); Lucide icons `Code2`, `Webhook`, `KeyRound`, `RotateCw`, `Power`, `Copy`; tokens from `apps/web/src/design/tokens.css`.

## 4. Technical specification

### Rust backend

- Domain entities in `crates/domain/src/public-api/`: `ApiApplication { id, tenant_id, name, description, client_id, scopes: Vec<Scope>, rate_limit_per_minute: u32, allowed_ips: Vec<IpNet>, status: AppStatus, version, audit fields, deleted_at }`, `Webhook { id, tenant_id, application_id: Option<ApplicationId>, url: HttpsUrl, events: Vec<EventPattern>, filters: WebhookFilters, secret_ref: EncryptedSecret, previous_secret_ref, previous_secret_expires_at, status: WebhookStatus (Active|Disabled), disabled_reason, consecutive_failures: u32, version, audit fields, deleted_at }`, `WebhookDelivery { id, tenant_id, webhook_id, event_id, event_name, payload: Json, status: Pending|Succeeded|Failed|Exhausted|Cancelled, attempts: Vec<DeliveryAttempt>, next_attempt_at, replay_of, created_at }`.
- Use cases: `create_application`, `update_application`, `delete_application`, `list_applications`, `create_webhook`, `update_webhook`, `delete_webhook`, `list_webhooks`, `list_deliveries`, `replay_delivery`, `match_event`, `sign_payload`, `dispatch_delivery`, `schedule_retry`, `disable_after_failures`.
- Shared conventions in `crates/contracts/src/public-api/`: `ListQuery { cursor, limit, filter, sort, fields, include_total }`, `Page<T>`, `FilterExpr` parser, `SignedCursor` (HMAC-SHA256 with 24-hour expiry), `ApiError`, `openapi.rs` builder that walks `utoipa` annotations on every contract module and emits `openapi/v1.json`; `check-contracts` diffs the emitted document against the committed file.
- API endpoints (`services/api/src/public-api/`): `GET /api/v1/openapi.json`, `GET /api/v1/applications`, `POST /api/v1/applications`, `PATCH /api/v1/applications/{id}`, `DELETE /api/v1/applications/{id}`, `GET /api/v1/webhooks`, `POST /api/v1/webhooks`, `PATCH /api/v1/webhooks/{id}`, `DELETE /api/v1/webhooks/{id}`, `GET /api/v1/webhooks/{id}/deliveries`, `POST /api/v1/webhook-deliveries/{id}/replay`. DTOs: `CreateApplicationRequest`, `UpdateApplicationRequest`, `ApplicationResponse`, `CreateWebhookRequest`, `UpdateWebhookRequest { url?, events?, filters?, status?, rotate_secret? }`, `WebhookResponse`, `WebhookSecretResponse`, `DeliveryResponse`, `Page<DeliveryResponse>`.
- Middleware (`services/api/src/public-api/middleware.rs`): `CorrelationId` layer, `RateLimit` layer keyed by application using F038 `rate_limit_buckets`, `AllowedIps` check, `ListQuery` extractor, and `ApiError` response mapper mounted for the whole `/api/v1` router.
- Worker (`services/worker/src/public-api/dispatcher.rs`): JetStream consumer on `outbox.>` subjects, matches events to webhooks per tenant, writes deliveries, performs HTTP POST with `reqwest` (10 s timeout, no redirects, DNS re-resolution and private-range rejection per attempt), retry schedule `[60, 300, 1800, 7200, 43200]` seconds with ±10 % jitter, disable-after-10 logic, replay handler.
- Events: `application.updated.v1`, `webhook.updated.v1`, `webhook.delivered.v1`, `webhook.failed.v1`, `webhook.disabled.v1`; payload per contract conventions.
- Authorization: `tenant-admin` for all application and webhook mutations and reads; `openapi.json` readable by any authenticated actor; delivery payloads filtered by the application's scopes through the F003 field-level filter.
- Validation: `name` 1–120; scopes must exist in F038 catalog; `rate_limit_per_minute` 60–6,000; `url` https with public IP; `events` 1–50 valid patterns; `limit` bounds per route; filter grammar depth ≤ 10 terms.
- Error mapping: `PublicApiError::InvalidCursor → 400 invalid`, `::InvalidFilter → 400 invalid`, `::PrivateUrl → 400 invalid`, `::StaleVersion → 409 conflict`, `::WebhookDisabled → 409 conflict`, `::ReplayExpired → 409 conflict`, `::NotFound → 404 not_found`, `RateLimit → 429 rate_limited`, `AuthzError::Denied → 403 denied`.

### PostgreSQL/SQLx

- Migration `*_public-api_*.sql` creates `api_applications(id uuid pk, tenant_id, name text, description text, client_id text not null, scopes text[] not null, rate_limit_per_minute int not null default 600, allowed_ips cidr[] not null default '{}', status text not null default 'active', version bigint, audit fields, deleted_at)`, `webhooks(id, tenant_id, application_id uuid null, url text not null, events text[] not null, filters jsonb not null default '{}', secret_ciphertext bytea not null, secret_key_id text not null, previous_secret_ciphertext bytea null, previous_secret_expires_at timestamptz null, status text not null default 'active', disabled_reason text null, consecutive_failures int not null default 0, version, audit fields, deleted_at)`, `webhook_deliveries(id uuid pk, tenant_id, webhook_id, event_id uuid not null, event_name text not null, payload jsonb not null, status text not null, attempts jsonb not null default '[]', attempt_count int not null default 0, next_attempt_at timestamptz null, replay_of uuid null, created_at, completed_at)`.
- Invariants: `api_applications(tenant_id, client_id)` unique; `api_applications(tenant_id, lower(name)) where deleted_at is null` unique; `webhook_deliveries(webhook_id, event_id) where replay_of is null` unique (idempotent dispatch); check `attempt_count <= 5`; `webhooks.consecutive_failures >= 0`.
- Indexes: `webhooks(tenant_id, status) where deleted_at is null`, `webhook_deliveries(webhook_id, created_at desc)`, `webhook_deliveries(next_attempt_at) where status = 'failed'`, `webhook_deliveries(tenant_id, status)`.
- Audit events: `application.create`, `application.update`, `application.delete`, `webhook.create`, `webhook.update`, `webhook.rotate-secret`, `webhook.delete`, `webhook.replay`, `webhook.disabled` with diffs.
- Retention/deletion: deliveries older than 30 days are deleted by the F027 retention sweep under kind `webhook_deliveries`; applications and webhooks soft-delete; rollback drops the three tables.

### React/TypeScript

- Routes: `/admin/developer/applications`, `/admin/developer/applications/:appId`, `/admin/developer/webhooks`, `/admin/developer/webhooks/:webhookId`, `/admin/developer/reference` in `apps/web/src/features/public-api/`; components `DeveloperPage`, `ApplicationTable`, `ApplicationForm`, `TokenRevealDialog`, `WebhookTable`, `WebhookForm`, `SecretRevealDialog`, `DeliveryLog`, `DeliveryDrawer`, `AttemptTable`, `ReferencePage`.
- State: TanStack Query keys `['applications']`, `['application', id]`, `['webhooks']`, `['webhook', id]`, `['deliveries', webhookId, filter, cursor]` (polls every 10 s while any delivery is `pending` or `failed`), `['openapi']`.
- API client: generated `PublicApi` with `listApplications`, `createApplication`, `updateApplication`, `deleteApplication`, `listWebhooks`, `createWebhook`, `updateWebhook`, `deleteWebhook`, `listDeliveries`, `replayDelivery`, `getOpenApi`.
- Telemetry: `application_created`, `webhook_created`, `webhook_secret_rotated`, `delivery_replayed`, `webhook_reenabled`, `reference_opened` with `application_id` or `webhook_id`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F028-01 through FR-F028-15 in `testing/features/F028/requirements/cases.md`
- [ ] Failure/edge-case tests: expired cursor, unknown filter field, private webhook URL, DNS rebinding to a private address at attempt time, timeout at 10 s, 10 consecutive exhausted deliveries, replay of a 31-day-old delivery, secret rotation grace
- [ ] Permission-negative and tenant-isolation tests: member cannot create applications or webhooks, foreign-tenant IDs return `not_found`, suspended application tokens rejected, delivery payload excludes fields outside scopes
- [ ] Rust unit tests: `crates/contracts/src/public-api/` filter parser, signed cursor, OpenAPI builder; `crates/domain/src/public-api/` signature, retry schedule, event matching
- [ ] API contract/integration tests: every route above with success and each error code; generated document validated against the OpenAPI 3.1 schema
- [ ] Database migration/constraint tests: uniqueness, idempotent delivery key, attempt cap, rollback
- [ ] React component tests: `ApplicationForm`, `WebhookForm`, `SecretRevealDialog`, `DeliveryLog`, `DeliveryDrawer` states
- [ ] Browser E2E tests: create application and webhook, receive signed delivery on a harness receiver, failures disable, re-enable and replay
- [ ] Accessibility tests: axe on developer routes and drawers
- [ ] Performance/load tests: 1,000 deliveries per minute, dispatch latency p95 under 5 s, OpenAPI under 50 ms

### Fast fanout configuration

- Test harness path: `testing/features/F028/`
- Feature flag: `F028_FEATURE`
- Fixture/seed factory: `testing/fixtures/public_api.rs` builds tenant A and B, tenant-admin, member, one application with two scopes, one webhook per tenant, 120 seeded deliveries in mixed states, and a harness HTTP receiver that records requests and can return 200, 500, or hang
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, UTC, fixed webhook secret for signature vectors
- Mock/stub contracts: harness receiver on `127.0.0.1` with an allowlist override for tests; outbox recorded in memory for API tests and real JetStream for dispatcher tests; envelope key from the test secret manager stub
- Parallel isolation: one schema per test worker, tenant ID per test, receiver port per worker
- Targeted command: `cargo xtask test-feature F028`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F028/`

## 6. Acceptance criteria

```gherkin
Feature: Public API conventions and signed webhooks

Scenario: Generated OpenAPI matches the router
  Given the service is built
  When a client requests /api/v1/openapi.json
  Then every registered /api/v1 route appears with typed schemas and the Error schema
  And check-contracts reports no drift

Scenario: Signed delivery with retry and disable
  Given webhook "partner" subscribed to row.updated.v1 on sheet "Budget"
  When a row in "Budget" is updated and the receiver returns 500 for every attempt
  Then the delivery has 5 attempts at 1m, 5m, 30m, 2h, 12h and status exhausted
  And after 10 exhausted deliveries the webhook is disabled and webhook.disabled.v1 is published

Scenario: Member cannot create a webhook
  Given a member without the tenant-admin role
  When they POST /api/v1/webhooks
  Then the response is 403 denied and no webhook exists

Scenario: Rate limit headers and 429
  Given an application limited to 60 requests per minute
  When it sends 121 requests in one minute
  Then the first 120 succeed with X-RateLimit-Remaining decreasing and the 121st is 429 rate_limited with Retry-After
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F003 (roles, field-level filter, audit); F038 (API tokens, scopes, rate-limit buckets); F004 (outbox, JetStream, worker runtime, secret manager); decisions sections 3, 4, 7; contracts row F028
- Blocks: F029, F047
- Conflicts with: none (disjoint owned paths)
- External dependencies: customer HTTPS endpoints; harness receiver stands in during tests
- Risks and mitigations: OpenAPI drift between annotations and handlers, mitigated by generating from the same route registration and failing CI on diff; SSRF through webhook URLs, mitigated by resolving and checking addresses at creation and at every attempt with redirects disabled; delivery storms after an outage, mitigated by per-tenant dispatch quota and jittered retries; secret exposure in logs, mitigated by envelope encryption and a redaction test on the logging layer.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F003, F038, and F004 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F028/`
- [ ] Migration file name and owned paths claimed
- [ ] Harness HTTP receiver available in `testing/harness/receiver.rs`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for every mutation and delivery outcome
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass with the committed `openapi/v1.json`
- [ ] Rollback verified: disable `F028_FEATURE`, run down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Tenant administrators can register API applications with scoped, rate-limited credentials, read a generated OpenAPI 3.1 reference, and subscribe HTTPS endpoints to signed events with retry, replay, and automatic disable after repeated failures.
- Migration adds `api_applications`, `webhooks`, and `webhook_deliveries`; rollback drops them. Feature is off by default behind `F028_FEATURE`.
