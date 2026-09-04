---
id: S096
type: story
status: planned
parent_epic: E006
parent_feature: F048
depends_on: [S095]
owned_paths: [crates/domain/src/entitlements/**, crates/persistence/src/entitlements/**, crates/auth/src/entitlements/**, services/api/src/entitlements/**, apps/web/src/features/entitlements/**, testing/features/F048/**]
feature_flag: F048_FEATURE
branch: s096-flag-administration
started_at: null
finished_at: null
---

# S096 — Flag administration

## Identity

- Parent feature: `F048` Entitlements and feature flags
- Owner: platform
- Branch: `s096-flag-administration`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 6, 10; `docs/capability-contracts.md` row F048

## Vertical slice

As a tenant administrator, I want to set or clear a tenant override on a feature flag with a reason, and as a platform operator I want to move a flag through its rollout lifecycle or kill it, all from an accessible admin page, so that module rollout is deliberate, attributable, and reversible within seconds.

Out of this slice: entitlement upsert and the `RequireModule` guard (S095, already available); per-user flag targeting; billing or plan catalogs.

## Requirements

- **SR-S096-01:** `GET /api/v1/feature-flags` returns the registry through `FeatureFlagRepository::list_flag_registry` joined with `FlagOverrideRepository::list_overrides_for_tenant`, with owner, rollout state, percent, default, disable procedure, cleanup ticket, and the caller's override including `expired: true` for past `expires_at`; the nightly prune calls `FlagOverrideRepository::prune_expired_overrides` and holds no SQL (covers FR-F048-03, FR-F048-13).
- **SR-S096-02:** `PATCH /api/v1/feature-flags/{key}` sets or clears a tenant override for `tenant-admin`; platform fields require `platform-operator` and otherwise return `403 denied` (FR-F048-04).
- **SR-S096-03:** Lifecycle transitions follow `draft→internal→percentage→tenant_list→general→retired` and any state to `retired`, checked against the seeded `flag_rollout_transitions` rows with `FeatureFlagRepository::transition_allowed` rather than a list in the handler; `retired` requires `cleanup_ticket` and a 20-character `disable_procedure`; invalid transitions return `409 conflict` (FR-F048-05).
- **SR-S096-04:** `{ kill: true, reason }` disables the default, resets state to `internal`, and suspends every override in one `UnitOfWork` spanning `FeatureFlagRepository::apply_lifecycle_change` and `FlagOverrideRepository::suspend_overrides_for_flag`, and every tenant's next evaluation returns `reason: killed` within 30 seconds on all instances (FR-F048-06, FR-F048-12).
- **SR-S096-05:** `decide_flag` is a pure function over the flag, the override, and the tenant, implements the evaluation order of FR-F048-08 including deterministic murmur3 percentage buckets and the internal-tenant rule, and receives its inputs from the repositories rather than reading them; the `flags` half of `GET /api/v1/feature-flags/evaluate` uses it (FR-F048-07, FR-F048-08).
- **SR-S096-06:** Every flag mutation writes its row change, the audit row, and the `feature-flag.updated.v1` outbox entry with `tenant_override_changed` and `killed` in one `UnitOfWork` (FR-F048-11).
- **SR-S096-07:** `/admin/entitlements` and `/admin/feature-flags` render list, drawer, override form, lifecycle editor (operator only), kill switch, and disable confirmation with loading, error, denied, stale, and offline states, and pass axe (FR-F048-14, NFR-F048-03).
- **SR-S096-08:** `useFlag`, `useEntitlement`, and `useModuleAllowed` hooks read one evaluation query and are the only way module features read flag state in the web app (FR-F048-09).

## Surfaces

- Infrastructure/container: none
- Data access: `crates/persistence/src/entitlements/{flag_repository.rs, override_repository.rs}` hold every SQL statement in this slice — `FeatureFlagRepository` owns `feature_flags` and `flag_rollout_transitions`, `FlagOverrideRepository` owns `flag_overrides`, and neither touches the tables owned by `EntitlementRepository` or `ModuleCatalogRepository`; `lifecycle.rs`, `decide.rs`, `service_flags.rs`, the handlers, the invalidator, and the prune job depend on the traits and contain no `sqlx::query*` call (decision section 2.1)
- Rust service/API: `crates/domain/src/entitlements/{flag.rs, override.rs, lifecycle.rs, decide.rs, service_flags.rs}`; `services/api/src/entitlements/{handlers_flag.rs, handlers_evaluate.rs}`; `crates/auth/src/entitlements/invalidator.rs` (kill propagation)
- Data/migration: none new; uses `feature_flags`, `flag_rollout_transitions`, `flag_overrides`, `modules`, and `entitlement_limits` from S095
- React/UI: `apps/web/src/features/entitlements/{EntitlementsPage.tsx, EntitlementRow.tsx, EntitlementEditDrawer.tsx, LimitFields.tsx, FeatureFlagsPage.tsx, FlagTable.tsx, FlagRow.tsx, FlagEditDrawer.tsx, OverrideForm.tsx, LifecycleEditor.tsx, KillSwitchDialog.tsx, DisableConfirmDialog.tsx, ModuleNotEntitled.tsx, hooks.ts, api.ts, routes.ts}`
- Mocks/fixtures: seeded registry of eleven flags in mixed states created through `FeatureFlagRepository` and `FlagOverrideRepository`; MSW handlers for component tests; two-instance harness with a shared PostgreSQL schema for kill propagation

## TDD harness

- Test path: `testing/features/F048/{api,frontend,e2e,accessibility}/`
- Feature flag: `F048_FEATURE`
- Targeted command: `cargo xtask test-feature F048`
- Full command: `cargo xtask test-all`
- First failing tests: `flag_override_set_and_clear`, `flag_platform_field_denied_for_tenant_admin`, `flag_retire_requires_cleanup_ticket`, `flag_kill_suspends_all_overrides`, `flag_transition_row_missing_conflicts`, `decide_flag_percentage_bucket_is_stable`, `kill_switch_requires_typed_key`

## Exit criteria

- [ ] Requirement tests SR-S096-01 through SR-S096-08 written first and failing
- [ ] Tasks T191 and T192 complete; UI wired to real API through generated client
- [ ] Unit, API, React, E2E, accessibility, permission, and performance tests pass
- [ ] Production call path named: `apps/web/src/features/entitlements/FeatureFlagsPage.tsx` mounted at `/admin/feature-flags`; `hooks.ts` exported from `apps/web/src/features/entitlements/index.ts`
- [ ] Handoff evidence recorded in the F048 ticket
