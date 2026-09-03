---
id: T101
type: task
status: planned
parent_epic: E006
parent_feature: F026
parent_story: S051
depends_on: [S051]
owned_paths: [services/api/migrations/*_sso_*.sql, crates/domain/src/sso/**, services/api/src/sso/**, apps/web/src/features/sso/**, testing/features/F026/api/**, testing/features/F026/database/**, testing/features/F026/frontend/**]
feature_flag: F026_FEATURE
branch: t101-saml-service
started_at: null
finished_at: null
---

# T101 — SAML service

## Identity

- Parent story: `S051` SAML login
- Owner: platform
- Branch: `t101-saml-service`
- Decision references: `docs/architecture-decisions.md` sections 3, 4; `docs/capability-contracts.md` row F026

## Objective

Create the `sso` schema and implement the identity-connection service, SP metadata, AuthnRequest issuance, ACS assertion verification with certificate rotation and clock skew, login audit, and the connection admin page.

## Specification

- Owned paths: `services/api/migrations/<ts>_sso_create_tables.sql` and `.down.sql`, `crates/domain/src/sso/{mod.rs, connection.rs, certificate.rs, errors.rs, service.rs, saml/mod.rs, saml/parse.rs, saml/verify.rs, saml/conditions.rs, saml/request.rs, saml/metadata.rs}`, `services/api/src/sso/{mod.rs, routes.rs, handlers_connection.rs, handlers_saml.rs, dto.rs}`, `apps/web/src/features/sso/{SsoPage.tsx, ConnectionTable.tsx, ConnectionForm.tsx, CertificatePanel.tsx, TestResultList.tsx, SamlErrorPage.tsx, api.ts, hooks.ts, routes.ts}`
- Contract/input: `CreateConnectionRequest { name, protocol: "saml", idp_entity_id, idp_sso_url, idp_certificate_pem, domains, attribute_map, clock_skew_seconds?, jit_provisioning?, ownership_transfer_to? }`, `UpdateConnectionRequest` per ticket section 4, `RelayState` query on login, `SAMLResponse` form field on ACS; headers `Idempotency-Key`, `If-Match`.
- Output/behavior: routes `GET/POST /api/v1/identity/connections`, `PATCH /api/v1/identity/connections/{id}`, `POST /api/v1/identity/connections/{id}/test`, `GET /auth/saml/{connection_id}/login`, `POST /auth/saml/{connection_id}/acs`, `GET /auth/saml/{connection_id}/metadata`; `verify.rs` checks an RSA-SHA256 or ECDSA-P256 signature over the referenced `Assertion` element with exclusive canonicalization, DTD and entity expansion disabled, and accepts any certificate with `not_before <= now <= not_after`; `conditions.rs` applies `clock_skew_seconds`; `saml_assertion_ids` rejects replay for 10 minutes; success creates an F038 session and redirects to `RelayState` (same-origin only); failure redirects to `/auth/saml/error?code=`; events `identity-connection.updated.v1`, `saml.login.v1`; audit `saml.login.succeeded|failed`; DDL for the seven tables and indexes from ticket section 4.
- Dependencies: F038 `sessions::create_for_user`; F002 `users::find_by_email`, `users::create_jit`; F003 audit writer; F004 outbox writer.
- Feature flag: `F026_FEATURE` gates router mounting and the admin route; migration runs regardless.

## TDD

- Failing test first: `testing/features/F026/api/connection_tests.rs::connection_create_returns_sp_metadata_fields`, `::connection_duplicate_domain_conflicts`, `::connection_activate_requires_recent_test`, `::member_cannot_create_connection`; `testing/features/F026/api/saml_tests.rs::acs_accepts_signed_assertion_within_skew`, `::acs_rejects_expired_outside_skew`, `::acs_rejects_unsigned_assertion`, `::acs_rejects_replayed_assertion_id`, `::acs_rejects_audience_mismatch`, `::rotation_accepts_either_current_certificate`, `::jit_provisioning_creates_user`; `testing/features/F026/database/migration_tests.rs::sso_tables_exist_with_constraints`, `::domain_unique_across_active_connections`; `testing/features/F026/frontend/ConnectionForm.test.tsx::validates_domains_and_https`
- Targeted command: `cargo xtask test-feature F026`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/sso.rs` stub IdP signer (RSA-2048, P-256), Microsoft and Google assertion shapes, fixed clock

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; router mounted behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S051
- [ ] `finished_at` recorded
