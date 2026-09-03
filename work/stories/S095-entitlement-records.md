---
id: S095
type: story
status: planned
parent_epic: E008
parent_feature: F048
depends_on: [F002, F003]
owned_paths: [crates/domain/src/entitlements/**, crates/auth/src/entitlements/**, services/api/src/entitlements/**, services/api/migrations/*_entitlements_*.sql, testing/features/F048/**]
feature_flag: F048_FEATURE
branch: s095-entitlement-records
started_at: null
finished_at: null
---

# S095 — Entitlement records

## Identity

- Parent feature: `F048` Entitlements and feature flags
- Owner: platform
- Branch: `s095-entitlement-records`
- Decision references: `docs/architecture-decisions.md` sections 2–4, 10; `docs/capability-contracts.md` row F048

## Vertical slice

As a tenant administrator, I want to record which modules my tenant is entitled to with limits and trial dates, and I want every module route to check that record through one guard, so that premium modules are gated by data rather than by code paths scattered across features.

Out of this slice: flag overrides, lifecycle transitions, kill switch, and the admin pages (S096); seat counting against F002 user totals (later ticket).

## Requirements

- **SR-S095-01:** `GET /api/v1/entitlements` returns all ten module slugs with stored or synthesized `state: none` records and `version` (covers FR-F048-01).
- **SR-S095-02:** `PUT /api/v1/entitlements/{module}` upserts with validation of `state`, `trial_ends_at`, and the module limit schema; unknown module → `404 not_found`, unknown limit key → `400 invalid` with `field_errors.limits.<key>` (FR-F048-02).
- **SR-S095-03:** `GET /api/v1/feature-flags/evaluate` returns `entitlements.<module>` decisions with `allowed`, `state`, `limits`, `reason` computed from entitlement state, trial expiry, and the module gate flag (FR-F048-07, FR-F048-09).
- **SR-S095-04:** `RequireModule` in `crates/auth/src/entitlements/` returns `403 denied` with `field_errors.module` before any handler executes, and reads a 30-second cache invalidated by outbox events (FR-F048-10, FR-F048-12).
- **SR-S095-05:** Every upsert requires `Idempotency-Key` and `If-Match`, writes an audit row with diff, and publishes `entitlement.updated.v1` (FR-F048-11).
- **SR-S095-06:** Tenant context comes from the gateway only; a body naming another `tenant_id` returns `400 invalid` and tenant B can never read tenant A records (FR-F048-15, NFR-F048-02).
- **SR-S095-07:** Warm guard evaluation is under 1 ms p99 and evaluate with 20 modules is under 100 ms p95 (NFR-F048-01).

## Surfaces

- Infrastructure/container: none beyond F004 baseline
- Rust service/API: `crates/domain/src/entitlements/{mod.rs, module.rs, entitlement.rs, decision.rs, errors.rs, service.rs}`; `crates/auth/src/entitlements/{mod.rs, evaluator.rs, guard.rs, invalidator.rs}`; `services/api/src/entitlements/{mod.rs, routes.rs, handlers_entitlement.rs, handlers_evaluate.rs, dto.rs}`
- Data/migration: `services/api/migrations/<ts>_entitlements_create_tables.sql` creating `entitlements`, `feature_flags`, `flag_overrides` with the seed rows from ticket section 4
- React/UI: none in this story (S096 covers admin UI)
- Mocks/fixtures: `testing/fixtures/entitlements.rs` tenants A/B/internal, tenant-admin, member, platform-operator; in-memory outbox recorder; injectable clock for cache TTL

## TDD harness

- Test path: `testing/features/F048/api/`, `testing/features/F048/database/`, `testing/features/F048/performance/`
- Feature flag: `F048_FEATURE`
- Targeted command: `cargo xtask test-feature F048`
- Full command: `cargo xtask test-all`
- First failing tests: `entitlement_list_synthesizes_none_rows`, `entitlement_upsert_rejects_unknown_limit_key`, `entitlement_trial_requires_end_date`, `module_guard_denies_before_handler`, `evaluate_marks_expired_trial`, `entitlement_cross_tenant_body_invalid`

## Exit criteria

- [ ] Requirement tests SR-S095-01 through SR-S095-07 written first and failing
- [ ] Tasks T189 and T190 complete and wired through `services/api` router
- [ ] Unit, API, database, permission, and performance tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/entitlements/routes.rs` mounted in `services/api/src/router.rs`; `crates/auth/src/entitlements/guard.rs` exported as `opshub_auth::entitlements::RequireModule`
- [ ] Handoff evidence recorded in the F048 ticket
