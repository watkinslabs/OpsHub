---
id: F048
type: feature
status: planned
priority: P0
owner: platform
estimate: 5
target_milestone: M7
parent_epic: E008
depends_on: [F002, F003]
blocks: [F050, F051, F052, F053, F054, F055, F056, F057, F039]
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/entitlements/**, crates/auth/src/entitlements/**, services/api/src/entitlements/**, apps/web/src/features/entitlements/**, services/api/migrations/*_entitlements_*.sql, testing/features/F048/**]
feature_flag: F048_FEATURE
flag_default: off
branch: f048-entitlements-and-feature-flags
started_at: null
finished_at: null
---

# F048 — Entitlements and feature flags

## 1. Identity and dates

- Branch: `f048-entitlements-and-feature-flags`
- Capability area: advanced module gating (spec 5.11 introduction, 5.9 INT-03, 5.10 "AI access is feature-flagged, admin-controllable", section 10 "Advanced modules use entitlement records plus feature flags")
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 9, 10; `docs/capability-contracts.md` row F048
- Module slug: `entitlements`

## 2. Requirement specification

### Problem and user outcome

Premium modules (Dynamic View, WorkApps, Data Shuttle, DataMesh, Bridge, Calendar, Pivot, DAM, AI) must be turned on per tenant, rolled out gradually, limited per tenant, and turned off instantly without touching domain data. Today nothing records which tenant is entitled to which module, and there is no single evaluator that a route can call. Every E008 feature needs one answer to "may this tenant use module X right now, and with which limits".

As a tenant administrator, I want to see and change which modules my tenant is entitled to and which feature flags are active for my tenant, so that I can roll a module out to my organization deliberately and switch it off if it misbehaves. As a platform operator, I want every flag to carry an owner, rollout state, disable procedure, and cleanup ticket, so that no flag becomes an orphan.

### Functional requirements

- **FR-F048-01:** `GET /api/v1/entitlements` returns one record per known module slug (`dynamic-views`, `workapps`, `data-shuttle`, `datamesh`, `bridge`, `calendar-app`, `pivots`, `assets`, `ai-assist`, `ai-insights`, `data-grid-pro`) with `state` (`none`, `trial`, `active`, `suspended`), `limits` object, `trial_ends_at`, `source` (`manual`, `plan`), and `version`; modules without a stored row are returned with `state: none` and `version: 0`.
- **FR-F048-02:** `PUT /api/v1/entitlements/{module}` by a `tenant-admin` upserts the record with `{ state, limits, trial_ends_at? }`; unknown `module` returns `404 not_found`; `state: trial` without `trial_ends_at` returns `400 invalid` with `field_errors.trial_ends_at`; `limits` keys must belong to the module's declared limit schema (for example `data-shuttle` accepts `max_flows`, `max_rows_per_run`, `max_file_mb`) or the request returns `400 invalid` with `field_errors.limits.<key>`.
- **FR-F048-03:** `GET /api/v1/feature-flags` returns every registered flag with `key`, `description`, `owner`, `rollout_state` (`draft`, `internal`, `percentage`, `tenant_list`, `general`, `retired`), `rollout_percent` (0–100), `default_enabled`, `disable_procedure`, `cleanup_ticket`, `override` (the calling tenant's override if any), and `version`; keys match `^F[0-9]{3}_FEATURE$` or `^[A-Z][A-Z0-9_]{2,63}$`.
- **FR-F048-04:** `PATCH /api/v1/feature-flags/{key}` by a `tenant-admin` with `If-Match` sets a tenant override `{ override: { enabled: bool, reason: string(1–500), expires_at?: rfc3339 } }` or clears it with `{ override: null }`; a platform operator (role `platform-operator`, granted through F003 role bindings on the platform tenant) may additionally patch `owner`, `rollout_state`, `rollout_percent`, `default_enabled`, `disable_procedure`, and `cleanup_ticket`; a tenant-admin sending platform fields receives `403 denied`.
- **FR-F048-05:** Rollout state transitions are restricted to `draft→internal→percentage→tenant_list→general→retired` and any state `→retired`; `retired` requires a non-empty `cleanup_ticket` matching `^[FST][0-9]{3}$` and a `disable_procedure` of at least 20 characters; an invalid transition returns `409 conflict` with `field_errors.rollout_state = "invalid_transition"`.
- **FR-F048-06:** `PATCH /api/v1/feature-flags/{key}` with `{ kill: true, reason }` by a platform operator sets `default_enabled: false`, `rollout_state: internal`, and marks every tenant override `suspended` in one transaction, so the next evaluation for every tenant returns `enabled: false` with `reason: killed`.
- **FR-F048-07:** `GET /api/v1/feature-flags/evaluate?keys=K1,K2&modules=M1,M2` returns `{ flags: { K: { enabled, reason } }, entitlements: { M: { allowed, state, limits, reason } } }` for the calling tenant where flag `reason` is one of `override`, `suspended_override`, `killed`, `retired`, `percentage`, `tenant_list`, `default`, and entitlement `reason` is one of `active`, `trial`, `trial_expired`, `suspended`, `not_entitled`; up to 50 keys and 20 modules per call, more returns `400 invalid`.
- **FR-F048-08:** Evaluation order for a flag is: killed or retired → `false`; active tenant override → its value; `general` → `true`; `tenant_list` → `true` only with an enabling override; `percentage` → `true` when `murmur3(tenant_id ‖ key) mod 100 < rollout_percent`; `internal` → `true` only for tenants with `is_internal = true`; `draft` → `false`; otherwise `default_enabled`.
- **FR-F048-09:** A module is `allowed` only when its entitlement `state` is `active`, or `trial` with `trial_ends_at` in the future, and the module's gate flag (`F050_FEATURE` for `dynamic-views`, `F051_FEATURE` for `workapps`, `F052_FEATURE` for `data-shuttle`, `F053_FEATURE` for `datamesh`, `F054_FEATURE` for `bridge`, `F055_FEATURE` for `calendar-app`, `F056_FEATURE` for `pivots`, `F057_FEATURE` for `assets`, `F039_FEATURE` for `ai-assist`, `F040_FEATURE` for `ai-insights`) evaluates `enabled: true`.
- **FR-F048-10:** The shared `RequireModule` guard in `crates/auth/src/entitlements/` rejects a request for a non-allowed module with `403 denied`, body `{ code: "denied", message, field_errors: { module: "<reason>" }, correlation_id }`, before any handler code runs; every E008 module router mounts this guard.
- **FR-F048-11:** Every entitlement or flag mutation requires `Idempotency-Key` and `If-Match`, writes an `audit_events` row with before/after diff, and publishes `entitlement.updated.v1` or `feature-flag.updated.v1` through the outbox with `changed_fields`.
- **FR-F048-12:** Evaluation results are cached in-process per `(tenant_id, key)` for at most 30 seconds and invalidated by the outbox consumer on `entitlement.updated.v1` and `feature-flag.updated.v1`, so a kill switch takes effect on every API instance within 30 seconds worst case and within 2 seconds on the instance that performed the write.
- **FR-F048-13:** Tenant overrides with `expires_at` in the past are ignored by evaluation and are pruned nightly by the worker-less SQL job invoked from the F004 scheduler; an expired override appears in `GET /feature-flags` with `override.expired: true`.
- **FR-F048-14:** The web admin pages `/admin/entitlements` and `/admin/feature-flags` render only for `tenant-admin` (denied state otherwise), let the admin change entitlement state and limits, set or clear a flag override with a reason, and show a confirmation dialog listing affected modules before disabling; a platform operator additionally sees the lifecycle editor and kill switch. Each module with `state: none` renders an upgrade row naming the capabilities it unlocks and the action that turns it on, and `data-grid-pro` additionally carries the licence-key field described in FR-F062-16 — the upgrade path a locked grid affordance links to.
- **FR-F048-15:** Cross-tenant reads of another tenant's entitlements or overrides are impossible by construction (tenant comes from gateway context, never from the request), and a request that names a foreign `tenant_id` in the body returns `400 invalid`.

### Non-functional requirements

- **NFR-F048-01 Performance:** in-process `RequireModule` evaluation with a warm cache completes in under 1 ms p99; `GET /api/v1/feature-flags/evaluate` with 50 keys responds in under 100 ms p95; admin list routes under 500 ms p95 (spec section 6).
- **NFR-F048-02 Security/privacy:** platform fields are writable only by `platform-operator`; tenant-admins never see other tenants' overrides; flag `reason` strings are redacted from logs; audit rows carry actor, IP/device metadata, and diff for every change.
- **NFR-F048-03 Accessibility:** admin pages pass axe with zero serious violations; the disable confirmation dialog traps focus and is fully keyboard operable; rollout-state badges use text plus color.
- **NFR-F048-04 Reliability/observability:** metrics `entitlement_denied_total{module,reason}`, `flag_eval_cache_hit_ratio`, and `flag_kill_switch_total{key}` exported; each evaluation span carries `tenant_id`, `flag_key`, `module`, `correlation_id`; cache invalidation lag is measured and alerts above 30 seconds.

### Scope

Included: entitlement records, module limit schemas, flag registry, rollout lifecycle, tenant overrides, kill switch, evaluation endpoint, `RequireModule` guard and `useFlag`/`useEntitlement` hooks consumed by other features, admin UI, audit, outbox events, cache invalidation.

Excluded: plan catalogs and billing (administration concern per spec section 10); the module features themselves (F050–F057, F039, F040); seat counting against user counts (F002 owns user state; a future ticket adds seat enforcement); per-user flag targeting.

## 3. UX specification

- Entry points: admin navigation `Modules` → `/admin/entitlements`; `Feature flags` → `/admin/feature-flags`; module pages that are not allowed render the shared `ModuleNotEntitled` panel linking to `/admin/entitlements`.
- Primary flow: admin opens `/admin/entitlements`, sees ten module rows with state badges and limits, clicks `Data Shuttle`, sets state `trial` with an end date and `max_flows: 5`, saves; the row shows `Trial until 2026-10-03`; admin opens `/admin/feature-flags`, finds `F052_FEATURE`, chooses `Override: on` with reason `Pilot for Ops team`, saves; the module link appears in the workspace navigation on the next page load.
- Loading: skeleton table rows; Empty: never for entitlements (all modules always listed), flags show `No flags registered` when the registry is empty; Error: inline banner with `correlation_id` and retry; Success: toast `Entitlement saved` / `Override saved`; Stale/conflict: banner `This record changed` with `Reload`; Offline: forms disabled with offline badge.
- Permission-denied: non-admins see the denied state with the message `Only tenant administrators can manage modules`; tenant-admins see platform-only fields read-only with a lock icon and tooltip.
- Disable flow: choosing `Override: off` or `Kill` opens a confirmation dialog listing affected modules and the flag's `disable_procedure`; confirmation requires typing the flag key.
- Responsive: tables collapse to stacked cards under 768 px; the edit drawer becomes a full-screen sheet under 640 px.
- Keyboard: tab order covers filter, rows, edit buttons; `Enter` opens the drawer; `Escape` closes without saving; focus returns to the triggering row; motion respects `prefers-reduced-motion`.
- Font/icon/design tokens: Inter variable, Lucide icons `ToggleLeft`, `ToggleRight`, `ShieldCheck`, `Lock`, `AlertTriangle`, `Power`; tokens from `apps/web/src/design/tokens.css`.

## 4. Technical specification

Canonical contract: `docs/capability-contracts.md` row F048 (aggregate `entitlement`, module `entitlements`, roles `tenant-admin`).

### Rust backend

- Domain entities in `crates/domain/src/entitlements/`: `ModuleSlug` (enum of the ten modules with `limit_schema() -> &[LimitKey]` and `gate_flag() -> FlagKey`), `Entitlement { id, tenant_id, module: ModuleSlug, state: EntitlementState, limits: Limits, trial_ends_at: Option<DateTime<Utc>>, source: EntitlementSource, version, created/updated actor+time }`, `FeatureFlag { key: FlagKey, description, owner: String, rollout_state: RolloutState, rollout_percent: u8, default_enabled: bool, disable_procedure: String, cleanup_ticket: Option<WorkItemId>, version, created/updated actor+time }`, `FlagOverride { id, tenant_id, flag_key, enabled: bool, reason, expires_at, suspended: bool, version, audit fields }`, `FlagDecision { enabled, reason: FlagReason }`, `ModuleDecision { allowed, state, limits, reason: EntitlementReason }`.
- Use cases: `list_entitlements`, `upsert_entitlement`, `list_flags`, `patch_flag`, `set_override`, `clear_override`, `kill_flag`, `evaluate_flags`, `evaluate_modules`, `prune_expired_overrides`; pure function `decide_flag(flag, override, tenant) -> FlagDecision` implements FR-F048-08 and is unit tested exhaustively.
- Shared guard in `crates/auth/src/entitlements/`: `RequireModule(ModuleSlug)` axum `FromRequestParts` extractor and `EntitlementLayer` tower layer; both call `Evaluator::module(tenant_id, slug)` backed by `moka` cache (30 s TTL, invalidated by `EvaluatorInvalidator` subscribed to the two events). `Evaluator` is constructed once in `services/api/src/main.rs` app state and injected as `Arc<Evaluator>`.
- API endpoints (`services/api/src/entitlements/`): `GET /api/v1/entitlements`, `PUT /api/v1/entitlements/{module}`, `GET /api/v1/feature-flags`, `PATCH /api/v1/feature-flags/{key}`, `GET /api/v1/feature-flags/evaluate`. DTOs: `EntitlementResponse`, `UpsertEntitlementRequest { state, limits, trial_ends_at? }`, `FeatureFlagResponse`, `PatchFlagRequest { override?: OverridePatch | null, owner?, rollout_state?, rollout_percent?, default_enabled?, disable_procedure?, cleanup_ticket?, kill?: bool, reason? }`, `EvaluateQuery { keys: Vec<FlagKey>, modules: Vec<ModuleSlug> }`, `EvaluateResponse { flags, entitlements }`.
- Events: `entitlement.updated.v1` (payload adds `module`, `state`), `feature-flag.updated.v1` (payload adds `key`, `rollout_state`, `tenant_override_changed: bool`, `killed: bool`).
- Authorization: reads by any authenticated member of the tenant (module navigation needs them); entitlement upsert and override patch by `tenant-admin`; platform fields and kill by `platform-operator`; role checks via F003 `authz::require`.
- Validation: `limits` values are non-negative integers ≤ 1,000,000; `reason` 1–500 chars; `rollout_percent` 0–100; `expires_at` must be in the future and at most 365 days out; `keys` ≤ 50, `modules` ≤ 20.
- Error mapping: `EntitlementError::UnknownModule → 404 not_found`, `EntitlementError::LimitKeyUnknown → 400 invalid`, `FlagError::InvalidTransition → 409 conflict`, `FlagError::StaleVersion → 409 conflict`, `FlagError::PlatformFieldDenied → 403 denied`, `AuthzError::Denied → 403 denied`, module guard → `403 denied` with `field_errors.module`.

### PostgreSQL/SQLx

- Migration `*_entitlements_*.sql` creates `entitlements(id uuid pk, tenant_id uuid not null, module text not null, state text not null check (state in ('none','trial','active','suspended')), limits jsonb not null default '{}', trial_ends_at timestamptz, source text not null default 'manual', version bigint not null default 1, created_by, created_at, updated_by, updated_at)`, `feature_flags(key text pk, description text not null, owner text not null, rollout_state text not null check (rollout_state in ('draft','internal','percentage','tenant_list','general','retired')), rollout_percent smallint not null default 0 check (rollout_percent between 0 and 100), default_enabled bool not null default false, disable_procedure text not null default '', cleanup_ticket text, version bigint not null default 1, created_by, created_at, updated_by, updated_at)`, `flag_overrides(id uuid pk, tenant_id uuid not null, flag_key text not null references feature_flags(key) on delete cascade, enabled bool not null, reason text not null, expires_at timestamptz, suspended bool not null default false, version bigint not null default 1, created_by, created_at, updated_by, updated_at)`.
- Invariants: unique `entitlements(tenant_id, module)`; unique `flag_overrides(tenant_id, flag_key)`; check `(state <> 'trial') or (trial_ends_at is not null)`; check `(rollout_state <> 'retired') or (cleanup_ticket is not null and length(disable_procedure) >= 20)`; `feature_flags` is platform-scoped (no `tenant_id`) and seeded by migration with the eleven `F###_FEATURE` keys for E008 in state `draft`, owner `platform`.
- Indexes: `entitlements(tenant_id)`, `flag_overrides(tenant_id, flag_key)`, `flag_overrides(expires_at) where expires_at is not null and suspended = false`.
- Audit events: `entitlement.upsert`, `flag.patch`, `flag.override.set`, `flag.override.clear`, `flag.kill`, `flag.override.prune` with field-level diffs.
- Retention/deletion: no soft delete (records are configuration, history lives in `audit_events`); rollback drops the three tables; the seed rows are recreated on re-apply.

### React/TypeScript

- Routes: `/admin/entitlements`, `/admin/feature-flags` in `apps/web/src/features/entitlements/`; components `EntitlementsPage`, `EntitlementRow`, `EntitlementEditDrawer`, `LimitFields`, `FeatureFlagsPage`, `FlagTable`, `FlagRow`, `FlagEditDrawer`, `OverrideForm`, `LifecycleEditor`, `KillSwitchDialog`, `DisableConfirmDialog`, `ModuleNotEntitled` (shared panel).
- Shared hooks exported from `apps/web/src/features/entitlements/hooks.ts`: `useFlag(key)`, `useEntitlement(module)`, `useModuleAllowed(module)`; they read one `['flag-evaluation', tenantId]` query populated at shell load with every E008 key and module, refetch on window focus, and `staleTime` 30 s.
- State: TanStack Query keys `['entitlements']`, `['feature-flags']`, `['flag-evaluation', tenantId]`; mutations invalidate all three.
- API client: generated `EntitlementsApi` with `listEntitlements`, `upsertEntitlement`, `listFlags`, `patchFlag`, `evaluate`.
- Telemetry: `entitlement_updated`, `feature_flag_override_set`, `feature_flag_override_cleared`, `feature_flag_lifecycle_changed`, `feature_flag_killed`, `module_not_entitled_viewed` with `module`, `key`, `state`, `reason`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F048-01 through FR-F048-15 in `testing/features/F048/requirements/cases.md`
- [ ] Failure/edge-case tests: trial without end date, unknown limit key, invalid lifecycle transition, retire without cleanup ticket, expired override ignored, kill switch clears all overrides, 51 keys rejected
- [ ] Permission-negative and tenant-isolation tests: tenant-admin patching platform fields denied, member upserting entitlement denied, tenant B override invisible to tenant A, guard returns denied before handler
- [ ] Rust unit tests: `decide_flag` truth table over every rollout state, percentage bucket determinism, limit schema validation
- [ ] API contract/integration tests: every route above with success and each error code
- [ ] Database migration/constraint tests: unique indexes, trial check, retired check, cascade on flag delete, seed rows, rollback
- [ ] React component tests: `EntitlementsPage`, `FeatureFlagsPage`, `KillSwitchDialog`, `ModuleNotEntitled` states
- [ ] Browser E2E tests: enable trial, set override, module link appears, kill switch removes access
- [ ] Accessibility tests: axe on both pages, dialog focus trap, badge text
- [ ] Performance/load tests: guard p99 < 1 ms warm, evaluate 50 keys p95 < 100 ms, invalidation lag < 30 s

### Fast fanout configuration

- Test harness path: `testing/features/F048/`
- Feature flag: `F048_FEATURE`
- Fixture/seed factory: `testing/fixtures/entitlements.rs` builds tenant A (admin, member), tenant B, an internal tenant, a platform-operator actor, the seeded flag registry, and entitlements for `data-shuttle` (active) and `bridge` (trial expired)
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, UTC, murmur3 buckets precomputed for the fixture tenants
- Mock/stub contracts: outbox publisher recorded in memory; authz uses the real F003 engine with fixture bindings; cache uses an injectable clock
- Parallel isolation: one schema per test worker, tenant ID per test
- Targeted command: `cargo xtask test-feature F048`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F048/`

## 6. Acceptance criteria

```gherkin
Feature: Entitlements and feature flags

Scenario: Enable a module on trial for one tenant
  Given tenant A has no entitlement for data-shuttle and F052_FEATURE is in rollout_state tenant_list
  When the tenant admin PUTs state trial with trial_ends_at 2026-10-03 and sets an enabling override on F052_FEATURE
  Then evaluate returns entitlements.data-shuttle.allowed true with reason trial
  And entitlement.updated.v1 and feature-flag.updated.v1 are in the outbox

Scenario: Kill switch removes access everywhere
  Given tenant A and tenant B both have enabling overrides on F054_FEATURE
  When a platform operator PATCHes F054_FEATURE with kill true
  Then evaluate for both tenants returns enabled false with reason killed
  And a request to POST /api/v1/bridge/flows returns 403 denied with field_errors.module killed

Scenario: Tenant admin cannot change platform fields
  Given a tenant admin of tenant A
  When they PATCH F050_FEATURE with rollout_state general
  Then the response is 403 denied and the flag version is unchanged

Scenario: Invalid lifecycle transition
  Given F051_FEATURE in rollout_state draft
  When a platform operator PATCHes rollout_state general
  Then the response is 409 conflict with field_errors.rollout_state invalid_transition
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F002 (tenants, `is_internal` flag, users), F003 (roles `tenant-admin`, `platform-operator`, audit writer); decisions sections 2–4, 9, 10; contracts row F048
- Blocks: F050, F051, F052, F053, F054, F055, F056, F057, F039
- Conflicts with: none (disjoint owned paths)
- External dependencies: none
- Risks and mitigations: a stale cache could keep a killed module alive on one instance, so the invalidator is tested with a two-instance harness and the TTL bounds the exposure to 30 seconds; a flag registry seeded by migration can drift from `work/plan.md`, so `cargo xtask check-flags` (F044) compares the seed list with feature IDs; percentage rollout must be stable across restarts, so bucketing uses murmur3 over `tenant_id ‖ key` with a fixed seed, never random.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F002 and F003 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F048/`
- [ ] Migration file name and owned paths claimed, including `crates/auth/src/entitlements/**`
- [ ] Fixture factory and schema-per-worker isolation available in `testing/harness/`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for every mutation
- [ ] `RequireModule` guard documented for module features and used by at least one downstream test
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets`, `check-contracts`, and `check-flags` pass
- [ ] Rollback verified: disable `F048_FEATURE` (admin routes unmounted, guard fails closed with reason `not_entitled`), run down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Tenant administrators can manage module entitlements and feature-flag overrides at `/admin/entitlements` and `/admin/feature-flags`; platform operators manage flag lifecycle and the kill switch.
- Migration adds `entitlements`, `feature_flags`, and `flag_overrides` and seeds the E008 flag registry in `draft`; rollback drops them. Feature is off by default behind `F048_FEATURE`.
