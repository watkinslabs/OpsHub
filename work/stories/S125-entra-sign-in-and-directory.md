---
id: S125
type: story
status: planned
parent_epic: E006
parent_feature: F063
depends_on: [F026, F037, F038]
owned_paths: [crates/domain/src/entra/**, crates/persistence/src/entra/**, services/api/src/entra/**, apps/web/src/features/entra/**, services/api/migrations/*_entra_*.sql, testing/features/F063/**]
feature_flag: F063_FEATURE
branch: s125-entra-sign-in-and-directory
started_at: null
finished_at: null
---

# S125 — Entra sign-in and directory

## Identity

- Parent feature: `F063` Microsoft Entra integration
- Owner: platform
- Branch: `s125-entra-sign-in-and-directory`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 7; `docs/capability-contracts.md` row F063

## Vertical slice

As a tenant identity administrator, I want to register our Entra app once, store its credentials sealed, test that consent is complete, and then let our people press `Sign in with Microsoft` on the existing login page, so that work accounts become a sign-in option without removing password, TOTP, WebAuthn, generic OIDC, or SAML.

## Requirements

- **SR-S125-01:** `PUT /api/v1/entra/connection` accepts `{ directory_tenant_id, client_id, client_secret | certificate_thumbprint, cloud: global|us_gov|china, capabilities, allowed_email_domains, require_verified_domain }` from an `identity-admin`, seals the credential through the F029 vault into `credential_key_id`/`credential_nonce`/`credential_ciphertext`, writes one `entra_connection_capabilities` row per capability and one `entra_connection_domains` row per allowed domain in the same `UnitOfWork` as the parent row, and returns `status`, `capabilities`, `version`, and the redirect URI to register in Entra with both sets reassembled as JSON arrays so the payload shape is unchanged; a bad `cloud`, an unknown capability, a duplicate domain, or a malformed GUID is `400 invalid` with `field_errors` (covers FR-F063-02, NFR-F063-02).
- **SR-S125-02:** `POST /api/v1/entra/connection/test` runs a client-credentials token request against the cloud's authority and `GET /v1.0/organization`, answering `{ ok, tenant_display_name, granted_scopes, missing_scopes, error_class }` inside 10 s and naming the exact scopes to consent — `GroupMember.Read.All`, `Mail.Send`, `User.Read.All` — never a raw provider string; the outcome is stored as one `entra_connection_scopes(connection_id, scope, granted, observed_at)` row per required scope through `EntraConnectionRepository::record_test_scopes`, and the response arrays are rebuilt from those rows (covers FR-F063-03, NFR-F063-01).
- **SR-S125-03:** `GET /auth/entra/login?tenant_slug=` redirects to the authorize endpoint with `code` flow, S256 PKCE, a tenant-bound `state` persisted as one `entra_sign_in_states` row with the sealed PKCE verifier, the nonce hash and a 10-minute `expires_at`, `nonce`, and `openid profile email`; `GET /auth/entra/callback` validates `state`, `nonce`, `iss`, `aud` and the signature against the cached JWKS, then issues a session through F038's existing session service rather than a second session store (covers FR-F063-04).
- **SR-S125-04:** Account matching uses the `email` claim, falling back to `preferred_username`, case-insensitively against `users.email` within the tenant; an unmatched claim provisions only when `EntraConnectionRepository::domain_is_allowed` finds the claim's domain as an `entra_connection_domains` row and just-in-time provisioning is on, otherwise `403 denied` with `reason: no_matching_user`; deactivated or suspended users get `reason: user_inactive`; the `oid` claim is written to `users.external_id` (covers FR-F063-05).
- **SR-S125-05:** Reused, expired, or foreign-tenant `state` — each a zero-row `EntraSignInStateRepository::claim_state` update rather than an application-level check — a bad `nonce`, and a signature from an unknown JWKS key all return `400 invalid` and write an `entra.signin-rejected` audit event; a suspended F002 tenant and an F003 deny rule cannot be bypassed by the Entra path (covers FR-F063-04, NFR-F063-02).
- **SR-S125-06:** `GET /api/v1/entra/connection` returns `status` in `disconnected|active|needs_consent|error`, `last_test_at`, `last_error_class`, per-capability state joined from `entra_connection_capabilities` and `entra_connection_scopes`, the domain list rebuilt from `entra_connection_domains`, and last sync counts, with no credential field, and answers `200` with `status: disconnected` and no Graph call when no connection exists (covers FR-F063-10, FR-F063-13).
- **SR-S125-07:** `DELETE /api/v1/entra/connection` deletes tokens and, by cascade from the parent row, the capability, domain, scope, sign-in state and group-map rows, reverts F037 to the SMTP transport, stops group sync, stops Entra sign-in immediately, publishes `entra.revoked.v1`, and deletes no OpsHub user or group; password and SAML sign-in keep working afterwards (covers FR-F063-01, FR-F063-10).
- **SR-S125-08:** Every mutation requires `Idempotency-Key` and `If-Match`, writes a redacted `audit_events` row, and publishes `entra.connected.v1` or `entra.revoked.v1`; a non-`identity-admin` is `403 denied` and a cross-tenant connection id is `404 not_found` (covers FR-F063-11).
- **SR-S125-09:** `/admin/entra` renders the connection form, the copyable redirect URI, `Test connection` with granted and missing scopes in a live region, and the capability switches; `MicrosoftSignInButton` renders on `/login` only when `sign_in` is active and sits beside the existing methods, with axe reporting zero serious violations (covers FR-F063-12, NFR-F063-03).

## Surfaces

- Infrastructure/container: per-cloud authority and Graph hosts resolved from the `cloud` field, never hardcoded; F004 secret manager key `kms/tenant-data-key` for envelope encryption; redirect URI fixed per deployment
- Data access: `crates/persistence/src/entra/{mod.rs, connection_repository.rs, sign_in_state_repository.rs, mail_log_repository.rs}` hold every SQL statement for this slice — `EntraConnectionRepository` owns `entra_connections` with its `entra_connection_capabilities`, `entra_connection_domains` and `entra_connection_scopes` children, `EntraSignInStateRepository` owns `entra_sign_in_states`, `EntraMailLogRepository` owns `entra_mail_log`; `crates/domain/src/entra/*` and the `services/api/src/entra` handlers depend on the traits and contain no `sqlx::query*` call or pool handle, and a connection upsert writes parent, capability, domain and scope rows in one `UnitOfWork` (decision section 2.1)
- Rust service/API: `crates/domain/src/entra/{mod.rs, connection.rs, cloud.rs, graph.rs, jwks.rs, sign_in.rs, matching.rs, errors.rs, service.rs}`; `services/api/src/entra/{mod.rs, routes.rs, handlers_connection.rs, handlers_auth.rs, dto.rs}`
- Data/migration: `services/api/migrations/<ts>_entra_create_tables.sql` creating `entra_connections`, `entra_connection_capabilities`, `entra_connection_domains`, `entra_connection_scopes`, `entra_sign_in_states`, `entra_group_map` and `entra_mail_log` with the checks, foreign keys and indexes in ticket section 4
- React/UI: `apps/web/src/features/entra/{EntraPage.tsx, ConnectionForm.tsx, RedirectUriField.tsx, TestResultPanel.tsx, CapabilitySwitches.tsx, DisconnectDialog.tsx, MicrosoftSignInButton.tsx, api.ts, hooks.ts, routes.ts}`
- Mocks/fixtures: `testing/fixtures/entra.rs`; mock Entra authority and mock Graph in `testing/harness/providers/entra/` serving token, JWKS with a rotation fixture, and `organization`; fixed PKCE verifier, nonce and clock `2026-09-03T00:00:00Z`

## TDD harness

- Test path: `testing/features/F063/{requirements,api,database,frontend,accessibility}/`
- Feature flag: `F063_FEATURE`
- Targeted command: `cargo xtask test-feature F063`
- Full command: `cargo xtask test-all`
- First failing tests: `put_connection_seals_secret_and_returns_redirect_uri`, `put_connection_rejects_unknown_cloud`, `test_connection_reports_missing_group_scope`, `login_redirect_carries_s256_pkce_and_nonce`, `callback_issues_f038_session_for_matched_user`, `callback_rejects_reused_state`, `callback_rejects_unknown_jwks_key`, `unmatched_domain_is_denied_no_matching_user`, `revoke_leaves_password_and_saml_working`, `connection_get_without_connection_is_disconnected`, `capability_rows_replace_array_and_reject_duplicates`, `allowed_domain_row_unique_per_connection`

## Exit criteria

- [ ] Requirement tests SR-S125-01 through SR-S125-09 written first and observed failing
- [ ] Tasks T249 and T250 complete and wired through the `services/api` router
- [ ] Unit, API, database, React, permission-negative and accessibility tests pass in targeted and full modes
- [ ] No credential appears in any response, log, audit diff or export
- [ ] Production call path named: `services/api/src/entra/routes.rs` mounted in `services/api/src/router.rs` (`/api/v1/entra`, `/auth/entra`); `MicrosoftSignInButton` consumed by the F038 login provider list
- [ ] Handoff evidence recorded in the F063 ticket
