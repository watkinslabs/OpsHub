---
id: T108
type: task
status: planned
parent_epic: E006
parent_feature: F027
parent_story: S054
depends_on: [T107]
owned_paths: [testing/features/F027/**]
feature_flag: F027_FEATURE
branch: t108-compliance-tests
started_at: null
finished_at: null
---

# T108 — Compliance tests

## Identity

- Parent story: `S054` Access review
- Owner: platform
- Branch: `t108-compliance-tests`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 4, 9; `docs/capability-contracts.md` row F027

## Objective

Complete the F027 harness with the permission-negative and tenant-isolation suite, database constraint checks, the end-to-end hold, export, purge, and review browser flow, accessibility checks, and the performance lane.

## Specification

- Owned paths: `testing/features/F027/api/negative_tests.rs`, `testing/features/F027/database/constraint_tests.rs`, `testing/features/F027/e2e/compliance.spec.ts`, `testing/features/F027/accessibility/compliance.a11y.spec.ts`, `testing/features/F027/performance/{purge_bench.rs, review_bench.rs}`, `testing/features/F027/{README.md, requirements/cases.md}`
- Contract/input: tenants A and B each with two compliance-admins and one tenant-admin; 12,400 soft-deleted rows of mixed ages with 310 held; 40 principals; 5,000-principal generator; two-person policies enabled on tenant A and disabled on tenant B.
- Output/behavior: negatives prove `denied` for tenant-admin on all ten routes, `not_found` for foreign-tenant holds, exports, purges, and reports, rejection of a tenant B download URL on tenant A, and proposer self-confirmation denial; database tests prove the running-export partial index, policy checks, the purge trigger, and the new child-table constraints (`tenant_export_kinds` and `purge_request_kinds` reject a repeated kind and an unknown `kind` value, `access_review_decisions` rejects a duplicate principal and a principal absent from `access_review_principals`, every child row cascades when its parent is deleted, and `legal_holds.scope_id` must be null exactly when `scope_kind = 'tenant'`); the E2E flow applies a hold, requests an export and downloads it, proposes a purge as admin one and confirms as admin two with the retyped code, generates a review, and revokes a stale guest; accessibility runs axe on all five routes and the purge dialog; performance proves purge of 100,000 rows under 10 minutes and review of 5,000 principals under 60 s.
- Data access: fixtures and assertions go through the `crates/persistence/src/compliance/` repositories — `RetentionPolicyRepository`, `LegalHoldRepository`, `TenantExportRepository`, `PurgeRequestRepository`, `AccessReviewRepository` — and through the owning repositories of F006, F045, F017, F016, F019, F003, F036, and F038 for their records; no test opens a connection or issues SQL of its own except `constraint_tests.rs`, which exercises the DDL directly and also asserts that no `jsonb` column exists in the `compliance` migration (decision section 2.1).
- Dependencies: T105, T106, T107 implementations; `testing/harness/` Playwright and criterion runners; MinIO from compose.
- Feature flag: `F027_FEATURE`

## TDD

- Failing test first: `testing/features/F027/api/negative_tests.rs::tenant_admin_denied_on_all_routes`, `::foreign_tenant_ids_not_found`, `::foreign_download_url_rejected`; `testing/features/F027/database/constraint_tests.rs::one_running_export_per_tenant`, `::purge_completed_requires_confirmed_at`, `::export_kind_duplicate_rejected`, `::export_kind_unknown_value_rejected`, `::purge_kind_duplicate_rejected`, `::review_decision_duplicate_principal_rejected`, `::review_decision_requires_principal_row`, `::child_rows_cascade_on_parent_delete`, `::hold_scope_id_null_only_for_tenant_scope`, `::compliance_migration_has_no_jsonb_column`; `testing/features/F027/e2e/compliance.spec.ts::hold_export_two_person_purge_review`, `::proposer_cannot_confirm_own_purge`; `testing/features/F027/accessibility/compliance.a11y.spec.ts::compliance_routes_have_no_serious_violations`; `testing/features/F027/performance/review_bench.rs::access_review_5000_principals_under_60s`
- Targeted command: `cargo xtask test-feature F027`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/compliance.rs`; Playwright signs in as two admins in separate contexts

## Exit criteria

- [ ] Tests written before implementation and observed failing where the behavior is not yet present
- [ ] All seven lanes green in targeted and full modes with evidence under `testing/evidence/F027/`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S054
- [ ] `finished_at` recorded
