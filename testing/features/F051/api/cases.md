# F051 api cases

File: `testing/features/F051/api/{app_tests.rs,manifest_tests.rs,publish_tests.rs,viewer_tests.rs,security_tests.rs}`. Flag `F051_FEATURE`.

- `app_create_rejects_duplicate_slug` — FR-F051-01: second app with slug `vendor-onboarding` (case differs) → 409 `conflict`, `field_errors.slug`.
- `app_create_rejects_invalid_slug` — FR-F051-01: `Vendor_App`, `ab`, and a 41-char slug → 400 `field_errors.slug`.
- `app_limit_reached_conflicts` — FR-F051-10: sixth app under `max_apps: 5` → 409 `field_errors.limit = "max_apps"`.
- `app_not_entitled_denied` — FR-F051-10: tenant without `workapps` entitlement → 403 `field_errors.module` before the handler.
- `app_list_filters_and_pages` — FR-F051-07: 60 apps, `limit=25`, three pages; `status=published` and `name_prefix=Vendor` filters.
- `app_archive_hides_slug_keeps_versions` — FR-F051-07: PATCH `status: archived` → `/apps/{slug}` 404; `GET /workapps/{id}` still lists versions.
- `non_admin_mutation_denied` — FR-F051-11: member without `app-admin` PUT pages → 403; GET draft → 404.
- `pages_reject_51st_page` — FR-F051-02: 51 pages → 400 `field_errors.pages = "max_50"`.
- `pages_reject_source_of_wrong_kind` — FR-F051-02: kind `form` with a sheet id → 400 `pages[2].source_id = "kind_mismatch"`.
- `pages_reject_source_from_other_workspace` — FR-F051-02: sheet in another workspace → 400 `other_workspace`.
- `pages_reject_soft_deleted_source` — FR-F051-02: deleted dashboard → 400 `deleted`.
- `pages_reject_unpublished_form` — FR-F051-02: draft form id → 400 `field_errors.pages[n].source_id`.
- `pages_text_requires_body` — FR-F051-02: kind `text` without body → 400; body of 20,001 chars → 400.
- `roles_reject_landing_page_not_visible` — FR-F051-03: `Vendor` landing on a page not in its `visible_to_roles` → 400.
- `roles_reject_duplicate_name` — FR-F051-03: two roles named `vendor` and `Vendor` → 400.
- `publish_snapshots_manifest_and_increments_version` — FR-F051-04: publish → `workapp_versions` row 1 with full manifest, `published_version 1`, `workapp.published.v1` with `page_count 4`, `role_count 2`.
- `publish_rejects_empty_manifest` — FR-F051-04: zero pages or zero roles → 400 `invalid`.
- `publish_restores_earlier_version_as_new_number` — FR-F051-13: after versions 1 and 2, `{ version_number: 1 }` → version 3 equal to version 1 manifest.
- `publish_failure_does_not_advance_published_version` — NFR-F051-04: outbox fault → rollback; `published_version` unchanged, no version row.
- `draft_edit_marks_dirty_without_changing_served` — FR-F051-08: PUT pages after publish → `draft_dirty: true`; `/apps/{slug}` returns version 1 pages.
- `viewer_manifest_filters_pages_by_role` — FR-F051-05: vendor → 2 pages, landing `Intake form`, `roles_held: [Vendor]`; procurement → 4 pages.
- `viewer_group_membership_grants_role` — FR-F051-05: user only in group `Vendors` receives the Vendor manifest.
- `viewer_without_role_not_found` — FR-F051-05: no-role member → 404 `not_found`.
- `viewer_manifest_omits_other_role_members` — NFR-F051-02: vendor response contains no Procurement member ids; procurement response contains no vendor ids.
- `viewer_unpublished_app_admin_only` — FR-F051-05: unpublished slug → 404 for vendor; admin receives draft with `status: draft`.
- `viewer_preview_role_admin_only` — FR-F051-12: `preview_role_id` honoured for admin; ignored for vendor.
- `cross_tenant_id_and_slug_not_found` — FR-F051-11: tenant B on every `/api/v1/workapps` route and `/apps/{slug}` → 404.
- `mutation_writes_audit_and_outbox` — FR-F051-09: pages PUT → audit diff lists page ids and titles; one `workapp.updated.v1` with `changed_fields: [pages]`.
- `viewer_span_and_metrics_recorded` — NFR-F051-04: `workapp_opened_total{slug}` +1; span has `workapp_id`, `version_number`, `correlation_id`.

Evidence: JUnit output and request logs under `testing/evidence/F051/api/`.
