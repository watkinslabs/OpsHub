---
id: T190
type: task
status: planned
parent_epic: E008
parent_feature: F048
parent_story: S095
depends_on: [T189]
owned_paths: [crates/domain/src/entitlements/**, crates/auth/src/entitlements/**, services/api/src/entitlements/**, testing/features/F048/api/**, testing/features/F048/requirements/**, testing/features/F048/performance/**]
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
- Decision references: `docs/architecture-decisions.md` sections 2–4, 10; `docs/capability-contracts.md` row F048

## Objective

Implement the entitlement domain service, the two entitlement routes plus the evaluation route, and the shared `RequireModule` guard with its cached evaluator and outbox-driven invalidation.

## Specification

- Owned paths: `crates/domain/src/entitlements/{mod.rs, entitlement.rs, decision.rs, errors.rs, service.rs}`, `crates/auth/src/entitlements/{mod.rs, evaluator.rs, guard.rs, invalidator.rs}`, `services/api/src/entitlements/{mod.rs, routes.rs, handlers_entitlement.rs, handlers_evaluate.rs, dto.rs}`
- Contract/input: `UpsertEntitlementRequest { state, limits, trial_ends_at? }` with headers `Idempotency-Key`, `If-Match`; `EvaluateQuery { keys?, modules? }`; `RequireModule(ModuleSlug)` extractor reading `{ tenant_id, correlation_id }` from the gateway context and `Arc<Evaluator>` from app state.
- Output/behavior: `GET /api/v1/entitlements` synthesizes `state: none, version: 0` rows for missing modules; `PUT /api/v1/entitlements/{module}` validates against `limit_schema()`, upserts, writes audit and `entitlement.updated.v1` in the same transaction, returns `EntitlementResponse` with the new `version`; `GET /api/v1/feature-flags/evaluate` returns `EvaluateResponse` per FR-F048-07 and FR-F048-09; guard denies with `403 { code: "denied", field_errors: { module: reason } }` where reason is `not_entitled`, `trial_expired`, `suspended`, `flag_disabled`, or `killed`; `Evaluator` caches decisions for 30 seconds in `moka` keyed by `(tenant_id, key)` and `Invalidator` drops entries on `entitlement.updated.v1` / `feature-flag.updated.v1`; errors map per ticket section 4.
- Dependencies: T189 schema; F003 `authz::require(actor, Permission::TenantAdmin)` and audit writer; F004 outbox writer and JetStream consumer for the invalidator; F002 `tenants.is_internal`.
- Feature flag: `F048_FEATURE` gates router mounting; the guard fails closed (`not_entitled`) when the flag is off so downstream modules stay dark.

## TDD

- Failing test first: `testing/features/F048/api/entitlement_tests.rs::entitlement_list_synthesizes_none_rows`, `::entitlement_upsert_rejects_unknown_limit_key`, `::entitlement_trial_requires_end_date`, `::entitlement_unknown_module_not_found`, `::entitlement_member_upsert_denied`, `::entitlement_cross_tenant_body_invalid`, `::entitlement_upsert_writes_audit_and_outbox`; `testing/features/F048/api/guard_tests.rs::module_guard_denies_before_handler`, `::module_guard_cache_invalidated_by_event`; `testing/features/F048/api/evaluate_tests.rs::evaluate_marks_expired_trial`, `::evaluate_rejects_more_than_20_modules`
- Targeted command: `cargo xtask test-feature F048`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/entitlements.rs` tenants A/B/internal, admin, member; in-memory outbox recorder; injectable clock for TTL; a probe handler that records whether it ran

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Router mounted in `services/api/src/router.rs` behind the flag; `Evaluator` in app state; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S095
- [ ] `finished_at` recorded
