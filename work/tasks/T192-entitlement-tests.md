---
id: T192
type: task
status: planned
parent_epic: E006
parent_feature: F048
parent_story: S096
depends_on: [T191]
owned_paths: [testing/features/F048/**]
feature_flag: F048_FEATURE
branch: t192-entitlement-tests
started_at: null
finished_at: null
---

# T192 — Entitlement tests

## Identity

- Parent story: `S096` Flag administration
- Owner: platform
- Branch: `t192-entitlement-tests`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 4, 9; `docs/capability-contracts.md` row F048

## Objective

Complete the F048 harness with the E2E, accessibility, performance, and two-instance propagation suites so every FR/NFR in the ticket has executable evidence before the feature is accepted.

## Specification

- Owned paths: `testing/features/F048/e2e/entitlements.spec.ts`, `testing/features/F048/accessibility/entitlements.a11y.spec.ts`, `testing/features/F048/database/constraint_tests.rs`, `testing/features/F048/performance/{guard_bench.rs, evaluate_bench.rs, propagation_tests.rs}`, `testing/features/F048/requirements/cases.md` (final traceability), `testing/features/F048/README.md`
- Contract/input: seeded tenant A (admin, member), tenant B, internal tenant, platform operator; flag registry in mixed states; Playwright sessions per role; two API instances sharing one PostgreSQL schema and one JetStream subject for propagation.
- Output/behavior: E2E covers enable trial with two limit values → override → module link appears → kill removes access with `denied` panel, asserting the `limits` object round-trips unchanged through the API while it is stored as `entitlement_limits` rows; accessibility covers axe on both pages, dialog focus trap, typed-key confirmation, badge text alternatives; performance covers guard p99 < 1 ms warm, evaluate 50 keys p95 < 100 ms, invalidation lag measured across two instances < 30 s and < 2 s on the writing instance; the requirements table maps every FR-F048-01..15 and NFR-F048-01..04 to at least one case ID with lane.
- Data access: every fixture write and every assertion in this harness goes through the `crates/persistence/src/entitlements/` repositories — no test opens a connection or issues SQL of its own (decision section 2.1). `constraint_tests.rs` proves the normalized shape: `entitlement_limits` rejects a duplicate `(entitlement_id, limit_key)`, rejects a key with no `module_limit_keys` row for the module, rejects a row whose `module` differs from its entitlement's, and loses its rows when the entitlement is deleted; `entitlements.module` must exist in `modules`; `modules.gate_flag_key` is unique and cannot be orphaned by deleting a seeded flag; a rollout pair absent from `flag_rollout_transitions` is refused; and no `jsonb` column remains in the module's tables.
- Dependencies: T191 UI and routes; F044 `check-flags` for the seed-list comparison run as part of this task's evidence.
- Feature flag: `F048_FEATURE` on for the suite; one E2E case runs with the flag off and asserts the admin routes are absent and the guard fails closed.

## TDD

- Failing test first: `testing/features/F048/e2e/entitlements.spec.ts::enable_trial_then_override_shows_module`, `::kill_switch_removes_module_access`, `::flag_off_hides_admin_routes`; `testing/features/F048/accessibility/entitlements.a11y.spec.ts::admin_pages_have_no_serious_axe_violations`, `::kill_dialog_traps_focus_and_requires_key`; `testing/features/F048/database/constraint_tests.rs::duplicate_limit_key_per_entitlement_rejected`, `::undeclared_limit_key_rejected`, `::limit_row_module_must_match_entitlement`, `::limit_rows_cascade_with_entitlement`, `::entitlement_module_must_exist_in_catalog`, `::rollout_transition_pair_must_be_seeded`, `::module_tables_hold_no_jsonb_column`; `testing/features/F048/performance/propagation_tests.rs::kill_propagates_to_second_instance_within_30s`, `guard_bench.rs::warm_guard_p99_under_1ms`
- Targeted command: `cargo xtask test-feature F048`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: Playwright against the real API with seeded roles; Rust fixtures seeded through `EntitlementRepository`, `ModuleCatalogRepository`, `FeatureFlagRepository`, and `FlagOverrideRepository`; k6 script for evaluate; docker compose profile `two-api` from F004 for the propagation test

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] E2E, accessibility, database-constraint, performance, and propagation lanes pass; evidence stored under `testing/evidence/F048/`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S096
- [ ] `finished_at` recorded
