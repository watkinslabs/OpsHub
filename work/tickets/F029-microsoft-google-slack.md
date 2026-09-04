---
id: F029
type: feature
status: planned
priority: P1
owner: platform
estimate: 8
target_milestone: M5
parent_epic: E006
depends_on: [F028, F037]
blocks: [F030]
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/integrations/**, crates/persistence/src/integrations/**, services/api/src/integrations/**, services/worker/src/integrations/**, apps/web/src/features/integrations/**, services/api/migrations/*_integrations_*.sql, testing/features/F029/**]
feature_flag: F029_FEATURE
flag_default: off
branch: f029-microsoft-google-slack
started_at: null
finished_at: null
---

# F029 — Microsoft/Google/Slack

## 1. Identity and dates

- Branch: `f029-microsoft-google-slack`
- Capability area: integrations and APIs (spec 5.9 INT-02, INT-03; section 10 connector decision)
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 7; `docs/capability-contracts.md` row F029
- Aggregate: `integration-connection`
- Module slug: `integrations`

## 2. Requirement specification

### Problem and user outcome

Teams live in Microsoft 365, Google Workspace, and Slack. They want OpsHub notifications where they already look, and they want dated work to show up on their calendars without copying it by hand. Doing this requires OAuth tokens that are stored safely, refreshed silently, and revocable, plus provider adapters that behave the same way so failures are visible in one place.

As an integration administrator, I want to connect Microsoft 365, Google Workspace, and Slack with OAuth, route notifications to Teams, Google Chat, or Slack, and sync sheet dates with Outlook or Google Calendar with a clear conflict policy, so that people see OpsHub work in their own tools and I can trust and audit the connection.

### Functional requirements

- **FR-F029-01:** `GET /api/v1/integrations/providers` returns the three providers `microsoft365`, `google`, `slack` with `display_name`, `capabilities` (`notify`, `calendar_sync`, `chat_sync`), required `scopes` per capability, and `enabled` (false when the deployment lacks client credentials for that provider); capabilities and their scopes are read from the seeded `integration_provider_capabilities` and `integration_provider_capability_scopes` rows, and the response reassembles them into the `capabilities` array and per-capability `scopes` arrays.
- **FR-F029-02:** `POST /api/v1/integrations/connections` with `{ provider, capabilities: [..], display_name? }` by an `integration-admin` returns `202` with `connection_id`, `status: pending`, and an `authorize_url` containing a PKCE `code_challenge` (S256) and a `state` bound to tenant, actor, and connection for 10 minutes; each requested capability is stored as one `integration_connection_capabilities` row and must exist in `integration_provider_capabilities` for that provider; a provider with `enabled: false` returns `400 invalid`.
- **FR-F029-03:** `GET /auth/integrations/{provider}/callback?code=&state=` validates `state` (unknown, expired, or reused returns `400 invalid` and an audit event), exchanges the code with the provider, stores access and refresh tokens envelope-encrypted, writes one `integration_connection_scopes` row per scope with `state = 'granted'`, `owner_id`, `external_account_id`, `last_success_at`, sets `status: active`, publishes `integration.connected.v1`, and redirects to `/admin/integrations?connected={id}`; when the granted set is narrower than requested, every unmet scope is written as an `integration_connection_scopes` row with `state = 'missing'` and `status` becomes `limited`.
- **FR-F029-04:** Refresh tokens are encrypted with AES-256-GCM using a per-tenant data key wrapped by the deployment secret-manager key; `oauth_tokens` stores `key_id`, `nonce`, ciphertexts, and `expires_at`, and the scopes the provider returned with the token set are stored as `oauth_token_scopes` rows; plaintext tokens never appear in logs, audit events, API responses, or exports (F027 redaction list).
- **FR-F029-05:** A worker job `integrations.refresh` refreshes access tokens 5 minutes before `expires_at`; `POST /api/v1/integrations/connections/{id}/refresh` forces one refresh; a failed refresh publishes `integration.refresh-failed.v1` with the provider error class and upserts the connection's `integration_connection_errors` row (`error_class`, `provider_status_code`, `message`, `occurred_at`), and three consecutive failures set `status: needs_reauth`, notify the owner through F037, and pause syncs using the connection; a successful refresh deletes that row.
- **FR-F029-06:** `DELETE /api/v1/integrations/connections/{id}` calls the provider revocation endpoint when the provider supports it, deletes the `oauth_tokens` row and its cascaded `oauth_token_scopes` rows, sets `status: revoked` with `revoked_at` and `revoked_by`, publishes `integration.revoked.v1`, and pauses dependent syncs; a `not_found` is returned for foreign tenants.
- **FR-F029-07:** `GET /api/v1/integrations/connections` lists connections with `provider`, `capabilities`, `scopes`, `missing_scopes`, `owner`, `status`, `last_success_at`, `last_error`, `external_account_label`, cursor pagination, and `provider` and `status` filters; the response arrays are assembled by `IntegrationConnectionRepository` from `integration_connection_capabilities` and `integration_connection_scopes` (split by `state`) in one batched read per page, and `last_error` is the connection's `integration_connection_errors` row or `null`.
- **FR-F029-08:** A connection with `notify` capability registers a F037 notification channel: Microsoft 365 posts Adaptive Cards to a Teams channel or chat, Google posts cards to a Google Chat space, Slack posts Block Kit messages to a channel or direct message; each channel maps OpsHub notification kinds (`mention`, `assignment`, `approval`, `due_soon`, `workflow_failed`) to a message template with a deep link back to the record.
- **FR-F029-09:** `POST /api/v1/integrations/connections/{id}/notify-test` with `{ target }` sends a test message through the adapter and returns `{ delivered: bool, provider_message_id?, error? }` within 10 s, publishing `integration.notified.v1` with `test: true`; a rate limit of 10 tests per connection per hour applies.
- **FR-F029-10:** A connection with `calendar_sync` capability can be bound to a sheet with a start date column, an optional end date column, a title column, and an optional assignee column; the worker job `integrations.calendar_sync` creates, updates, and deletes provider calendar events for rows (Outlook via Microsoft Graph, Google Calendar via the Calendar API) and applies provider-side changes to rows, using a per-binding cursor (Graph delta token, Google `syncToken`).
- **FR-F029-11:** Each calendar binding has a `conflict_policy` in `opshub_wins`, `provider_wins`, `newest_wins` (default), or `manual`; when both sides changed since the last cursor, the policy decides the winner and writes an `integration_events` row of `kind: conflict` plus one `integration_conflicts` row per contested field holding `field`, `opshub_value`, `provider_value`, both `updated_at` timestamps, and `winner` (`opshub`, `provider`, or `none`); `manual` leaves the row untouched, sets `calendar_event_links.review_state = 'needs_review'` with `winner = 'none'`, and surfaces it in the connection page until either side is edited again.
- **FR-F029-12:** Slack and Teams thread replies to an OpsHub notification message are imported as F016 comments on the referenced record (`chat_sync` capability) with the author mapped by email, or attributed to the connection owner with the external display name when no user matches; imported comments carry `source: provider` and cannot be edited in OpsHub.
- **FR-F029-13:** Every provider call goes through a typed adapter (`Microsoft365Adapter`, `GoogleAdapter`, `SlackAdapter`) implementing `NotifyAdapter`, `CalendarAdapter`, or `ChatAdapter`, each with a 10 s timeout, provider rate-limit handling (`429` and `Retry-After` honored), bounded retries (3 with exponential backoff), and an `integration_events` row per call outcome (`kind: call`, `operation`, `status_code`, `duration_ms`).
- **FR-F029-14:** All connection routes require `integration-admin`; `notify-test` also allows the connection owner; mutations require `Idempotency-Key` and write audit events; cross-tenant IDs return `not_found`.
- **FR-F029-15:** The integrations page lists providers and connections, starts the OAuth flow in a new window and reflects the callback result, shows `needs_reauth`, `limited`, and `revoked` states with a `Reconnect` action, offers `Send test message`, and lets an admin bind a sheet for calendar sync and choose the conflict policy.

### Non-functional requirements

- **NFR-F029-01 Performance:** connection list and provider reads under 500 ms p95; OAuth callback processing under 2 s p95 excluding provider latency; a calendar sync of 1,000 changed rows completes within 5 minutes under provider rate limits; notification send p95 under 3 s.
- **NFR-F029-02 Security/privacy:** PKCE and `state` on every flow, redirect URIs fixed per deployment, tokens envelope-encrypted with key rotation supported through `key_id`, least-privilege scopes per capability, provider webhooks (Graph change notifications, Slack events) verified by signature, and cross-tenant negatives tested.
- **NFR-F029-03 Accessibility:** the integrations page and binding dialog pass axe with zero serious violations; connection status uses text plus icon; the OAuth window hand-off announces the result.
- **NFR-F029-04 Reliability/observability:** refresh and sync jobs are idempotent per connection and cursor, resumable after restart, dead-lettered after 3 retries with the connection marked `error`; metrics `integration_calls_total{provider,operation,status}`, `integration_refresh_failures_total{provider}`, `calendar_sync_rows_total{provider,direction}`; every provider call has a tracing span with `connection_id`.

### Scope

Included: provider catalog, OAuth authorization with PKCE, callback, encrypted token vault, refresh job and forced refresh, revocation, connection list, notification channels for Teams, Google Chat, and Slack, notify test, calendar sync bindings with cursors and conflict policy, thread-reply comment import, typed adapters with retry and call logging, integrations page.

Excluded: API applications and webhooks (F028); notification preferences and digests (F037); Jira, Salesforce, Box, Dropbox, Tableau, and database connectors and the general mapping and conflict queue (F030); Bridge cross-system workflows (F054); OneDrive and Google Drive file sync (F030 file adapters); identity federation with Microsoft or Google (F026).

## 3. UX specification

- Entry points: admin navigation `Integrations`; routes `/admin/integrations`, `/admin/integrations/:connectionId`; sheet settings `Calendar sync` opens the binding dialog for a connected calendar provider.
- Primary flow: administrator clicks `Connect` on Slack, completes consent in the popup, returns to see `Slack · Acme workspace · active`, clicks `Send test message` to `#ops`, sees `Delivered`; connects Microsoft 365, opens sheet `Launch plan`, binds start and end date columns with policy `newest_wins`, and sees events appear in Outlook; edits a date in both places, sees a `conflict` entry with the winning value on the connection page.
- Loading: card skeletons; Empty: provider cards with `Connect`; Error: banner with `correlation_id` and retry; Success: toasts for connect, test, binding; Denied: non-admins see the denied page; `needs_reauth` and `limited` show warning rows with `Reconnect` and the missing scopes; `revoked` rows are muted with `Reconnect`.
- Binding dialog: connection picker, sheet columns for start, end, title, assignee, conflict policy radio group with one-line explanations, `Preview` showing the first 5 rows as events.
- Responsive: provider cards stack under 768 px; binding dialog fits 320 px.
- Keyboard: popup hand-off returns focus to the `Connect` button and announces the result; all dialogs trap focus; reduced motion disables the status transition.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062); Lucide icons `Plug`, `CalendarSync`, `MessageSquare`, `RefreshCw`, `Unplug`, `AlertTriangle`; tokens from `apps/web/src/design/tokens.css`.

- Design: `design/artboards/Integrations.dc.html` on the canvas indexed by `design/canvas.json`. The ticket is the contract and the artboard is the picture; when they disagree the ticket wins.

## 4. Technical specification

### Rust backend

- Data access (decision section 2.1): `crates/persistence/src/integrations/` holds `IntegrationProviderRepository` (owns `integration_providers`, `integration_provider_capabilities`, `integration_provider_capability_scopes`), `IntegrationConnectionRepository` (owns `integration_connections`, `integration_connection_capabilities`, `integration_connection_scopes`, `integration_connection_errors`), `OauthTokenRepository` (owns `oauth_tokens`, `oauth_token_scopes`), `OauthStateRepository` (owns `oauth_states`), `CalendarBindingRepository` (owns `calendar_bindings`, `calendar_event_links`), and `IntegrationEventRepository` (owns `integration_events`, `integration_conflicts`). Child tables belong to the repository of their parent object type, so no two classes write the same table. Named queries: `list_enabled_providers`, `list_capability_scopes`, `replace_connection_capabilities`, `replace_connection_scopes` (granted and missing in one pair of statements), `list_scopes_by_state`, `record_last_error`, `clear_last_error`, `increment_refresh_failures`, `find_by_external_account`, `store_sealed_tokens`, `replace_token_scopes`, `list_tokens_expiring_before`, `delete_tokens_for_connection`, `rewrap_by_key_id`, `claim_state`, `purge_expired_states`, `find_active_binding_for_sheet`, `save_binding_cursor`, `upsert_event_link`, `mark_link_needs_review`, `list_links_needing_review`, `append_call_event`, `append_conflict`, `list_events_for_connection`. No generic query escape hatch exists. Every use case, adapter caller, API handler, and worker job below depends on these repository traits and contains no SQL; the callback (connection row, scope rows, capability rows, token row, token scope rows, state consumption), the refresh job (token row, error row, status), and a calendar sync page (link rows, cursor, conflict rows, cell writes through the F006/F008 repositories) each run in one `UnitOfWork` that owns the transaction.
- Domain entities in `crates/domain/src/integrations/`: `Provider { id: ProviderId (Microsoft365|Google|Slack), capabilities: Vec<Capability>, scopes_for(capability) }` hydrated from the provider lookup tables, `IntegrationConnection { id, tenant_id, provider, capabilities: Vec<Capability>, display_name, owner_id, external_account_id, external_account_label, granted_scopes: Vec<String>, missing_scopes: Vec<String>, status: Pending|Active|Limited|NeedsReauth|Error|Revoked, last_success_at, last_error: Option<ConnectionError>, refresh_failures: u8, revoked_at, revoked_by, version, audit fields }` where the three collections are loaded from and written back to their child tables by `IntegrationConnectionRepository`, `ConnectionError { error_class, provider_status_code, message, occurred_at }`, `OauthToken { connection_id, key_id, nonce, access_ciphertext, refresh_ciphertext, expires_at, granted_scopes: Vec<String>, updated_at }`, `CalendarBinding { id, connection_id, sheet_id, start_column_id, end_column_id, title_column_id, assignee_column_id, conflict_policy, cursor, external_calendar_id, status }`, `IntegrationEvent { id, tenant_id, connection_id, kind: Call|Conflict|Notify|Sync, operation, status_code, duration_ms, detail, occurred_at }`, `ConflictRecord { event_id, binding_id, row_id, field, opshub_value, provider_value, opshub_updated_at, provider_updated_at, winner }`.
- Use cases: `list_providers`, `start_connection`, `complete_callback`, `refresh_connection`, `revoke_connection`, `list_connections`, `send_test_notification`, `register_notification_channel`, `bind_calendar`, `run_calendar_sync`, `resolve_conflict(policy, ours, theirs)`, `import_thread_reply`.
- Vault in `crates/domain/src/integrations/vault.rs`: `Envelope::seal(plaintext, tenant_key) -> Sealed { key_id, nonce, ciphertext }` and `open`; tenant data keys wrapped by the F004 secret manager `kms::wrap` and cached 10 minutes; key rotation re-wraps by `key_id`.
- Adapters in `crates/domain/src/integrations/adapters/{microsoft365.rs, google.rs, slack.rs}` implementing traits `NotifyAdapter { send(target, message) }`, `CalendarAdapter { list_changes(cursor), upsert_event, delete_event }`, `ChatAdapter { fetch_thread_replies(since) }` with an `HttpClient` wrapper enforcing timeout, retry, `Retry-After`, and `integration_events` logging.
- API endpoints (`services/api/src/integrations/`): `GET /api/v1/integrations/providers`, `GET /api/v1/integrations/connections`, `POST /api/v1/integrations/connections`, `GET /auth/integrations/{provider}/callback`, `DELETE /api/v1/integrations/connections/{id}`, `POST /api/v1/integrations/connections/{id}/refresh`, `POST /api/v1/integrations/connections/{id}/notify-test`. DTOs: `ProviderResponse`, `StartConnectionRequest`, `StartConnectionResponse { connection_id, status, authorize_url }`, `ConnectionResponse`, `Page<ConnectionResponse>`, `NotifyTestRequest { target }`, `NotifyTestResponse`, `CalendarBindingRequest` (carried in `PATCH /api/v1/sheets/{id}` settings through the F006 `settings.calendar_binding` key, validated here). The DTOs keep `capabilities`, `scopes`, `missing_scopes`, `granted_scopes`, and each provider capability's `scopes` as JSON arrays and `last_error` as a JSON object, so no request or response shape changes: `IntegrationProviderRepository`, `IntegrationConnectionRepository`, and `OauthTokenRepository` fan them out to rows on write and reassemble them on read.
- Worker jobs (`services/worker/src/integrations/`): `refresh` (every minute, tokens expiring within 5 minutes), `calendar_sync` (every 5 minutes per binding plus provider change notifications), `chat_sync` (every 2 minutes per connection with `chat_sync`), `notify` consumer of F037 channel deliveries.
- Events: `integration.connected.v1`, `integration.revoked.v1`, `integration.refresh-failed.v1`, `integration.notified.v1`; payload per contract conventions.
- Authorization: `integration-admin` for mutations and lists; owner allowed on `notify-test`; callback validated by `state` only (no session required, tenant derived from state); cross-tenant maps to `not_found`.
- Validation: provider enabled; capabilities subset of provider capabilities; `display_name` ≤ 120; `target` per provider (Slack channel ID or user ID, Teams channel or chat ID, Chat space name); binding columns must be date/datetime and text/person types.
- Error mapping: `IntegrationError::ProviderDisabled → 400 invalid`, `::BadState → 400 invalid`, `::ExchangeFailed → 502 unavailable`, `::NeedsReauth → 409 conflict`, `::TestRateLimited → 429 rate_limited`, `::NotFound → 404 not_found`, `AuthzError::Denied → 403 denied`.

### PostgreSQL/SQLx

- Migration `*_integrations_*.sql` creates `integration_connections(id uuid pk, tenant_id uuid not null, provider text not null references integration_providers(id) on delete restrict, display_name text, owner_id uuid not null references users(id) on delete restrict, external_account_id text, external_account_label text, status text not null default 'pending' check (status in ('pending','active','limited','needs_reauth','error','revoked')), last_success_at timestamptz, refresh_failures smallint not null default 0 check (refresh_failures between 0 and 3), revoked_at timestamptz, revoked_by uuid references users(id) on delete restrict, version bigint not null default 1, created_by, created_at, updated_by, updated_at, deleted_at)`, `oauth_tokens(connection_id uuid pk references integration_connections(id) on delete cascade, tenant_id, key_id text not null, nonce bytea not null, access_ciphertext bytea not null, refresh_ciphertext bytea, expires_at timestamptz not null, updated_at)`, `integration_events(id uuid pk, tenant_id, connection_id uuid not null references integration_connections(id) on delete cascade, kind text not null check (kind in ('call','conflict','notify','sync')), operation text, status_code int, duration_ms int, detail jsonb, occurred_at timestamptz not null)`, `oauth_states(state text pk, tenant_id, actor_id uuid not null references users(id) on delete restrict, connection_id uuid not null references integration_connections(id) on delete cascade, code_verifier_ciphertext bytea not null, expires_at timestamptz not null, consumed_at timestamptz)`, `calendar_bindings(id uuid pk, tenant_id, connection_id uuid not null references integration_connections(id) on delete cascade, sheet_id uuid not null references sheets(id) on delete cascade, start_column_id uuid not null, end_column_id uuid, title_column_id uuid not null, assignee_column_id uuid, conflict_policy text not null default 'newest_wins' check (conflict_policy in ('opshub_wins','provider_wins','newest_wins','manual')), cursor text, external_calendar_id text, status text not null default 'active' check (status in ('active','paused')), version, audit fields)`, `calendar_event_links(tenant_id, binding_id uuid not null references calendar_bindings(id) on delete cascade, row_id uuid not null, external_event_id text not null, opshub_updated_at timestamptz, provider_updated_at timestamptz, review_state text not null default 'clean' check (review_state in ('clean','needs_review')), primary key (binding_id, row_id))`.
- Provider catalog (decision section 2, seeded lookup rows rather than constants read by key): `integration_providers(id text primary key check (id in ('microsoft365','google','slack')), display_name text not null)`, `integration_provider_capabilities(provider_id text references integration_providers(id) on delete cascade, capability text not null check (capability in ('notify','calendar_sync','chat_sync')), primary key (provider_id, capability))`, `integration_provider_capability_scopes(provider_id text, capability text, scope text not null, primary key (provider_id, capability, scope), foreign key (provider_id, capability) references integration_provider_capabilities(provider_id, capability) on delete cascade)`. `enabled` stays derived at request time from the presence of deployment client credentials and is not stored.
- Normalized sets (decision section 2, no array columns): `integration_connection_capabilities(connection_id uuid references integration_connections(id) on delete cascade, tenant_id, provider text not null, capability text not null, primary key (connection_id, capability), foreign key (provider, capability) references integration_provider_capabilities(provider_id, capability) on delete restrict)` replaces `capabilities text[]`, with `provider` copied from the parent connection on insert so the composite key is real; `integration_connection_scopes(connection_id uuid references integration_connections(id) on delete cascade, tenant_id, scope text not null, state text not null check (state in ('granted','missing')), primary key (connection_id, scope))` replaces both `scopes text[]` and `missing_scopes text[]`, preserving the two sets exactly as the `granted` and `missing` partitions of one key space, so a scope can never appear in both; `oauth_token_scopes(connection_id uuid references oauth_tokens(connection_id) on delete cascade, tenant_id, scope text not null, primary key (connection_id, scope))` replaces `oauth_tokens.granted_scopes text[]` and records what the last token set actually carried, which `refresh` compares against the connection scope rows; `integration_connection_errors(connection_id uuid primary key references integration_connections(id) on delete cascade, tenant_id, error_class text not null check (error_class in ('invalid_grant','access_denied','rate_limited','provider_unavailable','network','unexpected')), provider_status_code int, message text not null, occurred_at timestamptz not null)` replaces `integration_connections.last_error jsonb`, which the connection list and the `needs_reauth` logic read by key; `integration_conflicts(id uuid pk, tenant_id, event_id uuid not null references integration_events(id) on delete cascade, binding_id uuid not null references calendar_bindings(id) on delete cascade, row_id uuid not null, field text not null check (field in ('start','end','title','assignee')), opshub_value text, provider_value text, opshub_updated_at timestamptz, provider_updated_at timestamptz, winner text not null check (winner in ('opshub','provider','none')))` replaces the per-field conflict payload that previously lived inside `integration_events.detail`, which `ConflictList` read by key and the review queue filters on.
- `jsonb` audit: `integration_events.detail` stays `jsonb` — for `kind: call` and `kind: notify` it is the verbatim provider request/response snapshot kept for support, never filtered, joined, sorted, or constrained; every query over the log uses `kind`, `operation`, `status_code`, `duration_ms`, `connection_id`, and `occurred_at`, and the one part the product did read by key (conflict values) is now `integration_conflicts`. `oauth_states.code_verifier_ciphertext` is opaque `bytea`, not `jsonb`. No other `jsonb` column exists in this module; the sheet-side `settings.calendar_binding` key is F006-owned view settings and is validated here into `calendar_bindings` columns rather than queried as `jsonb`.
- Behaviour preservation: the API keeps `capabilities`, `scopes`, `missing_scopes`, `granted_scopes`, per-capability provider `scopes`, and `last_error` in their existing JSON array and object shapes; `IntegrationConnectionRepository::replace_connection_scopes` and `replace_connection_capabilities` apply a set as one `delete` of removed rows plus one `insert ... on conflict (connection_id, scope) do update set state = excluded.state` inside the caller's `UnitOfWork`, and the read path reassembles the arrays in stable sort order.
- Invariants: one `oauth_tokens` row per connection (primary key); `oauth_token_scopes` cascades with it; `integration_connection_scopes` primary key gives one state per scope per connection, so the granted and missing sets stay disjoint and duplicate-free without an array scan, and `status = 'limited'` requires at least one `state = 'missing'` row (checked by `IntegrationConnectionRepository` in the same transaction that sets the status); `integration_connection_capabilities` primary key blocks duplicate capabilities and every row must match an `integration_provider_capabilities` row for the connection's provider; `integration_provider_capability_scopes` composite key blocks duplicate scopes per capability; `calendar_bindings(sheet_id) where status = 'active'` unique; `calendar_event_links(binding_id, external_event_id)` unique so one provider event maps to one row; `integration_conflicts(event_id, field)` unique; `oauth_states.expires_at` and single-use `consumed_at` enforced by `OauthStateRepository::claim_state` and cleaned nightly; `refresh_failures` in 0–3 via check; at most one `integration_connection_errors` row per connection by primary key.
- Indexes: `integration_connections(tenant_id, provider, status)`, `integration_connection_capabilities(capability, connection_id)` for "which connections offer calendar_sync", `integration_connection_scopes(connection_id, state)` for the limited-scope banner and `integration_connection_scopes(tenant_id, scope)` for scope audits, `oauth_tokens(expires_at)`, `oauth_token_scopes(scope)`, `integration_connection_errors(tenant_id, error_class)`, `integration_provider_capability_scopes(provider_id, capability)`, `integration_events(connection_id, occurred_at desc)`, `integration_events(tenant_id, kind, occurred_at desc)`, `integration_conflicts(binding_id, row_id)` and `integration_conflicts(event_id)`, `calendar_event_links(binding_id, external_event_id)` unique and `calendar_event_links(binding_id) where review_state = 'needs_review'` for the review queue.
- Audit events: `integration.connect-started`, `integration.connected`, `integration.callback-rejected`, `integration.refreshed`, `integration.refresh-failed`, `integration.revoked`, `integration.notify-test`, `calendar-binding.updated`, `calendar-conflict.resolved`.
- Retention/deletion: `integration_events` kept 90 days under the F027 sweep and takes its `integration_conflicts` rows with it by cascade; revoked connections soft-delete after 30 days; `oauth_tokens`, `oauth_token_scopes`, `integration_connection_capabilities`, `integration_connection_scopes`, and `integration_connection_errors` cascade on connection delete; rollback drops the fourteen tables, children before parents, and unseeds the provider catalog last.

### React/TypeScript

- Routes: `/admin/integrations`, `/admin/integrations/:connectionId` in `apps/web/src/features/integrations/`; components `IntegrationsPage`, `ProviderCard`, `ConnectionTable`, `ConnectionDetail`, `OauthPopup`, `NotifyTestDialog`, `CalendarBindingDialog`, `ConflictList`, `CallLogTable`.
- State: TanStack Query keys `['integration-providers']`, `['integration-connections', filter, cursor]`, `['integration-connection', id]`, `['integration-events', id, kind, cursor]`; popup completion invalidates the connection keys.
- API client: generated `IntegrationsApi` with `listProviders`, `listConnections`, `startConnection`, `revokeConnection`, `refreshConnection`, `notifyTest`; binding saved through `SheetsApi.updateSheet` settings.
- Telemetry: `integration_connect_started`, `integration_connected`, `integration_reconnect_clicked`, `integration_notify_test`, `calendar_binding_saved`, `calendar_conflict_viewed` with `provider` and `connection_id`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F029-01 through FR-F029-15 in `testing/features/F029/requirements/cases.md`
- [ ] Failure/edge-case tests: reused state, expired state, narrowed scopes, refresh failure three times, provider 429 with `Retry-After`, both-sides edit under each conflict policy, key rotation re-wrap, thread reply from unknown email
- [ ] Permission-negative and tenant-isolation tests: member cannot connect or revoke, owner may test but not revoke, foreign-tenant connection returns `not_found`, state from tenant A cannot complete on tenant B
- [ ] Rust unit tests: `crates/domain/src/integrations/` vault seal/open, PKCE, state binding, conflict resolution, adapter retry and `Retry-After`
- [ ] API contract/integration tests: every route above with success and each error code against mocked providers
- [ ] Database migration/constraint tests: one token row per connection, one active binding per sheet, cascade delete, rollback, `integration_connection_scopes` rejects a second state for the same scope, `integration_connection_capabilities` rejects a capability the provider does not offer, `oauth_token_scopes` cascades with the token row, `integration_conflicts` rejects a second row for the same `(event_id, field)`, `calendar_event_links` rejects a duplicate `external_event_id` per binding
- [ ] React component tests: `ProviderCard`, `ConnectionTable`, `NotifyTestDialog`, `CalendarBindingDialog`, `ConflictList` states
- [ ] Browser E2E tests: connect Slack through the mock provider, send test, bind calendar, resolve a conflict
- [ ] Accessibility tests: axe on integrations routes and dialogs, popup hand-off announcement
- [ ] Performance/load tests: 1,000-row calendar sync under 5 minutes with mocked rate limits, notification p95 under 3 s

### Fast fanout configuration

- Test harness path: `testing/features/F029/`
- Feature flag: `F029_FEATURE`
- Fixture/seed factory: `testing/fixtures/integrations.rs` builds tenant A and B, an integration-admin, a member, an active connection per provider, a sheet with date columns and 50 rows, and mock provider servers for Microsoft Graph, Google APIs, and Slack Web API with programmable responses
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, UTC, fixed PKCE verifier, fixed tenant data key
- Mock/stub contracts: mock provider servers in `testing/harness/providers/` recording requests and returning fixture payloads (token exchange, refresh, revoke, Graph delta, Calendar sync tokens, Slack `chat.postMessage`, `conversations.replies`); F037 channel registry in memory; secret manager stub with rotatable keys
- Parallel isolation: one schema per test worker, tenant ID per test, mock provider port per worker
- Targeted command: `cargo xtask test-feature F029`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F029/`

## 6. Acceptance criteria

```gherkin
Feature: OAuth connections and provider adapters

Scenario: Connect Slack and send a test message
  Given Slack is enabled for the deployment
  When an integration-admin starts a connection and completes the mock consent
  Then the connection is active with encrypted tokens and integration.connected.v1 is published
  And a notify-test to "#ops" returns delivered true with a provider message id

Scenario: Refresh failures require re-authorization
  Given an active Microsoft 365 connection whose refresh token the mock provider rejects
  When the refresh job runs three times
  Then integration.refresh-failed.v1 is published three times, status is needs_reauth, and syncs are paused

Scenario: Member cannot revoke a connection
  Given a member without the integration-admin role
  When they DELETE /api/v1/integrations/connections/{id}
  Then the response is 403 denied and the connection stays active

Scenario: Calendar conflict follows the policy
  Given a binding with policy newest_wins and a row changed in OpsHub at 10:00 and in Google Calendar at 10:05
  When the calendar sync runs
  Then the row takes the calendar value, an integration_events row of kind conflict is written, and an integration_conflicts row records field start with both values, both timestamps, and winner provider
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F028 (API conventions, correlation IDs, rate-limit layer); F037 (notification channel registry and delivery records); decisions sections 3, 4, 7; contracts row F029
- Blocks: F030
- Conflicts with: none (disjoint owned paths)
- External dependencies: Microsoft Graph, Google Calendar and Chat APIs, Slack Web API; deployment client credentials per provider; mock servers stand in during tests
- Risks and mitigations: provider API changes, mitigated by versioned adapter fixtures and contract tests against recorded responses; token leakage, mitigated by envelope encryption, redaction tests, and no token fields in DTOs; sync loops between OpsHub and calendars, mitigated by `calendar_event_links` timestamps and ignoring echoes of our own writes; provider rate limits, mitigated by honoring `Retry-After` and per-connection concurrency of 1.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F028 and F037 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F029/`
- [ ] Migration file name and owned paths claimed
- [ ] Mock provider servers available in `testing/harness/providers/`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for every connection mutation, refresh failure, and notification
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F029_FEATURE`, run down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Integration administrators can connect Microsoft 365, Google Workspace, and Slack with OAuth, receive OpsHub notifications in Teams, Google Chat, and Slack, sync sheet dates with Outlook and Google Calendar under a chosen conflict policy, and import thread replies as comments; tokens are envelope-encrypted and refreshed automatically.
- Migration adds `integration_providers`, `integration_provider_capabilities`, `integration_provider_capability_scopes`, `integration_connections`, `integration_connection_capabilities`, `integration_connection_scopes`, `integration_connection_errors`, `oauth_tokens`, `oauth_token_scopes`, `oauth_states`, `integration_events`, `integration_conflicts`, `calendar_bindings`, and `calendar_event_links`; rollback drops them. Feature is off by default behind `F029_FEATURE`.
