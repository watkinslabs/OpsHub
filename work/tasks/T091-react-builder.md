---
id: T091
type: task
status: planned
parent_epic: E005
parent_feature: F023
parent_story: S046
depends_on: [S046]
owned_paths: [crates/domain/src/dashboards/**, services/api/src/dashboards/**, services/worker/src/dashboards/**, apps/web/src/features/dashboards/**, testing/features/F023/api/**, testing/features/F023/frontend/**]
feature_flag: F023_FEATURE
branch: t091-react-builder
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 4, 6, 7
- Capability contract: `docs/capability-contracts.md` row F023

# T091 — React builder

## Identity

- Parent story: `S046` Sharing
- Owner: platform
- Branch: `t091-react-builder`
- Decision references: `docs/architecture-decisions.md` sections 4, 6, 7; `docs/capability-contracts.md` row F023

## Objective

Build the dashboard builder, viewer, widget renderer registry, share dialog, and refresh policy form, and wire sharing, `on_open`, and interval targeting on the server so the whole page works for editors, viewers, and link guests.

## Specification

- Owned paths: `crates/domain/src/dashboards/{sharing.rs, policy.rs}`, `services/api/src/dashboards/handlers_dashboard.rs` (share summary, `on_open` trigger), `services/worker/src/dashboards/scheduler.rs`, `apps/web/src/features/dashboards/{DashboardPage.tsx, DashboardViewer.tsx, DashboardBuilder.tsx, GridCanvas.tsx, WidgetFrame.tsx, WidgetPalette.tsx, WidgetConfigPanel.tsx, TableWidget.tsx, ReportEmbedWidget.tsx, TextWidget.tsx, ImageWidget.tsx, UnavailableWidget.tsx, DeniedWidget.tsx, FreshnessBadge.tsx, RefreshPolicyForm.tsx, ShareDashboardDialog.tsx, NewDashboardDialog.tsx, widgetRegistry.ts, layoutReducer.ts, api.ts, hooks.ts, routes.ts}`
- Contract/input: generated `DashboardsApi` client; F036 share components and `POST /api/v1/shares` with `target_kind = dashboard`; route params `workspaceId`, `dashboardId`; `/public/share/{token}` context from F036.
- Output/behavior: `sharing.rs` resolves read access through direct ACL, F036 shares, or a valid link and marks link actors read-only; `policy.rs` enforces `refresh_override ≤ interval` and `on_open` enqueue when cache is older than 60 s; `scheduler.rs` targets scopes read in 24 hours; `GridCanvas` implements drag, resize, keyboard move (`Arrow`), resize (`Shift+Arrow`), delete with confirm, and a live region announcing "Table moved to column 4 row 2"; `layoutReducer.ts` keeps 20 undo steps and validates with the same limits as the server; `WidgetPalette` lists twelve kinds; `WidgetConfigPanel` renders per-kind forms; `widgetRegistry.ts` exposes `registerWidgetRenderer` and falls back to `UnavailableWidget`; `DashboardViewer` polls `getWidgetData` every 3 s while computing and shows `FreshnessBadge`; responsive column folding per ticket section 3; telemetry `dashboard_created`, `dashboard_opened`, `widget_added`, `widgets_saved`, `dashboard_refresh_requested`, `dashboard_shared`, `widget_denied_shown`.
- Dependencies: T090 routes and worker; F036 share dialog components; F005 workspace shell.
- Feature flag: `F023_FEATURE` read through the flag hook; routes are not registered when off.

## TDD

- Failing test first: `testing/features/F023/api/sharing_tests.rs::share_link_guest_cannot_mutate_or_refresh`, `::share_link_guest_gets_denied_widget`, `::on_open_policy_enqueues_when_cache_old`, `::refresh_override_longer_than_interval_invalid`; `testing/features/F023/frontend/GridCanvas.test.tsx::grid_keyboard_move_announces_position`, `::overlap_blocked_client_side`; `testing/features/F023/frontend/DashboardViewer.test.tsx::viewer_renders_unavailable_for_unregistered_kind`, `::viewer_shows_denied_tile`, `::stale_badge_refreshes_widget`; `testing/features/F023/frontend/ShareDashboardDialog.test.tsx::creates_expiring_link`
- Targeted command: `cargo xtask test-feature F023`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: MSW handlers for widget data in all six statuses; share-link guest fixture; F036 component stubs

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Component tests pass; `registerWidgetRenderer` exported for F024
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S046
- [ ] `finished_at` recorded
