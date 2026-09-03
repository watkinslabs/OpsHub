# F051 database cases

File: `testing/features/F051/database/migration_tests.rs`. Flag `F051_FEATURE`.

- `workapp_tables_exist_with_constraints` — T201: `workapps`, `workapp_pages`, `workapp_roles`, `workapp_versions` exist with tenant, version, audit, and soft-delete columns; foreign key to `workspaces`.
- `duplicate_slug_per_tenant_rejected` — FR-F051-01: `vendor-onboarding` and `Vendor-Onboarding` in the same tenant violate the partial unique index; allowed in tenant B and after soft delete.
- `duplicate_page_position_rejected` — FR-F051-02: two pages with `position 3` in one app rejected.
- `text_page_requires_body_not_source` — FR-F051-02: `kind = 'text'` with `source_id` rejected; `kind = 'sheet'` with null `source_id` rejected.
- `duplicate_role_name_rejected` — FR-F051-03: `Vendor` and `vendor` in one app violate the unique index.
- `version_number_unique_per_app` — FR-F051-04: second `version_number 1` for the same app rejected.
- `published_version_must_exist` — FR-F051-04, NFR-F051-04: setting `published_version 5` with no such version row fails at commit (deferred foreign key).
- `pages_and_roles_cascade_on_app_purge` — FR-F051-07: hard delete of an app removes pages and roles; versions block deletion by foreign key until purged first.
- `members_gin_index_used_for_role_lookup` — NFR-F051-01: `EXPLAIN` on member containment query uses `workapp_roles_members_gin`.
- `rollback_drops_tables` — T201: `sqlx migrate revert` removes the four tables and indexes.

Evidence: migration log and `EXPLAIN` output under `testing/evidence/F051/database/`.
