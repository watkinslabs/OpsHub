---
id: F048
type: feature
status: planned
priority: P0
owner: platform
estimate: 5
target_milestone: M5
parent_epic: E006
depends_on: [F002, F003]
blocks: [F050, F051, F052, F053, F054, F055, F056, F057, F039]
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/entitlements/**, crates/persistence/src/entitlements/**, crates/auth/src/entitlements/**, services/api/src/entitlements/**, apps/web/src/features/entitlements/**, services/api/migrations/*_entitlements_*.sql, testing/features/F048/**]
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
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 9, 10; `docs/capability-contracts.md` row F048
- Module slug: `entitlements`

## 2. Requirement specification

### Problem and user outcome

Premium modules (Dynamic View, WorkApps, Data Shuttle, DataMesh, Bridge, Calendar, Pivot, DAM, AI) must be turned on per tenant, rolled out gradually, limited per tenant, and turned off instantly without touching domain data. Today nothing records which tenant is entitled to which module, and there is no single evaluator that a route can call. Every E008 feature needs one answer to "may this tenant use module X right now, and with which limits".

As a tenant administrator, I want to see and change which modules my tenant is entitled to and which feature flags are active for my tenant, so that I can roll a module out to my organization deliberately and switch it off if it misbehaves. As a platform operator, I want every flag to carry an owner, rollout state, disable procedure, and cleanup ticket, so that no flag becomes an orphan.

### Functional requirements

- **FR-F048-01:** `GET /api/v1/entitlements` returns one record per row of the seeded `modules` catalog (`dynamic-views`, `workapps`, `data-shuttle`, `datamesh`, `bridge`, `calendar-app`, `pivots`, `assets`, `ai-assist`, `ai-insights`) with `state` (`none`, `trial`, `active`, `suspended`), `limits`, `trial_ends_at`, `source` (`manual`, `plan`), and `version`; `limits` stays a JSON object in the response and is assembled by `EntitlementRepository` from one `entitlement_limits` row per limit key; a module with no `entitlements` row is returned with `state: none`, `limits: {}`, and `version: 0`.
- **FR-F048-02:** `PUT /api/v1/entitlements/{module}` by a `tenant-admin` upserts the record with `{ state, limits, trial_ends_at? }`, keeping `limits` as a request object; a `module` absent from the `modules` catalog returns `404 not_found`; `state: trial` without `trial_ends_at` returns `400 invalid` with `field_errors.trial_ends_at`; each `limits` key must have a `module_limit_keys(module, limit_key)` row (for example `data-shuttle` declares `max_flows`, `max_rows_per_run`, `max_file_mb`) or the request returns `400 invalid` with `field_errors.limits.<key>`, and the composite foreign key on `entitlement_limits` enforces the same rule in the database; the upsert replaces the record's limit rows with exactly the submitted keys, deleting the omitted ones in the same transaction.
- **FR-F048-03:** `GET /api/v1/feature-flags` returns every registered flag with `key`, `description`, `owner`, `rollout_state` (`draft`, `internal`, `percentage`, `tenant_list`, `general`, `retired`), `rollout_percent` (0–100), `default_enabled`, `disable_procedure`, `cleanup_ticket`, `override` (the calling tenant's override if any), and `version`; keys match `^F[0-9]{3}_FEATURE$` or `^[A-Z][A-Z0-9_]{2,63}$`.
- **FR-F048-04:** `PATCH /api/v1/feature-flags/{key}` by a `tenant-admin` with `If-Match` sets a tenant override `{ override: { enabled: bool, reason: string(1–500), expires_at?: rfc3339 } }` or clears it with `{ override: null }`; a platform operator (role `platform-operator`, granted through F003 role bindings on the platform tenant) may additionally patch `owner`, `rollout_state`, `rollout_percent`, `default_enabled`, `disable_procedure`, and `cleanup_ticket`; a tenant-admin sending platform fields receives `403 denied`.
- **FR-F048-05:** Rollout state transitions are restricted to `draft→internal→percentage→tenant_list→general→retired` and any state `→retired`; the permitted pairs are rows in the seeded `flag_rollout_transitions` table and are checked with `FeatureFlagRepository::transition_allowed`, never against a list held in the handler; `retired` requires a non-empty `cleanup_ticket` matching `^[FST][0-9]{3}$` and a `disable_procedure` of at least 20 characters; an invalid transition returns `409 conflict` with `field_errors.rollout_state = "invalid_transition"`.
- **FR-F048-06:** `PATCH /api/v1/feature-flags/{key}` with `{ kill: true, reason }` by a platform operator sets `default_enabled: false`, `rollout_state: internal`, and marks every tenant override `suspended` in one `UnitOfWork` transaction spanning `FeatureFlagRepository::apply_lifecycle_change` and `FlagOverrideRepository::suspend_overrides_for_flag`, so the next evaluation for every tenant returns `enabled: false` with `reason: killed`.
- **FR-F048-07:** `GET /api/v1/feature-flags/evaluate?keys=K1,K2&modules=M1,M2` returns `{ flags: { K: { enabled, reason } }, entitlements: { M: { allowed, state, limits, reason } } }` for the calling tenant where flag `reason` is one of `override`, `suspended_override`, `killed`, `retired`, `percentage`, `tenant_list`, `default`, and entitlement `reason` is one of `active`, `trial`, `trial_expired`, `suspended`, `not_entitled`; up to 50 keys and 20 modules per call, more returns `400 invalid`.
- **FR-F048-08:** Evaluation order for a flag is: killed or retired → `false`; active tenant override → its value; `general` → `true`; `tenant_list` → `true` only with an enabling override; `percentage` → `true` when `murmur3(tenant_id ‖ key) mod 100 < rollout_percent`; `internal` → `true` only for tenants with `is_internal = true`; `draft` → `false`; otherwise `default_enabled`.
- **FR-F048-09:** A module is `allowed` only when its entitlement `state` is `active`, or `trial` with `trial_ends_at` in the future, and the module's gate flag, read from `modules.gate_flag_key` (`F050_FEATURE` for `dynamic-views`, `F051_FEATURE` for `workapps`, `F052_FEATURE` for `data-shuttle`, `F053_FEATURE` for `datamesh`, `F054_FEATURE` for `bridge`, `F055_FEATURE` for `calendar-app`, `F056_FEATURE` for `pivots`, `F057_FEATURE` for `assets`, `F039_FEATURE` for `ai-assist`, `F040_FEATURE` for `ai-insights`) evaluates `enabled: true`.
- **FR-F048-10:** The shared `RequireModule` guard in `crates/auth/src/entitlements/` rejects a request for a non-allowed module with `403 denied`, body `{ code: "denied", message, field_errors: { module: "<reason>" }, correlation_id }`, before any handler code runs; every E008 module router mounts this guard.
- **FR-F048-11:** Every entitlement or flag mutation requires `Idempotency-Key` and `If-Match`, writes an `audit_events` row with before/after diff, and publishes `entitlement.updated.v1` or `feature-flag.updated.v1` through the outbox with `changed_fields`.
- **FR-F048-12:** Evaluation results are cached in-process per `(tenant_id, key)` for at most 30 seconds and invalidated by the outbox consumer on `entitlement.updated.v1` and `feature-flag.updated.v1`, so a kill switch takes effect on every API instance within 30 seconds worst case and within 2 seconds on the instance that performed the write.
- **FR-F048-13:** Tenant overrides with `expires_at` in the past are ignored by evaluation and are pruned nightly by the F004 scheduler calling `FlagOverrideRepository::prune_expired_overrides`; the job holds no SQL of its own; an expired override appears in `GET /feature-flags` with `override.expired: true`.
- **FR-F048-14:** The web admin pages `/admin/entitlements` and `/admin/feature-flags` render only for `tenant-admin` (denied state otherwise), let the admin change entitlement state and limits, set or clear a flag override with a reason, and show a confirmation dialog listing affected modules before disabling; a platform operator additionally sees the lifecycle editor and kill switch. Each module with `state: none` renders an upgrade row naming the capabilities it unlocks and the action that turns it on. Limit fields are rendered from the module's declared limit schema and submitted as the `limits` object.
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
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062), Lucide icons `ToggleLeft`, `ToggleRight`, `ShieldCheck`, `Lock`, `AlertTriangle`, `Power`; tokens from `apps/web/src/design/tokens.css`.

- Design: `design/artboards/Entitlements.dc.html` on the canvas indexed by `design/canvas.json`. The ticket is the contract and the artboard is the picture; when they disagree the ticket wins.

## 4. Technical specification

Canonical contract: `docs/capability-contracts.md` row F048 (aggregate `entitlement`, module `entitlements`, roles `tenant-admin`).

### Rust backend

- Data access (decision section 2.1): `crates/persistence/src/entitlements/` holds `EntitlementRepository` (owns `entitlements`, `entitlement_limits`), `ModuleCatalogRepository` (owns `modules`, `module_limit_keys`), `FeatureFlagRepository` (owns `feature_flags`, `flag_rollout_transitions`), and `FlagOverrideRepository` (owns `flag_overrides`); no other class writes those tables, and each child table belongs to the repository of its parent object type. Named queries: `list_entitlements_with_limits`, `find_entitlement_by_module`, `upsert_entitlement_with_limits`, `replace_limits`, `list_modules`, `find_module`, `list_limit_keys_for_module`, `gate_flag_for_module`, `list_flag_registry`, `find_flag_by_key`, `transition_allowed`, `apply_lifecycle_change`, `find_override`, `list_overrides_for_tenant`, `set_override`, `clear_override`, `suspend_overrides_for_flag`, `prune_expired_overrides` — there is no generic query escape hatch. Every use case below depends on these repository traits and contains no SQL; the handlers, the `RequireModule` guard, the invalidator, the nightly prune job, and the test fixtures call repositories only. `Evaluator` reads entitlement, module, flag, and override state through these traits behind its cache and never issues SQL of its own. An entitlement upsert (record plus its limit rows), a lifecycle change, an override change, and the kill switch (flag row plus every override) each run in one `UnitOfWork` that also writes the audit row and the outbox entry.
- Domain entities in `crates/domain/src/entitlements/`: `ModuleSlug` (enum of the ten modules; `limit_schema() -> &[LimitKey]` and `gate_flag() -> FlagKey` mirror the seeded `module_limit_keys` and `modules.gate_flag_key` rows and are verified against them by a startup check through `ModuleCatalogRepository`), `Entitlement { id, tenant_id, module: ModuleSlug, state: EntitlementState, limits: Limits (a `BTreeMap<LimitKey, i64>` materialized from `entitlement_limits` rows, never a `jsonb` blob), trial_ends_at: Option<DateTime<Utc>>, source: EntitlementSource, version, created/updated actor+time }`, `FeatureFlag { key: FlagKey, description, owner: String, rollout_state: RolloutState, rollout_percent: u8, default_enabled: bool, disable_procedure: String, cleanup_ticket: Option<WorkItemId>, version, created/updated actor+time }`, `FlagOverride { id, tenant_id, flag_key, enabled: bool, reason, expires_at, suspended: bool, version, audit fields }`, `FlagDecision { enabled, reason: FlagReason }`, `ModuleDecision { allowed, state, limits, reason: EntitlementReason }`.
- Use cases: `list_entitlements`, `upsert_entitlement`, `list_flags`, `patch_flag`, `set_override`, `clear_override`, `kill_flag`, `evaluate_flags`, `evaluate_modules`, `prune_expired_overrides` (the scheduler entry point, which calls `FlagOverrideRepository::prune_expired_overrides`); pure function `decide_flag(flag, override, tenant) -> FlagDecision` implements FR-F048-08 and is unit tested exhaustively.
- Shared guard in `crates/auth/src/entitlements/`: `RequireModule(ModuleSlug)` axum `FromRequestParts` extractor and `EntitlementLayer` tower layer; both call `Evaluator::module(tenant_id, slug)` backed by a `moka` cache (30 s TTL, invalidated by `EvaluatorInvalidator` subscribed to the two events) whose misses are filled through the four repository traits injected at construction — the middleware never opens a connection or writes SQL. `Evaluator` is constructed once in `services/api/src/main.rs` app state and injected as `Arc<Evaluator>`.
- API endpoints (`services/api/src/entitlements/`): `GET /api/v1/entitlements`, `PUT /api/v1/entitlements/{module}`, `GET /api/v1/feature-flags`, `PATCH /api/v1/feature-flags/{key}`, `GET /api/v1/feature-flags/evaluate`. DTOs: `EntitlementResponse`, `UpsertEntitlementRequest { state, limits, trial_ends_at? }`, `FeatureFlagResponse`, `PatchFlagRequest { override?: OverridePatch | null, owner?, rollout_state?, rollout_percent?, default_enabled?, disable_procedure?, cleanup_ticket?, kill?: bool, reason? }`, `EvaluateQuery { keys: Vec<FlagKey>, modules: Vec<ModuleSlug> }`, `EvaluateResponse { flags, entitlements }`.
- Events: `entitlement.updated.v1` (payload adds `module`, `state`), `feature-flag.updated.v1` (payload adds `key`, `rollout_state`, `tenant_override_changed: bool`, `killed: bool`).
- Authorization: reads by any authenticated member of the tenant (module navigation needs them); entitlement upsert and override patch by `tenant-admin`; platform fields and kill by `platform-operator`; role checks via F003 `authz::require`.
- Validation: `limits` values are non-negative integers ≤ 1,000,000 and every key must have a `module_limit_keys` row for the module; `reason` 1–500 chars; `rollout_percent` 0–100; `expires_at` must be in the future and at most 365 days out; `keys` ≤ 50, `modules` ≤ 20.
- Error mapping: `EntitlementError::UnknownModule → 404 not_found`, `EntitlementError::LimitKeyUnknown → 400 invalid`, `FlagError::InvalidTransition → 409 conflict`, `FlagError::StaleVersion → 409 conflict`, `FlagError::PlatformFieldDenied → 403 denied`, `AuthzError::Denied → 403 denied`, module guard → `403 denied` with `field_errors.module`.

### Interface

Conventions are F028's: the error body with its six codes, `Idempotency-Key`, and `If-Match`. These
routes return whole configuration sets rather than pages, so `Page<T>` and the cursor do not appear.
`T?` is nullable; an absent optional field and an explicit `null` are the same thing, except on
`PatchFlagRequest.override` where `null` is the instruction to clear. Timestamps are RFC 3339 UTC,
`version` increments by one per write, and unlisted request fields are rejected with `400 invalid`.
`tenant_id` is never accepted in a body: it comes from the gateway context, and a body naming one is
`400 invalid` (FR-F048-15).

**`ModuleSlug`** — the ten seeded `modules` rows: `dynamic-views`, `workapps`, `data-shuttle`,
`datamesh`, `bridge`, `calendar-app`, `pivots`, `assets`, `ai-assist`, `ai-insights`. A slug outside
the catalog is `404 not_found` on `PUT /api/v1/entitlements/{module}` and `400 invalid` inside an
`evaluate` query.

**`Limits`** — the `limits` object of every shape below: a JSON map from `limit_key` to a
non-negative integer. Each key must have a `module_limit_keys(module, limit_key)` row for that
module, and each value must be 0–1,000,000; a violation is `400 invalid` with
`field_errors.limits.<key>`. `{}` is legal and means the module declares no limits or none are set.
The map is stored as one `entitlement_limits` row per entry and reassembled on read; it is never a
`jsonb` column.

**`EntitlementResponse`** — items of `GET /api/v1/entitlements` and the body of `PUT /api/v1/entitlements/{module}` (FR-F048-01)

| Field | Type | Notes |
|---|---|---|
| `module` | `ModuleSlug` | one entry per catalog row, always all ten, whether or not an `entitlements` row exists |
| `state` | `"none" \| "trial" \| "active" \| "suspended"` | |
| `limits` | `Limits` | `{}` when unset |
| `trial_ends_at` | timestamp? | present only when `state` is `trial` |
| `source` | `"manual" \| "plan"` | how the record was set |
| `version` | integer | `0` for a module with no stored row; pass as `If-Match` on the next `PUT` |
| `created_at` / `created_by` / `updated_at` / `updated_by` | | absent on a `version: 0` synthetic record |

`GET /api/v1/entitlements` returns `{ items: EntitlementResponse[] }` — a fixed ten-element set, not
a page. Any authenticated member of the tenant may read it, because module navigation depends on it.

**`UpsertEntitlementRequest`** — `PUT /api/v1/entitlements/{module}` (FR-F048-02)

| Field | Type | Required | Constraint |
|---|---|---|---|
| `state` | `"none" \| "trial" \| "active" \| "suspended"` | yes | caller is `tenant-admin`, else `403 denied` |
| `limits` | `Limits` | yes | replaces the record's limit rows with exactly these keys, deleting omitted ones; `{}` clears them all |
| `trial_ends_at` | timestamp? | when `state` is `trial` | must be in the future; missing → `400 invalid` with `field_errors.trial_ends_at` |

**`FeatureFlagResponse`** — items of `GET /api/v1/feature-flags` (FR-F048-03)

| Field | Type | Notes |
|---|---|---|
| `key` | string | matches `^F[0-9]{3}_FEATURE$` or `^[A-Z][A-Z0-9_]{2,63}$` |
| `description` | string | |
| `owner` | string | the team or person accountable for the flag |
| `rollout_state` | `"draft" \| "internal" \| "percentage" \| "tenant_list" \| "general" \| "retired"` | |
| `rollout_percent` | integer | 0–100; meaningful only in `percentage` |
| `default_enabled` | bool | |
| `disable_procedure` | string | how to turn it off safely; at least 20 chars once `retired` |
| `cleanup_ticket` | string? | a work-item id matching `^[FST][0-9]{3}$`; required once `retired` |
| `override` | `OverrideResponse?` | the **calling tenant's** override only; another tenant's is never visible |
| `version` | integer | pass as `If-Match` on the next `PATCH` |

**`OverrideResponse`**

| Field | Type | Notes |
|---|---|---|
| `enabled` | bool | |
| `reason` | string | why the override exists |
| `expires_at` | timestamp? | |
| `expired` | bool | `true` when `expires_at` is in the past; such an override is ignored by evaluation and pruned nightly (FR-F048-13) |
| `suspended` | bool | `true` when a kill switch suspended it |

**`PatchFlagRequest`** — `PATCH /api/v1/feature-flags/{key}`, every field optional, at least one present (FR-F048-04)

| Field | Type | Required | Constraint |
|---|---|---|---|
| `override` | `OverridePatch?` | no | tenant field; `null` clears the calling tenant's override. Writable by `tenant-admin` |
| `owner` | string | no | platform field, 1–120 chars |
| `rollout_state` | enum | no | platform field; the pair `(current, new)` must be a `flag_rollout_transitions` row, else `409 conflict` with `field_errors.rollout_state = "invalid_transition"` |
| `rollout_percent` | integer | no | platform field, 0–100 |
| `default_enabled` | bool | no | platform field |
| `disable_procedure` | string | no | platform field; ≥ 20 chars when moving to `retired` |
| `cleanup_ticket` | string? | no | platform field; `^[FST][0-9]{3}$`, required when moving to `retired` |
| `kill` | bool | no | platform field; `true` applies FR-F048-06 and requires `reason` |
| `reason` | string | with `kill` | 1–500 chars |

Any platform field present in a request from a caller who is not `platform-operator` is
`403 denied` and nothing is written — the request is rejected whole, never partly applied. A
`tenant-admin` may send `override` alone.

**`OverridePatch`**

| Field | Type | Required | Constraint |
|---|---|---|---|
| `enabled` | bool | yes | |
| `reason` | string | yes | 1–500 chars |
| `expires_at` | timestamp? | no | must be in the future and at most 365 days out, else `400 invalid` with `field_errors.override.expires_at` |

**`EvaluateQuery`** — the query string of `GET /api/v1/feature-flags/evaluate` (FR-F048-07)

| Field | Type | Required | Constraint |
|---|---|---|---|
| `keys` | string | no | comma-separated flag keys, at most 50; more → `400 invalid` with `field_errors.keys`; an unregistered key is returned with `enabled: false` and `reason: "default"` rather than failing the call |
| `modules` | string | no | comma-separated `ModuleSlug` values, at most 20; more → `400 invalid` with `field_errors.modules`; an unknown slug → `400 invalid` |

**`EvaluateResponse`**

| Field | Type | Notes |
|---|---|---|
| `flags` | map<string, `FlagDecision`> | keyed by flag key, one entry per requested key |
| `entitlements` | map<`ModuleSlug`, `ModuleDecision`> | one entry per requested module |

**`FlagDecision`**

| Field | Type | Notes |
|---|---|---|
| `enabled` | bool | the outcome of the FR-F048-08 order |
| `reason` | enum | exactly one of `override`, `suspended_override`, `killed`, `retired`, `percentage`, `tenant_list`, `default` — the rule that decided it, so a support question is answerable without re-deriving the evaluation |

**`ModuleDecision`**

| Field | Type | Notes |
|---|---|---|
| `allowed` | bool | `true` only when the state qualifies *and* the module's gate flag evaluates true (FR-F048-09) |
| `state` | `"none" \| "trial" \| "active" \| "suspended"` | the stored state, independent of the gate flag |
| `limits` | `Limits` | the module's current limits, so a caller enforces them without a second request |
| `reason` | enum | exactly one of `active`, `trial`, `trial_expired`, `suspended`, `not_entitled` |

**`RequireModule`** — the guard every gated module mounts (FR-F048-10). It runs before any handler
code, so a denied request never reaches the module's own routes.

```rust
pub struct RequireModule(pub ModuleSlug);

impl<S: Send + Sync> FromRequestParts<S> for RequireModule
where Arc<Evaluator>: FromRef<S> {
    type Rejection = ApiError;
    async fn from_request_parts(parts: &mut Parts, state: &S) -> Result<Self, Self::Rejection>;
}

pub struct EntitlementLayer(pub ModuleSlug);   // the router-level form of the same check

impl Evaluator {
    pub fn module(&self, tenant: TenantId, slug: ModuleSlug) -> Result<ModuleDecision, DomainError>;
    pub fn flag(&self, tenant: TenantId, key: &FlagKey) -> Result<FlagDecision, DomainError>;
}
```

A module router mounts `EntitlementLayer(ModuleSlug::Bridge)` once rather than repeating the check
per handler; a handler that needs the limits takes `RequireModule` as an extractor and reads the
`ModuleDecision` it carries. On `allowed: false` both produce `403 denied` with the body
`{ code: "denied", message, field_errors: { module: "<reason>" }, correlation_id }`, where `<reason>`
is the `ModuleDecision.reason` value — so `not_entitled`, `trial_expired`, and `suspended` are
distinguishable by the client, and a killed gate flag surfaces as `not_entitled`. With
`F048_FEATURE` disabled the guard fails closed with `not_entitled`.

**Status codes**

| Status | `code` | Produced by |
|---|---|---|
| `400` | `invalid` | a limit key the module does not declare, a limit value out of range, `trial` without `trial_ends_at`, `expires_at` past or beyond 365 days, over 50 keys or 20 modules, a body naming a `tenant_id` |
| `403` | `denied` | a non-admin upserting an entitlement or setting an override; a `tenant-admin` sending any platform field or `kill`; the `RequireModule` guard on a module that is not allowed |
| `404` | `not_found` | a `{module}` slug with no `modules` row, or a `{key}` with no `feature_flags` row |
| `409` | `conflict` | a `rollout_state` pair with no `flag_rollout_transitions` row, a stale `If-Match`, or an `Idempotency-Key` replayed with a different body |
| `429` | `rate_limited` | the shared F028 limiter; this feature adds none of its own |
| `503` | `unavailable` | the database is unreachable on a cache miss; the guard fails closed rather than allowing the module |

### Use case signatures

In `crates/domain/src/entitlements/`, with the guard and evaluator in
`crates/auth/src/entitlements/`. `ctx` carries tenant, actor, and correlation id; a use case takes a
`UnitOfWork` or repository traits, never a pool or connection, and returns the shared `DomainError`
mapped above.

```rust
fn list_entitlements(ctx: &Ctx, catalog: &dyn ModuleCatalogRepository, repo: &dyn EntitlementRepository) -> Result<Vec<Entitlement>, DomainError>;
fn upsert_entitlement(ctx: &Ctx, uow: &mut UnitOfWork, module: ModuleSlug, expected: Version, req: UpsertEntitlement) -> Result<Entitlement, DomainError>;
fn list_flags(ctx: &Ctx, flags: &dyn FeatureFlagRepository, overrides: &dyn FlagOverrideRepository) -> Result<Vec<FeatureFlagView>, DomainError>;
fn patch_flag(ctx: &Ctx, uow: &mut UnitOfWork, key: FlagKey, expected: Version, req: PatchFlag) -> Result<FeatureFlagView, DomainError>;
fn set_override(ctx: &Ctx, uow: &mut UnitOfWork, key: FlagKey, req: OverridePatch) -> Result<FlagOverride, DomainError>;
fn clear_override(ctx: &Ctx, uow: &mut UnitOfWork, key: FlagKey) -> Result<(), DomainError>;
fn kill_flag(ctx: &Ctx, uow: &mut UnitOfWork, key: FlagKey, reason: String) -> Result<FeatureFlag, DomainError>;
fn evaluate_flags(ctx: &Ctx, evaluator: &Evaluator, keys: &FlagKeySet) -> Result<BTreeMap<FlagKey, FlagDecision>, DomainError>;
fn evaluate_modules(ctx: &Ctx, evaluator: &Evaluator, modules: &ModuleSet) -> Result<BTreeMap<ModuleSlug, ModuleDecision>, DomainError>;
fn prune_expired_overrides(ctx: &Ctx, uow: &mut UnitOfWork, now: DateTime<Utc>, limit: u32) -> Result<u64, DomainError>;

fn decide_flag(flag: &FeatureFlag, over: Option<&FlagOverride>, tenant: &TenantFacts, now: DateTime<Utc>) -> FlagDecision;
```

`decide_flag` is pure — no `ctx`, no repository, no clock of its own — which is what makes the
FR-F048-08 order exhaustively unit testable and the percentage bucket reproducible across restarts.
`TenantFacts { tenant_id, is_internal }` is everything evaluation may know about a tenant.

Transaction boundaries. `upsert_entitlement` writes the `entitlements` row, the full replacement of
its `entitlement_limits` rows, the audit row, and `entitlement.updated.v1` in one `UnitOfWork`, so a
guard never reads a record whose limits are half-replaced. `patch_flag`, `set_override`, and
`clear_override` each write their row plus audit plus `feature-flag.updated.v1` in one `UnitOfWork`
under the expected version. `kill_flag` is the boundary that matters most: the `feature_flags`
lifecycle change and the suspension of *every* tenant's override commit together, so there is no
window in which the flag is killed for one tenant and live for another (FR-F048-06). Cache
invalidation happens after commit, driven by the outbox consumer, which is why the worst case is the
30-second TTL of FR-F048-12 and never a stale allow inside a transaction.

### PostgreSQL/SQLx

- Migration `*_entitlements_*.sql` creates, parents first, `feature_flags(key text primary key, description text not null, owner text not null, rollout_state text not null check (rollout_state in ('draft','internal','percentage','tenant_list','general','retired')), rollout_percent smallint not null default 0 check (rollout_percent between 0 and 100), default_enabled bool not null default false, disable_procedure text not null default '', cleanup_ticket text check (cleanup_ticket ~ '^[FST][0-9]{3}$'), version bigint not null default 1, created_by uuid not null references users(id) on delete restrict, created_at timestamptz not null, updated_by uuid not null references users(id) on delete restrict, updated_at timestamptz not null)`, `modules(slug text primary key, display_name text not null, gate_flag_key text not null unique references feature_flags(key) on delete restrict)`, `module_limit_keys(module text not null references modules(slug) on delete cascade, limit_key text not null, max_allowed bigint not null default 1000000 check (max_allowed between 0 and 1000000), primary key (module, limit_key))`, `flag_rollout_transitions(from_state text not null check (from_state in ('draft','internal','percentage','tenant_list','general','retired')), to_state text not null check (to_state in ('draft','internal','percentage','tenant_list','general','retired')), primary key (from_state, to_state))`, `entitlements(id uuid primary key, tenant_id uuid not null references tenants(id) on delete cascade, module text not null references modules(slug) on delete restrict, state text not null check (state in ('none','trial','active','suspended')), trial_ends_at timestamptz, source text not null default 'manual' check (source in ('manual','plan')), version bigint not null default 1, created_by uuid not null references users(id) on delete restrict, created_at timestamptz not null, updated_by uuid not null references users(id) on delete restrict, updated_at timestamptz not null, unique (tenant_id, module), unique (id, module))`, `entitlement_limits(tenant_id uuid not null references tenants(id) on delete cascade, entitlement_id uuid not null, module text not null, limit_key text not null, limit_value bigint not null check (limit_value between 0 and 1000000), primary key (entitlement_id, limit_key), foreign key (entitlement_id, module) references entitlements(id, module) on delete cascade, foreign key (module, limit_key) references module_limit_keys(module, limit_key) on delete restrict)`, and `flag_overrides(id uuid primary key, tenant_id uuid not null references tenants(id) on delete cascade, flag_key text not null references feature_flags(key) on delete cascade, enabled bool not null, reason text not null check (length(reason) between 1 and 500), expires_at timestamptz, suspended bool not null default false, version bigint not null default 1, created_by uuid not null references users(id) on delete restrict, created_at timestamptz not null, updated_by uuid not null references users(id) on delete restrict, updated_at timestamptz not null)`.
- Normalized sets (decision section 2, no array or map columns): `entitlement_limits` replaces `entitlements.limits jsonb` — a per-module limit was read by key, compared against usage, and validated against the module schema, so it is one row per `(entitlement_id, limit_key)` with an integer `limit_value`, cascading with its entitlement. `module_limit_keys` replaces the limit schema that only existed in Rust, so FR-F048-02's key validation is a foreign key rather than a code-side check, and `modules` replaces the hard-coded slug list and slug→gate-flag mapping of FR-F048-09, giving `entitlements.module` a real foreign key. `flag_rollout_transitions` replaces the transition list of FR-F048-05 with seeded rows (`draft→internal`, `internal→percentage`, `percentage→tenant_list`, `tenant_list→general`, `general→retired`, and every state → `retired`). Request and response bodies are unchanged: `limits` stays a JSON object on `PUT /api/v1/entitlements/{module}`, on `GET /api/v1/entitlements`, and inside `entitlements.<module>.limits` of `GET /api/v1/feature-flags/evaluate`; `EntitlementRepository` fans the object out to rows and reassembles it on read, replacing a set with one `delete` of removed keys plus one `insert ... on conflict (entitlement_id, limit_key) do update` inside the upsert's `UnitOfWork` transaction.
- `jsonb` audit: no `jsonb` column remains in this module. `entitlements.limits` was the only one and became `entitlement_limits`, because the product filters on it (limit enforcement compares a stored value against usage), validates its keys, and returns it per module — exactly the modelling error decision section 2 names. The before/after diffs of FR-F048-11 and the `changed_fields` payload of `entitlement.updated.v1` and `feature-flag.updated.v1` remain `jsonb` in the F003 `audit_events` and F004 outbox tables, which this feature writes but does not own: a diff and an event payload are the permitted schema-less cases and are never filtered by key.
- Invariants: unique `entitlements(tenant_id, module)` (one record per tenant per module) and unique `entitlements(id, module)` (the target of the `entitlement_limits` composite foreign key, which keeps a limit row on the same module as its parent); `entitlement_limits` primary key `(entitlement_id, limit_key)` blocks a duplicate limit key and its second foreign key blocks a key the module does not declare; unique `flag_overrides(tenant_id, flag_key)`; check `(state <> 'trial') or (trial_ends_at is not null)`; check `(rollout_state <> 'retired') or (cleanup_ticket is not null and length(disable_procedure) >= 20)`; `modules.gate_flag_key` is unique, so no two modules share a gate flag, and its foreign key means a seeded flag cannot be deleted while a module points at it; `feature_flags` is platform-scoped (no `tenant_id`) and seeded by migration with the eleven `F###_FEATURE` keys for E008 in state `draft`, owner `platform`; `modules` is seeded with the ten slugs and their gate flags, `module_limit_keys` with each module's declared keys, and `flag_rollout_transitions` with the nine permitted pairs (five chain steps plus `draft`, `internal`, `percentage`, and `tenant_list` straight to `retired`).
- Indexes: `entitlements(tenant_id)` and `entitlements(tenant_id, module)` for the list and guard lookups; `entitlement_limits(entitlement_id)` from the primary key serves limit assembly, plus `entitlement_limits(tenant_id, module, limit_key)` for the per-tenant limit report and `entitlement_limits(module, limit_key)` for the reverse "which tenants set this limit" query; `modules(gate_flag_key)` for kill-switch fan-out from a flag to its module; `module_limit_keys(module)`; `flag_overrides(tenant_id, flag_key)`; `flag_overrides(flag_key)` for `suspend_overrides_for_flag`; `flag_overrides(expires_at) where expires_at is not null and suspended = false` for the nightly prune.
- Retention/deletion: no soft delete (records are configuration, history lives in `audit_events`); rollback drops the seven tables, children before parents (`entitlement_limits`, `flag_overrides`, `entitlements`, `module_limit_keys`, `modules`, `flag_rollout_transitions`, `feature_flags`); the seed rows are recreated on re-apply.

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
- [ ] Rust unit tests: `decide_flag` truth table over every rollout state, percentage bucket determinism, limit schema validation, and repository-trait fakes proving no use case, guard, or job holds SQL
- [ ] API contract/integration tests: every route above with success and each error code
- [ ] Database migration/constraint tests: unique indexes, trial check, retired check, cascade on flag delete, seed rows, rollback ordering, and the new child tables — duplicate `(entitlement_id, limit_key)` rejected, a limit key not declared in `module_limit_keys` rejected, a limit row surviving its entitlement rejected, `entitlements.module` without a `modules` row rejected, a transition pair missing from `flag_rollout_transitions` rejected
- [ ] React component tests: `EntitlementsPage`, `FeatureFlagsPage`, `KillSwitchDialog`, `ModuleNotEntitled` states
- [ ] Browser E2E tests: enable trial, set override, module link appears, kill switch removes access
- [ ] Accessibility tests: axe on both pages, dialog focus trap, badge text
- [ ] Performance/load tests: guard p99 < 1 ms warm, evaluate 50 keys p95 < 100 ms, invalidation lag < 30 s

### Fast fanout configuration

- Test harness path: `testing/features/F048/`
- Feature flag: `F048_FEATURE`
- Fixture/seed factory: `testing/fixtures/entitlements.rs` builds tenant A (admin, member), tenant B, an internal tenant, a platform-operator actor, the seeded flag registry, and entitlements for `data-shuttle` (active) and `bridge` (trial expired)
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, UTC, murmur3 buckets precomputed for the fixture tenants
- Mock/stub contracts: outbox publisher recorded in memory; authz uses the real F003 engine with fixture bindings; cache uses an injectable clock; fixtures and assertions write and read through the `crates/persistence/src/entitlements/` repositories, and unit tests substitute in-memory implementations of the four repository traits
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

Scenario: Module limits round-trip as rows without changing the API
  Given the seeded catalog declares max_flows, max_rows_per_run and max_file_mb for data-shuttle
  When the tenant admin PUTs limits { max_flows: 5, max_rows_per_run: 10000 }
  Then entitlement_limits holds exactly those two rows for the entitlement
  And GET /api/v1/entitlements returns the same limits object
  And a PUT naming max_seats returns 400 invalid with field_errors.limits.max_seats

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
- [ ] Migration file name and owned paths claimed, including `crates/persistence/src/entitlements/**` and `crates/auth/src/entitlements/**`
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
- Migration adds `entitlements`, `entitlement_limits`, `modules`, `module_limit_keys`, `feature_flags`, `flag_rollout_transitions`, and `flag_overrides`, and seeds the module catalog, the per-module limit keys, the rollout transition graph, and the E008 flag registry in `draft`; per-module limits are rows rather than a `jsonb` blob while the API keeps its `limits` object; rollback drops them children first. Feature is off by default behind `F048_FEATURE`.
