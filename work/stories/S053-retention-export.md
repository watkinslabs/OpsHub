---
id: S053
type: story
status: planned
parent_epic: E006
parent_feature: F027
depends_on: [F003, F010]
owned_paths: [crates/domain/src/compliance/**, services/api/src/compliance/**, services/worker/src/compliance/**, apps/web/src/features/compliance/**, services/api/migrations/*_compliance_*.sql, testing/features/F027/**]
feature_flag: F027_FEATURE
branch: s053-retention-export
started_at: null
finished_at: null
---

# S053 — Retention/export

## Identity

- Parent feature: `F027` Governance/compliance
- Owner: platform
- Branch: `s053-retention-export`
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 7; `docs/capability-contracts.md` row F027

## Vertical slice

As a compliance administrator, I want to set retention per record kind, freeze records under legal hold, export everything my tenant stores, and destroy expired records only after a second administrator confirms, so that my organization can prove retention and deletion obligations are met.

## Requirements

- **SR-S053-01:** `GET/PUT /api/v1/compliance/retention-policies` return and replace one policy per kind with the day limits and `audit_events` floor of 365, publishing `retention-policy.updated.v1` (covers FR-F027-01, FR-F027-02).
- **SR-S053-02:** The nightly `retention_sweep` job soft-deletes past `soft_delete_days` only for kinds with `auto_soft_delete`, marks `purge_eligible` past `purge_after_days`, and skips records under an active hold (FR-F027-03, FR-F027-04).
- **SR-S053-03:** `POST/DELETE /api/v1/compliance/legal-holds` apply and release holds by scope with two-person release when the security policy requires it, publishing `legal-hold.applied.v1` (FR-F027-04, FR-F027-05).
- **SR-S053-04:** `POST /api/v1/compliance/tenant-exports` enqueues one export per tenant at a time; the worker writes per-kind files and `manifest.json` into a ZIP with redacted secrets and a 7-day signed URL; `GET` returns progress and publishes `tenant-export.completed.v1` (FR-F027-06, FR-F027-07).
- **SR-S053-05:** `POST /api/v1/compliance/purges` returns a preview with candidate and held counts and a confirmation code; `POST /confirm` enforces the code, 24-hour window, and two-person rule, publishes `purge.confirmed.v1`, and the worker hard-deletes in 1,000-row batches skipping held records (FR-F027-08, FR-F027-09, FR-F027-10).
- **SR-S053-06:** Export and purge jobs resume from the last completed kind or batch after a worker restart and dead-letter after 3 retries with the request marked `failed` (NFR-F027-04).
- **SR-S053-07:** Non-compliance-admins receive `denied` and foreign-tenant IDs `not_found` on every route (FR-F027-13).
- **SR-S053-08:** The retention, holds, exports, and purges pages implement the states in ticket section 3 with the retyped confirmation code (FR-F027-14, NFR-F027-03).

## Surfaces

- Infrastructure/container: MinIO bucket `tenant-exports` with 7-day lifecycle in the compose baseline
- Rust service/API: `crates/domain/src/compliance/{policy.rs, hold.rs, export.rs, purge.rs, redaction.rs, errors.rs, service.rs}`; `services/api/src/compliance/{routes.rs, handlers_policy.rs, handlers_hold.rs, handlers_export.rs, handlers_purge.rs, dto.rs}`; `services/worker/src/compliance/{retention_sweep.rs, tenant_export.rs, purge_execute.rs}`
- Data/migration: `services/api/migrations/<ts>_compliance_create_tables.sql` creating the six tables and trigger from ticket section 4
- React/UI: `apps/web/src/features/compliance/{CompliancePage.tsx, RetentionTable.tsx, LegalHoldTable.tsx, NewHoldDialog.tsx, ExportPanel.tsx, ExportProgress.tsx, PurgeWizard.tsx, PurgePreview.tsx, PurgeConfirmDialog.tsx, api.ts, hooks.ts, routes.ts}`
- Mocks/fixtures: `testing/fixtures/compliance.rs` mixed-age soft-deleted rows, held rows, fixture secrets for redaction checks; in-process worker with controllable clock

## TDD harness

- Test path: `testing/features/F027/{api,database,frontend,performance}/`
- Feature flag: `F027_FEATURE`
- Targeted command: `cargo xtask test-feature F027`
- Full command: `cargo xtask test-all`
- First failing tests: `retention_policy_rejects_audit_below_365`, `retention_sweep_skips_held_records`, `legal_hold_two_person_release_denied`, `tenant_export_second_running_conflicts`, `tenant_export_redacts_secrets`, `purge_preview_counts_held_records`, `purge_confirm_same_actor_denied`, `purge_resumes_after_restart`

## Exit criteria

- [ ] Requirement tests SR-S053-01 through SR-S053-08 written first and failing
- [ ] Tasks T105 and T106 complete and wired through `services/api` router and `services/worker` job registry
- [ ] Unit, API, database, React, permission, and performance tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/compliance/routes.rs` mounted in `services/api/src/router.rs`; jobs registered in `services/worker/src/registry.rs`
- [ ] Handoff evidence recorded in the F027 ticket
