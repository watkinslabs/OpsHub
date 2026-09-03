# F051 e2e cases

File: `testing/features/F051/e2e/workapp.spec.ts`. Playwright against seeded tenant. Flag `F051_FEATURE`.

- `build_publish_vendor_sees_two_pages` — FR-F051-01, FR-F051-02, FR-F051-03, FR-F051-04, FR-F051-05, FR-F051-12: admin creates `Vendor onboarding`, adds four pages, two roles, previews as `Vendor`, publishes `Initial release`; vendor user opens `/apps/vendor-onboarding`, lands on `Intake form`, nav shows two items.
- `embed_requests_hit_source_endpoints_with_viewer_session` — FR-F051-06, NFR-F051-02: network capture shows the vendor's `My vendors` page calling `/api/v1/dynamic-views/{id}/rows` with the vendor session and no `/workapps` data call.
- `forbidden_source_shows_denied_frame` — FR-F051-06: vendor given `Status board` page opens it; sheets API returns 404; frame shows denied state.
- `draft_edit_does_not_change_served_app` — FR-F051-08: admin removes `KPIs` in the draft; procurement reload still shows `KPIs`; builder shows `Unpublished changes`.
- `restore_version_one` — FR-F051-13: after version 2, admin restores version 1 → toast `Published version 3`; procurement sees version 1 pages.
- `no_role_member_gets_not_found` — FR-F051-05: member without role opens the slug → not-found page.
- `flag_off_hides_apps` — FR-F051-10: with `F051_FEATURE` off, `/apps/vendor-onboarding` is not-found and the workspace tree has no `Apps` node.

Evidence: Playwright traces and videos under `testing/evidence/F051/e2e/`.
