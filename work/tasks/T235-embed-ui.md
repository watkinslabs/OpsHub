---
id: T235
type: task
status: planned
parent_epic: E008
parent_feature: F059
parent_story: S118
depends_on: [S118]
owned_paths: [crates/domain/src/publishing/**, crates/persistence/src/publishing/**, services/api/src/publishing/**, apps/web/src/features/publishing/**, testing/features/F059/api/**, testing/features/F059/frontend/**]
feature_flag: F059_FEATURE
branch: t235-embed-ui
started_at: null
finished_at: null
---

# T235 — Embed UI

## Identity

- Parent story: `S118` Embeds/access
- Owner: platform
- Branch: `t235-embed-ui`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 4, 6; `docs/capability-contracts.md` row F059

## Objective

Deliver the embed route with origin enforcement and CSP, tenant-scoped access, view analytics, rate limits, and the publish dialog, publications list, and public and embed render pages.

## Specification

- Owned paths: `crates/domain/src/publishing/{embed.rs, origin.rs, views.rs, rate_limit.rs}`, `services/api/src/publishing/{handlers_embed.rs, middleware_token_reject.rs}`, `apps/web/src/features/publishing/{PublishDialog.tsx, TokenRevealPanel.tsx, EmbedSnippet.tsx, OriginListEditor.tsx, PublicationsListPage.tsx, PublicationRow.tsx, FreshnessBanner.tsx, PublicRenderPage.tsx, EmbedRenderPage.tsx, PublicDashboard.tsx, PublicView.tsx, PublicReport.tsx, PublicErrorState.tsx, api.ts, hooks.ts, routes.ts}`
- Contract/input: `GET /embed/{token}` with `Origin`, `Referer`, or signed `origin` query; `access: tenant` session check; generated `PublishingApi` client; `postMessage` payload `{ type: "opshub-embed-height", height }`.
- Output/behavior: embed response carries `Content-Security-Policy: frame-ancestors <origins>` and no `X-Frame-Options`; unlisted origin renders the denied state; disabled embed returns `404`; tenant access from another tenant returns `404`; `record_view` samples one row per token per minute and throttles `publication.viewed.v1` to one per token per 5 minutes; rate limiting 60/min per token and 600/min per client with `Retry-After`; `middleware_token_reject` rejects publication tokens on `/api/v1/*` with `403` and increments the metric; UI renders the publish dialog with one-time token reveal and iframe snippet, origin editor validating `https://` origins, list with status and view counts, and public and embed pages with dashboard, view, report renderers, freshness banner, error, expired, denied-origin, and empty states; telemetry per ticket section 4.
- Dependencies: T234 token resolution and public render; F038 `rate_limit_buckets`; F013, F021, F023 client types for payload rendering.
- Feature flag: `F059_FEATURE` read through `useFlag`; public routes return not-found when off.

## TDD

- Failing test first: `testing/features/F059/api/embed_tests.rs::embed_sets_frame_ancestors_from_origins`, `::embed_unlisted_origin_denied_state`, `::embed_disabled_not_found`, `::tenant_access_other_tenant_not_found`, `::view_rows_sampled_per_minute`, `::render_rate_limited_after_60_per_minute`, `::token_on_api_route_denied`; `testing/features/F059/frontend/PublishDialog.test.tsx::publish_dialog_reveals_token_once`, `::origin_editor_rejects_http`, `PublicRenderPage.test.tsx::shows_freshness_banner_when_stale`, `::shows_error_state_with_reason`, `EmbedRenderPage.test.tsx::posts_height_only_to_allowed_origin`
- Targeted command: `cargo xtask test-feature F059`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: MSW handlers for render states; jsdom `window.parent.postMessage` spy; fixed client-hash salt

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Embed route mounted outside session middleware; publish dialog reachable from view, report, and dashboard `Share` menus
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S118
- [ ] `finished_at` recorded
