---
id: T105
type: task
status: planned
parent_epic: E006
parent_feature: F027
parent_story: S053
depends_on: [S053]
owned_paths: [services/api/migrations/*_compliance_*.sql, crates/domain/src/compliance/**, services/api/src/compliance/**, services/worker/src/compliance/**, apps/web/src/features/compliance/**, testing/features/F027/api/**, testing/features/F027/database/**, testing/features/F027/frontend/**]
feature_flag: F027_FEATURE
branch: t105-retention-and-legal-hold
started_at: null
finished_at: null
---

# T105 — Retention and legal hold

## Identity

- Parent story: `S053` Retention/export
- Owner: platform
- Branch: `t105-retention-and-legal-hold`
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 7; `docs/capability-contracts.md` row F027

## Objective

Create the `compliance` schema and implement retention policies, the nightly retention sweep, legal holds with scope matching and two-person release, and the retention and holds pages.

## Specification

- Owned paths: `services/api/migrations/<ts>_compliance_create_tables.sql` and `.down.sql`, `crates/domain/src/compliance/{mod.rs, policy.rs, hold.rs, errors.rs, service.rs}`, `services/api/src/compliance/{mod.rs, routes.rs, handlers_policy.rs, handlers_hold.rs, dto.rs}`, `services/worker/src/compliance/{mod.rs, retention_sweep.rs}`, `apps/web/src/features/compliance/{CompliancePage.tsx, RetentionTable.tsx, LegalHoldTable.tsx, NewHoldDialog.tsx, api.ts, hooks.ts, routes.ts}`
- Contract/input: `PutRetentionPolicyRequest { soft_delete_days, purge_after_days, auto_soft_delete }` with `If-Match`; `CreateLegalHoldRequest { name, reason, scope, expires_at? }`; job subject `jobs.compliance.retention_sweep` with `{ tenant_id, as_of }`.
- Output/behavior: routes `GET /api/v1/compliance/retention-policies`, `PUT /api/v1/compliance/retention-policies/{id}`, `POST /api/v1/compliance/legal-holds`, `DELETE /api/v1/compliance/legal-holds/{id}`; policies seeded per tenant on first read with defaults (30 days soft delete, purge `null`); `audit_events` policy floor 365; `hold.rs` exposes `HoldScope::matches(record_ref)` and `is_held` used by the sweep and by T106; release checks `security_policies.two_person_hold_release`; sweep soft-deletes only `auto_soft_delete` kinds, marks `purge_eligible`, skips held records, runs under per-tenant quota 1 with 1,000-row batches; events `retention-policy.updated.v1`, `legal-hold.applied.v1` (`action: applied|released`); audit `retention-policy.update`, `legal-hold.apply`, `legal-hold.release`; DDL for `retention_policies`, `legal_holds`, `tenant_exports`, `purge_requests`, `purge_batches`, `access_reviews`, the purge status trigger, and indexes from ticket section 4.
- Dependencies: F003 `authz::require(actor, Permission::ComplianceAdmin)` and audit writer; F038 `security_policies`; F004 outbox and job transport; F006/F045/F017/F016/F019 `deleted_at` columns for sweep targets.
- Feature flag: `F027_FEATURE` gates router mounting and job registration; migration runs regardless.

## TDD

- Failing test first: `testing/features/F027/api/policy_tests.rs::retention_policy_defaults_seeded`, `::retention_policy_rejects_audit_below_365`, `::retention_policy_stale_version_conflicts`, `::retention_policy_tenant_admin_denied`; `testing/features/F027/api/hold_tests.rs::legal_hold_scope_sheet_matches_rows`, `::legal_hold_two_person_release_denied`, `::legal_hold_foreign_tenant_not_found`; `testing/features/F027/api/sweep_tests.rs::retention_sweep_skips_held_records`, `::retention_sweep_marks_purge_eligible`; `testing/features/F027/database/migration_tests.rs::compliance_tables_exist_with_constraints`, `::purge_after_less_than_soft_delete_rejected`; `testing/features/F027/frontend/RetentionTable.test.tsx::edits_policy_and_shows_field_errors`
- Targeted command: `cargo xtask test-feature F027`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/compliance.rs` mixed-age soft-deleted rows and 310 held rows; in-process worker with fixed clock

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; router and job registered behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S053
- [ ] `finished_at` recorded
