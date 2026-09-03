# F051 requirements cases

Feature: WorkApps. Flag `F051_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F051-REQ-001` | FR-F051-01 | api | admin creates `vendor-onboarding` → 201, version 1, `status: draft`; same slug again → 409 `field_errors.slug`; `Vendor_App` → 400 |
| `F051-REQ-002` | FR-F051-02 | api | 51 pages → 400 `pages = max_50`; page kind `form` pointing at a sheet → 400 `pages[n].source_id = kind_mismatch` |
| `F051-REQ-003` | FR-F051-03 | api | role `Vendor` landing on `Status board` it cannot see → 400 `roles[n].default_landing_page_id`; 21 roles → 400 |
| `F051-REQ-004` | FR-F051-04 | api, database | publish → `workapp_versions` version 1, `published_version 1`; zero roles → 400; `version_number: 1` again → version 3 |
| `F051-REQ-005` | FR-F051-05 | api | vendor GET `/apps/vendor-onboarding` → 2 pages, landing `Intake form`; no-role member → 404; unpublished → 404 (admin gets draft) |
| `F051-REQ-006` | FR-F051-06 | frontend, e2e | vendor opens `Status board` → sheets API 404, frame shows denied; requests carry viewer session |
| `F051-REQ-007` | FR-F051-07 | api | list filters `status=published` and `name_prefix`; PATCH `status: archived` → slug 404, versions kept |
| `F051-REQ-008` | FR-F051-08 | api, e2e | draft pages replaced → `/apps/{slug}` unchanged, `draft_dirty: true` |
| `F051-REQ-009` | FR-F051-09 | api, database | each mutation → one audit row with page/role id diff and one `workapp.updated.v1` or `workapp.published.v1` |
| `F051-REQ-010` | FR-F051-10 | api | not-entitled tenant → 403 `field_errors.module`; sixth app under `max_apps 5` → 409 `field_errors.limit` |
| `F051-REQ-011` | FR-F051-11 | api | tenant B by id and slug → 404; non-admin PUT pages → 403, GET draft → 404 |
| `F051-REQ-012` | FR-F051-12 | frontend, e2e | shell renders role nav and landing page; builder edits, previews as `Vendor`, publishes |
| `F051-REQ-013` | FR-F051-13 | frontend, e2e | version list shows diff against previous; `Restore this version` publishes version 3 |
| `F051-NFR-001` | NFR-F051-01 | performance | manifest 50 pages/20 roles p95 < 300 ms; shell nav render < 500 ms |
| `F051-NFR-002` | NFR-F051-02 | api | vendor manifest omits Procurement members; slug response has no tenant id; embeds authorized by source |
| `F051-NFR-003` | NFR-F051-03 | accessibility | axe serious = 0; keyboard reorder; nav `aria-current`; preview switch announced |
| `F051-NFR-004` | NFR-F051-04 | api, database | span carries app, version, page; failed snapshot leaves `published_version` unchanged |

Evidence: command, fixture seed, result, and artifact path recorded under `testing/evidence/F051/`.
