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

Create the eight auth tables, the OIDC authorization-code client with PKCE, the session and refresh-token store with family reuse detection, the four `/auth` routes, the two session routes, and the shared `ActorContext` extractor.

## Specification

- Owned paths: `services/api/migrations/<ts>_auth_create_tables.sql` and `.down.sql`, `crates/auth/src/auth/{mod.rs, context.rs, extract.rs, audit_sink.rs, cipher.rs}`, `crates/domain/src/auth/{mod.rs, session.rs, refresh.rs, oidc.rs, provider.rs, errors.rs, service_session.rs, schema.rs}`, `services/api/src/auth/{mod.rs, routes.rs, handlers_oidc.rs, handlers_session.rs, dto.rs}`, `crates/persistence/src/auth/{mod.rs, session_repository.rs, mfa_factor_repository.rs, api_token_repository.rs, security_policy_repository.rs, rate_limit_bucket_repository.rs}` — with the migration, the only files in this task that may contain SQL
- Contract/input: DDL per F038 ticket section 4: `sessions`, `refresh_tokens`, `mfa_factors`, `api_tokens`, `api_token_scopes(tenant_id, token_id references api_tokens(id) on delete cascade, scope text check '^[a-z-]+:[a-z-]+$', granted_at, primary key (token_id, scope))`, `security_policies`, `security_policy_email_domains(tenant_id references security_policies(tenant_id) on delete cascade, domain citext, added_by, added_at, primary key (tenant_id, domain))`, `rate_limit_buckets`; no `scopes` or `allowed_email_domains` array column exists; unique `refresh_tokens_hash_idx`, `api_tokens_hash_idx`, partial unique `mfa_factors_credential_idx`; indexes `api_token_scopes(tenant_id, scope)`, `security_policy_email_domains(domain)`, `sessions(user_id, revoked_at)`, `sessions(tenant_id, expires_at) where revoked_at is null`, `refresh_tokens(family_id)`, `rate_limit_buckets(refilled_at)`; the `security_policies` default-row trigger on `tenants` insert, which leaves the tenant with no domain rows (any domain); `OidcProvider` trait `{ discovery(), authorize_url(pkce, state, nonce), exchange(code, verifier), jwks() }` with `GenericOidcProvider`; query `start { tenant, return_to? }`, `callback { code, state }`; `POST /auth/refresh` reads the session cookie and `{ refresh_token }`; `ActorContext` extractor reads `__Host-oh_session`.
- Output/behavior: routes `GET /auth/oidc/start`, `GET /auth/oidc/callback`, `POST /auth/logout`, `POST /auth/refresh`, `GET /api/v1/sessions`, `DELETE /api/v1/sessions/{id}`; callback validates `state`, `nonce`, JWKS signature (cache 1 h, one refresh on `kid` miss), `iss`, `aud`, `exp` with 60 s leeway, resolves the active user through the F002 `UserRepository`, inserts session and refresh token through `SessionRepository` in one `UnitOfWork`, sets the cookie, emits `session.created.v1`; refresh rotates within `family_id` and reuse revokes the family with `session.revoked.v1` reason `refresh_reuse` via `SessionRepository::revoke_family`; the five repositories in `crates/persistence/src/auth/` own every query against the eight tables, so `crates/auth`, `crates/domain/src/auth/`, `services/api/src/auth/`, and the tests hold no SQL string, `sqlx::query*` call, or connection and `cargo xtask check-persistence` passes; `SessionRevoker` implementation registered for F002 deactivation delegates to `SessionRepository` and `ApiTokenRepository`; errors map per ticket section 4.
- Dependencies: F002 tables and fixture; F004 outbox `enqueue` (in-memory recorder until F004 lands); `SecretCipher` test key until F004 `SecretSource` exists.
- Feature flag: `F038_FEATURE` gates router mounting; the extractor falls back to the F002 test-only header extractor when off.

## TDD

- Failing test first: `testing/features/F038/api/oidc_tests.rs::oidc_start_sets_pkce_state_cookie`, `::oidc_callback_creates_session_and_cookie`, `::oidc_callback_bad_state_denied`, `::oidc_callback_unprovisioned_user_denied`, `::oidc_callback_open_redirect_blocked`, `::refresh_rotates_and_reuse_revokes_family`, `::logout_is_idempotent`; `testing/features/F038/api/session_tests.rs::session_list_self_and_admin`, `::session_delete_other_user_not_found`; `testing/features/F038/database/migration_tests.rs::auth_tables_exist_with_constraints`, `::policy_default_row_created_by_trigger`, `::api_token_scope_duplicate_rejected_by_primary_key`, `::api_token_scopes_cascade_on_token_delete`, `::policy_email_domain_duplicate_rejected_case_insensitively`, `::rollback_drops_tables`
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
