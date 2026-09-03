# F051 frontend cases

File: `testing/features/F051/frontend/{AppShell.test.tsx,PageFrame.test.tsx,PageListEditor.test.tsx,RoleEditor.test.tsx,PublishDialog.test.tsx,VersionList.test.tsx}`. Vitest with MSW. Flag `F051_FEATURE`.

- `AppShell.test.tsx::renders_role_filtered_nav_and_landing_page` — FR-F051-12: vendor manifest renders two nav items and mounts `Intake form` as landing.
- `AppShell.test.tsx::shows_empty_state_when_no_pages_for_role` — FR-F051-12: manifest with zero pages shows `This app has no pages for your role`; admin variant links to the builder.
- `AppShell.test.tsx::shows_not_found_for_no_role` — FR-F051-05: 404 renders the not-found page without app name.
- `AppShell.test.tsx::module_not_entitled_panel` — FR-F051-10: `useModuleAllowed('workapps')` false renders the shared panel.
- `PageFrame.test.tsx::shows_denied_when_source_forbidden` — FR-F051-06: `SheetEmbed` receiving 404 from the sheets endpoint renders `You do not have access to this content` without the sheet name.
- `PageFrame.test.tsx::embed_requests_use_source_endpoint` — FR-F051-06: sheet page calls `/api/v1/sheets/{id}/rows`, form page calls `/api/v1/forms/{id}`, dashboard page calls `/api/v1/dashboards/{id}`; no `/workapps` data proxy call.
- `PageFrame.test.tsx::unavailable_source_shows_empty_state` — FR-F051-05: page marked `unavailable` shows `This content is no longer available`.
- `PageListEditor.test.tsx::reorders_with_keyboard` — NFR-F051-03: `Alt+ArrowDown` moves the focused page and calls `setPages` with new positions; rolls back on 409 with stale banner.
- `PageListEditor.test.tsx::blocks_51st_page` — FR-F051-02: add button disabled at 50 with explanation.
- `RoleEditor.test.tsx::landing_page_limited_to_visible_pages` — FR-F051-03: landing select lists only pages checked for that role.
- `PublishDialog.test.tsx::shows_warnings_for_empty_roles` — FR-F051-04: publish response warnings rendered; toast `Published version 3`.
- `VersionList.test.tsx::shows_diff_and_restores` — FR-F051-13: version 2 vs 1 diff lists added page `KPIs`; `Restore this version` calls `publish` with `version_number: 1`.
- `AppShell.test.tsx::offline_disables_builder_mutations` — FR-F051-12: `navigator.onLine=false` shows badge and disables publish and save.

Evidence: Vitest JUnit under `testing/evidence/F051/frontend/`.
