---
id: S096
type: story
status: planned
parent_epic: E008
parent_feature: F048
depends_on: [S095]
owned_paths: [crates/domain/src/entitlements/**, crates/auth/src/entitlements/**, services/api/src/entitlements/**, apps/web/src/features/entitlements/**, testing/features/F048/**]
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
- Decision references: `docs/architecture-decisions.md` sections 2–4, 6, 10; `docs/capability-contracts.md` row F048

## Vertical slice

As a tenant administrator, I want to set or clear a tenant override on a feature flag with a reason, and as a platform operator I want to move a flag through its rollout lifecycle or kill it, all from an accessible admin page, so that module rollout is deliberate, attributable, and reversible within seconds.

Out of this slice: entitlement upsert and the `RequireModule` guard (S095, already available); per-user flag targeting; billing or plan catalogs.

## Requirements

- **SR-S096-01:** `GET /api/v1/feature-flags` returns the registry with owner, rollout state, percent, default, disable procedure, cleanup ticket, and the caller's override including `expired: true` for past `expires_at` (covers FR-F048-03, FR-F048-13).
- **SR-S096-02:** `PATCH /api/v1/feature-flags/{key}` sets or clears a tenant override for `tenant-admin`; platform fields require `platform-operator` and otherwise return `403 denied` (FR-F048-04).
- **SR-S096-03:** Lifecycle transitions follow `draft→internal→percentage→tenant_list→general→retired`; `retired` requires `cleanup_ticket` and a 20-character `disable_procedure`; invalid transitions return `409 conflict` (FR-F048-05).
- **SR-S096-04:** `{ kill: true, reason }` disables the default, resets state to `internal`, suspends every override in one transaction, and every tenant's next evaluation returns `reason: killed` within 30 seconds on all instances (FR-F048-06, FR-F048-12).
- **SR-S096-05:** `decide_flag` implements the evaluation order of FR-F048-08 including deterministic murmur3 percentage buckets and the internal-tenant rule; the `flags` half of `GET /api/v1/feature-flags/evaluate` uses it (FR-F048-07, FR-F048-08).
- **SR-S096-06:** Every flag mutation writes an audit row and publishes `feature-flag.updated.v1` with `tenant_override_changed` and `killed` (FR-F048-11).
- **SR-S096-07:** `/admin/entitlements` and `/admin/feature-flags` render list, drawer, override form, lifecycle editor (operator only), kill switch, and disable confirmation with loading, error, denied, stale, and offline states, and pass axe (FR-F048-14, NFR-F048-03).
- **SR-S096-08:** `useFlag`, `useEntitlement`, and `useModuleAllowed` hooks read one evaluation query and are the only way module features read flag state in the web app (FR-F048-09).

## Surfaces

- Infrastructure/container: none
- Rust service/API: `crates/domain/src/entitlements/{flag.rs, override.rs, lifecycle.rs, decide.rs, service_flags.rs}`; `services/api/src/entitlements/{handlers_flag.rs, handlers_evaluate.rs}`; `crates/auth/src/entitlements/invalidator.rs` (kill propagation)
- Data/migration: none new; uses `feature_flags` and `flag_overrides` from S095
- React/UI: `apps/web/src/features/entitlements/{EntitlementsPage.tsx, EntitlementRow.tsx, EntitlementEditDrawer.tsx, LimitFields.tsx, FeatureFlagsPage.tsx, FlagTable.tsx, FlagRow.tsx, FlagEditDrawer.tsx, OverrideForm.tsx, LifecycleEditor.tsx, KillSwitchDialog.tsx, DisableConfirmDialog.tsx, ModuleNotEntitled.tsx, hooks.ts, api.ts, routes.ts}`
- Mocks/fixtures: seeded registry of eleven flags in mixed states; MSW handlers for component tests; two-instance harness with a shared PostgreSQL schema for kill propagation

## TDD harness

- Test path: `testing/features/F048/{api,frontend,e2e,accessibility}/`
- Feature flag: `F048_FEATURE`
- Targeted command: `cargo xtask test-feature F048`
- Full command: `cargo xtask test-all`
- First failing tests: `flag_override_set_and_clear`, `flag_platform_field_denied_for_tenant_admin`, `flag_retire_requires_cleanup_ticket`, `flag_kill_suspends_all_overrides`, `decide_flag_percentage_bucket_is_stable`, `kill_switch_requires_typed_key`

## Exit criteria

- [ ] Requirement tests SR-S096-01 through SR-S096-08 written first and failing
- [ ] Tasks T191 and T192 complete; UI wired to real API through generated client
- [ ] Unit, API, React, E2E, accessibility, permission, and performance tests pass
- [ ] Production call path named: `apps/web/src/features/entitlements/FeatureFlagsPage.tsx` mounted at `/admin/feature-flags`; `hooks.ts` exported from `apps/web/src/features/entitlements/index.ts`
- [ ] Handoff evidence recorded in the F048 ticket
