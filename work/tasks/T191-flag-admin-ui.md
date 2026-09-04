---
id: T191
type: task
status: planned
parent_epic: E006
parent_feature: F048
parent_story: S096
depends_on: [S096]
owned_paths: [crates/domain/src/entitlements/**, crates/persistence/src/entitlements/**, services/api/src/entitlements/**, apps/web/src/features/entitlements/**, testing/features/F048/api/**, testing/features/F048/frontend/**]
feature_flag: F048_FEATURE
branch: t191-flag-admin-ui
started_at: null
finished_at: null
---

# T191 — Flag admin UI

## Identity

- Parent story: `S096` Flag administration
- Owner: platform
- Branch: `t191-flag-admin-ui`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 6; `docs/capability-contracts.md` row F048

## Objective

Implement the flag registry routes, lifecycle and override logic, the kill switch, and the two admin pages with the shared flag hooks wired to the real API.

## Specification

- Owned paths: `crates/domain/src/entitlements/{flag.rs, override.rs, lifecycle.rs, decide.rs, service_flags.rs}`, `crates/persistence/src/entitlements/{flag_repository.rs, override_repository.rs}`, `services/api/src/entitlements/handlers_flag.rs`, `apps/web/src/features/entitlements/{EntitlementsPage.tsx, EntitlementRow.tsx, EntitlementEditDrawer.tsx, LimitFields.tsx, FeatureFlagsPage.tsx, FlagTable.tsx, FlagRow.tsx, FlagEditDrawer.tsx, OverrideForm.tsx, LifecycleEditor.tsx, KillSwitchDialog.tsx, DisableConfirmDialog.tsx, ModuleNotEntitled.tsx, hooks.ts, api.ts, routes.ts, index.ts}`
- Contract/input: `PatchFlagRequest { override?: { enabled, reason, expires_at? } | null, owner?, rollout_state?, rollout_percent?, default_enabled?, disable_procedure?, cleanup_ticket?, kill?, reason? }` with `If-Match`; generated `EntitlementsApi` client; route params none; roles from the session context (`tenant-admin`, `platform-operator`).
- Output/behavior: `GET /api/v1/feature-flags` and `PATCH /api/v1/feature-flags/{key}` per FR-F048-03 through FR-F048-06; `decide_flag` per FR-F048-08 with murmur3 seed `0x4f50_5348`, taking the flag, override and tenant as arguments; lifecycle changes are checked with `FeatureFlagRepository::transition_allowed` against `flag_rollout_transitions`; kill suspends every override through `FlagOverrideRepository::suspend_overrides_for_flag` in one `UnitOfWork` with the flag update and emits `feature-flag.updated.v1 { killed: true }`; pages render tables, drawers, override form, lifecycle editor (operator only), kill switch and disable confirmation requiring the typed key; states: loading skeleton, error banner with correlation ID, denied panel, stale banner with reload, offline badge; `useFlag`, `useEntitlement`, `useModuleAllowed` read `['flag-evaluation', tenantId]`; telemetry `entitlement_updated`, `feature_flag_override_set`, `feature_flag_override_cleared`, `feature_flag_lifecycle_changed`, `feature_flag_killed`, `module_not_entitled_viewed`.
- Data access: `crates/persistence/src/entitlements/flag_repository.rs` owns `feature_flags` and `flag_rollout_transitions`, `override_repository.rs` owns `flag_overrides`, and they hold every SQL statement of this task; `flag.rs`, `override.rs`, `lifecycle.rs`, `decide.rs`, `service_flags.rs`, and `handlers_flag.rs` depend on the traits and contain no `sqlx::query*` call; `LimitFields.tsx` renders the module's declared limit keys and submits the unchanged `limits` object (decision section 2.1).
- Dependencies: T190 routes, evaluator, and invalidator; F005 admin navigation shell for the entry points.
- Feature flag: `F048_FEATURE` read through the app bootstrap; admin routes are not registered when off.

## TDD

- Failing test first: `testing/features/F048/api/flag_tests.rs::flag_override_set_and_clear`, `::flag_platform_field_denied_for_tenant_admin`, `::flag_retire_requires_cleanup_ticket`, `::flag_invalid_transition_conflicts`, `::flag_transition_checked_against_seeded_rows`, `::flag_kill_suspends_all_overrides`, `::flag_expired_override_ignored`; `testing/features/F048/frontend/FeatureFlagsPage.test.tsx::renders_registry_with_override_badges`, `::tenant_admin_sees_platform_fields_locked`, `::kill_switch_requires_typed_key`, `EntitlementsPage.test.tsx::lists_all_ten_modules`, `::limit_fields_validate_schema`, `::limits_submit_as_object`, `ModuleNotEntitled.test.tsx::links_to_admin_for_admins_only`
- Targeted command: `cargo xtask test-feature F048`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: seeded registry of eleven flags in mixed states; MSW handlers from the fixture; role-switching test session helper

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Component and API lanes pass; hooks exported from `index.ts` and consumed by a downstream smoke test
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S096
- [ ] `finished_at` recorded
