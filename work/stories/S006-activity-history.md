---
id: S006
type: story
status: planned
parent_epic: E001
parent_feature: F003
depends_on: [S005]
owned_paths: [crates/domain/src/authz/**, services/api/src/authz/**, apps/web/src/features/authz/**, testing/features/F003/**]
feature_flag: F003_FEATURE
branch: s006-activity-history
started_at: null
finished_at: null
---

# S006 — Activity history

## Identity

- Parent feature: `F003` Authorization and audit
- Owner: platform
- Branch: `s006-activity-history`

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 9
- Canonical contract: `docs/capability-contracts.md` row F003

## Vertical slice

As a tenant administrator or resource owner, I want every mutation, authentication event, and permission change recorded in an immutable, queryable audit log with before/after diffs and correlation ids, so that I can answer who changed what and when, and so later features get audit for free by calling one writer.

## Requirements

- **SR-S006-01:** `record_audit(uow, AuditEvent)` calls `AuditEventRepository::insert` on the caller's `UnitOfWork` so the `audit_events` row lands in the caller's transaction with actor, action, resource, the opaque `jsonb` `before`, `after`, and `diff` snapshots, ip, user agent, and `correlation_id`, and enqueues `audit.recorded.v1` (covers FR-F003-09).
- **SR-S006-02:** `audit_events` rejects `UPDATE` and `DELETE` through the `audit_immutable` trigger and is partitioned monthly with three future partitions created by the migration and by a monthly worker job (FR-F003-10).
- **SR-S006-03:** `GET /api/v1/audit-events` pages newest-first with `limit` ≤ 200 and filters `actor_id`, `resource_kind`, `resource_id`, `action` prefix, `correlation_id`, `occurred_from`, `occurred_to`; tenant-admin reads all, resource-owner reads own resources, others get `403` (FR-F003-11).
- **SR-S006-04:** Role and ACL mutations from S005 write audit rows with entry-level diffs over their `role_permissions` and `resource_acl_permissions` rows and honour `Idempotency-Key` replays (FR-F003-12).
- **SR-S006-05:** Fields tagged `#[audit(redact)]` are redacted in `before`/`after` before insert; the database `AuthAuditSink` implementation replaces the F038 in-memory sink (FR-F003-09, NFR-F003-02).
- **SR-S006-06:** Cross-tenant audit queries return empty pages and foreign ids return `404`; the negative matrix covers every F003 route for cross-tenant, role, guest, and field-level cases (FR-F003-13, NFR-F003-02).
- **SR-S006-07:** `/admin/audit` renders filters, rows, the diff viewer, and copy-correlation-id with all UI states; audit write overhead and 10,000,000-row list meet NFR-F003-01 (FR-F003-14, NFR-F003-03).

## Surfaces

- Infrastructure/container: none
- Rust service/API: `crates/domain/src/authz/{audit.rs, redact.rs, service_audit.rs, partitions.rs}`; `services/api/src/authz/{handlers_audit.rs, audit_sink.rs}`; every `audit_events` statement — insert, cursor list, and partition creation — lives in `AuditEventRepository` in `crates/persistence/src/authz/`, and the writer, redaction, sink, query handler, partition job, and tests hold no SQL (decision 2.1)
- Data/migration: none new; uses the partitioned `audit_events` table from S005's migration, whose `before`, `after`, and `diff` stay `jsonb` as opaque snapshots and diffs that are never queried by key, reached only through `AuditEventRepository`; partition job registered with the F004 worker registry
- React/UI: `apps/web/src/features/authz/{AuditLogPage.tsx, AuditFilters.tsx, AuditEventRow.tsx, DiffViewer.tsx, CopyCorrelationButton.tsx}`
- Mocks/fixtures: `testing/fixtures/authz.rs` extended with 1,000 audit rows across two partitions and a 10,000,000-row generator for the performance lane; MSW handlers

## TDD harness

- Test path: `testing/features/F003/{api,database,frontend,e2e,accessibility,performance}/`
- Feature flag: `F003_FEATURE`
- Targeted command: `cargo xtask test-feature F003`
- Full command: `cargo xtask test-all`
- First failing tests: `record_audit_writes_row_in_caller_transaction`, `audit_update_and_delete_raise_immutable`, `audit_list_filters_and_pages_newest_first`, `audit_member_denied_owner_scoped`, `audit_redacts_tagged_fields`, `audit_cross_tenant_empty_page`, `audit_list_10m_rows_p95`

## Exit criteria

- [ ] Requirement tests SR-S006-01 through SR-S006-07 written first and failing
- [ ] Tasks T011 and T012 complete; database `AuthAuditSink` wired for F038 and the writer used by F002 routes
- [ ] Unit, API, database, React, E2E, accessibility, permission, and performance tests pass
- [ ] Production call path named: `crates/domain/src/authz/audit.rs::record_audit` called from every F002, F038, and F003 mutation; `services/api/src/authz/handlers_audit.rs` mounted at `GET /api/v1/audit-events`; `apps/web/src/features/authz/AuditLogPage.tsx` mounted at `/admin/audit`
- [ ] Handoff evidence recorded in the F003 ticket
