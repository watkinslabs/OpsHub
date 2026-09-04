---
id: S102
type: story
status: planned
parent_epic: E008
parent_feature: F051
depends_on: [S101]
owned_paths: [crates/domain/src/workapps/**, crates/persistence/src/workapps/**, services/api/src/workapps/**, apps/web/src/features/workapps/**, testing/features/F051/**]
feature_flag: F051_FEATURE
branch: s102-role-experiences
started_at: null
finished_at: null
---

# S102 — Role experiences

## Identity

- Parent feature: `F051` WorkApps
- Owner: platform
- Branch: `s102-role-experiences`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 6, 10; `docs/capability-contracts.md` row F051

## Vertical slice

As a member holding an app role, I want to open the app at its slug and see only my role's pages with my landing page, with every embedded surface loading under my own permissions, and as an app admin I want a builder to compose pages and roles, preview as a role, publish, and restore versions, so that each participant gets a focused, safe experience.

Out of this slice: manifest validation and publish transaction (S101, already available); anonymous or external app access (F059).

## Requirements

- **SR-S102-01:** `GET /apps/{slug}` resolves the caller's roles through direct and F002 group membership, applies `filter_for_viewer`, returns only visible pages, the landing page, and `roles_held`, and never lists other roles' members; no role → `404 not_found`; unpublished app → `404` except admins receive the draft (covers FR-F051-05, NFR-F051-02).
- **SR-S102-02:** Archived apps and cross-tenant slugs return `404 not_found` from `/apps/{slug}`; pages whose source is soft-deleted are marked `unavailable` (FR-F051-07, FR-F051-11).
- **SR-S102-03:** `AppShell`, `AppNav`, and `PageFrame` render the manifest at `/apps/:slug` and `/apps/:slug/:pageId`, dispatch each page kind to the native embed component that calls its own F006/F013/F014/F021/F023/F050 endpoint under the viewer's session, and render denied, empty, unavailable, error, and offline states per page (FR-F051-06, FR-F051-12).
- **SR-S102-04:** `AppBuilderPage` with `PageListEditor`, `PageSourcePicker`, `RoleEditor`, `MemberPicker`, `PreviewAsRole`, `PublishDialog`, `VersionList`, and `VersionDiff` lets the admin edit the draft, preview the filtered manifest for a chosen role, publish with a note, and restore a version (FR-F051-12, FR-F051-13).
- **SR-S102-05:** Draft edits in the builder never change the served manifest until publish; the builder shows `draft_dirty` and the stale banner on `conflict` (FR-F051-08).
- **SR-S102-06:** `GET /apps/{slug}` responds under 300 ms p95 with 50 pages and 20 roles and the shell renders navigation within 500 ms p95; metrics `workapp_opened_total`, `workapp_page_denied_total` recorded (NFR-F051-01, NFR-F051-04).
- **SR-S102-07:** Shell and builder pass axe with zero serious violations; page reorder has keyboard equivalents; navigation exposes the current page (NFR-F051-03).

## Surfaces

- Infrastructure/container: none
- Rust service/API: `crates/domain/src/workapps/{viewer.rs, membership.rs}`; `services/api/src/workapps/{handlers_viewer.rs, viewer_routes.rs}`
- Data/migration: none new; uses tables from S101
- React/UI: `apps/web/src/features/workapps/{AppShell.tsx, AppNav.tsx, AppPage.tsx, PageFrame.tsx, embeds/SheetEmbed.tsx, embeds/FormEmbed.tsx, embeds/ReportEmbed.tsx, embeds/DashboardEmbed.tsx, embeds/DynamicViewEmbed.tsx, embeds/TextPage.tsx, AppSwitcher.tsx, AppBuilderPage.tsx, PageListEditor.tsx, PageSourcePicker.tsx, RoleEditor.tsx, MemberPicker.tsx, PreviewAsRole.tsx, PublishDialog.tsx, VersionList.tsx, VersionDiff.tsx, NewAppDialog.tsx, api.ts, hooks.ts, routes.ts}`
- Mocks/fixtures: published app fixture with four pages and two roles; MSW handlers for component tests including a 404 from the sheets endpoint for the vendor; Playwright uses the real API with seeded roles

## TDD harness

- Test path: `testing/features/F051/{api,frontend,e2e,accessibility,performance}/`
- Feature flag: `F051_FEATURE`
- Targeted command: `cargo xtask test-feature F051`
- Full command: `cargo xtask test-all`
- First failing tests: `viewer_manifest_filters_pages_by_role`, `viewer_without_role_not_found`, `viewer_manifest_omits_other_role_members`, `page_frame_shows_denied_when_source_forbidden`, `builder_reorder_by_keyboard`, `vendor_role_sees_two_pages`

## Exit criteria

- [ ] Requirement tests SR-S102-01 through SR-S102-07 written first and failing
- [ ] Tasks T203 and T204 complete; UI wired to real API through generated client and native embed components
- [ ] Unit, API, React, E2E, accessibility, permission, and performance tests pass
- [ ] Production call path named: `apps/web/src/features/workapps/AppShell.tsx` mounted at `/apps/:slug`; `AppBuilderPage.tsx` mounted at `/w/:workspaceId/workapps/:id`; `services/api/src/workapps/viewer_routes.rs` mounted at `/apps`
- [ ] Handoff evidence recorded in the F051 ticket
