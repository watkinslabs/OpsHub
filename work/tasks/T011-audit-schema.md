---
id: T011
type: task
status: planned
parent_epic: E001
parent_feature: F003
parent_story: S006
depends_on: [T010]
owned_paths: [crates/domain/src/authz/**, services/api/src/authz/**, apps/web/src/features/authz/**, testing/features/F003/api/**, testing/features/F003/database/**, testing/features/F003/frontend/**]
feature_flag: F003_FEATURE
branch: t011-audit-schema
started_at: null
finished_at: null
---

# T011 — Audit schema

## Identity

- Parent story: `S006` Activity history
- Owner: platform
- Branch: `t011-audit-schema`

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4
- Canonical contract: `docs/capability-contracts.md` row F003

## Objective

Implement the audit writer with redaction, the database `AuthAuditSink`, the monthly partition job, the audit query route, and the audit log UI over the partitioned table created in T009, reached through the new `AuditEventRepository` in `crates/persistence/src/authz/`.

## Specification

- Owned paths: `crates/persistence/src/authz/audit_event_repository.rs`, `crates/domain/src/authz/{audit.rs, redact.rs, service_audit.rs, partitions.rs}`, `services/api/src/authz/{handlers_audit.rs, audit_sink.rs}`, `apps/web/src/features/authz/{AuditLogPage.tsx, AuditFilters.tsx, AuditEventRow.tsx, DiffViewer.tsx, CopyCorrelationButton.tsx}`
- Contract/input: `AuditEvent { actor_id, actor_kind, action, resource: Option<ResourceRef>, before: Option<Value>, after: Option<Value>, ip, user_agent, correlation_id, occurred_at }` where `before`, `after`, and the computed `diff` are stored in the `jsonb` columns as opaque snapshots that are never filtered or joined by key; `record_audit(uow: &mut UnitOfWork, event: AuditEvent) -> Result<AuditId, AuditError>` computing `diff` as RFC 6902 operations, applying `#[audit(redact)]` via the `Redact` derive, and calling `AuditEventRepository::insert` — the only place an `audit_events` statement exists; `AuditEventRepository` also owns `list_events` for the cursor query and `ensure_partition(month)`; list query `{ cursor?, limit? ≤ 200, actor_id?, resource_kind?, resource_id?, action_prefix?, correlation_id?, occurred_from?, occurred_to? }`; `PartitionJob` implementing the F004 `Job` trait on kind `authz.partitions` scheduled monthly and calling `ensure_partition`.
- Output/behavior: route `GET /api/v1/audit-events` returns `Page<AuditEventResponse { id, actor, action, resource, diff, ip, user_agent, correlation_id, occurred_at }>` newest first using partition pruning through `AuditEventRepository::list_events`; access rule tenant-admin all, resource-owner own resources, others `403`; `audit_sink.rs` implements F038 `AuthAuditSink` by calling `record_audit`; the writer enqueues `audit.recorded.v1`; a failed insert returns an error that aborts the caller's transaction; the writer, redaction, sink, handler, partition job, and tests contain no SQL string or `sqlx::query*` call (decision 2.1); UI per ticket section 3 with the diff viewer exposing additions and removals as text and the copy-correlation button.
- Dependencies: T010 routes and extractor; F004 worker registry (job registered when F004 lands, otherwise the migration's three pre-created partitions cover the gap).
- Feature flag: `F003_FEATURE` gates the route, the sink swap, and the audit navigation entry.

## TDD

- Failing test first: `testing/features/F003/api/audit_tests.rs::record_audit_writes_row_in_caller_transaction`, `::audit_write_failure_aborts_mutation`, `::audit_redacts_tagged_fields`, `::audit_list_filters_and_pages_newest_first`, `::audit_member_denied_owner_scoped`, `::auth_sink_writes_login_events`, `::audit_writer_uses_audit_event_repository`; `testing/features/F003/database/audit_tests.rs::audit_list_uses_partition_pruning`, `::partition_job_creates_next_month`, `::audit_snapshots_round_trip_as_opaque_jsonb`; `testing/features/F003/frontend/AuditLogPage.test.tsx::filters_and_renders_diff`, `DiffViewer.test.tsx::exposes_changes_as_text`
- Targeted command: `cargo xtask test-feature F003`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/authz.rs` 1,000 audit rows across two partitions; MSW handlers

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Route mounted behind the flag; F038 uses the database sink; F002 mutations call `record_audit`; page registered
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S006
- [ ] `finished_at` recorded
