---
id: S075
type: story
status: planned
parent_epic: E001
parent_feature: F038
depends_on: [F002]
owned_paths: [crates/domain/src/auth/**, crates/auth/src/auth/**, services/api/src/auth/**, apps/web/src/features/auth/**, services/api/migrations/*_auth_*.sql, testing/features/F038/**]
feature_flag: F038_FEATURE
branch: s075-oidc-login-and-sessions
started_at: null
finished_at: null
---

# S075 — OIDC login and sessions

## Identity

- Parent feature: `F038` Authentication and MFA
- Owner: platform
- Branch: `s075-oidc-login-and-sessions`

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 3, 4, 9
- Canonical contract: `docs/capability-contracts.md` row F038

## Vertical slice

As a tenant member, I want to sign in through my organisation's OIDC provider, stay signed in through refresh rotation, see and revoke my sessions, and enrol a passkey or authenticator app, so that every request carries a verified `ActorContext` and a second factor can be demanded by policy.

## Requirements

- **SR-S075-01:** `GET /auth/oidc/start` issues a PKCE `S256` authorization request with `state` and `nonce` in the signed 10-minute `__Host-oh_oidc` cookie and redirects to the tenant provider (covers FR-F038-01).
- **SR-S075-02:** `GET /auth/oidc/callback` validates `state`, `nonce`, JWKS signature, `iss`, `aud`, `exp`, resolves an active user by email, and returns `403 denied` reason `user_not_provisioned` otherwise (FR-F038-02).
- **SR-S075-03:** A successful callback inserts `sessions` and `refresh_tokens`, sets `__Host-oh_session`, updates `last_login_at`, emits `session.created.v1`, and redirects only to same-origin `return_to` paths (FR-F038-03).
- **SR-S075-04:** `POST /auth/refresh` rotates within the family; reuse revokes the family with `session.revoked.v1` reason `refresh_reuse`; `POST /auth/logout` revokes idempotently (FR-F038-04, FR-F038-05).
- **SR-S075-05:** `GET /api/v1/sessions` and `DELETE /api/v1/sessions/{id}` work for self and tenant-admin and return `404` for other users' sessions (FR-F038-06).
- **SR-S075-06:** TOTP enrol/verify and WebAuthn register/assert set `mfa_verified_at`, enforce the 5-factor cap and last-factor rule, and emit `mfa.enrolled.v1` / `mfa.removed.v1` (FR-F038-07, FR-F038-08, FR-F038-09).
- **SR-S075-07:** The shared extractor in `crates/auth` produces `ActorContext` from the session cookie and returns `401 denied` reason `unauthenticated` when absent (FR-F038-15).
- **SR-S075-08:** `/login`, `/login/callback`, and `/settings/security` render the session list, factor enrolment dialogs, and all UI states (NFR-F038-03).

## Surfaces

- Infrastructure/container: dev HTTPS certificate under `infra/` (F004) for WebAuthn origin; none owned here
- Rust service/API: `crates/auth/src/auth/{mod.rs, context.rs, extract.rs, audit_sink.rs, cipher.rs}`; `crates/domain/src/auth/{mod.rs, session.rs, refresh.rs, oidc.rs, provider.rs, factor.rs, totp.rs, webauthn.rs, errors.rs, service_session.rs, service_mfa.rs}`; `services/api/src/auth/{mod.rs, routes.rs, handlers_oidc.rs, handlers_session.rs, handlers_mfa.rs, dto.rs}`
- Data/migration: `services/api/migrations/<ts>_auth_create_tables.sql` creating all six tables from ticket section 4 (tokens, policy, and buckets are used by S076)
- React/UI: `apps/web/src/features/auth/{LoginPage.tsx, TenantSlugForm.tsx, CallbackPage.tsx, MfaInterstitial.tsx, SecuritySettingsPage.tsx, SessionsList.tsx, RevokeSessionDialog.tsx, MfaEnrollTotpDialog.tsx, MfaWebAuthnButton.tsx, FactorsList.tsx, AuthProvider.tsx, api.ts, hooks.ts, routes.ts}`
- Mocks/fixtures: `testing/fixtures/auth.rs` with `MockOidcServer` (Microsoft and Google claim shapes), fixed TOTP secret, software WebAuthn authenticator; in-memory `AuthAuditSink` and outbox recorder

## TDD harness

- Test path: `testing/features/F038/{api,database,frontend,accessibility}/`
- Feature flag: `F038_FEATURE`
- Targeted command: `cargo xtask test-feature F038`
- Full command: `cargo xtask test-all`
- First failing tests: `oidc_start_sets_pkce_state_cookie`, `oidc_callback_creates_session_and_cookie`, `oidc_callback_unprovisioned_user_denied`, `refresh_reuse_revokes_family`, `session_delete_other_user_not_found`, `totp_verify_within_one_step`, `webauthn_counter_replay_rejected`, `login_page_keyboard_and_axe`

## Exit criteria

- [ ] Requirement tests SR-S075-01 through SR-S075-08 written first and failing
- [ ] Tasks T149 and T150 complete and wired through the `services/api` router
- [ ] Unit, API, database, React, accessibility, and permission tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/auth/routes.rs` mounted in `services/api/src/router.rs`, with `crates/auth/src/auth/extract.rs` applied as the `/api/v1` extractor; `apps/web/src/features/auth/LoginPage.tsx` mounted at `/login`
- [ ] Handoff evidence recorded in the F038 ticket
