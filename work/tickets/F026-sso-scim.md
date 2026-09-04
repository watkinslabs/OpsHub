---
id: F026
type: feature
status: planned
priority: P1
owner: platform
estimate: 8
target_milestone: M5
parent_epic: E006
depends_on: [F038, F002]
blocks: []
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/sso/**, crates/persistence/src/sso/**, services/api/src/sso/**, apps/web/src/features/sso/**, services/api/migrations/*_sso_*.sql, testing/features/F026/**]
feature_flag: F026_FEATURE
flag_default: off
branch: f026-sso-scim
started_at: null
finished_at: null
---

# F026 — SSO/SCIM

## 1. Identity and dates

- Branch: `f026-sso-scim`
- Capability area: enterprise security and administration (spec 5.8 SEC-01, SEC-02; section 10 identity decision)
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4; `docs/capability-contracts.md` row F026
- Aggregate: `identity-connection`
- Module slug: `sso`

## 2. Requirement specification

### Problem and user outcome

An enterprise tenant already runs an identity provider (Microsoft Entra ID, Okta, Google Workspace). Its administrator needs employees to sign in to OpsHub with the corporate identity, needs joiners and leavers to appear and disappear automatically, and needs group membership in the identity provider to drive OpsHub roles. Without this, every hire is a manual invitation and every departure is a security gap.

As a tenant administrator, I want to register a SAML 2.0 connection for my email domains and hand my identity provider a SCIM 2.0 endpoint, so that login, provisioning, suspension, and role assignment follow the corporate directory without manual work.

### Functional requirements

- **FR-F026-01:** A `tenant-admin` can create an identity connection with `name`, `protocol: "saml"`, `idp_entity_id`, `idp_sso_url` (https only), `idp_certificate_pem`, `domains` (1–20 lowercase DNS names), `attribute_map` (`email`, `given_name`, `family_name`, `groups`), `clock_skew_seconds` (0–300, default 120), and `jit_provisioning: bool`; the response returns the connection with `version` 1, `status: "draft"`, the OpsHub `sp_entity_id`, and the ACS URL.
- **FR-F026-02:** Each submitted domain is stored as one `identity_connection_domains` row; a domain may belong to at most one active connection per tenant and at most one tenant platform-wide, enforced by the row's unique index rather than by scanning an array, and a duplicate returns `409 conflict` with `field_errors.domains`.
- **FR-F026-03:** `GET /auth/saml/{connection_id}/metadata` returns SP metadata XML with the current signing certificate and the ACS URL; `GET /auth/saml/{connection_id}/login?RelayState=` issues a signed `AuthnRequest` (HTTP-Redirect binding) whose `ID` is stored for 10 minutes and rejected after use.
- **FR-F026-04:** `POST /auth/saml/{connection_id}/acs` accepts an HTTP-POST binding `SAMLResponse`, verifies the assertion signature against every non-expired certificate on the connection, checks `Audience`, `Recipient`, `InResponseTo`, and `NotBefore`/`NotOnOrAfter` with the configured clock skew, and rejects any failure with `401 denied` and an audit event `saml.login.failed` carrying the reason code (`bad_signature`, `expired`, `audience_mismatch`, `replayed`, `unknown_domain`, `user_suspended`).
- **FR-F026-05:** A verified assertion whose `email` domain matches the connection creates an F038 session for the matching active user; when no user exists and `jit_provisioning` is true the user is created with `source: "saml"`, otherwise the login fails with `unknown_user`; a suspended user fails with `user_suspended`.
- **FR-F026-06:** A `tenant-admin` can add a second IdP certificate (`PATCH /api/v1/identity/connections/{id}` with `add_certificate_pem`) and retire the old one after `not_after`; verification accepts any certificate whose `not_before <= now <= not_after`, so rotation never causes downtime.
- **FR-F026-07:** `POST /api/v1/identity/connections/{id}/test` validates the IdP certificate parses, the SSO URL is reachable (HEAD within 5 s), and the metadata renders; it returns `{ ok, checks: [...] }` without changing state; `status` moves to `active` only through `PATCH { status: "active" }` after a successful test recorded within 24 hours.
- **FR-F026-08:** Every SAML login attempt writes an audit event (`saml.login.succeeded` or `saml.login.failed`) with `connection_id`, `name_id`, IP, user agent, assertion `ID`, and reason, and publishes `saml.login.v1`.
- **FR-F026-09:** A connection has at most one active SCIM bearer token; `PATCH { rotate_scim_token: true }` returns the new token once, stores only its SHA-256 hash, and invalidates the old token after a 15-minute grace period.
- **FR-F026-10:** `GET/POST /scim/v2/Users`, `PATCH/DELETE /scim/v2/Users/{id}` implement RFC 7644 with `userName`, `name`, `emails`, `active`, `externalId`, and `groups`; list supports `filter=userName eq "x"`, `startIndex`, and `count` (max 200); responses use `application/scim+json` and SCIM error bodies with `scimType`.
- **FR-F026-11:** `PATCH /scim/v2/Users/{id}` with `active: false` suspends the user: sessions and refresh tokens are revoked, API tokens disabled, shares to the user retained, and the user's owned sheets, workspaces, dashboards, and workflows are transferred to the connection's `ownership_transfer_to` user (or the tenant primary admin when unset), each transfer written as an audit event; `active: true` reinstates without restoring ownership.
- **FR-F026-12:** `DELETE /scim/v2/Users/{id}` deactivates (never hard-deletes) the user and returns 204; a second delete returns 404 per SCIM.
- **FR-F026-13:** `GET/POST /scim/v2/Groups` and `PATCH /scim/v2/Groups/{id}` create and update F002 groups with `displayName`, `externalId`, and `members` (add/remove/replace operations); each group sync writes a `scim_sync_log` row and publishes `scim.group-synced.v1`.
- **FR-F026-14:** A `tenant-admin` can map a SCIM group (`external_id` or `display_name`) to one or more OpsHub roles through `group_mappings` with one `group_mapping_roles` row per granted role; membership changes recompute role bindings for affected users within the same request, and removing a user from all mapped groups removes only the mapped bindings, never manually assigned ones.
- **FR-F026-15:** SCIM requests presented with an unknown, revoked, or expired token return 401 with a SCIM error; requests exceeding 60 per minute per token return 429 `rate_limited` with `Retry-After`.
- **FR-F026-16:** The web admin page lists connections with status, domains, certificate expiry, last login, and last SCIM sync; shows a rotation warning 30 days before a certificate expires; and lets a `tenant-admin` create, test, activate, rotate, and disable connections.

### Non-functional requirements

- **NFR-F026-01 Performance:** ACS processing (signature verification plus session creation) completes in under 800 ms p95; SCIM single-user operations complete in under 500 ms p95; a group PATCH touching 500 members completes in under 2 s.
- **NFR-F026-02 Security/privacy:** assertions must be signed (unsigned or `Response`-only signatures with an unsigned `Assertion` are rejected); XML parsing disables DTDs and external entities; SCIM tokens are stored hashed; IdP certificates and PEM material are never logged; cross-tenant connection or SCIM access returns `not_found`.
- **NFR-F026-03 Accessibility:** the connection admin page and dialogs pass axe with zero serious violations; certificate expiry warnings are announced to screen readers; every action is keyboard reachable.
- **NFR-F026-04 Reliability/observability:** every ACS and SCIM request has a tracing span with `tenant_id`, `connection_id`, and `correlation_id`; metrics `saml_login_total{result}` and `scim_request_total{resource,result}` exist; SCIM sync log rows are retained 90 days.

### Scope

Included: SAML connection CRUD and lifecycle, SP metadata, AuthnRequest, ACS verification, JIT provisioning, certificate rotation, clock skew, login audit, SCIM users and groups, suspended-user behavior, ownership transfer, group-to-role mapping, admin UI.

Excluded: OIDC login, sessions, MFA, API tokens (F038); user and group tables and manual CRUD (F002); role definitions and ACL evaluation (F003); SCIM Schemas/ResourceTypes discovery endpoints and bulk operations (later increment); IdP-initiated login without `InResponseTo` (rejected by design).

## 3. UX specification

- Entry points: admin navigation `Security > Single sign-on`; route `/admin/sso` lists connections; `/admin/sso/new` and `/admin/sso/:connectionId` edit; IdP-side users reach `/auth/saml/{connection_id}/login` from the OpsHub login page after entering an email whose domain matches an active connection.
- Primary flow: administrator clicks `New connection`, pastes IdP metadata values, adds `example.com`, saves as draft, copies SP entity ID and ACS URL into the IdP, clicks `Test connection`, sees three green checks, clicks `Activate`; on the `Provisioning` tab clicks `Generate SCIM token`, copies it once, and maps group `opshub-admins` to role `tenant-admin`.
- Loading: table skeleton; Empty: card explaining SAML and SCIM with `New connection`; Error: banner with `correlation_id` and retry; Success: toast on save, test, activate, rotate; Stale/conflict: banner `This connection changed` with reload; Denied: non-admins see the denied page.
- Login failure page: `/auth/saml/error?code=` renders a human message per reason code and the `correlation_id`, never assertion contents.
- Responsive: the connection form stacks to one column under 768 px; the SCIM token dialog fits 320 px width.
- Keyboard: tab order follows form order; `Escape` closes dialogs and returns focus; the one-time token field is selectable and has a `Copy` button with a live-region confirmation; reduced motion disables the status transition animation.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062); Lucide icons `ShieldCheck`, `KeyRound`, `RefreshCw`, `Users`, `AlertTriangle`; tokens from `apps/web/src/design/tokens.css`.

## 4. Technical specification

### Rust backend

- Data access (decision section 2.1): `crates/persistence/src/sso/` holds `IdentityConnectionRepository` (owns `identity_connections`, `identity_connection_domains`, `identity_connection_attribute_maps`), `SamlCertificateRepository` (`saml_certificates`), `ScimTokenRepository` (`scim_tokens`), `ScimSyncLogRepository` (`scim_sync_log`), `GroupMappingRepository` (`group_mappings`, `group_mapping_roles`), and `SamlAssertionRepository` (`saml_assertion_ids`). Named queries: `find_connection_by_domain`, `list_domains`, `replace_domains`, `save_attribute_map`, `list_active_certificates`, `find_by_token_hash`, `revoke_with_grace`, `append_sync_entry`, `list_mappings_for_external_id`, `replace_mapping_roles`, `claim_assertion_id`, `purge_expired_assertion_ids`. Every use case below depends on these repository traits and contains no SQL; the ACS handler, the SCIM handlers, and the nightly cleanup job call repositories only, and the ownership transfer and role recomputation run in one `UnitOfWork` shared with F002/F003 repositories.
- Domain entities in `crates/domain/src/sso/`: `IdentityConnection { id, tenant_id, name, protocol: Protocol::Saml, idp_entity_id, idp_sso_url, sp_entity_id, domains: Vec<Domain>, attribute_map: AttributeMap, clock_skew_seconds: u16, jit_provisioning: bool, ownership_transfer_to: Option<UserId>, status: ConnectionStatus (Draft|Active|Disabled), last_test_at, version, audit fields }`, `SamlCertificate { id, connection_id, fingerprint_sha256, pem, not_before, not_after, retired_at }`, `ScimToken { id, connection_id, token_hash, created_at, expires_at, revoked_at }`, `ScimSyncEntry { id, connection_id, resource: Users|Groups, operation, external_id, target_id, outcome, detail, occurred_at }`, `GroupMapping { id, connection_id, external_id, display_name, role_ids: Vec<RoleId> }`.
- Use cases: `create_connection`, `update_connection`, `test_connection`, `list_connections`, `build_metadata`, `start_login`, `consume_assertion`, `rotate_scim_token`, `scim_list_users`, `scim_create_user`, `scim_patch_user`, `scim_delete_user`, `scim_list_groups`, `scim_create_group`, `scim_patch_group`, `apply_group_mappings`, `transfer_ownership`.
- SAML verification in `crates/domain/src/sso/saml/`: `parse_response` (quick-xml with DTD and entity expansion disabled), `verify_signature` (RSA-SHA256 or ECDSA-P256 over the `Assertion` element, exclusive canonicalization), `check_conditions(clock: &Clock, skew)`, `AssertionId` replay cache held in `saml_assertion_ids(tenant_id, assertion_id, expires_at)` for 10 minutes and reached only through `SamlAssertionRepository::claim_assertion_id`.
- API endpoints (`services/api/src/sso/`): `GET /api/v1/identity/connections`, `POST /api/v1/identity/connections`, `PATCH /api/v1/identity/connections/{id}`, `POST /api/v1/identity/connections/{id}/test`, `GET /auth/saml/{connection_id}/login`, `POST /auth/saml/{connection_id}/acs`, `GET /auth/saml/{connection_id}/metadata`, `GET /scim/v2/Users`, `POST /scim/v2/Users`, `PATCH /scim/v2/Users/{id}`, `DELETE /scim/v2/Users/{id}`, `GET /scim/v2/Groups`, `POST /scim/v2/Groups`, `PATCH /scim/v2/Groups/{id}`. DTOs: `CreateConnectionRequest`, `UpdateConnectionRequest { name?, idp_sso_url?, domains?, attribute_map?, clock_skew_seconds?, jit_provisioning?, ownership_transfer_to?, status?, add_certificate_pem?, retire_certificate_id?, rotate_scim_token?, group_mappings? }`, `ConnectionResponse`, `ConnectionTestResponse`, `ScimUser`, `ScimGroup`, `ScimListResponse<T>`, `ScimError`.
- SCIM auth: a `ScimBearer` extractor resolves the token hash to `(tenant_id, connection_id)` and builds the gateway context with actor `scim:<connection_id>` and role `tenant-admin` limited to user/group scopes; the `/scim/v2` router is mounted outside the session middleware.
- Events: `identity-connection.updated.v1`, `saml.login.v1`, `scim.user-synced.v1`, `scim.group-synced.v1`; payload per contract conventions; `saml.login.v1` carries `result` and `reason`.
- Authorization: `tenant-admin` for connection routes; `/auth/saml/*` is public; `/scim/v2/*` requires the SCIM bearer; ownership transfer runs as a system actor with the SCIM actor recorded in `audit_events.actor_id`.
- Validation: `domains` matched against RFC 1123 labels, lowercased; `idp_sso_url` https; certificate PEM must parse as X.509 with `not_after` in the future; `clock_skew_seconds` 0–300; SCIM `count` 1–200.
- Error mapping: `SsoError::DomainTaken → 409 conflict`, `SsoError::StaleVersion → 409 conflict`, `SsoError::NotFound → 404 not_found`, `SamlError::* → 401 denied` (ACS redirects to the error page with the code), `ScimError::NotFound → 404 scim`, `ScimError::Uniqueness → 409 scimType uniqueness`, `ScimError::Unauthorized → 401`, rate limit → 429 `rate_limited`.

### PostgreSQL/SQLx

- Migration `*_sso_*.sql` creates `identity_connections(id uuid pk, tenant_id uuid not null, name text not null, protocol text not null default 'saml' check (protocol in ('saml')), idp_entity_id text not null, idp_sso_url text not null, sp_entity_id text not null, clock_skew_seconds smallint not null default 120, jit_provisioning bool not null default false, ownership_transfer_to uuid null references users(id) on delete restrict, status text not null default 'draft' check (status in ('draft','active','disabled')), last_test_at timestamptz, version bigint not null default 1, created_by, created_at, updated_by, updated_at, deleted_at)`, `saml_certificates(id, tenant_id, connection_id references identity_connections(id) on delete cascade, fingerprint_sha256 text, pem text, not_before timestamptz, not_after timestamptz, retired_at timestamptz)`, `scim_tokens(id, tenant_id, connection_id references identity_connections(id) on delete cascade, token_hash bytea not null, created_at, expires_at, revoked_at)`, `scim_sync_log(id, tenant_id, connection_id references identity_connections(id) on delete restrict, resource text, operation text, external_id text, target_id uuid, outcome text, detail jsonb, occurred_at timestamptz)`, `group_mappings(id, tenant_id, connection_id references identity_connections(id) on delete cascade, external_id text, display_name text, version, audit fields)`, and `saml_assertion_ids(tenant_id, assertion_id text, expires_at, primary key (tenant_id, assertion_id))`.
- Normalized sets (decision section 2, no array columns): `identity_connection_domains(id, tenant_id, connection_id references identity_connections(id) on delete cascade, domain text not null, created_at, primary key (connection_id, domain))` replaces `domains text[]`; `identity_connection_attribute_maps(connection_id references identity_connections(id) on delete cascade, tenant_id, field text not null check (field in ('email','given_name','family_name','groups')), source_attribute text not null, primary key (connection_id, field))` replaces `attribute_map jsonb`, which the assertion reader looked up by key; `group_mapping_roles(mapping_id references group_mappings(id) on delete cascade, tenant_id, role_id uuid not null references roles(id) on delete restrict, primary key (mapping_id, role_id))` replaces `group_mappings.role_ids uuid[]`. The request and response DTOs keep `domains`, `attribute_map`, and `role_ids` as JSON arrays and objects, so the admin API and IdP metadata are unchanged; `IdentityConnectionRepository` and `GroupMappingRepository` fan the sets out to rows and reassemble them on read, replacing a set in one statement pair (`delete` of removed rows, `insert ... on conflict do nothing`) inside the connection's `UnitOfWork` transaction.
- `jsonb` audit: `scim_sync_log.detail` stays `jsonb` — it is the verbatim SCIM request/response snapshot kept for support, never filtered, joined, or aggregated; queries use `resource`, `operation`, `outcome`, and `occurred_at`. No other `jsonb` column remains in this module.
- Invariants: `identity_connection_domains(domain)` carries a partial unique index `where deleted_at is null` on the parent connection's `status <> 'disabled'`, giving one active connection per domain per tenant and platform-wide, replacing the former `unnest(domains)` index; `identity_connection_attribute_maps` requires all four `field` rows present, checked by `IdentityConnectionRepository::save_attribute_map`; partial unique index on `scim_tokens(connection_id) where revoked_at is null and expires_at > now()`; `saml_certificates.fingerprint_sha256` unique per connection; `group_mappings(connection_id, external_id)` unique; `group_mapping_roles` primary key blocks duplicate role grants.
- Indexes: `identity_connections(tenant_id, status)`, `identity_connection_domains(tenant_id, connection_id)` and unique `identity_connection_domains(domain)` for login-time domain lookup, `identity_connection_attribute_maps(connection_id)`, `scim_sync_log(connection_id, occurred_at desc)`, `saml_assertion_ids(expires_at)` for the cleanup job, `group_mappings(tenant_id, connection_id)`, `group_mapping_roles(role_id)` for the reverse "who has this role from a mapping" query.
- Audit events: `identity-connection.create`, `identity-connection.update`, `identity-connection.test`, `saml.login.succeeded`, `saml.login.failed`, `scim.token.rotated`, `scim.user.created`, `scim.user.updated`, `scim.user.suspended`, `scim.user.reinstated`, `scim.group.synced`, `ownership.transferred` with before/after diffs.
- Retention/deletion: `scim_sync_log` rows older than 90 days and expired `saml_assertion_ids` are deleted by a nightly job; connections soft-delete; rollback drops the nine tables, children before parents.

### React/TypeScript

- Routes: `/admin/sso`, `/admin/sso/new`, `/admin/sso/:connectionId` in `apps/web/src/features/sso/`; components `SsoPage`, `ConnectionTable`, `ConnectionForm`, `CertificatePanel`, `TestResultList`, `ScimTokenDialog`, `GroupMappingEditor`, `SamlErrorPage`, `DomainLoginHint`.
- State: TanStack Query keys `['sso-connections']`, `['sso-connection', id]`, `['sso-sync-log', id, cursor]`; mutations invalidate by key and update cached `version`.
- API client: generated `IdentityApi` with `listConnections`, `createConnection`, `updateConnection`, `testConnection`.
- Telemetry: `sso_connection_created`, `sso_connection_tested`, `sso_connection_activated`, `scim_token_rotated`, `group_mapping_saved` with `connection_id`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F026-01 through FR-F026-16 in `testing/features/F026/requirements/cases.md`
- [ ] Failure/edge-case tests: unsigned assertion, expired assertion inside and outside skew, replayed assertion ID, wrong audience, rotated certificate overlap, SCIM token grace period, group PATCH with 500 members, suspended user with 40 owned objects
- [ ] Permission-negative and tenant-isolation tests: non-admin connection create returns `denied`, foreign-tenant connection read returns `not_found`, SCIM token from tenant A cannot read tenant B users, disabled connection login returns `denied`
- [ ] Rust unit tests: `crates/domain/src/sso/saml/` signature verification against Microsoft and Google fixture assertions, canonicalization, condition checks with fixed clock, SCIM filter parser
- [ ] API contract/integration tests: every route above with success and each error code
- [ ] Database migration/constraint tests: `identity_connection_domains` unique domain across tenants, attribute-map completeness check, `group_mapping_roles` duplicate rejection, one active SCIM token, certificate fingerprint uniqueness, rollback ordering
- [ ] React component tests: `ConnectionForm`, `ScimTokenDialog`, `GroupMappingEditor`, `SamlErrorPage` states
- [ ] Browser E2E tests: configure connection, sign in through the stub IdP, SCIM suspend transfers ownership
- [ ] Accessibility tests: axe on `/admin/sso` and dialogs, keyboard token copy
- [ ] Performance/load tests: ACS p95 under 800 ms, SCIM group PATCH with 500 members under 2 s

### Fast fanout configuration

- Test harness path: `testing/features/F026/`
- Feature flag: `F026_FEATURE`
- Fixture/seed factory: `testing/fixtures/sso.rs` builds tenant A and B, a tenant-admin, a member, an active SAML connection with two certificates, a SCIM token, 3 groups, and signed assertion fixtures for Microsoft and Google shapes
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, UTC, fixed RSA-2048 and P-256 test keys
- Mock/stub contracts: in-process stub IdP that signs assertions with the fixture key; outbox publisher recorded in memory; F038 session store real
- Parallel isolation: one schema per test worker, tenant ID per test
- Targeted command: `cargo xtask test-feature F026`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F026/`

## 6. Acceptance criteria

```gherkin
Feature: SAML login and SCIM lifecycle

Scenario: Federated login for a configured domain
  Given an active SAML connection for domain "example.com" with clock skew 120 seconds
  When the stub IdP posts a signed assertion for "ana@example.com" issued 60 seconds in the future
  Then an F038 session is created for Ana
  And audit event saml.login.succeeded and event saml.login.v1 are recorded

Scenario: Replayed assertion is rejected
  Given an assertion ID that was already consumed
  When the same SAMLResponse is posted again
  Then the response is 401 denied with reason "replayed" and no session is created

Scenario: Non-admin cannot create a connection
  Given a member without the tenant-admin role
  When they POST /api/v1/identity/connections
  Then the response is 403 denied and no connection exists

Scenario: SCIM suspension transfers ownership
  Given user Ben owns 3 sheets and the connection transfers ownership to Ana
  When the IdP patches Ben with active false
  Then Ben's sessions are revoked, the 3 sheets are owned by Ana, and 3 ownership.transferred audit events exist

Scenario: Group mapping assigns roles
  Given group "opshub-admins" mapped to role tenant-admin
  When SCIM adds Ana to the group
  Then Ana has a tenant-admin binding sourced from the mapping and scim.group-synced.v1 is published
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F038 (sessions, refresh-token revocation, security policy); F002 (users, groups, membership); decisions sections 3, 4; contracts row F026
- Blocks: none in the plan
- Conflicts with: none (disjoint owned paths)
- External dependencies: customer identity providers; verified with Microsoft Entra ID and Google Workspace metadata fixtures per spec section 10
- Risks and mitigations: XML signature wrapping attacks, mitigated by verifying the signature over the exact `Assertion` element referenced by ID and rejecting multiple assertions; certificate rotation outages, mitigated by multi-certificate verification; ownership transfer of hundreds of objects blocking the SCIM request, mitigated by batching in one transaction with a 5 s budget and a `scim_sync_log` outcome `partial` that a `tenant-admin` can retry.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F038 and F002 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F026/`
- [ ] Migration file name and owned paths claimed
- [ ] Stub IdP signer and assertion fixtures available in `testing/fixtures/sso.rs`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for every login, sync, and connection mutation
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F026_FEATURE`, run down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Tenant administrators can configure SAML 2.0 single sign-on per email domain with certificate rotation and login audit, and provision users and groups through SCIM 2.0 with group-to-role mapping and ownership transfer on suspension.
- Migration adds `identity_connections`, `identity_connection_domains`, `identity_connection_attribute_maps`, `saml_certificates`, `scim_tokens`, `scim_sync_log`, `group_mappings`, `group_mapping_roles`, and `saml_assertion_ids`; rollback drops them. Feature is off by default behind `F026_FEATURE`.
