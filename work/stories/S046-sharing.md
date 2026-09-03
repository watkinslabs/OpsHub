---
id: S046
type: story
status: planned
parent_epic: E005
parent_feature: F023
depends_on: [S045]
owned_paths: [crates/domain/src/dashboards/**, services/api/src/dashboards/**, services/worker/src/dashboards/**, apps/web/src/features/dashboards/**, testing/features/F023/**]
feature_flag: F023_FEATURE
branch: s046-sharing
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 4, 6, 7
- Capability contract: `docs/capability-contracts.md` row F023

# S046 — Sharing

## Identity

- Parent feature: `F023` Dashboard builder
- Owner: platform
- Branch: `s046-sharing`
- Decision references: `docs/architecture-decisions.md` sections 4, 6, 7; `docs/capability-contracts.md` row F023

## Vertical slice

As a dashboard editor, I want to build the layout in the browser, set a refresh policy, and share the dashboard with groups or an expiring link, and as a viewer or link guest I want every widget to show only what I may see with clear freshness, so that leadership reviews run from one governed page.

## Requirements

- **SR-S046-01:** Dashboards are F036 share targets: group and user shares grant `viewer` or `editor`, share links are read-only and expire within 30 days, and link guests receive widget data through the same `ViewerScope` with `denied` tiles for unreadable sources (FR-F023-09, NFR-F023-02).
- **SR-S046-02:** `refresh_policy` `interval` targets scopes read in the last 24 hours, `on_open` refreshes on `GET` when the cache is older than 60 s, and `refresh_override` may only shorten the interval (FR-F023-07).
- **SR-S046-03:** `DashboardBuilder` renders the 12-column `GridCanvas` with drag, resize, and keyboard placement, the `WidgetPalette` of twelve kinds, per-kind `WidgetConfigPanel`, and `RefreshPolicyForm`, validating limits client-side and saving with one `replaceWidgets` call (FR-F023-12, FR-F023-13).
- **SR-S046-04:** `DashboardViewer` renders registered widget renderers, `UnavailableWidget` for unregistered kinds, `DeniedWidget`, `FreshnessBadge` with `Refresh`, and the loading, empty, error, stale, computing, conflict, and offline states (FR-F023-12).
- **SR-S046-05:** `ShareDashboardDialog` reuses F036 components to add group and user shares and create or revoke a link, and shows `share_summary` (FR-F023-09).
- **SR-S046-06:** Grid interactions are keyboard operable with live-region announcements and pass axe with zero serious violations (NFR-F023-03).
- **SR-S046-07:** 40-widget `GET` p95 under 500 ms, cache hit p95 under 300 ms, full refresh under 60 s, and 60 fps drag with 40 widgets (NFR-F023-01).

## Surfaces

- Infrastructure/container: none
- Rust service/API: `crates/domain/src/dashboards/{sharing.rs, policy.rs}`; `services/api/src/dashboards/handlers_dashboard.rs` share summary and `on_open` trigger; `services/worker/src/dashboards/scheduler.rs` interval targeting
- Data/migration: none new
- React/UI: `apps/web/src/features/dashboards/{DashboardPage.tsx, DashboardViewer.tsx, DashboardBuilder.tsx, GridCanvas.tsx, WidgetFrame.tsx, WidgetPalette.tsx, WidgetConfigPanel.tsx, TableWidget.tsx, ReportEmbedWidget.tsx, TextWidget.tsx, ImageWidget.tsx, UnavailableWidget.tsx, DeniedWidget.tsx, FreshnessBadge.tsx, RefreshPolicyForm.tsx, ShareDashboardDialog.tsx, NewDashboardDialog.tsx, widgetRegistry.ts, layoutReducer.ts, api.ts, hooks.ts, routes.ts}`
- Mocks/fixtures: "Weekly review" fixture with five widgets; share-link guest fixture; MSW handlers for widget data in every status; 40-widget generator for performance

## TDD harness

- Test path: `testing/features/F023/{api,frontend,e2e,accessibility,performance}/`
- Feature flag: `F023_FEATURE`
- Targeted command: `cargo xtask test-feature F023`
- Full command: `cargo xtask test-all`
- First failing tests: `share_link_guest_cannot_mutate_or_refresh`, `share_link_guest_gets_denied_widget`, `on_open_policy_enqueues_when_cache_old`, `grid_keyboard_move_announces_position`, `viewer_renders_unavailable_for_unregistered_kind`, `dashboard_get_40_widgets_p95`

## Exit criteria

- [ ] Requirement tests SR-S046-01 through SR-S046-07 written first and failing
- [ ] Tasks T091 and T092 complete; UI wired to the real API through the generated `DashboardsApi` client
- [ ] Unit, API, React, E2E, accessibility, permission, and performance tests pass
- [ ] Production call path named: `apps/web/src/features/dashboards/DashboardPage.tsx` mounted at `/w/:workspaceId/dashboards/:dashboardId` and `/edit`; `/public/share/{token}` renders `DashboardViewer` for links
- [ ] Handoff evidence recorded in the F023 ticket
