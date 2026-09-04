---
id: T190
type: task
status: planned
parent_epic: E006
parent_feature: F048
parent_story: S095
depends_on: [T189]
owned_paths: [crates/domain/src/entitlements/**, crates/persistence/src/entitlements/**, crates/auth/src/entitlements/**, services/api/src/entitlements/**, testing/features/F048/api/**, testing/features/F048/requirements/**, testing/features/F048/performance/**]
feature_flag: F048_FEATURE
branch: t190-entitlement-middleware
started_at: null
finished_at: null
---

# T190 — Entitlement middleware

## Identity

- Parent story: `S095` Entitlement records
- Owner: platform
- Branch: `t190-entitlement-middleware`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 4, 10; `docs/capability-contracts.md` row F048

## Objective

Implement the entitlement domain service, the two entitlement routes plus the evaluation route, and the shared `RequireModule` guard with its cached evaluator and outbox-driven invalidation.

## Specification

- Owned paths: `crates/domain/src/entitlements/{mod.rs, entitlement.rs, decision.rs, errors.rs, service.rs}`, `crates/persistence/src/entitlements/entitlement_repository.rs`, `crates/auth/src/entitlements/{mod.rs, evaluator.rs, guard.rs, invalidator.rs}`, `services/api/src/entitlements/{mod.rs, routes.rs, handlers_entitlement.rs, handlers_evaluate.rs, dto.rs}`
- Contract/input: `UpsertEntitlementRequest { state, limits, trial_ends_at? }` with headers `Idempotency-Key`, `If-Match`; `EvaluateQuery { keys?, modules? }`; `RequireModule(ModuleSlug)` extractor reading `{ tenant_id, correlation_id }` from the gateway context and `Arc<Evaluator>` from app state.
- Output/behavior: `GET /api/v1/entitlements` lists the catalog through `ModuleCatalogRepository::list_modules` and synthesizes `state: none, limits: {}, version: 0` for modules with no row; `PUT /api/v1/entitlements/{module}` validates each key against `module_limit_keys`, then `EntitlementRepository::upsert_entitlement_with_limits` writes the record, replaces its `entitlement_limits` rows (delete removed keys, insert or update the submitted ones), and writes audit and `entitlement.updated.v1` in the same `UnitOfWork`, returning `EntitlementResponse` whose `limits` is still a JSON object; `GET /api/v1/feature-flags/evaluate` returns `EvaluateResponse` per FR-F048-07 and FR-F048-09; guard denies with `403 { code: "denied", field_errors: { module: reason } }` where reason is `not_entitled`, `trial_expired`, `suspended`, `flag_disabled`, or `killed`; `Evaluator` caches decisions for 30 seconds in `moka` keyed by `(tenant_id, key)` and `Invalidator` drops entries on `entitlement.updated.v1` / `feature-flag.updated.v1`; errors map per ticket section 4.
- Data access: `crates/persistence/src/entitlements/entitlement_repository.rs` owns `entitlements` and `entitlement_limits` and holds every SQL statement of this task; `service.rs`, the handlers, `evaluator.rs`, `guard.rs`, and `invalidator.rs` depend on `EntitlementRepository`, `ModuleCatalogRepository`, `FeatureFlagRepository`, and `FlagOverrideRepository` traits and contain no `sqlx::query*` call or connection; the `moka` cache is filled from repository reads, so the middleware never queries the database directly (decision section 2.1).
- Dependencies: T189 schema and `ModuleCatalogRepository`; F003 `authz::require(actor, Permission::TenantAdmin)` and audit writer; F004 outbox writer and JetStream consumer for the invalidator; F002 `tenants.is_internal`.
- Feature flag: `F048_FEATURE` gates router mounting; the guard fails closed (`not_entitled`) when the flag is off so downstream modules stay dark.

## TDD

- Failing test first: `testing/features/F048/api/entitlement_tests.rs::entitlement_list_synthesizes_none_rows`, `::entitlement_upsert_rejects_unknown_limit_key`, `::entitlement_trial_requires_end_date`, `::entitlement_unknown_module_not_found`, `::entitlement_member_upsert_denied`, `::entitlement_cross_tenant_body_invalid`, `::entitlement_upsert_writes_audit_and_outbox`, `::entitlement_upsert_deletes_omitted_limit_keys`, `::entitlement_response_keeps_limits_object`; `testing/features/F048/api/guard_tests.rs::module_guard_denies_before_handler`, `::module_guard_cache_invalidated_by_event`; `testing/features/F048/api/evaluate_tests.rs::evaluate_marks_expired_trial`, `::evaluate_rejects_more_than_20_modules`
- Targeted command: `cargo xtask test-feature F048`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/entitlements.rs` tenants A/B/internal, admin, member, seeded through the repositories; in-memory implementations of the four repository traits for the guard and evaluator unit tests; in-memory outbox recorder; injectable clock for TTL; a probe handler that records whether it ran

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Router mounted in `services/api/src/router.rs` behind the flag; `Evaluator` in app state; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S095
- [ ] `finished_at` recorded
