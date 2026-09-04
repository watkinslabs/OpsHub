---
id: F061
type: feature
status: planned
priority: P1
owner: platform
estimate: 3
target_milestone: M7
parent_epic: E008
depends_on: [F008, F037]
blocks: []
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/update-requests/**, services/api/src/update-requests/**, services/worker/src/update-requests/**, apps/web/src/features/update-requests/**, services/api/migrations/*_update-requests_*.sql, testing/features/F061/**]
feature_flag: F061_FEATURE
flag_default: off
branch: f061-update-requests
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 6
- Capability contract: `docs/capability-contracts.md` row F061

# F061 — Update requests

## 1. Identity and dates

- Branch: `f061-update-requests`
- Capability area: collaboration intake (spec 5.5 update requests bullet: "Update requests target selected fields or rows, record requester/recipient/due date/status, send configurable reminders, and preserve the response audit trail")
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 6; `docs/capability-contracts.md` row F061
- Module slug: `update-requests`; aggregate `update-request`

## 2. Requirement specification

### Problem and user outcome

A sheet owner chasing status is the most common manual loop in OpsHub: they email three people, paste the current values, retype the replies, and lose the trail of who said what. Some of those people — a subcontractor, a client contact, a supplier — have no OpsHub account and must never be given one just to type two dates. F014 already proves that an unauthenticated person can write into a sheet safely through a hashed token, and F037 already owns delivery; this feature adds the missing shape: a request that targets *existing rows and existing cells* instead of creating new ones, addressed to named people, with reminders, expiry, revocation, and per-recipient attribution of every cell that changed.

As a sheet owner, I want to ask named people — account or not — to fill in specific cells on specific rows through a link that expires, reminds them on a schedule I choose, and that I can revoke, so that the sheet stays current without me retyping replies and without widening anyone's access to the sheet.

### Functional requirements

- **FR-F061-01:** `POST /api/v1/update-requests` with `{ sheet_id, title (1–200), message (≤ 2,000), row_ids (1–200 unique), column_ids (1–20 unique), recipients (1–20, each { user_id } or { email, display_name? }), due_at, expires_at?, allow_partial (default true), reminder_policy { cadence: none|daily|every_3_days|weekly, max_reminders 0–5, stop_on_response (default true) } }` returns `201` with a UUIDv7 `id`, `status: open`, `version: 1`, and one `recipient_id` per recipient. The actor needs the `requester` role on the sheet plus F003 `cell.write` on every `column_id`; a column the actor may not write, a row outside `sheet_id`, or a read-only/system column (`created_at`, formula columns from F035) returns `400 invalid` with `field_errors.column_ids`.
- **FR-F061-02:** Each recipient gets its own link token: 32 CSPRNG bytes, URL-safe base64, delivered once inside the link `/public/update-requests/{token}`, stored only as `update_request_recipients.token_hash` (SHA-256, unique, constant-time compare). A token is bound to exactly one recipient of one request, is never a session credential, grants no `/api/v1` access, and stops working at `expires_at` (default `due_at + 7 days`, hard maximum 90 days after creation; a longer `expires_at` returns `400 invalid`).
- **FR-F061-03:** Creation materialises an immutable scope snapshot: the `(row_id, column_id)` pairs, each mapped to an opaque `row_key` and `field_key` (`[a-z0-9]{12}`, per request) stored in `update_requests.scope_keys`. Public responses address cells only by those keys and never contain `sheet_id`, `workspace_id`, `tenant_id`, `row_id`, `column_id`, or any user id. Rows or columns added to the sheet after creation are never part of the scope; a row deleted after creation drops out of the scope and is reported as `removed_count`.
- **FR-F061-04:** `GET /public/update-requests/{token}` is unauthenticated, resolves the tenant from the token hash, and returns `{ title, message, requester_display_name, due_at, expires_at, status, allow_partial, removed_count, rows: [{ row_key, label, row_version, fields: [{ field_key, label, type, options?, required, current_value, validation }] }] }`, where `label` is the sheet's primary column value only. Unknown, revoked, or expired tokens return `404 not_found` with no tenant detail; responses carry `Referrer-Policy: no-referrer`, `X-Robots-Tag: noindex`, and `Cache-Control: no-store`; the route is limited to 120 requests per hour per token and client IP.
- **FR-F061-05:** `POST /public/update-requests/{token}/responses` is unauthenticated, requires `Idempotency-Key`, and takes `{ values: { "<row_key>": { "<field_key>": value } }, row_versions: { "<row_key>": n }, comment (≤ 2,000), submit: bool }`. A key outside the scope snapshot returns `404 not_found`; a value failing the F007 column validator returns `400 invalid` with `field_errors.<row_key>.<field_key>`; the route is limited to 30 submissions per hour per token and client IP and 300 per day per token, and excess returns `429 rate_limited` with `Retry-After`.
- **FR-F061-06:** An accepted submission first inserts an immutable `update_request_responses` row (`payload`, `comment`, `ip_hash` salted SHA-256, `user_agent`, `received_at`, `status: received`) and then applies the cells through the F008 `apply_cell_edits` path in the same transaction with `source: update_request` and `source_id: recipient_id`, publishing `cell.updated.v1` per edited cell and `update-request.responded.v1 { request_id, recipient_id, rows_updated, cells_updated }`; the response row moves to `applied` with `cells_applied` and `applied_at`.
- **FR-F061-07:** Partial work is supported two ways: `submit: false` stores the payload as a `draft` response that writes no cells and can be reloaded and replaced with the same token for 7 days (`draft_expires_at`), and `submit: true` covering a subset of the scope is accepted when `allow_partial` is true, marks the recipient `partial`, and leaves the request `open`. When `allow_partial` is false, a submission missing any field of the scope returns `400 invalid` with reason `incomplete` and writes nothing.
- **FR-F061-08:** Optimistic concurrency reuses F008 row versions: the submitted `row_versions.<row_key>` must equal the row's current `version`; a mismatch returns `409 conflict` with `{ row_key, current_version, current_values }` for every stale row, applies no cell of that submission, and records the response as `rejected` with reason `stale_row`.
- **FR-F061-09:** A recipient becomes `completed` when every field of the scope has a submitted value from that recipient; the request becomes `completed` when every `(row_key, field_key)` pair has at least one submitted value from any recipient, and `expired` when `expires_at` passes while still `open`. Reaching `completed` or `expired` cancels that recipient's pending reminders and makes further submissions return `409 conflict` with reason `closed`.
- **FR-F061-10:** The worker job `update-requests.remind` runs every minute, claims due `reminder_schedules` rows with `for update skip locked`, and for each sends through the F037 `NotificationService::create` with category `update_request` and `dedupe_key = update-request:{recipient_id}:{sequence}`, publishes `update-request.reminded.v1 { request_id, recipient_id, sequence, manual: false }`, sets `state: sent` with `sent_at` and `notification_id`, and inserts the next `sequence` at `next_run_at` from the cadence. Scheduling stops at `max_reminders`, at `expires_at`, and — when `stop_on_response` is true — at the recipient's first submitted response, which sets remaining rows to `state: cancelled`.
- **FR-F061-11:** `POST /api/v1/update-requests/{id}/remind` with `{ recipient_ids? }` by the requester sends immediately to `pending`, `opened`, or `partial` recipients as `kind: manual`, returns `{ sent: [recipient_id], skipped: [{ recipient_id, reason }] }` for `completed`, `revoked`, or `expired` recipients, requires `Idempotency-Key`, and is limited to 3 manual reminders per recipient per 24 hours (`429 rate_limited`). The link is never regenerated by a reminder; the existing token is reused.
- **FR-F061-12:** `POST /api/v1/update-requests/{id}/cancel` with `{ reason? (≤ 500) }` sets `status: cancelled`, `cancelled_at`, `cancelled_by`, sets `revoked_at` and nulls `token_hash` on every recipient, sets every `pending` `reminder_schedules` row to `cancelled`, and publishes `update-request.cancelled.v1`. Every public route then returns `404 not_found`; already-applied responses and their cell edits are kept; a repeat cancel returns `200` unchanged; cancelling a `completed` request returns `409 conflict`.
- **FR-F061-13:** `GET /api/v1/update-requests` pages by cursor (`limit` ≤ 100) with filters `status`, `sheet_id`, `requested_by`, `due_before`, and `GET /api/v1/update-requests/{id}` returns the request with `recipients[] { recipient_id, display_name, email_masked, status, opened_at, last_reminded_at, reminder_count, completed_at }` and `changes[] { row_key, field_key, column_label, old_value, new_value, recipient_id, applied_at }`. The requester and any actor with F003 `sheet.admin` on the sheet may read; anyone else gets `403 denied`; another tenant's id gets `404 not_found`; `email_masked` shows `a***@example.com` to non-owners.
- **FR-F061-14:** Every mutation writes an F003 `audit_events` row through `record_audit` in the same transaction — `update-request.create`, `update-request.remind`, `update-request.cancel`, `update-request.respond` — and requires `Idempotency-Key`. A recipient response records `actor_kind: 'system'`, `actor_id: null`, and `after.recipient = { recipient_id, email, display_name }`, and shares its `correlation_id` with the `cell_history` rows it produced, so `GET /api/v1/audit-events?correlation_id=` returns the request event and every resulting cell change together.
- **FR-F061-15:** The grid offers `Request an update` on a row selection, opening a dialog for columns, recipients, message, due date, and reminder cadence; `/w/{workspace_id}/update-requests` lists requests with status, due date, and completion count; the detail drawer shows per-recipient status with `Remind` and `Cancel request`; the recipient page is a mobile-first single-column form per row with a save-draft action, a submit summary, and distinct terminal screens for expired, cancelled, and already-completed links.

### Non-functional requirements

- **NFR-F061-01 Performance:** `GET /public/update-requests/{token}` p95 under 300 ms for a 200-row × 20-column scope; submission with 50 cells p95 under 900 ms including the F008 write; `GET /api/v1/update-requests` p95 under 500 ms with 10,000 requests in the tenant; the reminder claim query over 100,000 `reminder_schedules` rows completes under 2 s using the partial index on `(state, next_run_at)`.
- **NFR-F061-02 Security/privacy:** tokens are 256-bit CSPRNG values stored only as SHA-256, compared in constant time, absent from logs, metrics, exports, and API responses after creation; the scope snapshot is the entire authority of a token, so any key outside it returns `not_found`; the requester's `cell.write` permission is re-checked at apply time, and a revoked requester permission rejects the response with reason `requester_denied`; only a salted `ip_hash` is stored; cross-tenant tokens and ids return `not_found`.
- **NFR-F061-03 Accessibility:** the request dialog, request list, detail drawer, and public recipient form pass axe with zero serious or critical violations; every field has a visible label with errors wired through `aria-describedby`; draft-save and submit results are announced through a polite live region; the recipient form is completable by keyboard alone and usable at 320 px; status is never conveyed by colour alone.
- **NFR-F061-04 Reliability/observability:** the reminder job is idempotent per `(recipient_id, sequence)` and resumable after restart; a cell-write failure leaves the response `received` with `error_code` and is retried under the same `Idempotency-Key` without a second notification; metrics `update_requests_sent_total`, `update_request_reminders_total{kind}`, `update_request_responses_total{outcome}`, `update_request_cells_written_total`, `update_request_token_rejections_total{reason}`; spans carry `tenant_id`, `request_id`, `recipient_id`, `correlation_id`.

### Scope

Included: request creation over an existing sheet scope, per-recipient hashed link tokens with expiry and revocation, opaque row/field keys, public schema and submission routes, F007 validation, F008 cell application with row-version conflict detection, drafts and partial submission, recipient and request completion state, scheduled and manual reminders through F037, cancel, request list and detail with per-cell attribution, F003 audit for every mutation, requester UI and public recipient form.

Excluded: new-row intake and form building (F014 owns forms, tokens, and CAPTCHA), notification channels, templates, quiet hours, and digests (F037), guest accounts and durable share grants (F036), approvals of the submitted values (F020), row and cell editing rules themselves (F007, F008), attachments on responses (F017), cross-tenant or portfolio-level chasing (F031).

## 3. UX specification

- Entry points: grid row selection action `Request an update`; sheet header menu `Update requests`; routes `/w/:workspaceId/update-requests`, `/w/:workspaceId/update-requests/:requestId`; recipient link `/public/update-requests/:token`.
- Primary flow: Maya selects 12 rows in `Site works`, picks columns `Status`, `Forecast finish`, and `Blocker note`, adds two teammates and `paul@contractor.example`, sets the due date to Friday and cadence `every_3_days`, and sends. Paul opens the link on a phone, sees 12 cards with the current values, fills 9, taps `Save draft`, returns the next day, completes the rest, and submits; Maya's detail drawer shows `Paul — completed`, the 12 changed cells with old and new values, and the request marked `completed`.
- Loading: skeleton row cards on the public page and a skeleton table in the list; Empty: `No update requests yet` with the grid action explained; Error: banner with `correlation_id` and retry; Success: toast `Request sent to 3 people`, public submit confirmation with the count of updated cells; Stale/conflict: per-row `Changed since you opened` panel showing the current value and a `Use current` control; Offline: public page keeps the draft in `localStorage` under `update-request-draft:{token}` and shows an offline badge.
- Permission-denied: a member without `sheet.admin` who opens another person's request sees the denied state; the grid action is hidden without `requester`; expired, cancelled, and completed links render distinct terminal screens that name the requester and offer no data.
- Responsive: recipient form is single-column under 640 px with a sticky submit bar showing `9 of 12 filled`; the requester dialog becomes a full-screen sheet under 640 px; the detail drawer stacks recipients above changes under 768 px.
- Keyboard: the scope picker moves with arrow keys and toggles with `Space`; the recipient form is a native `<form>` with per-row `<fieldset>`/`<legend>`; `Ctrl+Enter` submits; `Escape` closes the dialog and returns focus to the grid action; motion respects `prefers-reduced-motion`.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062); Lucide icons `MailQuestion`, `CalendarClock`, `BellRing`, `Ban`, `CheckCheck`, `Link2Off`; spacing, colour, and elevation from `apps/web/src/design/tokens.css`.

## 4. Technical specification

### Rust backend

- Domain entities in `crates/domain/src/update-requests/`: `UpdateRequest { id, tenant_id, sheet_id, workspace_id, requested_by, title, message, status: RequestStatus(Open|Completed|Cancelled|Expired), allow_partial, due_at, expires_at, row_ids, column_ids, scope_keys: ScopeKeys, reminder_policy: ReminderPolicy, cancelled_at, cancelled_by, cancel_reason, version, audit fields }`, `Recipient { id, request_id, user_id, email, display_name, token_hash, status: RecipientStatus(Pending|Opened|Partial|Completed|Revoked|Expired), opened_at, last_reminded_at, reminder_count, completed_at, revoked_at }`, `Response { id, request_id, recipient_id, status: ResponseStatus(Draft|Received|Applied|Rejected), reason, payload, comment, ip_hash, user_agent, idempotency_key, cells_applied, error_code, received_at, applied_at, draft_expires_at }`, `ReminderSchedule { id, request_id, recipient_id, sequence, kind: Scheduled|Manual, state: Pending|Sent|Cancelled|Skipped, next_run_at, sent_at, attempt, notification_id }`, `ScopeKeys { rows: BTreeMap<RowKey, RowId>, fields: BTreeMap<FieldKey, ColumnId> }`.
- Use cases: `create_request`, `list_requests`, `get_request`, `cancel_request`, `remind_now`, `load_public_scope`, `save_draft`, `submit_response`, `apply_response`, `evaluate_completion`, `schedule_reminders`, `run_due_reminders`, `expire_requests`.
- API endpoints (`services/api/src/update-requests/`): `GET /api/v1/update-requests`, `POST /api/v1/update-requests`, `GET /api/v1/update-requests/{id}`, `POST /api/v1/update-requests/{id}/cancel`, `POST /api/v1/update-requests/{id}/remind`, `GET /public/update-requests/{token}`, `POST /public/update-requests/{token}/responses`. DTOs: `CreateUpdateRequest`, `UpdateRequestResponse`, `Page<UpdateRequestSummary>`, `CancelRequest { reason? }`, `RemindRequest { recipient_ids? }`, `RemindResponse { sent, skipped }`, `PublicScopeResponse`, `SubmitResponseRequest`, `SubmitResponseResult { response_id, cells_updated, recipient_status, request_status }`.
- Worker jobs (`services/worker/src/update-requests/`): `remind` (every minute, claims due schedules), `expire` (every 5 minutes, closes requests past `expires_at` and revokes their tokens), `purge_drafts` (nightly, deletes `draft` responses past `draft_expires_at`).
- Events: `update-request.sent.v1`, `update-request.reminded.v1`, `update-request.responded.v1`, `update-request.cancelled.v1` through the outbox with the standard envelope; F037 maps `update-request.sent.v1` and `update-request.reminded.v1` to category `update_request` per FR-F037-01.
- Authorization: create, list, detail, remind, and cancel require `requester` on the sheet, plus `cell.write` on every scoped column at creation and again at apply time; `sheet.admin` may read any request on the sheet; public routes carry no session and derive tenant, request, and recipient from `token_hash` alone.
- Validation: `title` 1–200, `message` ≤ 2,000, `comment` ≤ 2,000, `row_ids` 1–200 and all in `sheet_id`, `column_ids` 1–20 and all writable, `recipients` 1–20 with RFC 5322 email syntax or a tenant `user_id`, `due_at` in the future, `expires_at` ≤ creation + 90 days, cell values validated by the F007 column validator, payload capped at 1 MB.
- Error mapping: `UpdateRequestError::ColumnNotWritable | ::ScopeInvalid | ::ExpiryTooFar → 400 invalid`, `::Incomplete → 400 invalid (reason incomplete)`, `::UnknownToken | ::TokenRevoked | ::TokenExpired | ::OutOfScope → 404 not_found`, `::StaleRow → 409 conflict`, `::Closed | ::AlreadyCompleted → 409 conflict`, `::RemindRateLimited | ::SubmitRateLimited → 429 rate_limited`, `::RequesterDenied → 400 invalid`, `AuthzError::Denied → 403 denied`.

### PostgreSQL/SQLx

- Migration `*_update-requests_*.sql` creates `update_requests(id uuid pk, tenant_id uuid not null, sheet_id uuid not null, workspace_id uuid not null, requested_by uuid not null, title text not null, message text, status text not null default 'open', allow_partial bool not null default true, due_at timestamptz not null, expires_at timestamptz not null, row_ids uuid[] not null, column_ids uuid[] not null, scope_keys jsonb not null, reminder_policy jsonb not null, cancelled_at timestamptz, cancelled_by uuid, cancel_reason text, version bigint not null default 1, audit fields, deleted_at)`, `update_request_recipients(id uuid pk, tenant_id, request_id uuid not null references update_requests(id) on delete cascade, user_id uuid, email text, display_name text, token_hash bytea, status text not null default 'pending', opened_at timestamptz, last_reminded_at timestamptz, reminder_count smallint not null default 0, completed_at timestamptz, revoked_at timestamptz, created_at)`, `update_request_responses(id uuid pk, tenant_id, request_id, recipient_id uuid not null references update_request_recipients(id) on delete cascade, status text not null, reason text, payload jsonb not null, comment text, ip_hash bytea, user_agent text, idempotency_key text not null, cells_applied int not null default 0, error_code text, received_at timestamptz not null, applied_at timestamptz, draft_expires_at timestamptz)`, `reminder_schedules(id uuid pk, tenant_id, request_id, recipient_id, sequence smallint not null, kind text not null default 'scheduled', state text not null default 'pending', next_run_at timestamptz not null, sent_at timestamptz, attempt smallint not null default 0, notification_id uuid, created_at)`.
- Invariants: `check (status in ('open','completed','cancelled','expired'))`; `check (array_length(row_ids,1) between 1 and 200)`; `check (array_length(column_ids,1) between 1 and 20)`; `check (expires_at > due_at)`; recipients `check (user_id is not null or email is not null)`; unique `update_request_recipients_token_idx on (token_hash) where token_hash is not null`; unique `update_request_recipients_party_idx on (request_id, coalesce(user_id::text, lower(email)))`; unique `update_request_responses_idem_idx on (tenant_id, request_id, idempotency_key)`; unique `reminder_schedules_seq_idx on (recipient_id, sequence)`; trigger `update_request_responses_append_only` allowing only `status` transitions `received → applied|rejected` and `draft → received` plus `cells_applied`, `applied_at`, `error_code`, `reason`.
- Indexes: `update_requests(tenant_id, status, due_at)`, `update_requests(tenant_id, sheet_id) where deleted_at is null`, `update_requests(tenant_id, requested_by, created_at desc)`, `update_request_recipients(request_id, status)`, `update_request_responses(request_id, received_at desc)`, `reminder_schedules(state, next_run_at) where state = 'pending'`, `reminder_schedules(recipient_id)`.
- Audit events: `update-request.create`, `update-request.remind`, `update-request.cancel`, `update-request.respond` written through F003 `record_audit`; response rows are referenced by `response_id` rather than copied, and `token_hash` is never placed in `before`, `after`, or `diff`.
- Retention/deletion: `draft` responses purged after `draft_expires_at`; cancelled and completed requests soft-delete after 180 days under the F027 sweep with their recipients and responses cascading; `audit_events` rows outlive the request; rollback drops the four tables, their indexes, and the append-only trigger.

### React/TypeScript

- Routes: `/w/:workspaceId/update-requests`, `/w/:workspaceId/update-requests/:requestId`, `/public/update-requests/:token` in `apps/web/src/features/update-requests/`; components `RequestUpdateDialog`, `ScopePicker`, `RecipientPicker`, `ReminderPolicyEditor`, `UpdateRequestList`, `UpdateRequestDetail`, `RecipientStatusTable`, `ChangeLogTable`, `PublicRequestPage`, `PublicRowCard`, `DraftBar`, `ConflictPanel`, `TerminalNotice`.
- State: TanStack Query keys `['update-requests', { status, sheetId, cursor }]`, `['update-request', requestId]`, `['public-update-request', token]`; cancel and remind invalidate both request keys; the public page keeps its draft in `localStorage` under `update-request-draft:{token}` and posts it with `submit: false` when online.
- API client: generated `UpdateRequestsApi` with `listRequests`, `createRequest`, `getRequest`, `cancelRequest`, `remind`, and `PublicUpdateRequestsApi` with `getScope`, `submitResponse`; the public client sends no auth header and no tenant hint.
- Telemetry: `update_request_created`, `update_request_opened_public`, `update_request_draft_saved`, `update_request_submitted`, `update_request_conflict_shown`, `update_request_reminded`, `update_request_cancelled` with `request_id`, `recipient_count`, `cadence`, and `cells_updated`; no cell values are sent.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F061-01 through FR-F061-15 in `testing/features/F061/requirements/cases.md`
- [ ] Failure/edge-case tests: read-only column in the scope, expiry beyond 90 days, deleted row dropped from the scope, key outside the scope, stale row version, `allow_partial: false` with a gap, submission after completion, cancel then open link, expired link, draft replaced then submitted
- [ ] Permission-negative and tenant-isolation tests: member without `requester` cannot create, non-owner without `sheet.admin` cannot read the request, requester's `cell.write` revoked after send rejects the apply, another tenant's token and request id return `not_found`
- [ ] Rust unit tests: `crates/domain/src/update-requests/` scope-key mapping, completion evaluation, cadence arithmetic across DST, reminder stop conditions, email masking
- [ ] API contract/integration tests: every route above with success and each error code, including the two public routes without a session
- [ ] Database migration/constraint tests: token-hash uniqueness, recipient uniqueness per party, idempotency uniqueness, reminder sequence uniqueness, append-only trigger, cascade delete, rollback
- [ ] React component tests: `RequestUpdateDialog`, `PublicRequestPage`, `ConflictPanel`, `RecipientStatusTable`, `TerminalNotice` states
- [ ] Browser E2E tests: send to an external recipient, complete in two visits with a draft, watch a reminder fire, cancel and confirm the link dies
- [ ] Accessibility tests: axe on the dialog, list, drawer, and public form; keyboard-only completion; live-region announcements
- [ ] Performance/load tests: 200×20 scope read, 50-cell submission, 10,000-request list, 100,000-row reminder claim

### Fast fanout configuration

- Test harness path: `testing/features/F061/`
- Feature flag: `F061_FEATURE`
- Fixture/seed factory: `testing/fixtures/update_requests.rs` builds tenant A and B, a sheet `Site works` with 12 typed columns (text, date, single-select, contact, formula) and 250 rows, a requester, a sheet-admin, a plain member, two internal recipients, one external recipient `paul@contractor.example`, an open request with a 12-row × 3-column scope, a completed request, and a cancelled request
- Deterministic test data: fixed UUIDv7 seeds, fixed token seed producing stable hashes, fixed clock `2026-09-03T00:00:00Z`, UTC with an `Australia/Sydney` DST case for cadence tests
- Mock/stub contracts: F037 `NotificationService` recorded in memory returning fixed `notification_id`s; outbox recorded in memory; F008 `apply_cell_edits` exercised for real against the seeded sheet; rate-limit buckets namespaced per test
- Parallel isolation: one schema per test worker, tenant id per test, token namespace per worker
- Targeted command: `cargo xtask test-feature F061`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F061/`

## 6. Acceptance criteria

```gherkin
Feature: Update requests

Scenario: External recipient completes a scoped request in two visits
  Given a requester sends an update request for 12 rows and 3 columns to paul@contractor.example
  When Paul opens the link, saves a draft with 9 fields, returns and submits all 36 fields
  Then the draft writes no cells, the submission writes 36 cells through the grid path
  And update-request.responded.v1 is published, the recipient is completed, and the request is completed

Scenario: Reminders stop after a response and never double-send
  Given an open request with cadence every_3_days, max_reminders 3, and stop_on_response true
  When the reminder job runs twice for the same due schedule row and the recipient then responds
  Then only one notification exists for that sequence and the remaining schedule rows are cancelled

Scenario: Cancelling revokes every link immediately
  Given an open request with three recipients who have not responded
  When the requester cancels it with reason "handled in the meeting"
  Then update-request.cancelled.v1 is published, pending reminders are cancelled
  And GET /public/update-requests/{token} returns 404 not_found for all three tokens

Scenario: A token grants nothing beyond its scope
  Given a token for a request scoped to rows 1-12 and columns Status and Forecast finish
  When the recipient posts a value for a field_key from another request or an unscoped column
  Then the response is 404 not_found and no cell is written

Scenario: A row changed since the recipient opened the link
  Given the recipient loaded row_version 4 and the requester has since edited that row to version 5
  When the recipient submits values for that row
  Then the response is 409 conflict with the current value, the response row is rejected with reason stale_row
  And no cell of that submission is written
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F008 (`apply_cell_edits`, row versions, `cell_history`, `cell.updated.v1`); F037 (`NotificationService::create`, category `update_request`, delivery log); F014 token-hash pattern and public-route conventions; F007 column validators; F003 `record_audit` and permission checks; F038 `rate_limit_buckets`; decisions sections 2, 3, 4, 6; contracts row F061
- Blocks: none
- Conflicts with: none (disjoint owned paths)
- External dependencies: none directly; email reaches recipients through the F037 SMTP adapter (Mailpit in tests)
- Risks and mitigations: a leaked link is a real access path, so tokens are per recipient, hashed, expiring, revocable, scope-limited, and rate-limited, and the scope snapshot — not the sheet ACL — bounds what the token can read or write; a requester whose own access is later removed could otherwise write by proxy, so `cell.write` is re-checked at apply time; reminder storms after a worker restart are prevented by the `(recipient_id, sequence)` unique key plus the F037 `dedupe_key`; a scope pointing at rows that are later deleted degrades to `removed_count` rather than an error.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F008 and F037 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F061/`
- [ ] Migration file name and owned paths claimed
- [ ] Fixture factory and recorded notification service available in `testing/fixtures/update_requests.rs`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for send, reminder, response, and cancel, with a shared `correlation_id` proven against `cell_history`
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F061_FEATURE`, run the down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Sheet owners can ask named people — including people without an OpsHub account — to update specific cells on specific rows through a per-recipient link that expires, reminds on a chosen cadence, and can be revoked; every applied value is attributed to its recipient in the audit trail and the cell history.
- Migration adds `update_requests`, `update_request_recipients`, `update_request_responses`, and `reminder_schedules`; rollback drops them. Feature is off by default behind `F061_FEATURE`.
