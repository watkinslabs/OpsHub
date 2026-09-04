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
owned_paths: [crates/domain/src/entra/**, services/api/src/entra/**, services/worker/src/entra/**, apps/web/src/features/entra/**, services/api/migrations/*_entra_*.sql, testing/features/F063/**]
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
- Decision references: `docs/architecture-decisions.md` sections 3, 4, 7; `docs/capability-contracts.md` row F063
- Module slug: `entra`

## 2. Requirement specification

### Problem and user outcome

Most enterprise buyers run Microsoft Entra ID. They want their people to press "Sign in with Microsoft" instead of managing another password, their OpsHub groups to follow the directory groups they already maintain, and OpsHub's mail to come from their own Microsoft 365 tenant so it passes their SPF and DMARC policy instead of arriving from an unfamiliar SMTP host. OpsHub already has generic OIDC (F038), SAML and SCIM (F026), and SMTP delivery (F037) — what it lacks is the Entra-shaped path that makes those work without an integration project.

As a tenant identity administrator, I want to connect our Entra tenant once and choose which of Microsoft sign-in, directory group sync, and Graph mail delivery to turn on, so that our people sign in with their work account, their access follows our directory, and OpsHub mail comes from our own domain — without taking away any existing sign-in method.

### Functional requirements

- **FR-F063-01:** Entra is optional and additive. Enabling it never disables password, TOTP, WebAuthn, generic OIDC, or SAML: FR-F038 methods stay available, a tenant may run Entra alongside SAML, and disconnecting Entra leaves every other method working. A tenant with no Entra connection sees no Entra affordance anywhere.
- **FR-F063-02:** `PUT /api/v1/entra/connection` by an `identity-admin` upserts the connection with `{ directory_tenant_id (GUID), client_id (GUID), client_secret | certificate_thumbprint, cloud: global|us_gov|china, capabilities: [sign_in, group_sync, mail], allowed_email_domains: [..], require_verified_domain: bool }`; the secret is envelope-encrypted through the F029 vault, never returned, and the response carries `status`, `capabilities`, `version`, and the redirect URI to register in Entra. An unknown `cloud` or a malformed GUID returns `400 invalid` with `field_errors`.
- **FR-F063-03:** `POST /api/v1/entra/connection/test` performs a client-credentials token request against the configured cloud's authority and a `GET /v1.0/organization` Graph read, returning `{ ok, tenant_display_name, granted_scopes, missing_scopes, error_class }` within 10 s; missing consent for a capability's required scopes returns `ok: false` naming exactly which scopes the administrator must grant, and never a raw provider error string.
- **FR-F063-04:** With the `sign_in` capability, `GET /auth/entra/login?tenant_slug=` redirects to the Entra authorize endpoint with OIDC `code` flow, S256 PKCE, `state` bound to tenant and 10-minute expiry, `nonce`, and scopes `openid profile email`; `GET /auth/entra/callback` validates `state`, `nonce`, the `iss` and `aud` claims, and the token signature against the cached JWKS, then issues an F038 session. A reused, expired, or foreign-tenant `state` returns `400 invalid` and writes an audit event.
- **FR-F063-05:** Account matching is by verified email: the `email` (or `preferred_username` when `email` is absent) claim is matched case-insensitively against `users.email` in that tenant. An unmatched claim provisions a user only when `allowed_email_domains` contains its domain and the tenant permits just-in-time provisioning, otherwise sign-in fails with `denied` and `reason: no_matching_user`. A matched but deactivated or suspended user is refused with `reason: user_inactive`, and the Entra `oid` claim is stored as `users.external_id` so a later email change does not orphan the account.
- **FR-F063-06:** With the `group_sync` capability, `POST /api/v1/entra/sync-groups` and a nightly worker job read directory groups through Graph `GET /v1.0/groups` with delta tokens, and `entra_group_map` maps a directory group `object_id` to an OpsHub group (F002) or role binding (F003); membership changes add and remove OpsHub group members, never touch manually-added members flagged `source: manual`, and publish `entra.group-synced.v1` with counts. A mapping to a group in another tenant returns `404 not_found`.
- **FR-F063-07:** Group sync is bounded and reversible: at most 500 mapped groups and 50,000 members per run, a run that would remove more than 20% of a group's members halts with `status: needs_review` and changes nothing until an administrator confirms, and every add and removal writes an audit event with the directory group as the actor reason.
- **FR-F063-08:** With the `mail` capability, F037 gains a `graph` delivery transport that sends through Graph `POST /v1.0/users/{sender}/sendMail` as the configured sender mailbox, with the same templates, retry schedule, and delivery records as SMTP; `entra.mail-sent.v1` carries `message_id` and `recipient_domain` only. The transport is selected per tenant, SMTP remains the default and the fallback, and a Graph failure falls back to SMTP when the tenant has one configured, recording both attempts on the delivery.
- **FR-F063-09:** Graph calls go through one typed client with a 10 s timeout, bounded retries with exponential backoff, `Retry-After` honoured on `429` and `503`, per-tenant concurrency of 4, and a circuit breaker that opens for 5 minutes after 5 consecutive failures; every call records an `entra_mail_log` or integration event row with operation, status code, and duration, and never logs a token, mail body, or recipient address beyond its domain.
- **FR-F063-10:** `GET /api/v1/entra/connection` returns the connection without secret material, with `status` in `disconnected|active|needs_consent|error`, `last_test_at`, `last_error_class`, per-capability state, and the counts from the last group sync. `DELETE /api/v1/entra/connection` revokes it: tokens are deleted, the mail transport reverts to SMTP, group sync stops, sign-in through Entra stops working immediately, `entra.revoked.v1` is published, and no OpsHub user or group is deleted.
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

## 4. Technical specification

### Rust backend

- Domain entities in `crates/domain/src/entra/`: `EntraConnection { id, tenant_id, directory_tenant_id, client_id, credential: Sealed, cloud: Cloud, capabilities: Vec<Capability>, allowed_email_domains, require_verified_domain, status, last_test_at, last_error_class, sender_mailbox, delta_token, version, audit fields }`, `EntraGroupMap { id, tenant_id, connection_id, directory_group_id, directory_group_name, target: GroupRef|RoleRef, last_synced_at, last_counts }`, `GraphCall { operation, status_code, duration_ms, occurred_at }`.
- Use cases: `upsert_connection`, `test_connection`, `get_connection`, `revoke_connection`, `begin_sign_in`, `complete_sign_in`, `match_or_provision_user`, `list_directory_groups`, `upsert_group_map`, `run_group_sync`, `send_graph_mail`.
- `graph.rs` is the single Graph client: authority per `Cloud`, client-credentials and authorization-code flows, JWKS cache with rotation, timeout, retry with `Retry-After`, per-tenant concurrency 4, and the circuit breaker from FR-F063-09.
- API endpoints (`services/api/src/entra/`): `GET /api/v1/entra/connection`, `PUT /api/v1/entra/connection`, `POST /api/v1/entra/connection/test`, `DELETE /api/v1/entra/connection`, `GET /auth/entra/login`, `GET /auth/entra/callback`, `POST /api/v1/entra/sync-groups`. DTOs `EntraConnectionRequest`, `EntraConnectionResponse`, `TestResponse`, `GroupMapRequest`, `SyncResponse`.
- Worker (`services/worker/src/entra/`): `group_sync` nightly per connection and on demand; the F037 `graph` transport is registered at startup when the tenant has the `mail` capability.
- Registration, not modification: the sign-in path issues a session through F038's existing session service, the mail transport is registered into F037's channel registry the way F029 registers its own, and group targets resolve to F002 groups and F003 role bindings. This feature adds no second session store, no second template system, and no second group model.
- Events: `entra.connected.v1`, `entra.revoked.v1`, `entra.group-synced.v1`, `entra.mail-sent.v1`.
- Authorization: `identity-admin` for every `/api/v1/entra` route; the login and callback routes are unauthenticated and protected by `state`, `nonce` and PKCE; cross-tenant IDs map to `not_found`.
- Error mapping: `EntraError::BadCloud|BadGuid → 400 invalid`, `::MissingConsent → 409 conflict` with `field_errors.capabilities`, `::TokenExchangeFailed → 502 unavailable`, `::Throttled → 429 rate_limited`, `::StateInvalid → 400 invalid`, `::NoMatchingUser|UserInactive → 403 denied`, `NotFound → 404 not_found`, `AuthzError::Denied → 403 denied`.

### PostgreSQL/SQLx

- Migration `*_entra_*.sql` creates `entra_connections(id uuid pk, tenant_id uuid not null unique, directory_tenant_id uuid not null, client_id uuid not null, credential_key_id text not null, credential_nonce bytea not null, credential_ciphertext bytea not null, cloud text not null check (cloud in ('global','us_gov','china')), capabilities text[] not null default '{}', allowed_email_domains text[] not null default '{}', require_verified_domain bool not null default true, sender_mailbox text, status text not null default 'disconnected', last_test_at timestamptz, last_error_class text, delta_token text, version bigint not null default 1, audit fields)`, `entra_group_map(id uuid pk, tenant_id uuid not null, connection_id uuid not null references entra_connections(id) on delete cascade, directory_group_id text not null, directory_group_name text not null, target_kind text not null check (target_kind in ('group','role')), target_id uuid not null, last_synced_at timestamptz, last_added int, last_removed int, version bigint not null default 1, audit fields)`, `entra_mail_log(id uuid pk, tenant_id uuid not null, operation text not null, status_code int, duration_ms int, recipient_domain text, message_id text, occurred_at timestamptz not null)`.
- Invariants: one connection per tenant (`entra_connections(tenant_id)` unique); unique `entra_group_map(connection_id, directory_group_id)`; `capabilities` a subset of `{sign_in,group_sync,mail}` enforced by a check; `sender_mailbox` required when `mail` is present.
- Indexes: `entra_group_map(connection_id)`, `entra_mail_log(tenant_id, occurred_at desc)`, `entra_mail_log(tenant_id, status_code)`.
- Audit events: `entra.connect`, `entra.test`, `entra.revoke`, `entra.signin`, `entra.signin-rejected`, `entra.group-map.upsert`, `entra.group-sync`, with credentials redacted.
- Retention/deletion: `entra_mail_log` kept 90 days under the F027 sweep; connection deletion cascades the map and leaves users and groups intact; rollback drops the three tables.

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
- [ ] Database migration/constraint tests: one connection per tenant, unique group mapping, capability check, cascade on delete, rollback
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
- Migration adds `entra_connections`, `entra_group_map` and `entra_mail_log`; rollback drops them. Feature is off by default behind `F063_FEATURE` and inert until a tenant connects.
