---
id: T114
type: task
status: planned
parent_epic: E006
parent_feature: F029
parent_story: S057
depends_on: [T113]
owned_paths: [crates/domain/src/integrations/**, crates/persistence/src/integrations/**, services/api/src/integrations/**, apps/web/src/features/integrations/**, testing/features/F029/api/**, testing/features/F029/frontend/**]
feature_flag: F029_FEATURE
branch: t114-provider-adapters
started_at: null
finished_at: null
---

# T114 — Provider adapters

## Identity

- Parent story: `S057` OAuth connections
- Owner: platform
- Branch: `t114-provider-adapters`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 6, 7; `docs/capability-contracts.md` row F029

## Objective

Implement the typed Microsoft 365, Google Workspace, and Slack adapters for OAuth exchange, refresh, revoke, and account lookup over the shared HTTP client, and build the integrations page with provider cards, the OAuth popup hand-off, and connection states.

## Specification

- Owned paths: `crates/domain/src/integrations/adapters/{mod.rs, traits.rs, microsoft365.rs, google.rs, slack.rs}`, `crates/domain/src/integrations/http_client.rs`, `crates/persistence/src/integrations/event_repository.rs`, `apps/web/src/features/integrations/{IntegrationsPage.tsx, ProviderCard.tsx, ConnectionTable.tsx, ConnectionDetail.tsx, OauthPopup.tsx, api.ts, hooks.ts, routes.ts}`
- Contract/input: trait `OauthAdapter { authorize_url(scopes, state, challenge), exchange(code, verifier) -> TokenSet, refresh(refresh_token) -> TokenSet, revoke(token), account() -> ExternalAccount }`; provider endpoints: Microsoft `login.microsoftonline.com/common/oauth2/v2.0/{authorize,token}` and Graph `/me`, Google `accounts.google.com/o/oauth2/v2/auth`, `oauth2.googleapis.com/{token,revoke}`, `openidconnect.googleapis.com/v1/userinfo`, Slack `slack.com/oauth/v2/authorize`, `slack.com/api/{oauth.v2.access,auth.test,auth.revoke}`; base URLs overridable for the mock servers.
- Output/behavior: `http_client.rs` wraps `reqwest` with 10 s timeout, 3 retries with exponential backoff on 5xx and network errors, `429` handling that sleeps for `Retry-After` (max 60 s), and an `integration_events` row per call (`kind: call`, `operation`, `status_code`, `duration_ms`) with tracing span `connection_id`; adapters map provider error bodies to `IntegrationError` classes (`invalid_grant → NeedsReauth`, `access_denied → ExchangeFailed`); scopes per capability: Microsoft `offline_access ChannelMessage.Send Calendars.ReadWrite Chat.Read`, Google `calendar.events chat.messages openid email`, Slack `chat:write channels:history users:read.email`; UI renders provider cards with `enabled` state, opens `authorize_url` in a popup, listens for the callback redirect, refetches connections, announces the result, and shows `active`, `limited` (missing scopes), `needs_reauth`, `error`, `revoked` rows with `Reconnect`, `Refresh now`, and `Revoke` actions; telemetry `integration_connect_started`, `integration_connected`, `integration_reconnect_clicked`.
- Data access: the adapters and `http_client.rs` hold no SQL and open no connection; the per-call log row is appended by `IntegrationEventRepository::append_call_event` in `crates/persistence/src/integrations/event_repository.rs`, and the page's `limited` row reads its missing scopes from the `integration_connection_scopes` rows the connection list response already carries (decision section 2.1).
- Dependencies: T113 vault, routes, and state handling; F028 generated client; F037 channel registry (registration wired in T115).
- Feature flag: `F029_FEATURE` gates the admin route.

## TDD

- Failing test first: `testing/features/F029/api/adapter_tests.rs::microsoft_exchange_parses_token_set_and_account`, `::google_refresh_invalid_grant_maps_to_needs_reauth`, `::slack_revoke_calls_auth_revoke`, `::http_client_retries_5xx_three_times`, `::http_client_honors_retry_after_on_429`, `::http_client_logs_integration_event_per_call`; `testing/features/F029/frontend/ProviderCard.test.tsx::disabled_provider_shows_missing_credentials`, `OauthPopup.test.tsx::callback_result_refetches_and_announces`, `ConnectionTable.test.tsx::limited_row_lists_missing_scopes`
- Targeted command: `cargo xtask test-feature F029`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: mock provider servers with recorded token, userinfo, `auth.test`, and error responses; MSW handlers for the page

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Adapters registered in `crates/domain/src/integrations/adapters/mod.rs` and used by the callback and refresh paths
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S057
- [ ] `finished_at` recorded
