# F048 frontend cases

File: `testing/features/F048/frontend/{EntitlementsPage.test.tsx,FeatureFlagsPage.test.tsx,KillSwitchDialog.test.tsx,ModuleNotEntitled.test.tsx,hooks.test.tsx}`. Vitest with MSW. Flag `F048_FEATURE`.

- `EntitlementsPage.test.tsx::lists_all_ten_modules` — FR-F048-14: ten rows with state badges; `bridge` shows `Trial expired`.
- `EntitlementsPage.test.tsx::limit_fields_validate_schema` — FR-F048-02: `data-shuttle` drawer shows `max_flows`, `max_rows_per_run`, `max_file_mb`; negative value blocks submit.
- `EntitlementsPage.test.tsx::shows_denied_for_member` — FR-F048-14: member session renders `Only tenant administrators can manage modules`.
- `EntitlementsPage.test.tsx::shows_stale_banner_on_conflict` — FR-F048-11: PUT 409 → banner `This record changed` with reload.
- `FeatureFlagsPage.test.tsx::renders_registry_with_override_badges` — FR-F048-03: 11 flags; override badge `On · Pilot for Ops team`; expired badge for past `expires_at`.
- `FeatureFlagsPage.test.tsx::tenant_admin_sees_platform_fields_locked` — FR-F048-04: lifecycle editor read-only with lock icon and tooltip for tenant-admin; editable for platform-operator.
- `FeatureFlagsPage.test.tsx::disable_override_opens_confirmation_listing_modules` — FR-F048-14: choosing `Override: off` on `F052_FEATURE` lists `Data Shuttle` and the disable procedure.
- `FeatureFlagsPage.test.tsx::shows_error_banner_with_correlation_id` — NFR-F048-04: 500 response shows banner with `correlation_id` and retry.
- `KillSwitchDialog.test.tsx::kill_switch_requires_typed_key` — FR-F048-06: confirm disabled until the exact key is typed; submit calls `patchFlag` with `kill: true`.
- `ModuleNotEntitled.test.tsx::links_to_admin_for_admins_only` — FR-F048-10: admin sees link to `/admin/entitlements`; member sees text only; emits `module_not_entitled_viewed`.
- `hooks.test.tsx::use_module_allowed_reads_single_evaluation_query` — FR-F048-09: three hooks share one `['flag-evaluation', tenantId]` request.
- `hooks.test.tsx::offline_disables_forms` — FR-F048-14: `navigator.onLine=false` shows offline badge and disables save buttons.

Evidence: Vitest JUnit under `testing/evidence/F048/frontend/`.
