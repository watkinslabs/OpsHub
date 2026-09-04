---
id: F063
type: feature
status: planned
priority: P1
owner: platform
estimate: 8
target_milestone: M5
parent_epic: E006
depends_on: [F026, F037, F038]
blocks: []
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/entra/**, crates/persistence/src/entra/**, services/api/src/entra/**, services/worker/src/entra/**, apps/web/src/features/entra/**, services/api/migrations/*_entra_*.sql, testing/features/F063/**]
feature_flag: F063_FEATURE
flag_default: off
branch: f063-microsoft-entra-integration
started_at: null
finished_at: null
---

# F063 — Microsoft Entra integration

## 1. Identity and dates

- Branch: `f063-microsoft-entra-integration`
- Aggregate: `entra-connection`
- Capability area: enterprise security and administration (spec 5.8 SEC-01, SEC-02 identity federation and provisioning; 5.5 notification delivery; 5.9 INT-02 Microsoft 365)
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 7; `docs/capability-contracts.md` row F063
- Module slug: `entra`

## 2. Requirement specification

### Problem and user outcome

Most enterprise buyers run Microsoft Entra ID. They want their people to press "Sign in with Microsoft" instead of managing another password, their OpsHub groups to follow the directory groups they already maintain, and OpsHub's mail to come from their own Microsoft 365 tenant so it passes their SPF and DMARC policy instead of arriving from an unfamiliar SMTP host. OpsHub already has generic OIDC (F038), SAML and SCIM (F026), and SMTP delivery (F037) — what it lacks is the Entra-shaped path that makes those work without an integration project.

As a tenant identity administrator, I want to connect our Entra tenant once and choose which of Microsoft sign-in, directory group sync, and Graph mail delivery to turn on, so that our people sign in with their work account, their access follows our directory, and OpsHub mail comes from our own domain — without taking away any existing sign-in method.

### Functional requirements

- **FR-F063-01:** Entra is optional and additive. Enabling it never disables password, TOTP, WebAuthn, generic OIDC, or SAML: FR-F038 methods stay available, a tenant may run Entra alongside SAML, and disconnecting Entra leaves every other method working. A tenant with no Entra connection sees no Entra affordance anywhere.
- **FR-F063-02:** `PUT /api/v1/entra/connection` by an `identity-admin` upserts the connection with `{ directory_tenant_id (GUID), client_id (GUID), client_secret | certificate_thumbprint, cloud: global|us_gov|china, capabilities: [sign_in, group_sync, mail], allowed_email_domains: [..], require_verified_domain: bool }`; the secret is envelope-encrypted through the F029 vault, never returned, and the response carries `status`, `capabilities`, `version`, and the redirect URI to register in Entra. The request and response keep `capabilities` and `allowed_email_domains` as JSON arrays; `EntraConnectionRepository` fans each out to one `entra_connection_capabilities` row and one `entra_connection_domains` row and reassembles both arrays on read, so no API shape changes. An unknown `cloud`, an unknown capability, a duplicate domain, or a malformed GUID returns `400 invalid` with `field_errors`.
- **FR-F063-03:** `POST /api/v1/entra/connection/test` performs a client-credentials token request against the configured cloud's authority and a `GET /v1.0/organization` Graph read, returning `{ ok, tenant_display_name, granted_scopes, missing_scopes, error_class }` within 10 s; missing consent for a capability's required scopes returns `ok: false` naming exactly which scopes the administrator must grant, and never a raw provider error string. The result is persisted as one `entra_connection_scopes(connection_id, scope, granted, observed_at)` row per scope the enabled capabilities require, so the admin page and `GET /api/v1/entra/connection` report per-capability consent by joining rows rather than re-calling Graph; the response arrays are rebuilt from those rows.
- **FR-F063-04:** With the `sign_in` capability, `GET /auth/entra/login?tenant_slug=` redirects to the Entra authorize endpoint with OIDC `code` flow, S256 PKCE, `state` bound to tenant and 10-minute expiry, `nonce`, and scopes `openid profile email`; `GET /auth/entra/callback` validates `state`, `nonce`, the `iss` and `aud` claims, and the token signature against the cached JWKS, then issues an F038 session. Each `state` is one `entra_sign_in_states(tenant_id, state)` row holding the sealed PKCE verifier, the nonce hash, and `expires_at`, and is claimed once by `EntraSignInStateRepository::claim_state`, so a reused, expired, or foreign-tenant `state` returns `400 invalid` and writes an audit event.
- **FR-F063-05:** Account matching is by verified email: the `email` (or `preferred_username` when `email` is absent) claim is matched case-insensitively against `users.email` in that tenant. An unmatched claim provisions a user only when the claim's domain has an `entra_connection_domains` row for this connection — a single indexed row lookup, not a scan of an array — and the tenant permits just-in-time provisioning, otherwise sign-in fails with `denied` and `reason: no_matching_user`. A matched but deactivated or suspended user is refused with `reason: user_inactive`, and the Entra `oid` claim is stored as `users.external_id` so a later email change does not orphan the account.
- **FR-F063-06:** With the `group_sync` capability, `POST /api/v1/entra/sync-groups` and a nightly worker job read directory groups through Graph `GET /v1.0/groups` with delta tokens, and `entra_group_map` maps a directory group `object_id` to an OpsHub group (F002) through `target_group_id` or a role (F003) through `target_role_id`, exactly one of which is set and each a declared foreign key; the DTO keeps the `{ target_kind, target_id }` pair and `EntraGroupMapRepository` resolves it to the matching column. Membership changes add and remove OpsHub group members, never touch manually-added members flagged `source: manual`, and publish `entra.group-synced.v1` with counts. A mapping to a group in another tenant returns `404 not_found`.
- **FR-F063-07:** Group sync is bounded and reversible: at most 500 mapped groups and 50,000 members per run, a run that would remove more than 20% of a group's members halts with `status: needs_review` and changes nothing until an administrator confirms, and every add and removal writes an audit event with the directory group as the actor reason.
- **FR-F063-08:** With the `mail` capability — one `entra_connection_capabilities(connection_id, 'mail')` row, which the transport registry joins on rather than testing array membership — F037 gains a `graph` delivery transport that sends through Graph `POST /v1.0/users/{sender}/sendMail` as the configured sender mailbox, with the same templates, retry schedule, and delivery records as SMTP; `entra.mail-sent.v1` carries `message_id` and `recipient_domain` only. The transport is selected per tenant, SMTP remains the default and the fallback, and a Graph failure falls back to SMTP when the tenant has one configured, recording both attempts on the delivery.
- **FR-F063-09:** Graph calls go through one typed client with a 10 s timeout, bounded retries with exponential backoff, `Retry-After` honoured on `429` and `503`, per-tenant concurrency of 4, and a circuit breaker that opens for 5 minutes after 5 consecutive failures; every call records one `entra_mail_log` row with operation, status code, and duration through `EntraMailLogRepository::append_graph_call` rather than SQL in the client, and never logs a token, mail body, or recipient address beyond its domain.
- **FR-F063-10:** `GET /api/v1/entra/connection` returns the connection without secret material, with `status` in `disconnected|active|needs_consent|error`, `last_test_at`, `last_error_class`, per-capability state assembled from `entra_connection_capabilities` joined to `entra_connection_scopes`, the `allowed_email_domains` array rebuilt from `entra_connection_domains`, and the counts from the last group sync. `DELETE /api/v1/entra/connection` revokes it: tokens are deleted, the mail transport reverts to SMTP, group sync stops, sign-in through Entra stops working immediately, `entra.revoked.v1` is published, and no OpsHub user or group is deleted.
- **FR-F063-11:** Every mutation requires `Idempotency-Key` and `If-Match`, writes an `audit_events` row with a redacted diff, and publishes `entra.connected.v1` or `entra.revoked.v1`; cross-tenant connection IDs return `404 not_found` and only `identity-admin` may read or write the connection.
- **FR-F063-12:** The admin page `/admin/entra` shows the connection form, the redirect URI to copy, a `Test connection` action reporting granted and missing scopes, per-capability switches, the group mapping table with an `Add mapping` picker searching directory groups, the last sync result with its counts, and a `Disconnect` confirmation naming what stops. The login page shows a `Sign in with Microsoft` button only when the tenant has `sign_in` active, alongside the existing methods rather than replacing them.
- **FR-F063-13:** `GET /api/v1/entra/connection` and the login button are safe before the connection exists: a tenant without a connection gets `200` with `status: disconnected` and no button renders, and no Graph call is attempted.

### Non-functional requirements

- **NFR-F063-01 Performance:** the connection read responds under 300 ms p95; `test` completes under 10 s including two provider round trips; a 500-group, 50,000-member delta sync completes within 10 minutes under Graph throttling; a Graph mail send is acknowledged to the F037 queue in under 3 s p95.
- **NFR-F063-02 Security/privacy:** client secrets and certificates are envelope-encrypted with the F029 vault and never returned, logged, exported, or included in an audit diff; PKCE, `state`, `nonce`, `iss` and `aud` validation are mandatory on every sign-in; JWKS is cached with rotation and a signature from an unknown key is rejected; sign-in cannot bypass the F002 tenant `suspended` state or the F003 deny rules; recipient addresses appear in logs only as their domain.
- **NFR-F063-03 Accessibility:** `/admin/entra` and the login button pass axe with zero serious violations; the button carries a text label and is reachable and operable by keyboard; connection status uses text with the icon, never colour alone; the test result is announced in a live region.
- **NFR-F063-04 Reliability/observability:** the sync job is idempotent per delta token, resumable after restart, and dead-lettered after 3 retries with the connection marked `error`; metrics `entra_graph_calls_total{operation,status}`, `entra_signins_total{result}`, `entra_group_sync_members_total{direction}`, and `entra_mail_total{result}`; every Graph call carries a tracing span with `tenant_id` and `correlation_id`.

### Scope

Included: the tenant Entra connection with encrypted credentials and cloud selection, connection test with scope reporting, Microsoft sign-in through OIDC issuing an F038 session, account matching and bounded just-in-time provisioning, directory group sync with delta tokens and a destructive-change guard, the Graph mail transport registered into F037 with SMTP fallback, the shared Graph client with throttling and a circuit breaker, revocation, the admin page, and the login button.

Excluded: SAML and SCIM, which stay F026 and are the alternative federation path, not a duplicate of this one; session, refresh, MFA and API tokens, which stay F038 and are reused unchanged; notification templates, preferences, digests and the SMTP transport, which stay F037; Outlook calendar sync and Teams notifications, which stay F029 and use its own OAuth connection; Google and Slack identity; on-premises Active Directory federation without Entra; conditional-access policy authoring, which belongs to the customer's Entra tenant.

## 3. UX specification

- Entry points: admin navigation `Admin → Identity → Microsoft Entra` at `/admin/entra`; the `Sign in with Microsoft` button on `/login`; the group mapping table at `/admin/entra#groups`.
- Primary flow: an identity administrator opens `/admin/entra`, copies the redirect URI into their Entra app registration, pastes directory tenant ID, client ID and secret, presses `Test connection`, sees `Connected · Contoso Ltd` with `Missing scope: GroupMember.Read.All` listed against the group-sync switch, grants consent in Entra, re-tests, turns on `Sign in` and `Group sync`, maps `Delivery Team` to the OpsHub group `Delivery`, runs a sync, and sees `Added 24, removed 2`. A member then signs in from `/login` with one click.
- Loading: skeleton form and mapping rows. Empty: `disconnected` state explaining what a connection enables, with a `Connect` action. Error: `needs_consent` and `error` banners naming the scope or the error class with a retry, and a `correlation_id`. Denied: non-`identity-admin` administrators get the denied state. Success: toasts on save, test, sync and disconnect. Offline: switches disabled with the offline banner.
- Responsive: the form is single-column under 768 px; the mapping table scrolls inside its own container.
- Keyboard: the button and every switch are reachable in order; the disconnect dialog traps focus and returns it; the test result is announced once, not per field.
- Font/icon/design tokens: from F062; icons `Building2`, `KeyRound`, `Users`, `Mail`, `RefreshCw`, `Unplug` through `apps/web/src/ui/icons.ts`.

- Design: `design/artboards/Entra.dc.html` on the canvas indexed by `design/canvas.json`. The ticket is the contract and the artboard is the picture; when they disagree the ticket wins.

## 4. Technical specification

### Rust backend

- Data access (decision section 2.1): `crates/persistence/src/entra/` holds `EntraConnectionRepository` (owns `entra_connections`, `entra_connection_capabilities`, `entra_connection_domains`, `entra_connection_scopes`), `EntraGroupMapRepository` (owns `entra_group_map`), `EntraSignInStateRepository` (owns `entra_sign_in_states`), and `EntraMailLogRepository` (owns `entra_mail_log`) in `{mod.rs, connection_repository.rs, group_map_repository.rs, sign_in_state_repository.rs, mail_log_repository.rs}`; the child tables belong to the repository of their parent object type and no two classes write the same table. Named queries: `find_by_tenant`, `upsert_connection`, `replace_capabilities`, `list_capabilities`, `replace_allowed_domains`, `domain_is_allowed`, `record_test_scopes`, `list_scope_state`, `set_status_and_error_class`, `advance_delta_token`, `clear_credential`, `list_maps_for_connection`, `find_map_by_directory_group`, `upsert_map`, `record_sync_counts`, `issue_state`, `claim_state`, `purge_expired_states`, `append_graph_call`, `list_recent_calls_for_tenant`, `purge_calls_older_than` — no generic query escape hatch. Every use case below depends on these traits and contains no SQL; `graph.rs`, the API handlers, the worker job, the F037 transport, and the tests reach PostgreSQL only through them. A connection upsert (row, capability rows, domain rows, scope rows, audit row, outbox row), a sign-in that provisions a user, and a group-sync run (member changes through the F002 group and F003 role-binding repositories plus `record_sync_counts`) each run in one `UnitOfWork` that owns the transaction.
- Domain entities in `crates/domain/src/entra/`: `EntraConnection { id, tenant_id, directory_tenant_id, client_id, credential: Sealed, cloud: Cloud, capabilities: Vec<Capability>, allowed_email_domains: Vec<Domain>, require_verified_domain, status, last_test_at, last_error_class, sender_mailbox, delta_token, version, audit fields }` — `capabilities` and `allowed_email_domains` are in-memory projections of their child tables, not columns — `EntraGroupMap { id, tenant_id, connection_id, directory_group_id, directory_group_name, target: GroupRef|RoleRef, last_synced_at, last_counts }`, `SignInState { tenant_id, state, connection_id, nonce_hash, code_verifier: Sealed, expires_at, consumed_at }`, `GraphCall { operation, status_code, duration_ms, occurred_at }`.
- Use cases: `upsert_connection`, `test_connection`, `get_connection`, `revoke_connection`, `begin_sign_in`, `complete_sign_in`, `match_or_provision_user`, `list_directory_groups`, `upsert_group_map`, `run_group_sync`, `send_graph_mail`.
- `graph.rs` is the single Graph client: authority per `Cloud`, client-credentials and authorization-code flows, JWKS cache with rotation, timeout, retry with `Retry-After`, per-tenant concurrency 4, and the circuit breaker from FR-F063-09.
- API endpoints (`services/api/src/entra/`): `GET /api/v1/entra/connection`, `PUT /api/v1/entra/connection`, `POST /api/v1/entra/connection/test`, `DELETE /api/v1/entra/connection`, `GET /auth/entra/login`, `GET /auth/entra/callback`, `POST /api/v1/entra/sync-groups`. DTOs `EntraConnectionRequest`, `EntraConnectionResponse`, `TestResponse`, `GroupMapRequest`, `SyncResponse`.
- Worker (`services/worker/src/entra/`): `group_sync` nightly per connection and on demand; the F037 `graph` transport is registered at startup for the connections `EntraConnectionRepository::list_capabilities` reports as `mail`-enabled. Neither the job nor the transport holds SQL or a pool handle; both take repository traits.
- Registration, not modification: the sign-in path issues a session through F038's existing session service, the mail transport is registered into F037's channel registry the way F029 registers its own, and group targets resolve to F002 groups and F003 role bindings. This feature adds no second session store, no second template system, and no second group model.
- Events: `entra.connected.v1`, `entra.revoked.v1`, `entra.group-synced.v1`, `entra.mail-sent.v1`.
- Authorization: `identity-admin` for every `/api/v1/entra` route; the login and callback routes are unauthenticated and protected by `state`, `nonce` and PKCE; cross-tenant IDs map to `not_found`.
- Error mapping: `EntraError::BadCloud|BadGuid → 400 invalid`, `::MissingConsent → 409 conflict` with `field_errors.capabilities`, `::TokenExchangeFailed → 502 unavailable`, `::Throttled → 429 rate_limited`, `::StateInvalid → 400 invalid`, `::NoMatchingUser|UserInactive → 403 denied`, `NotFound → 404 not_found`, `AuthzError::Denied → 403 denied`.

### PostgreSQL/SQLx

- Migration `*_entra_*.sql` creates `entra_connections(id uuid pk, tenant_id uuid not null unique references tenants(id) on delete cascade, directory_tenant_id uuid not null, client_id uuid not null, credential_key_id text not null, credential_nonce bytea not null, credential_ciphertext bytea not null, cloud text not null check (cloud in ('global','us_gov','china')), require_verified_domain bool not null default true, sender_mailbox text, status text not null default 'disconnected' check (status in ('disconnected','active','needs_consent','error')), last_test_at timestamptz, last_error_class text check (last_error_class is null or last_error_class in ('consent','credential','throttled','unreachable','provider')), delta_token text, version bigint not null default 1, audit fields)`, `entra_group_map(id uuid pk, tenant_id uuid not null references tenants(id) on delete cascade, connection_id uuid not null references entra_connections(id) on delete cascade, directory_group_id text not null, directory_group_name text not null, target_kind text not null check (target_kind in ('group','role')), target_group_id uuid references groups(id) on delete cascade, target_role_id uuid references roles(id) on delete restrict, check ((target_kind = 'group') = (target_group_id is not null) and (target_kind = 'role') = (target_role_id is not null)), last_synced_at timestamptz, last_added int, last_removed int, version bigint not null default 1, audit fields)` — the former polymorphic `target_id uuid` carried no foreign key, so it is split into two declared references with exactly one set — and `entra_mail_log(id uuid pk, tenant_id uuid not null references tenants(id) on delete cascade, connection_id uuid references entra_connections(id) on delete cascade, operation text not null check (operation in ('token','organization','groups_delta','group_members','send_mail')), status_code int, duration_ms int, recipient_domain text, message_id text, occurred_at timestamptz not null)`.
- Normalized sets (decision section 2, no array columns): `entra_connection_capabilities(tenant_id, connection_id references entra_connections(id) on delete cascade, capability text not null check (capability in ('sign_in','group_sync','mail')), enabled_at timestamptz not null, enabled_by uuid, primary key (connection_id, capability))` replaces `capabilities text[]`; `entra_connection_domains(tenant_id, connection_id references entra_connections(id) on delete cascade, domain text not null, created_at timestamptz not null, primary key (connection_id, domain))` replaces `allowed_email_domains text[]`; `entra_connection_scopes(tenant_id, connection_id references entra_connections(id) on delete cascade, scope text not null check (scope in ('User.Read.All','GroupMember.Read.All','Mail.Send')), granted bool not null, observed_at timestamptz not null, primary key (connection_id, scope))` holds the last test's per-scope consent that `granted_scopes`/`missing_scopes` previously existed only in a response body; `entra_sign_in_states(tenant_id, state text, connection_id uuid not null references entra_connections(id) on delete cascade, nonce_hash bytea not null, code_verifier_key_id text not null, code_verifier_nonce bytea not null, code_verifier_ciphertext bytea not null, created_at timestamptz not null, expires_at timestamptz not null, consumed_at timestamptz, primary key (tenant_id, state))` gives the single-use PKCE `state` of FR-F063-04 a real store. `EntraConnectionRequest`/`EntraConnectionResponse` keep `capabilities` and `allowed_email_domains` as JSON arrays and `TestResponse` keeps `granted_scopes`/`missing_scopes` as arrays; `EntraConnectionRepository` fans each set out with a `delete` of removed rows plus `insert ... on conflict do nothing` inside the connection's `UnitOfWork` and reassembles the arrays on read, so the API, the admin page and the redirect URI are unchanged.
- `jsonb` audit: this module declares no `jsonb` column, and none is added. The three shapes that would otherwise have become `jsonb` are all queried by key and are therefore tables or typed columns: the connection test result is filtered per capability by the admin page and so is `entra_connection_scopes` rows, not a `test_result` blob; the last sync outcome is read as numbers by the banner and the API and so is `entra_group_map.last_added`/`last_removed`/`last_synced_at`, not a `last_counts` object; and a Graph call record is filtered by `operation` and `status_code` and aggregated into `entra_graph_calls_total`, so it is the typed `entra_mail_log` columns. Graph response bodies are never persisted — FR-F063-09 and NFR-F063-02 forbid storing tokens, mail bodies and recipient addresses, so the one payload `jsonb` would legitimately carry does not exist here.
- Invariants: one connection per tenant (`entra_connections(tenant_id)` unique); unique `entra_group_map(connection_id, directory_group_id)`; the capability set is constrained by the `entra_connection_capabilities.capability` check and its `(connection_id, capability)` primary key, which also blocks a duplicate capability that an array could not; `sender_mailbox` is required when a `mail` capability row exists, enforced by `EntraConnectionRepository::replace_capabilities` in the same transaction and rejected as `400 invalid` with `field_errors.sender_mailbox`; each allowed domain appears at most once per connection by primary key; `entra_connection_scopes` carries exactly the scopes the enabled capabilities require, rewritten wholesale by `record_test_scopes`; `entra_sign_in_states` is claimed once — `claim_state` updates `consumed_at` where it is null and `expires_at > now()`, so replay is a zero-row update, not an application check.
- Indexes: `entra_connections(status)` for the sweep of connections in `error`; `entra_connection_capabilities(capability)` for "which tenants have `mail`", the query the transport registry runs at worker startup; `entra_connection_domains(domain)` for sign-in domain lookup and `entra_connection_domains(tenant_id, connection_id)`; `entra_connection_scopes(connection_id) where granted = false` for the missing-consent banner; `entra_sign_in_states(expires_at)` for `purge_expired_states`; `entra_group_map(connection_id)`, `entra_group_map(target_group_id)` and `entra_group_map(target_role_id)` for the reverse "which directory group drives this OpsHub group or role" lookup; `entra_mail_log(tenant_id, occurred_at desc)`, `entra_mail_log(tenant_id, status_code)`.
- Audit events: `entra.connect`, `entra.test`, `entra.revoke`, `entra.signin`, `entra.signin-rejected`, `entra.group-map.upsert`, `entra.group-sync`, with credentials redacted.
- Retention/deletion: `entra_mail_log` kept 90 days under the F027 sweep through `purge_calls_older_than`, expired `entra_sign_in_states` purged hourly; connection deletion cascades the capability, domain, scope, state and map rows and leaves users and groups intact; rollback drops the seven tables, children before parents.

### React/TypeScript

- Routes: `/admin/entra` in `apps/web/src/features/entra/`; components `EntraPage`, `ConnectionForm`, `RedirectUriField`, `TestResultPanel`, `CapabilitySwitches`, `GroupMapTable`, `GroupPickerDialog`, `SyncResultBanner`, `DisconnectDialog`, and `MicrosoftSignInButton` exported for the F038 login page.
- State: TanStack Query keys `['entra-connection']`, `['entra-directory-groups', search]`, `['entra-group-map']`; the test action invalidates the connection key; sign-in status is read from the F038 login provider list rather than a second source.
- API client: generated `EntraApi` with `getConnection`, `putConnection`, `testConnection`, `deleteConnection`, `syncGroups`, `listDirectoryGroups`.
- Telemetry: `entra_connection_saved`, `entra_connection_tested`, `entra_capability_toggled`, `entra_group_mapped`, `entra_sync_run`, `entra_signin_clicked` with the resolved capability.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F063-01 through FR-F063-13 in `testing/features/F063/requirements/cases.md`
- [ ] Failure/edge-case tests: reused state, expired state, bad nonce, unknown JWKS key, missing consent per capability, throttled Graph with `Retry-After`, circuit breaker open, delta token expiry, a sync that would remove 30% of a group, Graph mail failure falling back to SMTP
- [ ] Permission-negative and tenant-isolation tests: a non-`identity-admin` is denied every route, a foreign-tenant connection or group map returns `not_found`, a `state` minted for tenant A cannot complete on tenant B, a suspended tenant cannot sign in through Entra, a deactivated user is refused
- [ ] Rust unit tests: `crates/domain/src/entra/` claim validation, account matching and provisioning rules, group diffing with the 20% guard, retry and `Retry-After` handling, circuit breaker
- [ ] API contract/integration tests: every route above with success and each error code against a mock Entra and Graph
- [ ] Database migration/constraint tests: one connection per tenant, unique group mapping, capability row check and duplicate rejection, duplicate allowed domain rejection, scope row check, `entra_group_map` rejecting both or neither target column, single-claim `entra_sign_in_states`, cascade of capability/domain/scope/state/map rows on connection delete, rollback ordering — every fixture and assertion goes through the `crates/persistence/src/entra/` repositories
- [ ] React component tests: `ConnectionForm`, `TestResultPanel` with missing scopes, `CapabilitySwitches`, `GroupMapTable`, `DisconnectDialog`, `MicrosoftSignInButton` present and absent
- [ ] Browser E2E tests: connect through the mock provider, test, enable sign-in, sign in with Microsoft, map a group, run a sync, disconnect and confirm other methods still work
- [ ] Accessibility tests: axe on `/admin/entra` and the login page, keyboard path through the form and dialog, announced test result
- [ ] Performance/load tests: 500-group 50,000-member delta sync within 10 minutes under mocked throttling, mail acknowledged under 3 s p95

### Fast fanout configuration

- Test harness path: `testing/features/F063/`
- Feature flag: `F063_FEATURE`
- Fixture/seed factory: `testing/fixtures/entra.rs` builds tenants A and B, an identity-admin, a member, a deactivated user, a suspended tenant, a connection per cloud, 500 directory groups with 50,000 members, and a mock Entra authority plus mock Graph in `testing/harness/providers/entra/` serving token, JWKS, organization, groups delta, and `sendMail` with programmable `429` and `503`
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, UTC, fixed PKCE verifier and nonce, fixed signing key with a rotation fixture
- Mock/stub contracts: no real Microsoft endpoint is contacted in any lane; the F037 channel registry and F029 vault run in memory
- Parallel isolation: one schema per worker, tenant per test, mock provider port per worker
- Targeted command: `cargo xtask test-feature F063`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F063/`

## 6. Acceptance criteria

```gherkin
Feature: Optional Microsoft Entra identity, directory and mail

Scenario: Entra is additive, never a replacement
  Given a tenant with password and SAML sign-in enabled
  When an identity-admin connects Entra and enables sign_in
  Then the login page offers password, SAML and Sign in with Microsoft
  And disconnecting Entra leaves password and SAML working

Scenario: Missing consent is reported as a scope, not an error string
  Given a connection whose app registration lacks GroupMember.Read.All
  When the administrator presses Test connection
  Then the result is ok false with missing_scopes listing GroupMember.Read.All
  And the group_sync switch explains which consent is required

Scenario: A destructive directory sync halts for review
  Given a mapped group of 100 members where the directory now returns 70
  When the sync runs
  Then no member is removed and the run status is needs_review

Scenario: Graph mail failure falls back to SMTP
  Given a tenant with the mail capability and an SMTP transport configured
  When Graph sendMail returns 503 three times
  Then the notification is delivered over SMTP and both attempts are recorded

Scenario: A state from another tenant cannot complete sign-in
  Given a state minted for tenant A
  When the callback is presented in tenant B's context
  Then the response is 400 invalid and an audit event records the rejection
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F026 (identity connection model and the federation admin area this sits beside); F037 (notification channel registry, templates, delivery records, SMTP transport and fallback); F038 (session issue, refresh, `ActorContext`, login page provider list); and at implementation time the F029 vault for credential sealing and F002/F003 for group and role targets
- Blocks: none
- Conflicts with: none; `entra` is its own module and no other feature owns these paths
- External dependencies: Microsoft Entra ID and Microsoft Graph, one app registration per customer tenant with admin consent; mock authority and Graph stand in for every test
- Risks and mitigations: Graph throttling on large directories, mitigated by delta tokens, `Retry-After`, per-tenant concurrency 4 and the 10-minute budget; a mis-mapped group silently stripping access, mitigated by the 20% destructive-change halt and per-member audit; secret leakage, mitigated by envelope encryption, redaction tests and DTOs that carry no credential field; sovereign clouds differing in endpoints, mitigated by the `cloud` field selecting the authority and Graph host rather than hardcoding; customers assuming Entra replaces SAML, mitigated by FR-F063-01 and the excluded list naming F026 as the alternative path
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F026, F037 and F038 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F063/`
- [ ] Migration file name and owned paths claimed
- [ ] Mock Entra authority and Graph available in `testing/harness/providers/entra/`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility and performance gates pass
- [ ] Audit events and outbox events verified for connect, test, revoke, sign-in, mapping and sync
- [ ] No credential appears in any response, log, audit diff or export; the redaction test passes
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F063_FEATURE`, run the down migration on an empty tenant, and confirm password, OIDC and SAML sign-in still work
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Tenants running Microsoft Entra ID can connect their directory once and choose any of Microsoft sign-in, directory group sync, and Graph mail delivery from their own Microsoft 365 tenant. Every existing sign-in method keeps working; Entra is an option, never a replacement.
- Migration adds `entra_connections`, `entra_connection_capabilities`, `entra_connection_domains`, `entra_connection_scopes`, `entra_sign_in_states`, `entra_group_map` and `entra_mail_log`; rollback drops them. Feature is off by default behind `F063_FEATURE` and inert until a tenant connects.
