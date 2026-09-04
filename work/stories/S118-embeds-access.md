---
id: S118
type: story
status: planned
parent_epic: E008
parent_feature: F059
depends_on: [S117]
owned_paths: [crates/domain/src/publishing/**, crates/persistence/src/publishing/**, services/api/src/publishing/**, apps/web/src/features/publishing/**, testing/features/F059/**]
feature_flag: F059_FEATURE
branch: s118-embeds-access
started_at: null
finished_at: null
---

# S118 — Embeds/access

## Identity

- Parent feature: `F059` Publishing/embedding
- Owner: platform
- Branch: `s118-embeds-access`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 6, 9; `docs/capability-contracts.md` row F059

## Vertical slice

As a publisher and an external viewer, I want origin-restricted embeds, tenant-scoped access, view analytics, rate limits, and a publish dialog with a one-time token reveal, so that publications are safe to place on intranet pages and lobby screens.

## Requirements

- **SR-S118-01:** `GET /embed/{token}` renders the snapshot in an iframe-safe document with `Content-Security-Policy: frame-ancestors` assembled by space-joining the `origin` column of `PublicationRepository::list_allowed_origins` ordered by `origin`, byte-identical to the header the former array produced, renders the `denied` state when `Origin`, `Referer`, or the signed `origin` query matches no `publication_allowed_origins` row, and returns `404` when embedding is disabled (FR-F059-07).
- **SR-S118-02:** `access: tenant` publications require a same-tenant session plus target read; another tenant's session receives `404` (FR-F059-06).
- **SR-S118-03:** Every render records a sampled `publication_views` row (one per token per minute) through `PublicationViewRepository::record_sampled_view` with salted client hash and referrer origin in typed columns and publishes `publication.viewed.v1` at most once per token per 5 minutes (FR-F059-10).
- **SR-S118-04:** Public and embed routes enforce 60 requests per minute per token and 600 per client address with `429 rate_limited` and `Retry-After`; publication tokens presented to `/api/v1/*` are rejected with `403 denied` and counted in `publication_token_rejected_total` (FR-F059-12, FR-F059-14).
- **SR-S118-05:** `PublishDialog` shows the token and iframe snippet once with copy actions, edits expiry, access, origins (sent and received as the unchanged `allowed_origins` array, persisted as `publication_allowed_origins` rows), refresh interval, and freshness display; `PublicationsListPage` shows status, `view_count_7d`, `last_viewed_at`, and `Rotate` and `Revoke` actions (FR-F059-13).
- **SR-S118-06:** `PublicRenderPage` and `EmbedRenderPage` render dashboards, views, and reports read-only with the freshness banner, error, expired, denied-origin, and empty states, poll every `refresh_interval_s`, and post iframe height only to allowed origins (FR-F059-03, FR-F059-05, NFR-F059-03).
- **SR-S118-07:** Renders of a 12-widget dashboard meet NFR-F059-01 and a 10,000-row view refresh completes under 10 s p95.

## Surfaces

- Infrastructure/container: rate-limit buckets reuse the F038 `rate_limit_buckets` store keyed by token hash and client hash, reached through F038's `RateLimitRepository` because that table belongs to F038's aggregate and no publishing class writes it
- Data access: `crates/persistence/src/publishing/{publication_repository.rs, token_repository.rs, view_repository.rs}` serve this slice — `list_allowed_origins` for the origin check and CSP, `find_by_token_hash` for the unauthenticated embed and public routes, `record_sampled_view`, `count_views_since`, and `last_viewed_at` for analytics; `embed.rs`, `origin.rs`, `views.rs`, `rate_limit.rs`, `handlers_embed.rs`, and `middleware_token_reject.rs` hold no SQL and no connection (decision section 2.1)
- Rust service/API: `crates/domain/src/publishing/{embed.rs, origin.rs, views.rs, rate_limit.rs}`; `services/api/src/publishing/{handlers_embed.rs, middleware_token_reject.rs}`
- Data/migration: none new; reads `publications`, `publication_allowed_origins`, and `publication_tokens` and appends to `publication_views`, all created by S117's migration
- React/UI: `apps/web/src/features/publishing/{PublishDialog.tsx, TokenRevealPanel.tsx, EmbedSnippet.tsx, OriginListEditor.tsx, PublicationsListPage.tsx, PublicationRow.tsx, FreshnessBanner.tsx, PublicRenderPage.tsx, EmbedRenderPage.tsx, PublicDashboard.tsx, PublicView.tsx, PublicReport.tsx, PublicErrorState.tsx, api.ts, hooks.ts, routes.ts}`
- Mocks/fixtures: Playwright second origin `https://host.test` serving an iframe host page; MSW handlers for render states; fixed client-hash salt

## TDD harness

- Test path: `testing/features/F059/{api,frontend,e2e,accessibility,performance}/`
- Feature flag: `F059_FEATURE`
- Targeted command: `cargo xtask test-feature F059`
- Full command: `cargo xtask test-all`
- First failing tests: `embed_sets_frame_ancestors_from_origins`, `embed_unlisted_origin_denied_state`, `tenant_access_other_tenant_not_found`, `token_on_api_route_denied`, `render_rate_limited_after_60_per_minute`, `publish_dialog_reveals_token_once`, `render_dashboard_12_widgets_p95`, `removed_origin_row_denies_embed`

## Exit criteria

- [ ] Requirement tests SR-S118-01 through SR-S118-07 written first and failing
- [ ] Tasks T235 and T236 complete; UI wired to real API through generated client
- [ ] Unit, API, React, E2E, accessibility, permission, and performance tests pass
- [ ] Production call path named: `apps/web/src/features/publishing/PublicRenderPage.tsx` mounted at `/public/publications/:token` and `EmbedRenderPage.tsx` at `/embed/:token`; `PublishDialog.tsx` opened from the `Share` menu of view, report, and dashboard pages
- [ ] Handoff evidence recorded in the F059 ticket
