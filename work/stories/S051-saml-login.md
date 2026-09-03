---
id: S051
type: story
status: planned
parent_epic: E006
parent_feature: F026
depends_on: [F038, F002]
owned_paths: [crates/domain/src/sso/**, services/api/src/sso/**, apps/web/src/features/sso/**, services/api/migrations/*_sso_*.sql, testing/features/F026/**]
feature_flag: F026_FEATURE
branch: s051-saml-login
started_at: null
finished_at: null
---

# S051 — SAML login

## Identity

- Parent feature: `F026` SSO/SCIM
- Owner: platform
- Branch: `s051-saml-login`
- Decision references: `docs/architecture-decisions.md` sections 3, 4; `docs/capability-contracts.md` row F026

## Vertical slice

As a tenant administrator, I want to register a SAML 2.0 connection for my email domains, test and activate it, rotate its certificate, and have employees sign in through my identity provider with every attempt audited, so that corporate identity controls who can reach OpsHub.

## Requirements

- **SR-S051-01:** `POST /api/v1/identity/connections` creates a draft connection with `sp_entity_id`, ACS URL, one certificate, and `version` 1; domains are validated and unique across active connections (covers FR-F026-01, FR-F026-02).
- **SR-S051-02:** `GET /auth/saml/{connection_id}/metadata` renders SP metadata and `GET /auth/saml/{connection_id}/login` issues a signed `AuthnRequest` whose ID is stored for 10 minutes (FR-F026-03).
- **SR-S051-03:** `POST /auth/saml/{connection_id}/acs` verifies signature, audience, recipient, `InResponseTo`, and time conditions with the configured skew, and rejects each failure with `401 denied` and a reason code (FR-F026-04, NFR-F026-02).
- **SR-S051-04:** A verified assertion creates an F038 session for the matching user, JIT-provisions when enabled, and refuses suspended users (FR-F026-05).
- **SR-S051-05:** `PATCH` with `add_certificate_pem` and `retire_certificate_id` supports overlapping certificates; verification accepts any current certificate (FR-F026-06).
- **SR-S051-06:** `POST /api/v1/identity/connections/{id}/test` runs the three checks and activation requires a passing test within 24 hours (FR-F026-07).
- **SR-S051-07:** Every attempt writes `saml.login.succeeded` or `saml.login.failed` and publishes `saml.login.v1`; connection mutations publish `identity-connection.updated.v1` (FR-F026-08).
- **SR-S051-08:** The `/admin/sso` page lists, creates, tests, activates, and rotates connections with the states from ticket section 3 (FR-F026-16, NFR-F026-03).
- **SR-S051-09:** The `/scim/v2` router authenticates a hashed bearer token with a 15-minute rotation grace, serves `Users` and `Groups` list/create/patch/delete per RFC 7644 with `application/scim+json`, and rate-limits at 60 requests per minute per token (FR-F026-09, FR-F026-10, FR-F026-12, FR-F026-13, FR-F026-15).

## Surfaces

- Infrastructure/container: none beyond F004 baseline
- Rust service/API: `crates/domain/src/sso/{connection.rs, certificate.rs, errors.rs, service.rs, saml/{parse.rs, verify.rs, conditions.rs, request.rs, metadata.rs}, scim/{token.rs, filter.rs, users.rs, groups.rs}}`; `services/api/src/sso/{routes.rs, handlers_connection.rs, handlers_saml.rs, handlers_scim.rs, scim_auth.rs, dto.rs, scim_dto.rs}`
- Data/migration: `services/api/migrations/<ts>_sso_create_tables.sql` creating `identity_connections`, `identity_connection_domains`, `saml_certificates`, `saml_assertion_ids`, `scim_tokens`, `scim_sync_log`, `group_mappings`
- React/UI: `apps/web/src/features/sso/{SsoPage.tsx, ConnectionTable.tsx, ConnectionForm.tsx, CertificatePanel.tsx, TestResultList.tsx, SamlErrorPage.tsx, api.ts, hooks.ts, routes.ts}`
- Mocks/fixtures: `testing/fixtures/sso.rs` stub IdP signer with RSA-2048 and P-256 keys, Microsoft and Google assertion shapes; in-memory outbox recorder

## TDD harness

- Test path: `testing/features/F026/{api,database,frontend,accessibility}/`
- Feature flag: `F026_FEATURE`
- Targeted command: `cargo xtask test-feature F026`
- Full command: `cargo xtask test-all`
- First failing tests: `connection_create_returns_sp_metadata_fields`, `connection_duplicate_domain_conflicts`, `acs_accepts_signed_assertion_within_skew`, `acs_rejects_replayed_assertion_id`, `acs_rejects_unsigned_assertion`, `rotation_accepts_either_current_certificate`, `member_cannot_create_connection`

## Exit criteria

- [ ] Requirement tests SR-S051-01 through SR-S051-08 written first and failing
- [ ] Tasks T101 and T102 complete and wired through `services/api` router
- [ ] Unit, API, database, React, permission, and accessibility tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/sso/routes.rs` mounted in `services/api/src/router.rs` (`/api/v1/identity`, `/auth/saml`, `/scim/v2`)
- [ ] Handoff evidence recorded in the F026 ticket
