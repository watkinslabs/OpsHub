---
id: S067
type: story
status: planned
parent_epic: E007
parent_feature: F034
depends_on: [F034]
owned_paths: [crates/domain/src/workload/**, services/api/src/workload/**, services/worker/src/workload/**, services/api/migrations/*_workload_*.sql, testing/features/F034/api/**, testing/features/F034/database/**, testing/features/F034/requirements/**]
feature_flag: F034_FEATURE
branch: s067-workload-conflicts
started_at: null
finished_at: null
---

# S067 — Workload conflicts and time entries

## Identity

- Parent feature: `F034` Workload/actuals
- Owner: platform
- Branch: `s067-workload-conflicts`
- Child tasks: `T133` workload query, `T134` time entry tracking
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 7, 9; `docs/capability-contracts.md` row F034

## Vertical slice

As a resource manager, I want a workload read across resources and periods, persistent over-allocation conflicts with shift and reassign suggestions, and native time entries that an external timesheet import can never silently overwrite, so that I can find over-commitment and trust recorded actuals.

The slice is the `workload` backend: the three tables (`time_entries`, `effort_summaries`, `workload_conflicts`), the eight routes of the contract, the `conflict_detector` worker, and the three outbox events. The heatmap, conflicts panel, time sheet, reconciliation queue, and effort panel that consume it are S068 (T135); the load and latency gates are S068 (T136).

## Requirements

- **SR-S067-01:** `GET /api/v1/workload?from&to&granularity=week|day&resource_ids[]&project_sheet_id&skill` returns one row per resource and period with `available_hours`, `allocated_hours`, `actual_hours`, `utilization_pct` (null when `available_hours = 0`) and `status` in {`under` < 70, `ok` 70–100, `over` > 100, `no_capacity`}, plus per-period totals; > 500 resources or > 182 days → 400 `invalid` (`WorkloadError::RangeTooLarge`) (covers FR-F034-01).
- **SR-S067-02:** `services/worker/src/workload/conflict_detector.rs` consumes `capacity.computed.v1` and, for the affected resource and span, upserts one `workload_conflicts` row per over-allocated period with `over_hours`, contributing `allocation_ids`, and `status: open`, publishes `workload-conflict.detected.v1` per newly opened conflict, and flips periods that are no longer over to `status: resolved` with `resolved_at`; it is idempotent by `(scope_id, source_version)` (FR-F034-02, NFR-F034-04).
- **SR-S067-03:** `GET /api/v1/workload/conflicts?resource_id&project_sheet_id&status&from&to` pages open and resolved conflicts and returns `suggestions`: `shift_within_float` for each contributing allocation whose task row has `total_float_days > 0` in F012 `schedule_results`, and up to three `reassign_to` candidates — active resources sharing a required skill with `remaining_hours ≥ over_hours` in that period, ranked by descending `remaining_hours` (FR-F034-03).
- **SR-S067-04:** `POST /api/v1/time-entries` writes a `source: native` entry with `resource_id`, `row_id`, its `project_sheet_id`, `entry_date` not after today in the tenant time zone, `hours` in 0.25–24 on quarter-hour steps, optional `note` ≤ 500 chars, and a `cost_snapshot` from the resource's effective cost rate; the resource's daily total may not exceed 24 h (400 `invalid` with `field_errors.hours`); `self` or `resource-admin` may create (FR-F034-04).
- **SR-S067-05:** `PATCH` and `DELETE /api/v1/time-entries/{id}` require `If-Match`, are allowed for the entry's own user inside `time_entry_lock_days` (default 30) and for `resource-admin` at any time, return 403 `denied` (`TimeEntryError::Locked`) otherwise, and return 409 `conflict` with `code_detail: external_entry` for an external entry (FR-F034-05).
- **SR-S067-06:** `POST /api/v1/time-entries/import` by a `resource-admin` accepts `source_system` (1–50 chars) and ≤ 2,000 entries, is idempotent per `(source_system, external_id)` — a repeat updates rather than duplicates — writes `source: external`, is atomic per request, and returns `{ created, updated, pending_reconciliation, rejected: [{ index, code }] }`; a `resource_id` outside the tenant is rejected per entry, not per request (FR-F034-06, NFR-F034-02, NFR-F034-04).
- **SR-S067-07:** An imported entry matching a native entry on `(resource_id, row_id, entry_date)` is stored `reconciliation_state: pending` and excluded from `actual_hours`; one with no native counterpart is `accepted`; no external write ever modifies or deletes a native row (FR-F034-07).
- **SR-S067-08:** `POST /api/v1/time-entries/reconcile` by a `resource-admin` applies `decisions[]` of `{ time_entry_id, resolution in {keep_native, accept_external, sum} }` with a `reason` of 10–1,000 chars: `keep_native` → external `rejected`; `accept_external` → native `superseded` with `superseded_by` and external `accepted`; `sum` → external `accepted` with both counting; a decision on a non-pending entry returns 409 `conflict` (`TimeEntryError::NotPending`). `reconciled_by`, `reconciled_at`, `resolution`, and `reason` are immutable once set — the DDL trigger rejects the `UPDATE` (FR-F034-08, FR-F034-14).
- **SR-S067-09:** Every mutation requires `Idempotency-Key`, writes an `audit_events` row with before/after state, and publishes `time-entry.recorded.v1` (native create, patch, delete, and each imported entry, with `changed_fields.source`), `time-entry.reconciled.v1` (per decision), or `workload-conflict.detected.v1` (per new open conflict) (FR-F034-11).
- **SR-S067-10:** Authorization: `resource-viewer` reads workload and conflicts and is denied import, reconcile, and other users' entries; a user without `resource-viewer` sees only their own workload row and entries; any cross-tenant id returns 404 `not_found`; cost fields pass through `ResponseScope::with_costs(actor)` and are absent for non-admins, and notes are excluded from log fields (FR-F034-12, NFR-F034-02).

## Surfaces

- Rust domain: `crates/domain/src/workload/{mod.rs, time_entry.rs, workload_row.rs, conflict.rs, suggestion.rs, effort.rs, errors.rs, service.rs}` with use cases `query_workload`, `detect_conflicts`, `list_conflicts_with_suggestions`, `record_time_entry`, `update_time_entry`, `delete_time_entry`, `import_time_entries`, `reconcile_time_entries`
- Rust API: `services/api/src/workload/{mod.rs, routes.rs, handlers_workload.rs, handlers_conflicts.rs, handlers_time_entries.rs, handlers_import.rs, handlers_reconcile.rs, dto.rs}` with `WorkloadResponse`, `Page<ConflictResponse>`, `CreateTimeEntryRequest`, `UpdateTimeEntryRequest`, `TimeEntryResponse`, `ImportTimeEntriesRequest`, `ImportResult`, `ReconcileRequest`, `ReconcileResult`
- Worker: `services/worker/src/workload/{mod.rs, conflict_detector.rs}` registered in `services/worker/src/registry.rs` behind `F034_FEATURE`
- Data/migration: `services/api/migrations/<ts>_workload_create_tables.sql` and `.down.sql` creating `time_entries`, `effort_summaries`, `workload_conflicts` with the checks, the `time_entries_external_ref_idx` partial unique index, the `(resource_id, period_start)` conflict uniqueness, and the reconciliation-immutability trigger from ticket section 4
- Events consumed/published: consumes `capacity.computed.v1` (F033); publishes `time-entry.recorded.v1`, `time-entry.reconciled.v1`, `workload-conflict.detected.v1`
- Mocks/fixtures: `testing/fixtures/workload.rs` — tenants A and B, `resource-admin`, `resource-viewer`, two linked users, F033 resources with capacity and an over-allocated week of 2026-10-12 (16 available, 22 allocated), F012 `schedule_results` with 4 days of float on `Design API`, native entries, and a 2,000-row external payload with one colliding entry; fixed clock `2026-09-03T00:00:00Z`, tenant time zone UTC

## TDD harness

- Test path: `testing/features/F034/{requirements,api,database}/`
- Feature flag: `F034_FEATURE`
- Targeted command: `cargo xtask test-feature F034`
- Full command: `cargo xtask test-all`
- First failing tests: `workload_rows_carry_utilization_and_status`, `workload_range_over_182_days_is_invalid`, `capacity_event_opens_conflict_with_over_hours`, `conflict_lists_shift_and_reassign_suggestions`, `time_entry_daily_cap_rejects_over_24_hours`, `import_is_idempotent_per_external_id`, `imported_entry_colliding_with_native_is_pending`, `accept_external_supersedes_native_and_audits`, `viewer_cannot_import_or_reconcile`, `foreign_tenant_time_entry_is_not_found`

## Exit criteria

- [ ] SR-S067-01 through SR-S067-10 written as failing tests before implementation
- [ ] Tasks T133 and T134 complete; routes mounted from `services/api/src/workload/routes.rs` in `services/api/src/router.rs` under `/api/v1/workload` and `/api/v1/time-entries`, and `conflict_detector.rs` registered in `services/worker/src/registry.rs`
- [ ] Migration applies and reverts on CI PostgreSQL 18; constraint and trigger tests pass in `testing/features/F034/database/`
- [ ] Permission-negative and tenant-isolation cases pass: viewer import, other user's entry, non-viewer own-row-only, cross-tenant `not_found`, costs hidden
- [ ] Audit rows and outbox events verified for create, patch, delete, import, and each reconciliation decision
- [ ] Handoff evidence recorded in the F034 ticket under `testing/evidence/F034/`
