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
owned_paths: [crates/domain/src/public-api/**, crates/persistence/src/public-api/**, crates/contracts/src/public-api/**, services/api/src/public-api/**, services/worker/src/public-api/**, apps/web/src/features/public-api/**, services/api/migrations/*_public-api_*.sql, testing/features/F028/**]
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
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 7; `docs/capability-contracts.md` row F028
- Aggregate: `api-application`
- Module slug: `public-api`

## 2. Requirement specification

### Problem and user outcome

Customers and partners need to read and write OpsHub records from their own systems and react to changes without polling. Today the API exists only as internal handlers with no published description, no consistent list conventions, and no way to subscribe to events.

As a tenant administrator, I want to register an API application with scoped credentials, read a generated OpenAPI 3.1 document that matches the running service, rely on one set of pagination, filtering, error, and rate-limit conventions, and subscribe HTTPS endpoints to signed events with retry and replay, so that integrations are buildable from the documentation alone and observable when they fail.

### Functional requirements

- **FR-F028-01:** `GET /api/v1/openapi.json` returns an OpenAPI 3.1 document generated at build time from the typed Rust contracts in `crates/contracts` covering every `/api/v1` route registered in the router; the document includes `info.version` equal to the service build, component schemas for every DTO, the shared `Error` schema, `Page<T>` schemas, and security schemes `sessionCookie` and `apiToken`; a route missing from the document fails the `check-contracts` CI gate.
- **FR-F028-02:** A `tenant-admin` can create an API application with `name`, `description`, `scopes` (subset of the F038 token scopes), `rate_limit_per_minute` (60–6,000, default 600), and `allowed_ips` (0–20 CIDRs); each requested scope is stored as one `api_application_scopes` row and each CIDR as one `api_application_allowed_ips` row, and a scope outside the F038 catalog returns `400 invalid` with `field_errors.scopes`; creation returns the application with `version` 1 and a `client_id`; credentials are issued as F038 API tokens bound to the application.
- **FR-F028-03:** `PATCH /api/v1/applications/{id}` updates name, description, scopes, rate limit, allowed IPs, and `status: active|suspended` with `If-Match`; a scope or CIDR change replaces the `api_application_scopes` and `api_application_allowed_ips` rows for the application in the same transaction as the parent version bump, so a token's effective scopes are the current rows and never a stale copy; suspending an application rejects its tokens with `401 denied` within 5 s; `DELETE` soft-deletes and revokes all bound tokens; both publish `application.updated.v1`.
- **FR-F028-04:** Every `/api/v1` list route accepts `cursor` (opaque, HMAC-signed, expires after 24 hours), `limit` (1–200 default 50 unless the route documents a higher cap), `filter` (grammar `field op value` joined by `and`, operators `eq`, `ne`, `lt`, `lte`, `gt`, `gte`, `in`, `contains`, `is_null`), `sort` (`field` or `-field`, at most 3 keys), and `fields` (comma-separated projection); an invalid cursor returns `400 invalid` with `field_errors.cursor`, an unknown filter field returns `400 invalid` with `field_errors.filter`.
- **FR-F028-05:** List responses are `{ items, next_cursor, has_more, total?: number }` where `total` is present only when `include_total=true` and the route allows it; `fields` projection removes non-requested attributes but always returns `id` and `version`.
- **FR-F028-06:** Every error response uses `{ code, message, field_errors, correlation_id }` with `code` in `invalid`, `denied`, `not_found`, `conflict`, `rate_limited`, `unavailable`; HTTP status maps `400`, `403`, `404`, `409`, `429`, `503`; `correlation_id` equals the request's `X-Correlation-Id` header when supplied (UUID) or a generated UUIDv7, and is echoed on every response.
- **FR-F028-07:** Requests authenticated by an application token are rate-limited per application with a token bucket of `rate_limit_per_minute` and burst 2x; every response carries `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` (epoch seconds); an exhausted bucket returns `429 rate_limited` with `Retry-After`.
- **FR-F028-08:** A `tenant-admin` can create a webhook with `url` (https, public IP only, ≤ 2,048 chars), `events` (1–50 names from the contract event catalog, wildcards `row.*`), `filters` (optional `{ workspace_id?, sheet_id? }`), `secret` (generated 32 bytes, returned once), `status: active`; each event pattern becomes one `webhook_events` row and each filter becomes one `webhook_filters(filter_key, filter_value)` row, so a duplicate pattern is rejected by the primary key and an unsupported filter key by the `check` constraint with `field_errors.filters`; creation returns `version` 1 and publishes `webhook.updated.v1`.
- **FR-F028-09:** For each outbox event the dispatcher selects candidate webhooks by joining `webhook_events` on an exact pattern or its `row.*` prefix and requiring that every `webhook_filters` row for the webhook is satisfied by the envelope, then creates a `webhook_deliveries` row with a UUIDv7 `delivery_id` and POSTs the JSON envelope `{ id, event, occurred_at, tenant_id, data, correlation_id }` with headers `X-OpsHub-Delivery-Id`, `X-OpsHub-Event`, `X-OpsHub-Timestamp`, and `X-OpsHub-Signature: v1=<hex HMAC-SHA256 of "<timestamp>.<body>">` within 10 s timeout; any 2xx marks the delivery `succeeded`.
- **FR-F028-10:** Every attempt is one `webhook_delivery_attempts` row (`attempt_no`, `outcome`, `status_code`, `duration_ms`, `error_code`, `error_detail`, `attempted_at`); a non-2xx response, timeout, or connection error marks the attempt `failed` and schedules retries at 1 min, 5 min, 30 min, 2 h, and 12 h (5 attempts total) with jitter; after the final failure the delivery is `exhausted` and `webhook.failed.v1` is published once per delivery.
- **FR-F028-11:** After 10 consecutive exhausted deliveries a webhook moves to `status: disabled` with `disabled_reason: consecutive_failures`, publishes `webhook.disabled.v1`, and stops receiving events until a `tenant-admin` sets `status: active` again; a successful delivery resets the consecutive counter.
- **FR-F028-12:** `GET /api/v1/webhooks/{id}/deliveries` lists deliveries with `status`, `attempts` (the delivery's `webhook_delivery_attempts` rows in `attempt_no` order, each rendered as `{ status_code, duration_ms, error, attempted_at }`), `event`, and `created_at`, filterable by `status` and `event` against the delivery columns; `POST /api/v1/webhook-deliveries/{id}/replay` creates a new delivery with the same payload and a new delivery ID within 30 days of the original, returns `202`, and is rejected with `409 conflict` when the webhook is disabled.
- **FR-F028-13:** `PATCH /api/v1/webhooks/{id}` supports `rotate_secret: true` which returns a new secret once and honors the old secret for signatures during a 24-hour grace where both signatures are sent as `v1=<new>,v1=<old>`; `DELETE` soft-deletes and cancels pending deliveries.
- **FR-F028-14:** Every application and webhook mutation requires `Idempotency-Key` and writes an audit event; cross-tenant IDs return `not_found`; a non-admin receives `denied`; delivery payloads contain only fields the application's current `api_application_scopes` rows allow to read.
- **FR-F028-15:** The web developer console lists applications and webhooks, shows the one-time secret and token, renders the delivery log with attempt details, offers `Replay` and `Re-enable`, and links the OpenAPI document and a rendered reference page.

### Non-functional requirements

- **NFR-F028-01 Performance:** OpenAPI document served from an in-memory build artifact in under 50 ms p95; list conventions add under 20 ms p95 over the underlying query; dispatcher latency from outbox commit to first delivery attempt under 5 s p95; 1,000 deliveries per minute per tenant sustained.
- **NFR-F028-02 Security/privacy:** webhook URLs are resolved and rejected when they point to private, loopback, link-local, or metadata ranges at creation and at each attempt; secrets stored encrypted with the deployment envelope key and never logged; signature uses constant-time comparison in the verification sample; application tokens honor the application's `api_application_allowed_ips` rows, and an empty row set means no source restriction.
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

- Design: `design/artboards/Api.dc.html` on the canvas indexed by `design/canvas.json`. The ticket is the contract and the artboard is the picture; when they disagree the ticket wins.

## 4. Technical specification

### Rust backend

- Data access (decision section 2.1): `crates/persistence/src/public-api/` holds `ApiApplicationRepository` (owns `api_applications`, `api_application_scopes`, `api_application_allowed_ips`), `WebhookRepository` (owns `webhooks`, `webhook_events`, `webhook_filters`), and `WebhookDeliveryRepository` (owns `webhook_deliveries`, `webhook_delivery_attempts`). Each child table is written only by the repository of its parent object type, so no two classes write the same table. Named queries: `find_application_by_client_id`, `list_scopes`, `replace_scopes`, `list_allowed_ips`, `replace_allowed_ips`, `suspend_application`, `list_active_webhooks_for_event` (joins `webhook_events` on exact pattern or `row.*` prefix and requires every `webhook_filters` row to match the envelope), `replace_event_patterns`, `replace_filters`, `rotate_secret_with_grace`, `claim_delivery_for_event` (`insert ... on conflict (webhook_id, event_id) do nothing` returning the row), `claim_due_deliveries` (bounded batch on `next_attempt_at`), `append_attempt`, `record_delivery_outcome`, `list_deliveries_by_status_and_event`, `insert_replay_of`, `cancel_pending_for_webhook`, `count_trailing_exhausted`, `reset_consecutive_failures`, `purge_deliveries_before`. There is no generic query entry point. Every use case below depends on these repository traits and contains no SQL; the application and webhook handlers, the `middleware.rs` scope and allowed-IP lookups, the worker dispatcher, and the retention sweep call repositories only. Multi-table writes — a webhook save that replaces its event and filter rows, an application save that replaces its scope and CIDR rows, an attempt append that also flips delivery status and the webhook's `consecutive_failures` — run in one `UnitOfWork` that owns the transaction.
- Domain entities in `crates/domain/src/public-api/`: `ApiApplication { id, tenant_id, name, description, client_id, scopes: Vec<Scope>, rate_limit_per_minute: u32, allowed_ips: Vec<IpNet>, status: AppStatus, version, audit fields, deleted_at }`, `Webhook { id, tenant_id, application_id: Option<ApplicationId>, url: HttpsUrl, events: Vec<EventPattern>, filters: WebhookFilters, secret_ref: EncryptedSecret, previous_secret_ref, previous_secret_expires_at, status: WebhookStatus (Active|Disabled), disabled_reason, consecutive_failures: u32, version, audit fields, deleted_at }`, `WebhookDelivery { id, tenant_id, webhook_id, event_id, event_name, payload: Json, status: Pending|Succeeded|Failed|Exhausted|Cancelled, attempts: Vec<DeliveryAttempt>, next_attempt_at, replay_of, created_at }`. The `Vec` and struct fields are in-memory projections the repositories assemble from the child rows; the aggregates never see an array column.
- Use cases: `create_application`, `update_application`, `delete_application`, `list_applications`, `create_webhook`, `update_webhook`, `delete_webhook`, `list_webhooks`, `list_deliveries`, `replay_delivery`, `match_event`, `sign_payload`, `dispatch_delivery`, `schedule_retry`, `disable_after_failures`.
- Shared conventions in `crates/contracts/src/public-api/`: `ListQuery { cursor, limit, filter, sort, fields, include_total }`, `Page<T>`, `FilterExpr` parser, `SignedCursor` (HMAC-SHA256 with 24-hour expiry), `ApiError`, `openapi.rs` builder that walks `utoipa` annotations on every contract module and emits `openapi/v1.json`; `check-contracts` diffs the emitted document against the committed file.
- API endpoints (`services/api/src/public-api/`): `GET /api/v1/openapi.json`, `GET /api/v1/applications`, `POST /api/v1/applications`, `PATCH /api/v1/applications/{id}`, `DELETE /api/v1/applications/{id}`, `GET /api/v1/webhooks`, `POST /api/v1/webhooks`, `PATCH /api/v1/webhooks/{id}`, `DELETE /api/v1/webhooks/{id}`, `GET /api/v1/webhooks/{id}/deliveries`, `POST /api/v1/webhook-deliveries/{id}/replay`. DTOs: `CreateApplicationRequest`, `UpdateApplicationRequest`, `ApplicationResponse`, `CreateWebhookRequest`, `UpdateWebhookRequest { url?, events?, filters?, status?, rotate_secret? }`, `WebhookResponse`, `WebhookSecretResponse`, `DeliveryResponse`, `Page<DeliveryResponse>`.
- Middleware (`services/api/src/public-api/middleware.rs`): `CorrelationId` layer, `RateLimit` layer keyed by application reading and writing F038 `rate_limit_buckets` through F038's `RateLimitBucketRepository` (this feature never issues SQL against another module's tables), `AllowedIps` check fed by `ApiApplicationRepository::list_allowed_ips`, `ListQuery` extractor, and `ApiError` response mapper mounted for the whole `/api/v1` router; the layers cache the application's scope and CIDR rows for the token cache TTL and re-read on `application.updated.v1`.
- Worker (`services/worker/src/public-api/dispatcher.rs`): JetStream consumer on `outbox.>` subjects, matches events to webhooks per tenant through `WebhookRepository::list_active_webhooks_for_event`, writes deliveries and attempts through `WebhookDeliveryRepository` (no `sqlx` call in the worker crate), performs HTTP POST with `reqwest` (10 s timeout, no redirects, DNS re-resolution and private-range rejection per attempt), retry schedule `[60, 300, 1800, 7200, 43200]` seconds with ±10 % jitter, disable-after-10 logic, replay handler.
- Events: `application.updated.v1`, `webhook.updated.v1`, `webhook.delivered.v1`, `webhook.failed.v1`, `webhook.disabled.v1`; payload per contract conventions.
- Authorization: `tenant-admin` for all application and webhook mutations and reads; `openapi.json` readable by any authenticated actor; delivery payloads filtered by the application's scopes through the F003 field-level filter.
- Validation: `name` 1–120; scopes must exist in F038 catalog; `rate_limit_per_minute` 60–6,000; `url` https with public IP; `events` 1–50 valid patterns; `limit` bounds per route; filter grammar depth ≤ 10 terms.
- Error mapping: `PublicApiError::InvalidCursor → 400 invalid`, `::InvalidFilter → 400 invalid`, `::PrivateUrl → 400 invalid`, `::StaleVersion → 409 conflict`, `::WebhookDisabled → 409 conflict`, `::ReplayExpired → 409 conflict`, `::NotFound → 404 not_found`, `RateLimit → 429 rate_limited`, `AuthzError::Denied → 403 denied`.

### Interface

This is the canonical definition of the conventions every `/api/v1` route in the product follows.
Other tickets reference `ListQuery`, `Page<T>`, the signed cursor, the error body, the standard
headers, and the rate-limit headers by name and do not restate them. Field tables give the JSON
name, the type, whether the field is required, and the constraint whose violation produces the
stated error. `T?` is nullable; an absent optional field and an explicit `null` mean the same thing.
Timestamps are RFC 3339 UTC, ids are UUIDv7 strings, and `version` is an integer that increments by
one per write. Unlisted request fields are rejected with `400 invalid` carrying the offending field
in `field_errors`.

**Standard request headers** — every route

| Field | Type | Required | Constraint |
|---|---|---|---|
| `X-Correlation-Id` | uuid | no | echoed on the response and in the error body; a generated UUIDv7 when absent, `400 invalid` when present and not a UUID (FR-F028-06) |
| `Idempotency-Key` | string | on every mutation | 1–255 chars; replay with the same body returns the original response, a different body returns `409 conflict` |
| `If-Match` | integer | on every update of a versioned aggregate | the `version` last read; a mismatch is `409 conflict` carrying the current version |
| `Authorization` | string | on token-authenticated calls | `Bearer <F038 API token>`; the token's application supplies the scopes, rate limit, and allowed-IP set |

**`ListQuery`** — the query string every list route accepts (FR-F028-04)

| Field | Type | Required | Constraint |
|---|---|---|---|
| `cursor` | string? | no | opaque signed cursor from a previous `next_cursor`; malformed, re-signed, expired, or issued for a different filter/sort/limit → `400 invalid` with `field_errors.cursor` |
| `limit` | integer | no | 1–200, default 50, unless the route documents a higher cap (F006 rows cap at 500); out of range → `400 invalid` with `field_errors.limit` |
| `filter` | string? | no | `field op value` terms joined by `and`, at most 10 terms; `op` is `eq`, `ne`, `lt`, `lte`, `gt`, `gte`, `in`, `contains`, `is_null`; unknown field or unparsable term → `400 invalid` with `field_errors.filter` |
| `sort` | string? | no | `field` or `-field`, at most 3 keys, each a sortable field of the route; otherwise `400 invalid` with `field_errors.sort` |
| `fields` | string? | no | comma-separated projection; unknown name → `400 invalid` with `field_errors.fields`; `id` and `version` are always returned regardless (FR-F028-05) |
| `include_total` | bool | no | default `false`; `true` on a route that does not allow it → `400 invalid` |

**`Page<T>`** — the envelope of every list response (FR-F028-05)

| Field | Type | Notes |
|---|---|---|
| `items` | T array | at most `limit` entries, in the requested sort order, projected by `fields` |
| `next_cursor` | string? | signed cursor for the next page; `null` on the last page |
| `has_more` | bool | `true` when `next_cursor` is non-null; stated separately so a client need not inspect the cursor |
| `total` | integer? | present only when `include_total=true` was accepted, because counting costs a second query |

**Signed cursor payload** — the plaintext that `SignedCursor` HMACs, base64url of the JSON below
concatenated with the tag; a client treats the whole string as opaque and never constructs one

| Field | Type | Notes |
|---|---|---|
| `k` | string array | the sort-key values of the last item of the previous page, in `sort` order |
| `i` | uuid | the last item's `id`, the tiebreak that makes the key total |
| `q` | string | hash of the route, `filter`, `sort`, and `limit` the cursor was issued for; a mismatch is an invalid cursor, so a cursor cannot be replayed against a different query |
| `e` | integer | expiry as epoch seconds, issue time plus 24 hours |
| `t` | uuid | issuing `tenant_id`; a cursor never crosses a tenant |

**Error body** — every non-2xx response (FR-F028-06)

| Field | Type | Notes |
|---|---|---|
| `code` | enum | exactly one of `invalid`, `denied`, `not_found`, `conflict`, `rate_limited`, `unavailable`; clients branch on this, never on `message` |
| `message` | string | human-readable, not stable, never parsed |
| `field_errors` | map<string, string> | request field path (dotted, e.g. `filters.workspace_id`) to a stable reason key; `{}` when the failure is not field-specific |
| `correlation_id` | uuid | the request's `X-Correlation-Id` or the generated one; the same value the response header carries |

**Status codes** — the whole product uses these and no others

| Status | `code` | Produced by |
|---|---|---|
| `400` | `invalid` | any constraint in a field table above, an unlisted field, a malformed cursor or filter, a private or non-https webhook URL, a scope outside the F038 catalog |
| `403` | `denied` | the caller is authenticated and may see the resource exists but lacks the permission — non-admin on any application or webhook route |
| `404` | `not_found` | the id does not exist, belongs to another tenant, or the caller may not see it; an invisible resource is never `denied`, so ids do not leak existence |
| `409` | `conflict` | stale `If-Match`, name or `client_id` uniqueness, `Idempotency-Key` replayed with a different body, replay of a delivery on a disabled webhook or older than 30 days |
| `429` | `rate_limited` | the application's token bucket is exhausted; carries `Retry-After` |
| `503` | `unavailable` | a dependency the request cannot complete without is down; safe to retry after `Retry-After` |

`401` is the one status outside the six-code body's own mapping: an application token whose
application is `suspended` or deleted is rejected at authentication with `401` and a body whose
`code` is `denied` (FR-F028-03). Authentication failure is not authorization failure, which is why
the status differs from the `denied → 403` row above.

**Rate-limit headers** — on every response to a token-authenticated request (FR-F028-07)

| Field | Type | Notes |
|---|---|---|
| `X-RateLimit-Limit` | integer | the application's `rate_limit_per_minute` |
| `X-RateLimit-Remaining` | integer | tokens left in the bucket, floor 0 |
| `X-RateLimit-Reset` | integer | epoch seconds at which the bucket is full again |
| `Retry-After` | integer | seconds; present only on `429` |

**`CreateApplicationRequest`** — `POST /api/v1/applications`

| Field | Type | Required | Constraint |
|---|---|---|---|
| `name` | string | yes | 1–120 chars after trim, unique per tenant among live applications, else `409 conflict` with `field_errors.name` |
| `description` | string? | no | ≤ 2,000 chars |
| `scopes` | string array | yes | 1–50 entries, each in the F038 scope catalog and matching `<resource>:read` or `<resource>:write`, no duplicates; otherwise `400 invalid` with `field_errors.scopes`. One `api_application_scopes` row per entry |
| `rate_limit_per_minute` | integer | no | 60–6,000, default 600 |
| `allowed_ips` | string array | no | 0–20 CIDRs, no duplicates; empty means no source restriction. One `api_application_allowed_ips` row per entry |

**`UpdateApplicationRequest`** — `PATCH /api/v1/applications/{id}`, every field optional, at least one present

| Field | Type | Required | Constraint |
|---|---|---|---|
| `name` | string | no | as above |
| `description` | string? | no | ≤ 2,000 chars; explicit null clears it |
| `scopes` | string array | no | replaces the scope set whole; the rows are rewritten in the same transaction as the version bump (FR-F028-03) |
| `rate_limit_per_minute` | integer | no | 60–6,000 |
| `allowed_ips` | string array | no | replaces the CIDR set whole |
| `status` | `"active" \| "suspended"` | no | suspending rejects the application's tokens within 5 s |

**`ApplicationResponse`**

| Field | Type | Notes |
|---|---|---|
| `id` / `client_id` | uuid / string | `client_id` is stable and safe to log |
| `name` / `description` | string / string? | |
| `scopes` | string array | reassembled from `api_application_scopes`, sorted |
| `rate_limit_per_minute` | integer | |
| `allowed_ips` | string array | reassembled from `api_application_allowed_ips`, sorted |
| `status` | `"active" \| "suspended"` | |
| `version` | integer | pass as `If-Match` on the next write |
| `created_at` / `updated_at` | timestamp | |
| `created_by` / `updated_by` | uuid | |
| `token` | string? | the issued F038 API token, present only in the `201` body of the create call and never again |

**`CreateWebhookRequest`** — `POST /api/v1/webhooks` (FR-F028-08)

| Field | Type | Required | Constraint |
|---|---|---|---|
| `url` | string | yes | https, ≤ 2,048 chars, resolving to a public address; private, loopback, link-local, or metadata ranges → `400 invalid` with `field_errors.url` |
| `events` | string array | yes | 1–50 catalog event names or the `row.*` wildcard form, no duplicates; one `webhook_events` row per entry |
| `filters` | `WebhookFilters?` | no | see below; an unsupported key → `400 invalid` with `field_errors.filters` |
| `application_id` | uuid? | no | binds the webhook to an application so delivery payloads are filtered to that application's scopes (FR-F028-14) |

**`WebhookFilters`** — the only supported keys, one `webhook_filters` row each

| Field | Type | Required | Constraint |
|---|---|---|---|
| `workspace_id` | uuid? | no | delivery only when the envelope's workspace matches |
| `sheet_id` | uuid? | no | delivery only when the envelope's sheet matches |

**`UpdateWebhookRequest`** — `PATCH /api/v1/webhooks/{id}`, every field optional, at least one present

| Field | Type | Required | Constraint |
|---|---|---|---|
| `url` | string | no | as above |
| `events` | string array | no | replaces the pattern set whole |
| `filters` | `WebhookFilters?` | no | replaces the filter set whole; `null` clears every filter |
| `status` | `"active" \| "disabled"` | no | setting `active` on a webhook disabled by failures clears `disabled_reason` and resets `consecutive_failures` |
| `rotate_secret` | bool | no | `true` returns a new secret once and keeps the old one valid for 24 hours (FR-F028-13) |

**`WebhookResponse`**

| Field | Type | Notes |
|---|---|---|
| `id` / `application_id` | uuid / uuid? | |
| `url` | string | |
| `events` | string array | reassembled from `webhook_events`, sorted |
| `filters` | `WebhookFilters` | reassembled from `webhook_filters`; `{}` when none |
| `status` | `"active" \| "disabled"` | |
| `disabled_reason` | `"consecutive_failures" \| "admin"`? | present only when `status` is `disabled` |
| `consecutive_failures` | integer | resets to 0 on any successful delivery |
| `secret` | string? | present only in the `201` create body and in the `200` body of a `rotate_secret` patch |
| `previous_secret_expires_at` | timestamp? | present during the 24-hour rotation grace |
| `version`, `created_at`, `created_by`, `updated_at`, `updated_by` | | as `ApplicationResponse` |

**`DeliveryResponse`** — items of `GET /api/v1/webhooks/{id}/deliveries` (FR-F028-12)

| Field | Type | Notes |
|---|---|---|
| `id` | uuid | the `X-OpsHub-Delivery-Id` the receiver saw |
| `webhook_id` / `event_id` / `event` | uuid / uuid / string | `event` is the event name; `event_id` is the outbox event |
| `status` | `"pending" \| "succeeded" \| "failed" \| "exhausted" \| "cancelled"` | |
| `attempts` | `DeliveryAttempt` array | the `webhook_delivery_attempts` rows in `attempt_no` order |
| `next_attempt_at` | timestamp? | present while `status` is `failed` and attempts remain |
| `replay_of` | uuid? | the original delivery when this row is a replay |
| `payload_preview` | string | the envelope truncated to the first 4 KB for the drawer |
| `created_at` / `completed_at` | timestamp / timestamp? | |

**`DeliveryAttempt`**

| Field | Type | Notes |
|---|---|---|
| `attempt_no` | integer | 1–5 |
| `status_code` | integer? | null when the attempt never got a response |
| `duration_ms` | integer? | |
| `error` | `{ code, detail }`? | `code` is `timeout`, `connect`, `tls`, `dns`, `private_address`, or `http_status` |
| `attempted_at` | timestamp | |

List route: `GET /api/v1/webhooks/{id}/deliveries` returns `Page<DeliveryResponse>` sorted by
`-created_at` with `id` as tiebreak, filtering on `status` and `event`. `POST /api/v1/webhook-deliveries/{id}/replay` takes no body
and returns `202` with the new `DeliveryResponse`.

**Webhook delivery envelope** — the POST body the receiver gets (FR-F028-09)

| Field | Type | Notes |
|---|---|---|
| `id` | uuid | the delivery id, unique per attempt series; the receiver deduplicates on it |
| `event` | string | `<aggregate>.<verb>.v1` |
| `occurred_at` | timestamp | when the aggregate changed, not when the POST was sent |
| `tenant_id` | uuid | |
| `data` | object | the outbox payload, field-filtered to the bound application's current scopes |
| `correlation_id` | uuid | the correlation id of the request that caused the change |

Delivery headers: `X-OpsHub-Delivery-Id` (the envelope `id`), `X-OpsHub-Event`, `X-OpsHub-Timestamp`
(epoch seconds), and `X-OpsHub-Signature`. The signature value is `v1=<hex>` where `<hex>` is
HMAC-SHA256 of the exact string `<timestamp>.<raw body>` under the webhook secret, and during a
rotation grace both are sent as `v1=<new>,v1=<old>`. A receiver recomputes over the raw body before
parsing and compares in constant time; a timestamp more than 5 minutes from now is a replay.

### Use case signatures

In `crates/domain/src/public-api/`. `ctx` carries tenant, actor, scopes, and correlation id; every
use case returns the shared `DomainError` whose mapping to the six codes is the status table above.
A use case takes a `UnitOfWork` or a repository trait, never a pool or a connection, and never
returns a database row type.

```rust
fn create_application(ctx: &Ctx, uow: &mut UnitOfWork, req: CreateApplication) -> Result<ApiApplication, DomainError>;
fn update_application(ctx: &Ctx, uow: &mut UnitOfWork, id: ApplicationId, expected: Version, req: UpdateApplication) -> Result<ApiApplication, DomainError>;
fn delete_application(ctx: &Ctx, uow: &mut UnitOfWork, id: ApplicationId, expected: Version) -> Result<(), DomainError>;
fn list_applications(ctx: &Ctx, repo: &dyn ApiApplicationRepository, query: ListQuery) -> Result<Page<ApiApplication>, DomainError>;
fn create_webhook(ctx: &Ctx, uow: &mut UnitOfWork, req: CreateWebhook) -> Result<(Webhook, WebhookSecret), DomainError>;
fn update_webhook(ctx: &Ctx, uow: &mut UnitOfWork, id: WebhookId, expected: Version, req: UpdateWebhook) -> Result<(Webhook, Option<WebhookSecret>), DomainError>;
fn delete_webhook(ctx: &Ctx, uow: &mut UnitOfWork, id: WebhookId, expected: Version) -> Result<(), DomainError>;
fn list_webhooks(ctx: &Ctx, repo: &dyn WebhookRepository, query: ListQuery) -> Result<Page<Webhook>, DomainError>;
fn list_deliveries(ctx: &Ctx, repo: &dyn WebhookDeliveryRepository, webhook: WebhookId, filter: DeliveryFilter, query: ListQuery) -> Result<Page<WebhookDelivery>, DomainError>;
fn replay_delivery(ctx: &Ctx, uow: &mut UnitOfWork, id: DeliveryId, now: DateTime<Utc>) -> Result<WebhookDelivery, DomainError>;
fn match_event(envelope: &EventEnvelope, subscriptions: &WebhookSubscriptions) -> Vec<WebhookId>;
fn sign_payload(secret: &WebhookSecret, timestamp: i64, body: &str) -> SignatureHeader;
fn dispatch_delivery(ctx: &Ctx, uow: &mut UnitOfWork, id: DeliveryId, http: &dyn DeliveryTransport) -> Result<DeliveryOutcome, DomainError>;
fn schedule_retry(ctx: &Ctx, uow: &mut UnitOfWork, id: DeliveryId, outcome: DeliveryOutcome, now: DateTime<Utc>) -> Result<Option<DateTime<Utc>>, DomainError>;
fn disable_after_failures(ctx: &Ctx, uow: &mut UnitOfWork, webhook: WebhookId) -> Result<WebhookStatus, DomainError>;
```

Transaction boundaries. `create_application` and `update_application` write the parent row, the full
replacement of its `api_application_scopes` and `api_application_allowed_ips` rows, the audit row,
and the outbox entry in one `UnitOfWork`, which is what makes a token's effective scopes the current
rows and never a half-applied set. `create_webhook` and `update_webhook` do the same across
`webhooks`, `webhook_events`, and `webhook_filters`, so the dispatcher never matches a webhook
against a pattern set that is mid-rewrite. `dispatch_delivery` and `schedule_retry` share one
`UnitOfWork` per attempt covering the `webhook_delivery_attempts` insert, the `webhook_deliveries`
status and `next_attempt_at` update, and the webhook's `consecutive_failures` change, so the
attempt cap and the disable-after-10 counter can never disagree with the attempt rows; the HTTP call
itself happens before that transaction opens, never inside it. `match_event` and `sign_payload` are
pure and take no `ctx`.

### PostgreSQL/SQLx

- Migration `*_public-api_*.sql` creates `api_applications(id uuid pk, tenant_id uuid not null, name text not null, description text, client_id text not null, rate_limit_per_minute int not null default 600 check (rate_limit_per_minute between 60 and 6000), status text not null default 'active' check (status in ('active','suspended')), version bigint not null default 1, created_by, created_at, updated_by, updated_at, deleted_at)`, `webhooks(id uuid pk, tenant_id uuid not null, application_id uuid null references api_applications(id) on delete restrict, url text not null check (url like 'https://%' and length(url) <= 2048), secret_ciphertext bytea not null, secret_key_id text not null, previous_secret_ciphertext bytea null, previous_secret_expires_at timestamptz null, status text not null default 'active' check (status in ('active','disabled')), disabled_reason text null check (disabled_reason is null or disabled_reason in ('consecutive_failures','admin')), consecutive_failures int not null default 0 check (consecutive_failures >= 0), version bigint not null default 1, audit fields, deleted_at)`, `webhook_deliveries(id uuid pk, tenant_id uuid not null, webhook_id uuid not null references webhooks(id) on delete cascade, event_id uuid not null, event_name text not null, payload jsonb not null, status text not null check (status in ('pending','succeeded','failed','exhausted','cancelled')), attempt_count int not null default 0 check (attempt_count between 0 and 5), next_attempt_at timestamptz null, replay_of uuid null references webhook_deliveries(id) on delete restrict, created_at, completed_at)`.
- Normalized sets (decision section 2, no array columns): `api_application_scopes(application_id uuid not null references api_applications(id) on delete cascade, tenant_id uuid not null, scope text not null check (scope ~ '^[a-z][a-z0-9-]*:(read|write)$'), granted_at timestamptz not null default now(), primary key (application_id, scope))` replaces `scopes text[]`; the scope vocabulary is the compile-time F038 catalog in `crates/contracts`, so it stays a checked `text` column per decision section 2 rather than a lookup table, and membership is validated by `ApiApplicationRepository::replace_scopes` against that catalog before insert; `api_application_allowed_ips(application_id uuid not null references api_applications(id) on delete cascade, tenant_id uuid not null, cidr cidr not null, primary key (application_id, cidr))` replaces `allowed_ips cidr[]`; `webhook_events(webhook_id uuid not null references webhooks(id) on delete cascade, tenant_id uuid not null, event_pattern text not null, primary key (webhook_id, event_pattern))` replaces `events text[]`; `webhook_filters(webhook_id uuid not null references webhooks(id) on delete cascade, tenant_id uuid not null, filter_key text not null check (filter_key in ('workspace_id','sheet_id')), filter_value uuid not null, primary key (webhook_id, filter_key, filter_value))` replaces `filters jsonb`, which the dispatcher read by known key; `webhook_delivery_attempts(delivery_id uuid not null references webhook_deliveries(id) on delete cascade, tenant_id uuid not null, attempt_no smallint not null check (attempt_no between 1 and 5), outcome text not null check (outcome in ('succeeded','failed')), status_code smallint null, duration_ms int null, error_code text null check (error_code is null or error_code in ('timeout','connect','tls','dns','private_address','http_status')), error_detail text null, attempted_at timestamptz not null, primary key (delivery_id, attempt_no))` replaces `attempts jsonb`, which the delivery log rendered and `attempt_count` counted. All five children cascade because none can outlive its parent; `webhooks.application_id` and `api_application_scopes.scope` are `on delete restrict` so a bound application or a catalogued scope cannot vanish under a live subscription. The DTOs are unchanged: `CreateApplicationRequest`/`ApplicationResponse` keep `scopes` and `allowed_ips` as JSON arrays, `CreateWebhookRequest`/`WebhookResponse` keep `events` as an array and `filters` as an object, and `DeliveryResponse` keeps `attempts` as an ordered array; `ApiApplicationRepository`, `WebhookRepository`, and `WebhookDeliveryRepository` fan each shape out to rows on write (`delete` of removed rows plus `insert ... on conflict do nothing`) and reassemble it on read inside the aggregate's `UnitOfWork`.
- `jsonb` audit: `webhook_deliveries.payload` stays `jsonb` — it is the frozen outbox event envelope captured at dispatch and re-sent verbatim on replay, never filtered, joined, sorted, or constrained; routing uses `event_name`, `webhook_events`, and `webhook_filters`, and the delivery log filters on `status` and `event_name`. It is the only `jsonb` column in the module: `webhooks.filters` and `webhook_deliveries.attempts` were queried by key and became `webhook_filters` and `webhook_delivery_attempts`.
- Invariants: `api_applications(tenant_id, client_id)` unique; `api_applications(tenant_id, lower(name)) where deleted_at is null` unique; `api_application_scopes` primary key blocks a duplicate grant and its `check` blocks a malformed scope name; `api_application_allowed_ips` primary key blocks a duplicate CIDR and a trigger caps the set at 20 rows per application; `webhook_events` primary key blocks a duplicate pattern and a trigger caps the set at 50 rows per webhook, with at least one row required on an active webhook; `webhook_filters` primary key plus the `filter_key` check blocks a duplicate or unsupported filter; `webhook_deliveries(webhook_id, event_id) where replay_of is null` unique (idempotent dispatch); `webhook_delivery_attempts` primary key makes an attempt append idempotent and its `attempt_no` check caps a delivery at 5 attempts alongside `webhook_deliveries.attempt_count`; `webhooks.consecutive_failures >= 0`.
- Indexes: `webhooks(tenant_id, status) where deleted_at is null`, `webhook_events(event_pattern, webhook_id)` for the dispatcher's pattern lookup and `webhook_events(webhook_id)` for the subscription list, `webhook_filters(webhook_id)` for the per-webhook filter check, `api_application_scopes(scope)` for the reverse "which applications hold this scope" audit and `api_application_scopes(application_id)` for the middleware read, `api_application_allowed_ips(application_id)`, `webhook_deliveries(webhook_id, created_at desc)`, `webhook_deliveries(next_attempt_at) where status = 'failed'`, `webhook_deliveries(tenant_id, status)`, `webhook_delivery_attempts(delivery_id, attempt_no)` served by the primary key for the drawer's attempt list.
- Audit events: `application.create`, `application.update`, `application.delete`, `webhook.create`, `webhook.update`, `webhook.rotate-secret`, `webhook.delete`, `webhook.replay`, `webhook.disabled` with diffs.
- Retention/deletion: deliveries older than 30 days are deleted by the F027 retention sweep under kind `webhook_deliveries` through `WebhookDeliveryRepository::purge_deliveries_before`, taking their `webhook_delivery_attempts` rows with them by cascade; applications and webhooks soft-delete, keeping their scope, CIDR, event, and filter rows so a restore reinstates the same subscription; rollback drops the eight tables, children before parents.

### React/TypeScript

- Routes: `/admin/developer/applications`, `/admin/developer/applications/:appId`, `/admin/developer/webhooks`, `/admin/developer/webhooks/:webhookId`, `/admin/developer/reference` in `apps/web/src/features/public-api/`; components `DeveloperPage`, `ApplicationTable`, `ApplicationForm`, `TokenRevealDialog`, `WebhookTable`, `WebhookForm`, `SecretRevealDialog`, `DeliveryLog`, `DeliveryDrawer`, `AttemptTable`, `ReferencePage`.
- State: TanStack Query keys `['applications']`, `['application', id]`, `['webhooks']`, `['webhook', id]`, `['deliveries', webhookId, filter, cursor]` (polls every 10 s while any delivery is `pending` or `failed`), `['openapi']`.
- API client: generated `PublicApi` with `listApplications`, `createApplication`, `updateApplication`, `deleteApplication`, `listWebhooks`, `createWebhook`, `updateWebhook`, `deleteWebhook`, `listDeliveries`, `replayDelivery`, `getOpenApi`.
- Telemetry: `application_created`, `webhook_created`, `webhook_secret_rotated`, `delivery_replayed`, `webhook_reenabled`, `reference_opened` with `application_id` or `webhook_id`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F028-01 through FR-F028-15 in `testing/features/F028/requirements/cases.md`
- [ ] Failure/edge-case tests: expired cursor, unknown filter field, private webhook URL, DNS rebinding to a private address at attempt time, timeout at 10 s, 10 consecutive exhausted deliveries, replay of a 31-day-old delivery, secret rotation grace
- [ ] Permission-negative and tenant-isolation tests: member cannot create applications or webhooks, foreign-tenant IDs return `not_found`, suspended application tokens rejected, delivery payload excludes fields outside scopes
- [ ] Rust unit tests: `crates/contracts/src/public-api/` filter parser, signed cursor, OpenAPI builder; `crates/domain/src/public-api/` signature, retry schedule, event matching against repository-supplied pattern and filter rows
- [ ] API contract/integration tests: every route above with success and each error code; generated document validated against the OpenAPI 3.1 schema
- [ ] Database migration/constraint tests: application name and `client_id` uniqueness, idempotent delivery key, attempt cap on `webhook_delivery_attempts`, duplicate scope, CIDR, event pattern, and filter rejection, the 20-CIDR and 50-pattern caps, unsupported `filter_key` rejection, cascade of children on parent delete, rollback ordering
- [ ] React component tests: `ApplicationForm`, `WebhookForm`, `SecretRevealDialog`, `DeliveryLog`, `DeliveryDrawer` states
- [ ] Browser E2E tests: create application and webhook, receive signed delivery on a harness receiver, failures disable, re-enable and replay
- [ ] Accessibility tests: axe on developer routes and drawers
- [ ] Performance/load tests: 1,000 deliveries per minute, dispatch latency p95 under 5 s, OpenAPI under 50 ms

### Fast fanout configuration

- Test harness path: `testing/features/F028/`
- Feature flag: `F028_FEATURE`
- Fixture/seed factory: `testing/fixtures/public_api.rs` builds tenant A and B, tenant-admin, member, one application with two scopes, one webhook per tenant, 120 seeded deliveries in mixed states with their attempt rows — every fixture write going through `crates/persistence/src/public-api/` repositories — and a harness HTTP receiver that records requests and can return 200, 500, or hang
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
- Migration adds `api_applications`, `api_application_scopes`, `api_application_allowed_ips`, `webhooks`, `webhook_events`, `webhook_filters`, `webhook_deliveries`, and `webhook_delivery_attempts`; rollback drops them. Feature is off by default behind `F028_FEATURE`.
