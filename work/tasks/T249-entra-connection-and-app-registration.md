---
id: T249
type: task
status: planned
parent_epic: E006
parent_feature: F063
parent_story: S125
depends_on: [S125]
owned_paths: [services/api/migrations/*_entra_*.sql, crates/domain/src/entra/**, services/api/src/entra/**, testing/features/F063/api/**, testing/features/F063/database/**]
feature_flag: F063_FEATURE
branch: t249-entra-connection-and-app-registration
started_at: null
finished_at: null
---

# T249 — Entra connection and app registration

## Identity

- Parent story: `S125` Entra sign-in and directory
- Owner: platform
- Branch: `t249-entra-connection-and-app-registration`
- Decision references: `docs/architecture-decisions.md` sections 2, 7; `docs/capability-contracts.md` row F063

## Objective

Create the `entra` schema and the connection lifecycle: sealed credentials, cloud selection, capability set, the connection test that reports granted and missing consent scopes, the read that is safe before a connection exists, and revocation that leaves every other sign-in method and every OpsHub user and group intact.

## Specification

- Owned paths: `services/api/migrations/<ts>_entra_create_tables.sql` and `.down.sql`; `crates/domain/src/entra/{mod.rs, connection.rs, cloud.rs, graph.rs, errors.rs, service.rs}`; `services/api/src/entra/{mod.rs, routes.rs, handlers_connection.rs, dto.rs}`
- Contract/input: `EntraConnectionRequest { directory_tenant_id: Uuid, client_id: Uuid, client_secret: Option<String>, certificate_thumbprint: Option<String>, cloud: Cloud, capabilities: Vec<Capability>, allowed_email_domains: Vec<String>, require_verified_domain: bool, sender_mailbox: Option<String> }` with `Idempotency-Key` and `If-Match`; `Cloud` is `global|us_gov|china`; `Capability` is `sign_in|group_sync|mail`.
- Output/behavior: `PUT /api/v1/entra/connection` upserts one row per tenant, seals the secret with AES-256-GCM under the F029 vault into `credential_key_id`, `credential_nonce`, `credential_ciphertext`, bumps `version`, publishes `entra.connected.v1`, writes the `entra.connect` audit row with the credential redacted, and returns `EntraConnectionResponse { status, capabilities, version, redirect_uri, last_test_at, last_error_class, per-capability state, last sync counts }` with no credential field. `POST /api/v1/entra/connection/test` requests a client-credentials token from the cloud's authority and reads `GET /v1.0/organization`, returning `TestResponse { ok, tenant_display_name, granted_scopes, missing_scopes, error_class }` under 10 s, computing `missing_scopes` per enabled capability (`User.Read.All` for `sign_in`, `GroupMember.Read.All` for `group_sync`, `Mail.Send` for `mail`), setting `status` to `active` or `needs_consent`, and writing `entra.test`. `GET /api/v1/entra/connection` answers `200` with `status: disconnected` and attempts no Graph call when no row exists. `DELETE` deletes tokens, reverts the F037 transport to SMTP, stops sync and Entra sign-in, publishes `entra.revoked.v1`, writes `entra.revoke`, and deletes no user or group. `graph.rs` is the only Graph client: authority and Graph host per `Cloud`, 10 s timeout, bounded retry, `Retry-After` on `429`/`503`, per-tenant concurrency 4, breaker opening 5 minutes after 5 consecutive failures, one `entra_mail_log` row per call. Error map: `BadCloud|BadGuid → 400 invalid`, `MissingConsent → 409 conflict` with `field_errors.capabilities`, `TokenExchangeFailed → 502 unavailable`, `Throttled → 429 rate_limited`, `NotFound → 404 not_found`, `AuthzError::Denied → 403 denied`. DDL creates `entra_connections`, `entra_group_map` and `entra_mail_log` with the checks, unique keys and indexes from ticket section 4.
- Dependencies: F029 vault for sealing; F037 for the transport revert; F038 `ActorContext`; F003 `identity-admin` permission; F004 secret manager and outbox.
- Feature flag: `F063_FEATURE` gates the routes; the migration runs regardless.

## TDD

- Failing test first: `testing/features/F063/api/connection_tests.rs::put_connection_seals_secret_and_returns_redirect_uri`, `::put_connection_rejects_unknown_cloud`, `::put_connection_rejects_malformed_guid_with_field_errors`, `::connection_response_never_contains_credential`, `::connection_get_without_connection_is_disconnected`, `::mail_capability_requires_sender_mailbox`, `::revoke_reverts_transport_and_publishes_revoked`, `::revoke_deletes_no_user_or_group`, `::member_cannot_read_or_write_connection`, `::foreign_tenant_connection_not_found`; `testing/features/F063/api/test_connection_tests.rs::test_connection_reports_missing_group_scope`, `::test_connection_returns_error_class_not_provider_string`, `::test_connection_completes_under_ten_seconds`; `testing/features/F063/api/graph_client_tests.rs::graph_client_honors_retry_after_on_429`, `::breaker_opens_after_five_consecutive_failures`, `::graph_call_logs_domain_only`; `testing/features/F063/database/migration_tests.rs::entra_tables_exist_with_constraints`, `::one_connection_per_tenant`, `::capabilities_subset_check_rejects_unknown`, `::group_map_cascades_on_connection_delete`, `::rollback_drops_entra_tables`
- Targeted command: `cargo xtask test-feature F063`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/entra.rs` with tenants A and B, an identity-admin and a member, one connection per cloud; mock Entra authority and mock Graph in `testing/harness/providers/entra/` serving token and `organization` with programmable `429`/`503`; vault stub with two key versions; fixed clock `2026-09-03T00:00:00Z`

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; routes registered behind the flag; OpenAPI regenerated without drift
- [ ] Redaction test proves no credential in any response, log, audit diff or export
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S125
- [ ] `finished_at` recorded
