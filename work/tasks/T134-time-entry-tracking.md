---
id: T134
type: task
status: planned
parent_epic: E007
parent_feature: F034
parent_story: S067
depends_on: [S067]
owned_paths: [crates/domain/src/workload/**, crates/persistence/src/workload/**, services/api/src/workload/**, services/api/migrations/*_workload_*.sql, testing/features/F034/database/**]
feature_flag: F034_FEATURE
branch: t134-time-entry-tracking
started_at: null
finished_at: null
---

# T134 — Time entry tracking, import, and reconciliation

## Identity

- Parent story: `S067` Workload conflicts and time entries
- Owner: platform
- Branch: `t134-time-entry-tracking`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 4, 7; `docs/capability-contracts.md` row F034

## Objective

Create the `workload` migration and implement native time entries, the external timesheet import with pending reconciliation, and the audited reconciliation decisions — SR-S067-04 through SR-S067-09 and the write half of SR-S067-10.

## Specification

- Owned files: `services/api/migrations/<ts>_workload_create_tables.sql` and `.down.sql`, `crates/domain/src/workload/{time_entry.rs, effort.rs, service.rs, errors.rs}`, `services/api/src/workload/{handlers_time_entries.rs, handlers_import.rs, handlers_reconcile.rs, dto.rs}`, `crates/persistence/src/workload/{mod.rs, time_entry_repository.rs, effort_summary_repository.rs}`.
- DDL: `time_entries`, `effort_summaries`, `effort_summary_sources`, `workload_conflicts`, and `workload_conflict_allocations` exactly as in ticket section 4, including `check (hours between 0.25 and 24 and (hours * 4) = floor(hours * 4))`, `check (source in ('native','external'))`, `check (reconciliation_state in ('none','pending','accepted','rejected','superseded'))`, `check (resolution in ('keep_native','accept_external','sum'))`, `check ((source = 'external') = (source_system is not null and external_id is not null))`, `check (cost_amount = round(hours * cost_rate, 2))` over the typed `cost_rate`, `cost_currency`, `cost_amount` columns that replace `cost_snapshot jsonb`, the partial unique `time_entries_external_ref_idx on (tenant_id, source_system, external_id) where source = 'external' and deleted_at is null`, unique `(resource_id, period_start)` on `workload_conflicts`, `workload_conflict_allocations(conflict_id, allocation_id)` cascading from the conflict and restricting the allocation, `effort_summary_sources` keyed by `(tenant_id, scope, scope_id, period_start, source_kind)` with `check (source_kind in ('time_entry','reconciliation','allocation','capacity'))` and a composite cascade to `effort_summaries` (replacing `source_versions jsonb`), the `effort_summaries` scope check that exactly one of `row_id`, `project_sheet_id`, `resource_id` is set and matches `scope`, restrict foreign keys from `time_entries` to `resources`, `rows`, `sheets`, `users`, and itself, and a statement trigger rejecting an `UPDATE` of `reconciled_by`, `reconciled_at`, `resolution`, or `reason` once set.
- Routes: `POST /api/v1/time-entries`, `PATCH /api/v1/time-entries/{id}`, `DELETE /api/v1/time-entries/{id}`, `POST /api/v1/time-entries/import`, `POST /api/v1/time-entries/reconcile`, `GET /api/v1/rows/{id}/effort?include_children=true|false`.
- Behavior: create validates `entry_date ≤ today` in the tenant time zone, quarter-hour steps, a 24 h daily total per resource, a note of at most 500 characters, and stamps `source: native` with the resource's effective cost rate in `cost_rate`, `cost_currency`, and `cost_amount`. Patch and delete require `If-Match`, honor `time_entry_lock_days` (default 30) for the owner, allow `resource-admin` at any time, and refuse external entries with 409 `conflict` `code_detail: external_entry`. Import accepts `source_system` (1–50 chars) and up to 2,000 entries, resolves `resource_id` or `user_email` inside the tenant, is atomic per request, deduplicates on `(source_system, external_id)`, marks an entry `pending` when `(resource_id, row_id, entry_date)` matches a native entry and `accepted` otherwise, and returns `{ created, updated, pending_reconciliation, rejected }`. Reconcile applies `keep_native`, `accept_external`, or `sum` with a 10–1,000 character reason, writes the immutable reconciliation fields, and returns 409 `conflict` for a non-pending entry. Row effort returns `planned_hours`, `actual_hours` (native plus accepted external), `pending_external_hours`, `remaining_hours`, `variance_hours`, `variance_pct`, `by_resource`, the F009 descendant rollup when requested, and cost fields only through `ResponseScope::with_costs(actor)`.
- Data access (decision section 2.1): `time_entry.rs`, `effort.rs`, `service.rs`, and the three handlers hold no SQL. `TimeEntryRepository` (owns `time_entries`) exposes `record_native_entry`, `daily_total_for_resource`, `find_native_collision`, `upsert_external_by_external_ref`, `list_pending_reconciliation`, `apply_reconciliation_decision`, `mark_superseded`, `sum_actual_hours_by_row`, `sum_actual_hours_by_resource`, and `sum_pending_external_hours`; `EffortSummaryRepository` (owns `effort_summaries`, `effort_summary_sources`) serves `get_row_effort`. The whole import batch, and each reconciliation decision with its audit row and outbox enqueue, run in one `UnitOfWork`, which is what makes the import atomic per request.
- Events and audit: `time-entry.recorded.v1` on native create, patch, delete, and each imported entry with `changed_fields.source`; `time-entry.reconciled.v1` per decision; audit rows `time-entry.create`, `time-entry.update`, `time-entry.delete`, `time-entry.import`, `time-entry.reconcile` with before and after states. Every mutation requires `Idempotency-Key`, held 24 hours in `idempotency_keys`.
- Dependencies: F033 resources, cost rates, and the `resource-admin` role; F009 hierarchy for the descendant rollup; F027 retention for soft-deleted entries; F004 outbox and idempotency store.
- Feature flag: `F034_FEATURE` gates the routes; the migration runs regardless.
- Rollback: disable `F034_FEATURE`, then run the down migration on an empty tenant, which drops the five tables — `effort_summary_sources` and `workload_conflict_allocations` before their parents — and the trigger.

## TDD

- Failing test first: `testing/features/F034/api/time_entry_tests.rs::time_entry_create_stores_native_source_and_cost_snapshot`, `::time_entry_daily_cap_rejects_over_24_hours`, `::time_entry_rejects_non_quarter_hours_and_future_dates`, `::locked_entry_denies_owner_but_allows_admin`, `::patch_of_external_entry_returns_external_entry_conflict`; `testing/features/F034/api/import_tests.rs::import_is_idempotent_per_external_id`, `::imported_entry_colliding_with_native_is_pending`, `::import_rejects_bad_rows_by_index_only`; `testing/features/F034/api/reconcile_tests.rs::accept_external_supersedes_native_and_audits`, `::reconcile_on_accepted_entry_is_conflict`; `testing/features/F034/api/effort_tests.rs::row_effort_returns_planned_actual_and_variance`, `::effort_costs_hidden_for_non_admin`; `testing/features/F034/database/constraint_tests.rs::hours_check_rejects_out_of_range_and_non_quarter_values`, `::external_ref_partial_unique_index_blocks_duplicates`, `::reconciliation_fields_are_immutable_once_set`, `::cost_amount_check_rejects_mismatched_rate`, `::conflict_allocation_row_pair_is_unique`, `::deleting_conflict_cascades_allocation_rows`, `::allocation_restrict_blocks_purge_with_conflict_rows`, `::effort_summary_requires_exactly_one_scope_column`, `::summary_source_kind_is_unique_per_summary_and_cascades`; `testing/features/F034/database/migration_tests.rs::migration_down_drops_tables_and_trigger`
- Fixtures/mocks: `testing/fixtures/workload.rs` (Ana with 6 native hours on `Design API` for 2026-09-02, a colliding 8-hour external row, tenant B twin); in-memory outbox recorder; fixed clock `2026-09-03T00:00:00Z`
- Targeted command: `cargo xtask test-feature F034`
- Full command: `cargo xtask test-all`

## Exit criteria

- [ ] Tests above written before implementation and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; routes mounted in `services/api/src/router.rs` behind `F034_FEATURE`; OpenAPI regenerated without drift
- [ ] Audit rows and outbox events verified for create, patch, delete, import, and each reconciliation decision
- [ ] Owned-path, 500-line, lint, and security gates pass
- [ ] Handoff evidence recorded in S067
- [ ] `finished_at` recorded
