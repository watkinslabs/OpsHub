---
id: F038
type: feature
status: planned
priority: P0
owner: platform
estimate: 8
target_milestone: M1
parent_epic: E001
depends_on: [F002]
blocks: [F003, F026, F028]
conflicts_with: []
parallel_safe: true
owned_paths: [crates/persistence/src/auth/**, crates/domain/src/auth/**, crates/auth/src/auth/**, services/api/src/auth/**, apps/web/src/features/auth/**, services/api/migrations/*_auth_*.sql, testing/features/F038/**]
feature_flag: F038_FEATURE
flag_default: off
branch: f038-authentication-and-mfa
started_at: null
finished_at: null
---

# F038 — Authentication and MFA

## 1. Identity and dates

- Branch: `f038-authentication-and-mfa`
- Capability area: enterprise security and administration (spec 5.8 SEC-01, SEC-02; low-level bullets on MFA policy, session expiration, refresh-token revocation, IP/device metadata, API token scopes, login audit; section 10 identity decision: generic OIDC, WebAuthn, TOTP, provider fixtures for Microsoft and Google)
- Aggregate: `session`
- Module slug: `auth`

### Decision references

- Architecture: `docs/architecture-decisions.md` sections 3, 4, 9
- Canonical contract: `docs/capability-contracts.md` row F038

## 2. Requirement specification

### Problem and user outcome

Users exist (F002) but nobody can prove who they are. The platform needs OIDC login against the tenant's identity provider, a server-side session store with refresh rotation and revocation, WebAuthn and TOTP second factors governed by a tenant security policy, scoped API tokens for integrations, and rate-limit buckets that stop credential stuffing. Every service then receives one `ActorContext` from the gateway and never parses credentials itself.

As a tenant member, I want to sign in with my organisation's identity provider, enrol a passkey or authenticator app, see and revoke my sessions, and mint scoped API tokens, so that my access is strong, visible, and revocable. As a tenant administrator, I want to require MFA and bound session lifetimes for the whole tenant.

### Functional requirements

- **FR-F038-01:** `GET /auth/oidc/start?tenant={slug}&return_to={path}` builds an authorization-code request with PKCE `S256`, a random `state` and `nonce`, stores them in a signed, HttpOnly, 10-minute cookie `__Host-oh_oidc`, and redirects (302) to the tenant's configured provider; an unknown slug returns `404 not_found` and a missing provider config returns `503 unavailable`.
- **FR-F038-02:** `GET /auth/oidc/callback?code&state` verifies `state`, exchanges the code, validates the ID token signature against the provider JWKS (cached 1 hour, refreshed once on `kid` miss), checks `iss`, `aud`, `exp`, and `nonce`, and resolves the user by `email` in the tenant; a user that does not exist or is not `active` returns `403 denied` with `reason = user_not_provisioned` and no session (provisioning is SCIM, F026).
- **FR-F038-03:** A successful callback inserts `sessions` (ip, user agent, device label, `expires_at = now + session_max_age_seconds`) and one `refresh_tokens` row, sets cookie `__Host-oh_session` (HttpOnly, Secure, SameSite=Lax, Path=/) holding the opaque session id, updates `users.last_login_at`, emits `session.created.v1`, and redirects to `return_to` (same-origin paths only; anything else redirects to `/`).
- **FR-F038-04:** `POST /auth/refresh` with the session cookie and the refresh token rotates the token inside the same `family_id`; presenting an already-used token revokes every session in the family, emits `session.revoked.v1` with `reason = refresh_reuse`, and returns `401 denied`; refresh tokens expire after `refresh_ttl_seconds` and sessions after `idle_timeout_seconds` without activity.
- **FR-F038-05:** `POST /auth/logout` revokes the current session and its refresh family, clears the cookie, emits `session.revoked.v1` with `reason = logout`, and is idempotent (a second call returns `204`).
- **FR-F038-06:** `GET /api/v1/sessions` lists the caller's sessions (`id`, `device_label`, `ip`, `user_agent`, `created_at`, `last_seen_at`, `mfa_verified_at`, `current`); a `tenant-admin` may pass `user_id` to list another user's sessions; `DELETE /api/v1/sessions/{id}` revokes one session for self or tenant-admin and returns `404 not_found` for a session of another user or tenant.
- **FR-F038-07:** `POST /api/v1/mfa/totp/enroll` returns a new `otpauth://` URI and base32 secret exactly once, storing the secret envelope-encrypted in `mfa_factors` as unverified; `POST /api/v1/mfa/totp/verify` with a 6-digit code valid within ±1 step of 30 seconds marks the factor verified, sets `sessions.mfa_verified_at`, and emits `mfa.enrolled.v1`; a wrong code returns `400 invalid` with `field_errors.code`.
- **FR-F038-08:** `POST /api/v1/mfa/webauthn/register` returns creation options with a challenge stored for 5 minutes and, on the second call with the attestation, stores `credential_id`, `public_key`, and `sign_count`; `POST /api/v1/mfa/webauthn/assert` verifies an assertion (origin, RP id, sign count increasing), sets `mfa_verified_at`, and rejects replayed or downgraded counters with `400 invalid`.
- **FR-F038-09:** A user may hold at most 5 factors; `DELETE /api/v1/mfa/factors/{id}` revokes a factor and emits `mfa.removed.v1`, except that removing the last verified factor while the tenant policy has `mfa_required = true` returns `400 invalid` with `reason = mfa_required`.
- **FR-F038-10:** When `security_policies.mfa_required = true` and the session has no `mfa_verified_at`, every `/api/v1` route except `/api/v1/mfa/*`, `GET /api/v1/sessions`, and `POST /auth/logout` returns `403 denied` with `reason = mfa_required`; the web app redirects such users to `/settings/security?enroll=1`.
- **FR-F038-11:** `POST /api/v1/api-tokens` with `{ name, scopes, expires_at? }` returns the plaintext token exactly once in the form `oh_` plus 8 visible characters plus 32 random characters, stores only a SHA-256 hash, writes one `api_token_scopes` row per requested scope in the same transaction, requires that set to be a subset of the creator's effective scopes, caps `expires_at` at `api_token_max_ttl_seconds`, and emits `api-token.created.v1`; `GET /api/v1/api-tokens` lists prefix, name, the joined scope rows, `last_used_at`, `expires_at`; `DELETE /api/v1/api-tokens/{id}` revokes and emits `api-token.revoked.v1`.
- **FR-F038-12:** A request with `Authorization: Bearer oh_...` is authenticated by hash lookup, yields `ActorContext { auth_kind: ApiToken, scopes }`, updates `last_used_at` at most once per minute, and a revoked, expired, or unknown token returns `401 denied` with `reason = invalid_token`.
- **FR-F038-13:** Rate limits are enforced through `rate_limit_buckets`: login start and callback 10 per minute per IP and 5 per minute per user, MFA verify and assert 5 per 10 minutes per user, API token authentication 600 per minute per token; exceeding a bucket returns `429 rate_limited` with `Retry-After` seconds and increments `auth_rate_limited_total{bucket}`.
- **FR-F038-14:** `PATCH /api/v1/tenants/{id}/security-policy` (tenant-admin, `If-Match`) updates `mfa_required`, `session_max_age_seconds` (300–86400), `idle_timeout_seconds` (300–28800), `refresh_ttl_seconds` (3600–7776000), the allowed email domains (replaced as a set of `security_policy_email_domains` rows in the same transaction), and `api_token_max_ttl_seconds` (3600–31536000); out-of-range values return `400 invalid` with `field_errors`; turning on `mfa_required` does not revoke sessions but flags them `mfa_required` on the next request.
- **FR-F038-15:** Every service extracts `ActorContext { tenant_id, actor_id, roles, scopes, correlation_id, auth_kind }` through the shared `crates/auth` extractor from either the session cookie or the bearer token; handlers never read cookies or headers themselves, and a request with neither credential on a non-public route returns `401 denied` with `reason = unauthenticated`.
- **FR-F038-16:** Login success, login failure, refresh reuse, MFA enrol/verify/remove, token create/revoke, session revoke, and policy change each write an audit row through the `AuthAuditSink` (in-memory until F003 lands) with ip, user agent, and correlation id; secrets, codes, and token plaintext never appear in audit rows or logs.

### Non-functional requirements

- **NFR-F038-01 Performance:** OIDC callback (excluding provider latency) completes in under 800 ms p95; session lookup by cookie is a single indexed read under 20 ms p95; bearer token hash lookup under 20 ms p95; rate-limit check adds under 2 ms.
- **NFR-F038-02 Security/privacy:** TOTP secrets are envelope-encrypted with the deployment key from `SecretSource` (F004); refresh and API tokens are stored only as SHA-256 hashes; cookies are `__Host-` prefixed; PKCE and nonce are mandatory; provider adapters are tested against Microsoft and Google fixtures; logs redact `code`, `state`, tokens, and secrets.
- **NFR-F038-03 Accessibility:** the login, MFA enrolment, WebAuthn prompt, sessions list, and token dialogs pass axe with zero serious violations; the TOTP secret is available as copyable text as well as a QR code; countdown and error states are announced through live regions.
- **NFR-F038-04 Reliability/observability:** a provider JWKS outage does not block refresh or session validation (cached keys are used for up to 24 hours); metrics `auth_logins_total{result}`, `auth_sessions_active`, `auth_rate_limited_total{bucket}`, `auth_mfa_verifications_total{kind,result}`; every span carries `tenant_id`, `actor_id`, `correlation_id`, `auth_kind`.

### Scope

Included: OIDC authorization-code login with PKCE, session store and cookie, refresh rotation with reuse detection, logout, session listing and revocation, TOTP and WebAuthn enrolment and verification, factor removal, MFA enforcement, API token lifecycle and bearer authentication, rate-limit buckets, tenant security policy, the shared `ActorContext` extractor, audit sink, login and security settings UI.

Excluded: SAML 2.0, SCIM provisioning, group mapping (F026); role and permission evaluation (F003); OAuth connections to third-party providers (F029); public API applications (F028); password-based login (not supported in this release).

## 3. UX specification

- Entry points: `/login` (tenant slug field or `?tenant=` deep link), `/login/callback`, avatar menu `Security settings` → `/settings/security`, admin menu `Security policy` → `/admin/security-policy`; unauthenticated deep links store `return_to` and resume after login.
- Primary flow: user opens `/login`, enters slug `acme`, is redirected to the provider, returns to `/login/callback`, lands on `return_to`; if the policy requires MFA and no factor is verified the app routes to `/settings/security?enroll=1`, the user chooses `Passkey` (browser prompt) or `Authenticator app` (QR code plus copyable secret, 6-digit input), verifies, and continues.
- Loading: spinner with `Signing you in` on callback; Empty: sessions list shows only the current session; Error: callback errors show the `reason` text, `correlation_id`, and `Try again`; Success: toast on enrolment, token creation (with the one-time token panel and copy button), and revocation; Stale/conflict: policy form shows the reload banner on `409`; Offline: login button disabled with the offline badge.
- Permission-denied: `/admin/security-policy` renders the denied state for members; `mfa_required` responses render the enrolment interstitial rather than a generic error; a suspended tenant shows the F002 notice.
- Destructive actions: `Revoke session`, `Remove factor`, and `Revoke token` open confirm dialogs naming the item; removing the last factor under a required policy is disabled with the explanation.
- Responsive: forms are single column under 640 px; the token panel wraps the token in a monospace block with a copy button.
- Keyboard: the 6-digit input accepts paste and auto-advances, `Enter` submits, `Escape` closes dialogs and returns focus; the QR code has an accessible label and a text alternative.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062); Lucide icons `LogIn`, `KeyRound`, `Fingerprint`, `Smartphone`, `MonitorSmartphone`, `ShieldCheck`, `Trash2`, `Copy`; tokens from `apps/web/src/design/tokens.css`.

- Design: `design/artboards/Login.dc.html` on the canvas indexed by `design/canvas.json`. The ticket is the contract and the artboard is the picture; when they disagree the ticket wins.

## 4. Technical specification

### Rust backend

- Shared crate `crates/auth/src/auth/`: `ActorContext`, `AuthKind { Session, ApiToken }`, `Scope` newtype (`<resource>:<verb>`), `extract.rs` Axum extractor reading `__Host-oh_session` or `Authorization: Bearer`, `AuthAuditSink` trait with `InMemoryAuditSink`, `RateLimiter` trait whose default implementation calls `RateLimitBucketRepository::consume` (no SQL in `crates/auth`), `SecretCipher` for envelope encryption.
- Domain entities in `crates/domain/src/auth/`: `Session { id, tenant_id, user_id, auth_kind, mfa_verified_at, ip, user_agent, device_label, created_at, last_seen_at, expires_at, revoked_at, revoked_reason }`, `RefreshToken { id, session_id, token_hash, family_id, issued_at, expires_at, used_at, revoked_at }`, `MfaFactor { id, tenant_id, user_id, kind: FactorKind, label, totp: Option<TotpSecret>, webauthn: Option<WebAuthnCredential>, verified_at, last_used_at, revoked_at }`, `ApiToken { id, tenant_id, user_id, name, token_hash, prefix, scopes: Vec<Scope>, expires_at, last_used_at, revoked_at }` with `scopes` loaded from and written to `api_token_scopes` by its repository, `SecurityPolicy { tenant_id, mfa_required, session_max_age_seconds, idle_timeout_seconds, refresh_ttl_seconds, allowed_email_domains: Vec<EmailDomain>, api_token_max_ttl_seconds, version }` with the domains held in `security_policy_email_domains`, `RateLimitBucket { key, tokens, refilled_at, window_seconds, capacity }`.
- Data access (decision 2.1): `SessionRepository` (`sessions`, `refresh_tokens`), `MfaFactorRepository` (`mfa_factors`), `ApiTokenRepository` (`api_tokens`, `api_token_scopes`), `SecurityPolicyRepository` (`security_policies`, `security_policy_email_domains`), and `RateLimitBucketRepository` (`rate_limit_buckets`) in `crates/persistence/src/auth/`; each table is written by exactly one of them. Every use case below depends on those repository traits and the shared `UnitOfWork`; `crates/auth`, `crates/domain/src/auth/`, `services/api/src/auth/`, and the sweeper job contain no SQL.
- Use cases: `start_oidc`, `complete_oidc`, `refresh_session`, `logout`, `list_sessions`, `revoke_session`, `enroll_totp`, `verify_totp`, `begin_webauthn_registration`, `finish_webauthn_registration`, `assert_webauthn`, `remove_factor`, `create_api_token`, `list_api_tokens`, `revoke_api_token`, `authenticate_bearer`, `update_security_policy`, `check_rate_limit`; `OidcProvider` trait with `GenericOidcProvider` plus Microsoft and Google fixture adapters.
- API endpoints (`services/api/src/auth/`): `GET /auth/oidc/start`, `GET /auth/oidc/callback`, `POST /auth/logout`, `POST /auth/refresh`, `GET /api/v1/sessions`, `DELETE /api/v1/sessions/{id}`, `POST /api/v1/mfa/totp/enroll`, `POST /api/v1/mfa/totp/verify`, `POST /api/v1/mfa/webauthn/register`, `POST /api/v1/mfa/webauthn/assert`, `DELETE /api/v1/mfa/factors/{id}`, `GET /api/v1/api-tokens`, `POST /api/v1/api-tokens`, `DELETE /api/v1/api-tokens/{id}`, `PATCH /api/v1/tenants/{id}/security-policy`. DTOs `SessionResponse`, `TotpEnrollResponse { factor_id, otpauth_uri, secret }`, `TotpVerifyRequest { factor_id, code }`, `WebAuthnRegisterRequest`, `WebAuthnAssertRequest`, `CreateApiTokenRequest { name, scopes, expires_at? }`, `ApiTokenCreatedResponse { id, prefix, token, scopes, expires_at }`, `ApiTokenResponse`, `UpdateSecurityPolicyRequest`, `SecurityPolicyResponse`.
- Events: `session.created.v1`, `session.revoked.v1`, `mfa.enrolled.v1`, `mfa.removed.v1`, `api-token.created.v1`, `api-token.revoked.v1` through the outbox with `changed_fields` and `reason` where applicable.
- Authorization: `self` for sessions, factors, and tokens; `tenant-admin` for other users' sessions and the security policy; tenant scoping comes from the session or token row, never from the request; `SessionRevoker` implementation provided to F002 for deactivation.
- Validation: slug per F002 rules, `return_to` must start with `/` and not `//`, TOTP code 6 digits, `name` 1–80 chars, `scopes` non-empty, deduplicated, and ≤ 32 entries (checked before the scope rows are written), `allowed_email_domains` ≤ 64 entries and lowercase, policy ranges per FR-F038-14. `RateLimitBucketRepository::consume` refills and debits one bucket row per key in a single upsert statement inside the repository.
- Error mapping: `AuthError::Unauthenticated | InvalidToken | RefreshReuse → 401 denied`, `UserNotProvisioned | MfaRequired | Forbidden → 403 denied`, `InvalidCode | CounterReplay | FactorLimit | LastFactor | PolicyRange → 400 invalid`, `NotFound → 404 not_found`, `StaleVersion → 409 conflict`, `RateLimited → 429 rate_limited`, `ProviderUnavailable → 503 unavailable`.

### PostgreSQL/SQLx

- Migration `*_auth_*.sql` creates `sessions(id uuid pk, tenant_id uuid not null references tenants(id), user_id uuid not null references users(id), auth_kind text not null, mfa_verified_at timestamptz, ip inet, user_agent text, device_label text, created_at timestamptz not null, last_seen_at timestamptz not null, expires_at timestamptz not null, revoked_at timestamptz, revoked_reason text)`, `refresh_tokens(id uuid pk, session_id uuid references sessions(id) on delete cascade, token_hash bytea not null, family_id uuid not null, issued_at, expires_at, used_at, revoked_at)`, `mfa_factors(id uuid pk, tenant_id, user_id, kind text check (kind in ('totp','webauthn')), label text, secret_enc bytea, credential_id bytea, public_key bytea, sign_count bigint, verified_at, last_used_at, revoked_at, created_at)`, `api_tokens(id uuid pk, tenant_id, user_id, name text, token_hash bytea not null, prefix text not null, expires_at timestamptz, last_used_at timestamptz, revoked_at timestamptz, created_at)`, `api_token_scopes(tenant_id uuid not null, token_id uuid not null references api_tokens(id) on delete cascade, scope text not null check (scope ~ '^[a-z-]+:[a-z-]+$'), granted_at timestamptz not null, primary key (token_id, scope))`, `security_policies(tenant_id uuid pk references tenants(id), mfa_required bool not null default false, session_max_age_seconds int not null default 43200, idle_timeout_seconds int not null default 3600, refresh_ttl_seconds int not null default 2592000, api_token_max_ttl_seconds int not null default 7776000, version bigint not null default 1, updated_by, updated_at)`, `security_policy_email_domains(tenant_id uuid not null references security_policies(tenant_id) on delete cascade, domain citext not null, added_by uuid, added_at timestamptz not null, primary key (tenant_id, domain))`, `rate_limit_buckets(key text pk, tokens numeric not null, capacity int not null, window_seconds int not null, refilled_at timestamptz not null)`.
- Invariants: unique `refresh_tokens_hash_idx on (token_hash)`; unique `api_tokens_hash_idx on (token_hash)`; unique `mfa_factors_credential_idx on (credential_id) where credential_id is not null`; scopes and allowed domains are sets, not arrays, so `api_token_scopes` primary key `(token_id, scope)` and `security_policy_email_domains` primary key `(tenant_id, domain)` make a duplicate impossible and the `citext` domain makes matching case-insensitive as the old array comparison was; check constraints on policy ranges; a default `security_policies` row is inserted for every tenant by a trigger on `tenants` insert, with no domain rows, which means "any domain" exactly as the empty array did.
- Indexes: `sessions(user_id, revoked_at)`, `sessions(tenant_id, expires_at) where revoked_at is null`, `refresh_tokens(family_id)`, `mfa_factors(user_id) where revoked_at is null`, `api_tokens(user_id) where revoked_at is null`, `api_token_scopes(tenant_id, scope)` for "which tokens hold this scope" and for the subset check on creation, `security_policy_email_domains(domain)`, `rate_limit_buckets(refilled_at)` for the sweeper.
- Audit actions: `auth.login.success`, `auth.login.failure`, `auth.refresh.reuse`, `auth.logout`, `session.revoke`, `mfa.enroll`, `mfa.verify`, `mfa.remove`, `api_token.create`, `api_token.revoke`, `security_policy.update`.
- Retention/deletion: expired sessions, refresh tokens, and buckets are deleted by an hourly worker sweep after 30 days; factors and tokens are revoked, never deleted, until the F027 purge, and their scope rows are kept with them so a revoked token still shows what it could do; rollback drops the eight tables and the policy trigger.

### React/TypeScript

- Routes in `apps/web/src/features/auth/`: `/login`, `/login/callback`, `/settings/security`, `/admin/security-policy`; components `LoginPage`, `TenantSlugForm`, `CallbackPage`, `MfaInterstitial`, `SecuritySettingsPage`, `SessionsList`, `RevokeSessionDialog`, `MfaEnrollTotpDialog`, `MfaWebAuthnButton`, `FactorsList`, `ApiTokensTable`, `CreateApiTokenDialog`, `TokenRevealPanel`, `SecurityPolicyForm`.
- State: TanStack Query keys `['me']`, `['sessions']`, `['mfa-factors']`, `['api-tokens']`, `['security-policy', tenantId]`; a global `AuthProvider` retries once through `POST /auth/refresh` on `401` and redirects to `/login` on failure; `403 mfa_required` routes to the interstitial.
- API client: generated `AuthApi` with `listSessions`, `revokeSession`, `enrollTotp`, `verifyTotp`, `registerWebAuthn`, `assertWebAuthn`, `removeFactor`, `listApiTokens`, `createApiToken`, `revokeApiToken`, `updateSecurityPolicy`; WebAuthn calls use `navigator.credentials` with base64url conversion helpers.
- Telemetry: `login_started`, `login_completed`, `login_failed{reason}`, `mfa_enrolled{kind}`, `mfa_verified{kind}`, `session_revoked`, `api_token_created`, `security_policy_saved`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F038-01 through FR-F038-16 in `testing/features/F038/requirements/cases.md`
- [ ] Failure/edge-case tests: bad `state`, wrong `nonce`, expired ID token, unknown `kid` with JWKS refresh, refresh reuse, expired refresh, TOTP code at ±1 step and ±2 steps, WebAuthn counter replay, sixth factor, last factor under required policy, token scope escalation, token past policy cap, policy out of range, open-redirect `return_to`
- [ ] Permission-negative and tenant-isolation tests: member patching policy, user revoking another user's session, tenant-B admin listing tenant-A sessions, token with `sheets:read` calling a write route, unauthenticated request on `/api/v1`
- [ ] Rust unit tests: `crates/domain/src/auth/` PKCE, token formats, TOTP window, WebAuthn verification, bucket refill math, policy validation
- [ ] API contract/integration tests: every route above with success and each error code, against Microsoft and Google provider fixtures
- [ ] Database migration/constraint tests: hash uniqueness, policy trigger, cascade on session delete, rollback
- [ ] React component tests: `LoginPage`, `MfaEnrollTotpDialog`, `SessionsList`, `CreateApiTokenDialog`, `SecurityPolicyForm` states
- [ ] Browser E2E tests: login through the mock provider, enrol TOTP, revoke a session, create and use a token, policy enforcement
- [ ] Accessibility tests: axe on all auth pages, keyboard 6-digit entry, QR text alternative, live-region announcements
- [ ] Performance/load tests: callback p95, session lookup p95, bearer lookup p95, rate-limit overhead

### Fast fanout configuration

- Test harness path: `testing/features/F038/`
- Feature flag: `F038_FEATURE`
- Fixture/seed factory: `testing/fixtures/auth.rs` builds on `testing/fixtures/tenants.rs` and adds a mock OIDC provider (`MockOidcServer` serving discovery, JWKS, token endpoint with Microsoft and Google claim shapes), a verified TOTP factor, a registered WebAuthn credential from a software authenticator, and one API token per tenant
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, fixed TOTP secret, deterministic WebAuthn key pair, UTC
- Mock/stub contracts: mock OIDC server in-process; in-memory `AuthAuditSink`; in-memory outbox recorder; `SecretCipher` with a test key
- Parallel isolation: one schema per test worker, tenant ids per test, unique rate-limit key prefixes per test
- Targeted command: `cargo xtask test-feature F038`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F038/`

## 6. Acceptance criteria

```gherkin
Feature: Authentication, sessions, MFA, and API tokens

Scenario: OIDC login creates a session
  Given tenant "acme" with an active user "pat@acme.test" and the mock provider
  When Pat completes the authorization-code flow with a valid nonce
  Then a session row exists with expires_at 12 hours ahead and the __Host-oh_session cookie is set
  And session.created.v1 is in the outbox and users.last_login_at is updated

Scenario: Refresh reuse revokes the family
  Given a session whose refresh token was already rotated
  When the old refresh token is presented again
  Then the response is 401 denied and every session in the family is revoked with reason refresh_reuse

Scenario: MFA required blocks the API until verified
  Given the tenant policy has mfa_required = true and Pat has no verified factor
  When Pat calls GET /api/v1/groups
  Then the response is 403 denied with reason mfa_required
  When Pat verifies a TOTP code within one step
  Then the same call returns 200 and mfa.enrolled.v1 is published

Scenario: Member cannot change the security policy
  Given a member without the tenant-admin role
  When they PATCH /api/v1/tenants/{id}/security-policy
  Then the response is 403 denied and the policy version is unchanged

Scenario: Scoped API token cannot escalate
  Given an API token with scopes ["sheets:read"]
  When it calls a route requiring "sheets:edit"
  Then the response is 403 denied and last_used_at is still updated once
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F002 (tenants, users, fixture); decisions sections 3, 4, 9; contracts row F038
- Blocks: F003, F026, F028
- Conflicts with: none (disjoint owned paths)
- External dependencies: tenant OIDC provider metadata (discovery URL, client id, client secret via `SecretSource`); WebAuthn requires an HTTPS origin, so local E2E uses `https://localhost` with a dev certificate from `infra/`
- Risks and mitigations: the F003 audit writer arrives after this feature, so audit goes through `AuthAuditSink` with an in-memory default swapped for the database sink under `F003_FEATURE`; clock skew with providers is bounded by a 60-second leeway on `iat`/`exp`; rate-limit buckets in PostgreSQL add a write per login, acceptable at the M1 scale and replaceable by a cache-backed `RateLimiter` implementation behind the trait; TOTP secrets depend on the F004 `SecretSource`, so the test cipher key is injected until F004 lands.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F002 accepted and archived; `testing/fixtures/tenants.rs` available
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F038/`
- [ ] Migration file name and owned paths claimed
- [ ] Mock OIDC server and software authenticator available in `testing/harness/`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit rows and outbox events verified for every auth mutation; no secret appears in logs or audit rows
- [ ] `ActorContext` extractor consumed by F002 routes without handler changes
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F038_FEATURE`, run down migration on an empty database
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Users sign in with their organisation's OIDC provider, enrol passkeys or authenticator apps, manage sessions, and mint scoped API tokens; administrators set the tenant security policy.
- Migration adds `sessions`, `refresh_tokens`, `mfa_factors`, `api_tokens`, `api_token_scopes`, `security_policies`, `security_policy_email_domains`, and `rate_limit_buckets`; rollback drops them. Feature is off by default behind `F038_FEATURE`.
