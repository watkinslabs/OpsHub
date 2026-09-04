---
id: S057
type: story
status: planned
parent_epic: E006
parent_feature: F029
depends_on: [F028, F037]
owned_paths: [crates/domain/src/integrations/**, crates/persistence/src/integrations/**, services/api/src/integrations/**, services/worker/src/integrations/**, apps/web/src/features/integrations/**, services/api/migrations/*_integrations_*.sql, testing/features/F029/**]
feature_flag: F029_FEATURE
branch: s057-oauth-connections
started_at: null
finished_at: null
---

# S057 — OAuth connections

## Identity

- Parent feature: `F029` Microsoft/Google/Slack
- Owner: platform
- Branch: `s057-oauth-connections`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 7; `docs/capability-contracts.md` row F029

## Vertical slice

As an integration administrator, I want to connect Microsoft 365, Google Workspace, and Slack through OAuth with PKCE, have tokens stored encrypted and refreshed silently, see connection health, and revoke a connection, so that provider access is safe, auditable, and ready for notifications and sync.

## Requirements

- **SR-S057-01:** `GET /api/v1/integrations/providers` lists the three providers with capabilities, scopes, and `enabled` derived from deployment credentials, reading `integration_provider_capabilities` and `integration_provider_capability_scopes` through `IntegrationProviderRepository` and reassembling the JSON arrays the client already expects (covers FR-F029-01).
- **SR-S057-02:** `POST /api/v1/integrations/connections` returns an `authorize_url` with S256 PKCE and a 10-minute `state` bound to tenant, actor, and connection stored in `oauth_states`, and writes one `integration_connection_capabilities` row per requested capability, rejecting a capability the provider does not offer (FR-F029-02, NFR-F029-02).
- **SR-S057-03:** `GET /auth/integrations/{provider}/callback` validates and consumes `state`, exchanges the code through the provider adapter, seals tokens in the vault, writes `integration_connection_scopes` rows with `state = 'granted'` and, for any unmet scope, `state = 'missing'`, writes `oauth_token_scopes` for the returned token set, records the account, sets `active` or `limited`, and publishes `integration.connected.v1`; the connection row, its scope rows, and the token rows are written in one `UnitOfWork` (FR-F029-03, FR-F029-04).
- **SR-S057-04:** The `refresh` job and `POST /refresh` renew tokens 5 minutes before expiry; a failure upserts the `integration_connection_errors` row with the provider error class and three failures set `needs_reauth`, publish `integration.refresh-failed.v1`, notify the owner, and pause syncs; a success clears the error row (FR-F029-05).
- **SR-S057-05:** `DELETE` revokes at the provider, deletes the `oauth_tokens` row with its cascaded `oauth_token_scopes`, sets `revoked`, and publishes `integration.revoked.v1` (FR-F029-06).
- **SR-S057-06:** `GET /api/v1/integrations/connections` pages and filters by `provider` and `status`, assembles `capabilities`, `scopes`, `missing_scopes`, and `last_error` from the child tables in one batched read per page, and never exposes token material (FR-F029-07, FR-F029-04).
- **SR-S057-07:** Typed adapters for the three providers implement token exchange, refresh, and revoke through the shared `HttpClient` with timeout, retry, `Retry-After`, and `integration_events` logging (FR-F029-13).
- **SR-S057-08:** Members are denied, foreign-tenant IDs return `not_found`, and a state from tenant A cannot complete on tenant B (FR-F029-14).
- **SR-S057-09:** The integrations page shows provider cards, the OAuth popup hand-off, connection states, `Reconnect`, and `Revoke` (FR-F029-15, NFR-F029-03).

## Surfaces

- Infrastructure/container: provider client credentials via the F004 secret manager keys `integrations/<provider>/client_id|client_secret`; fixed redirect URI per deployment
- Data access: `crates/persistence/src/integrations/{mod.rs, provider_repository.rs, connection_repository.rs, oauth_token_repository.rs, oauth_state_repository.rs, event_repository.rs}` hold every SQL statement for this slice; `crates/domain/src/integrations`, the `services/api/src/integrations` handlers, and the `services/worker/src/integrations/refresh.rs` job depend on the repository traits and contain no `sqlx::query*` call or connection, and the callback and revoke paths run their multi-table writes in one `UnitOfWork` (decision section 2.1)
- Rust service/API: `crates/domain/src/integrations/{provider.rs, connection.rs, vault.rs, oauth.rs, errors.rs, service.rs, http_client.rs, adapters/{mod.rs, microsoft365.rs, google.rs, slack.rs}}`; `services/api/src/integrations/{routes.rs, handlers_provider.rs, handlers_connection.rs, handlers_callback.rs, dto.rs}`; `services/worker/src/integrations/{mod.rs, refresh.rs}`
- Data/migration: `services/api/migrations/<ts>_integrations_create_tables.sql` creating the fourteen tables and indexes from ticket section 4, seeding the provider catalog rows, and creating the `integration_connection_capabilities`, `integration_connection_scopes`, `oauth_token_scopes`, `integration_connection_errors`, and `integration_conflicts` child tables that replace the former array and `jsonb` columns
- React/UI: `apps/web/src/features/integrations/{IntegrationsPage.tsx, ProviderCard.tsx, ConnectionTable.tsx, ConnectionDetail.tsx, OauthPopup.tsx, api.ts, hooks.ts, routes.ts}`
- Mocks/fixtures: `testing/fixtures/integrations.rs`; mock provider servers in `testing/harness/providers/` for token exchange, refresh, and revoke; secret manager stub with rotatable keys

## TDD harness

- Test path: `testing/features/F029/{api,database,frontend}/`
- Feature flag: `F029_FEATURE`
- Targeted command: `cargo xtask test-feature F029`
- Full command: `cargo xtask test-all`
- First failing tests: `providers_list_reflects_deployment_credentials`, `start_connection_returns_pkce_authorize_url`, `callback_rejects_reused_state`, `callback_stores_sealed_tokens_and_publishes_connected`, `callback_narrowed_scopes_writes_missing_scope_rows_and_sets_limited`, `refresh_three_failures_sets_needs_reauth`, `revoke_deletes_tokens_and_publishes_revoked`, `member_cannot_start_or_revoke_connection`

## Exit criteria

- [ ] Requirement tests SR-S057-01 through SR-S057-09 written first and failing
- [ ] Tasks T113 and T114 complete and wired through `services/api` router and `services/worker` registry
- [ ] Unit, API, database, React, and permission tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/integrations/routes.rs` mounted in `services/api/src/router.rs` (`/api/v1/integrations`, `/auth/integrations`); `services/worker/src/integrations/refresh.rs` registered in `services/worker/src/registry.rs`
- [ ] Handoff evidence recorded in the F029 ticket
