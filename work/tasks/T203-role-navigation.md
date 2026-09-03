---
id: T203
type: task
status: planned
parent_epic: E008
parent_feature: F051
parent_story: S102
depends_on: [S102]
owned_paths: [crates/domain/src/workapps/**, services/api/src/workapps/**, apps/web/src/features/workapps/**, testing/features/F051/api/**, testing/features/F051/frontend/**]
feature_flag: F051_FEATURE
branch: t203-role-navigation
started_at: null
finished_at: null
---

# T203 — Role navigation

## Identity

- Parent story: `S102` Role experiences
- Owner: platform
- Branch: `t203-role-navigation`
- Decision references: `docs/architecture-decisions.md` sections 3, 4, 6; `docs/capability-contracts.md` row F051

## Objective

Implement the role-filtered viewer manifest route and build the app shell, navigation, native page embeds, and the builder with preview, publish, and version restore wired to the real API.

## Specification

- Owned paths: `crates/domain/src/workapps/{viewer.rs, membership.rs}`, `services/api/src/workapps/{handlers_viewer.rs, viewer_routes.rs}`, `apps/web/src/features/workapps/{AppShell.tsx, AppNav.tsx, AppPage.tsx, PageFrame.tsx, embeds/SheetEmbed.tsx, embeds/FormEmbed.tsx, embeds/ReportEmbed.tsx, embeds/DashboardEmbed.tsx, embeds/DynamicViewEmbed.tsx, embeds/TextPage.tsx, AppSwitcher.tsx, AppBuilderPage.tsx, PageListEditor.tsx, PageSourcePicker.tsx, RoleEditor.tsx, MemberPicker.tsx, PreviewAsRole.tsx, PublishDialog.tsx, VersionList.tsx, VersionDiff.tsx, NewAppDialog.tsx, api.ts, hooks.ts, routes.ts}`
- Contract/input: `GET /apps/{slug}` with the session context; `filter_for_viewer(manifest, roles_held)`; generated `WorkAppsApi`; route params `slug`, `pageId`, `workspaceId`, `id`; `preview_role_id` query honoured for admins on the viewer route.
- Output/behavior: viewer route resolves roles through direct membership and F002 groups, returns `ViewerManifestResponse { app, pages, landing_page_id, roles_held }` with other roles' members omitted, `404` for no role, unpublished (non-admin), archived, or foreign tenant, and marks soft-deleted sources `unavailable`; `AppShell` renders `AppNav` (labelled `nav`, current page state, drawer under 960 px) and `PageFrame`, which mounts the native embed component that fetches through its own feature API with the viewer's session and shows denied, empty, unavailable, error, and offline states; builder edits pages (keyboard reorder with `Alt+Arrow`), roles, previews as role via the viewer route, publishes with a note, and restores from `VersionList`; states loading, error with correlation ID, denied, stale, offline, module-not-entitled; telemetry `workapp_opened`, `workapp_page_viewed`, `workapp_page_denied`, `workapp_published`, `workapp_restored_version`.
- Dependencies: T202 publish; embed components from F006/F013/F014/F021/F023/F050 features exported for reuse; F048 `useModuleAllowed('workapps')` and `ModuleNotEntitled`; F005 workspace shell for the `Apps` node and header switcher.
- Feature flag: `F051_FEATURE` read through the flag hook; routes not registered when off.

## TDD

- Failing test first: `testing/features/F051/api/viewer_tests.rs::viewer_manifest_filters_pages_by_role`, `::viewer_without_role_not_found`, `::viewer_manifest_omits_other_role_members`, `::viewer_group_membership_grants_role`, `::viewer_archived_app_not_found`, `::viewer_preview_role_admin_only`; `testing/features/F051/frontend/AppShell.test.tsx::renders_role_filtered_nav_and_landing_page`, `PageFrame.test.tsx::shows_denied_when_source_forbidden`, `::embed_requests_use_source_endpoint`, `PageListEditor.test.tsx::reorders_with_keyboard`, `RoleEditor.test.tsx::landing_page_limited_to_visible_pages`, `PublishDialog.test.tsx::shows_warnings_for_empty_roles`
- Targeted command: `cargo xtask test-feature F051`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: MSW handlers from the published app fixture; sheets endpoint returning 404 for the vendor; role-switching session helper

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] API and component lanes pass; viewer router mounted in `services/api/src/router.rs` at `/apps`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S102
- [ ] `finished_at` recorded
