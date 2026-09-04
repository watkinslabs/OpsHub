---
id: T113
type: task
status: planned
parent_epic: E006
parent_feature: F029
parent_story: S057
depends_on: [S057]
owned_paths: [services/api/migrations/*_integrations_*.sql, crates/domain/src/integrations/**, crates/persistence/src/integrations/**, services/api/src/integrations/**, services/worker/src/integrations/**, testing/features/F029/api/**, testing/features/F029/database/**]
feature_flag: F029_FEATURE
branch: t113-oauth-vault
started_at: null
finished_at: null
---

# T113 — OAuth vault

## Identity

- Parent story: `S057` OAuth connections
- Owner: platform
- Branch: `t113-oauth-vault`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 7; `docs/capability-contracts.md` row F029

## Objective

Create the `integrations` schema and implement the envelope-encrypted token vault, PKCE authorization start, state handling, callback exchange, refresh job, revocation, and connection list routes.

## Specification

- Owned paths: `services/api/migrations/<ts>_integrations_create_tables.sql` and `.down.sql`, `crates/domain/src/integrations/{mod.rs, provider.rs, connection.rs, vault.rs, oauth.rs, errors.rs, service.rs, http_client.rs}`, `crates/persistence/src/integrations/{mod.rs, provider_repository.rs, connection_repository.rs, oauth_token_repository.rs, oauth_state_repository.rs, event_repository.rs}`, `services/api/src/integrations/{mod.rs, routes.rs, handlers_provider.rs, handlers_connection.rs, handlers_callback.rs, dto.rs}`, `services/worker/src/integrations/{mod.rs, refresh.rs}`
- Contract/input: `StartConnectionRequest { provider, capabilities, display_name? }`; callback query `code`, `state`, `error?`; list query `{ cursor?, limit?, provider?, status? }`; secret manager keys `integrations/<provider>/client_id|client_secret` and `kms/tenant-data-key`.
- Output/behavior: routes `GET /api/v1/integrations/providers`, `GET /api/v1/integrations/connections`, `POST /api/v1/integrations/connections`, `GET /auth/integrations/{provider}/callback`, `DELETE /api/v1/integrations/connections/{id}`, `POST /api/v1/integrations/connections/{id}/refresh`; `vault.rs` seals with AES-256-GCM under a per-tenant data key wrapped by `kms::wrap`, stores `key_id` and `nonce`, supports `rewrap(old_key_id, new_key_id)`; `oauth.rs` builds the authorize URL with S256 PKCE and a 10-minute `state` in `oauth_states` (verifier sealed), consumes state once, exchanges the code through the provider adapter (T114), computes the missing scopes, writes `integration_connection_scopes` rows with `state` `granted` or `missing` plus `oauth_token_scopes` for the returned token set, and sets `active` or `limited`; `refresh.rs` calls `OauthTokenRepository::list_tokens_expiring_before(now + 5m)` every minute, renews, records the provider error class in `integration_connection_errors` and increments `refresh_failures` on error, sets `needs_reauth` at 3, notifies the owner through F037, pauses bindings, and clears the error row on success; revoke calls the adapter, deletes `oauth_tokens` (cascading `oauth_token_scopes`), sets `revoked`; events `integration.connected.v1`, `integration.refresh-failed.v1`, `integration.revoked.v1`; DTOs never include token fields and keep `capabilities`, `scopes`, `missing_scopes`, and `last_error` in their existing array and object shapes, reassembled by the repositories; DDL for the fourteen tables and indexes from ticket section 4, including the provider catalog seed and the `integration_connection_capabilities`, `integration_connection_scopes`, `oauth_token_scopes`, `integration_connection_errors`, and `integration_conflicts` child tables that replace the former array and `jsonb` columns.
- Data access: `vault.rs`, `oauth.rs`, `service.rs`, `connection.rs`, the four handler modules, and `refresh.rs` hold no SQL; every read and write goes through `IntegrationProviderRepository`, `IntegrationConnectionRepository`, `OauthTokenRepository`, `OauthStateRepository`, and `IntegrationEventRepository` in `crates/persistence/src/integrations/`, using the named queries listed in ticket section 4 with no generic query escape hatch, and the callback (state claim, connection update, capability and scope rows, token and token-scope rows) and revoke paths each commit in one `UnitOfWork` (decision section 2.1).
- Dependencies: F028 conventions and correlation IDs; F037 owner notification; F004 secret manager and job transport; F003 authz `Permission::IntegrationAdmin`.
- Feature flag: `F029_FEATURE` gates routes and the refresh job; migration runs regardless.

## TDD

- Failing test first: `testing/features/F029/api/vault_tests.rs::vault_seal_open_round_trip`, `::vault_rewrap_changes_key_id_only`, `::vault_tampered_ciphertext_rejected`; `testing/features/F029/api/connection_tests.rs::providers_list_reflects_deployment_credentials`, `::start_connection_returns_pkce_authorize_url`, `::callback_rejects_reused_state`, `::callback_rejects_expired_state`, `::callback_stores_sealed_tokens_and_publishes_connected`, `::callback_narrowed_scopes_writes_missing_scope_rows_and_sets_limited`, `::refresh_three_failures_sets_needs_reauth`, `::refresh_failure_records_error_class_row`, `::revoke_deletes_tokens_and_publishes_revoked`, `::connection_response_never_contains_tokens`, `::member_cannot_start_or_revoke_connection`, `::foreign_state_cannot_complete_on_other_tenant`; `testing/features/F029/database/migration_tests.rs::integrations_tables_exist_with_constraints`, `::oauth_tokens_cascade_on_connection_delete`, `::connection_scope_row_unique_per_scope`, `::connection_capability_must_exist_for_provider`, `::oauth_token_scopes_cascade_with_token_row`
- Targeted command: `cargo xtask test-feature F029`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/integrations.rs`; mock provider token endpoints; secret manager stub with two key versions; fixed clock

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; routes and job registered behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S057
- [ ] `finished_at` recorded
