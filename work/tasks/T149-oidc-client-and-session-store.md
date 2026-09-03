---
id: T149
type: task
status: planned
parent_epic: E001
parent_feature: F038
parent_story: S075
depends_on: [S075]
owned_paths: [services/api/migrations/*_auth_*.sql, crates/domain/src/auth/**, crates/auth/src/auth/**, services/api/src/auth/**, testing/features/F038/api/**, testing/features/F038/database/**]
feature_flag: F038_FEATURE
branch: t149-oidc-client-and-session-store
started_at: null
finished_at: null
---

# T149 — OIDC client and session store

## Identity

- Parent story: `S075` OIDC login and sessions
- Owner: platform
- Branch: `t149-oidc-client-and-session-store`

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4
- Canonical contract: `docs/capability-contracts.md` row F038

## Objective

Create the six auth tables, the OIDC authorization-code client with PKCE, the session and refresh-token store with family reuse detection, the four `/auth` routes, the two session routes, and the shared `ActorContext` extractor.

## Specification

- Owned paths: `services/api/migrations/<ts>_auth_create_tables.sql` and `.down.sql`, `crates/auth/src/auth/{mod.rs, context.rs, extract.rs, audit_sink.rs, cipher.rs}`, `crates/domain/src/auth/{mod.rs, session.rs, refresh.rs, oidc.rs, provider.rs, errors.rs, service_session.rs, schema.rs}`, `services/api/src/auth/{mod.rs, routes.rs, handlers_oidc.rs, handlers_session.rs, dto.rs}`
- Contract/input: DDL per F038 ticket section 4 including the `security_policies` default-row trigger; `OidcProvider` trait `{ discovery(), authorize_url(pkce, state, nonce), exchange(code, verifier), jwks() }` with `GenericOidcProvider`; query `start { tenant, return_to? }`, `callback { code, state }`; `POST /auth/refresh` reads the session cookie and `{ refresh_token }`; `ActorContext` extractor reads `__Host-oh_session`.
- Output/behavior: routes `GET /auth/oidc/start`, `GET /auth/oidc/callback`, `POST /auth/logout`, `POST /auth/refresh`, `GET /api/v1/sessions`, `DELETE /api/v1/sessions/{id}`; callback validates `state`, `nonce`, JWKS signature (cache 1 h, one refresh on `kid` miss), `iss`, `aud`, `exp` with 60 s leeway, resolves the active user, inserts session and refresh token, sets the cookie, emits `session.created.v1`; refresh rotates within `family_id` and reuse revokes the family with `session.revoked.v1` reason `refresh_reuse`; `SessionRevoker` implementation registered for F002 deactivation; errors map per ticket section 4.
- Dependencies: F002 tables and fixture; F004 outbox `enqueue` (in-memory recorder until F004 lands); `SecretCipher` test key until F004 `SecretSource` exists.
- Feature flag: `F038_FEATURE` gates router mounting; the extractor falls back to the F002 test-only header extractor when off.

## TDD

- Failing test first: `testing/features/F038/api/oidc_tests.rs::oidc_start_sets_pkce_state_cookie`, `::oidc_callback_creates_session_and_cookie`, `::oidc_callback_bad_state_denied`, `::oidc_callback_unprovisioned_user_denied`, `::oidc_callback_open_redirect_blocked`, `::refresh_rotates_and_reuse_revokes_family`, `::logout_is_idempotent`; `testing/features/F038/api/session_tests.rs::session_list_self_and_admin`, `::session_delete_other_user_not_found`; `testing/features/F038/database/migration_tests.rs::auth_tables_exist_with_constraints`, `::policy_default_row_created_by_trigger`, `::rollback_drops_tables`
- Targeted command: `cargo xtask test-feature F038`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/auth.rs` `MockOidcServer` with Microsoft and Google claim fixtures; schema-per-worker database

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; router mounted behind the flag; OpenAPI regenerated
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S075
- [ ] `finished_at` recorded
