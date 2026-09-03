---
id: T133
type: task
status: planned
parent_epic: E007
parent_feature: F034
parent_story: S067
depends_on: [S067]
owned_paths: [crates/domain/src/workload/**, services/api/src/workload/**, services/worker/src/workload/**, testing/features/F034/api/**]
feature_flag: F034_FEATURE
branch: t133-workload-query
started_at: null
finished_at: null
---

# T133 — Workload query and conflict detection

## Identity

- Parent story: `S067` Workload conflicts and time entries
- Owner: platform
- Branch: `t133-workload-query`
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 9; `docs/capability-contracts.md` row F034

## Objective

Implement the workload read (`GET /api/v1/workload`), the `capacity.computed.v1` conflict detector that maintains `workload_conflicts`, and the conflicts list with shift and reassign suggestions — SR-S067-01, SR-S067-02, SR-S067-03 and the read half of SR-S067-10.

## Specification

- Owned files: `crates/domain/src/workload/{mod.rs, workload_row.rs, conflict.rs, suggestion.rs, errors.rs}`, `services/api/src/workload/{mod.rs, routes.rs, handlers_workload.rs, handlers_conflicts.rs, dto.rs}`, `services/worker/src/workload/{mod.rs, conflict_detector.rs}`.
- Input: `GET /api/v1/workload` query `{ from, to, granularity: week|day, resource_ids[]?, project_sheet_id?, skill? }`; `GET /api/v1/workload/conflicts` query `{ resource_id?, project_sheet_id?, status?, from?, to?, cursor?, limit? }`; worker input `capacity.computed.v1 { tenant_id, resource_id, period_start, period_end, available_hours, source_version }`.
- Output: `WorkloadResponse { granularity, rows: [{ resource_id, period_start, period_end, available_hours, allocated_hours, actual_hours, utilization_pct, status }], totals }`. `utilization_pct = allocated_hours ÷ available_hours × 100`, rounded to one decimal, `null` when `available_hours = 0`; `status` is `no_capacity` when `available_hours = 0`, else `under` < 70, `ok` 70–100 inclusive, `over` > 100. `actual_hours` counts native plus `accepted` external entries only. Rows are served from `effort_summaries` scope `resource_period` and carry `stale: true` when a newer source event is queued.
- Limits: `resource_ids` resolving to more than 500 resources, or `to − from` greater than 182 days, or `to < from` → `WorkloadError::RangeTooLarge` → 400 `invalid`.
- Conflict detector: for each `(resource_id, period)` in the event span, compare `allocated_hours` from F033 allocations against `available_hours`; where allocated exceeds available, upsert `workload_conflicts` on `(resource_id, period_start)` with `over_hours = allocated − available`, `allocation_ids` (the contributing allocations, ascending), `status: open`, `detected_at`; publish `workload-conflict.detected.v1` only on the `open` transition. Periods no longer over move to `status: resolved` with `resolved_at` and write audit `workload-conflict.resolve`. Idempotent by `(scope_id, source_version)`; 3 retries then dead letter with `last_error`; spans carry `tenant_id`, `resource_id`, `correlation_id`; metric `conflict_detection_ms` exported.
- Suggestions: `shift_within_float { allocation_id, float_days }` for each contributing allocation whose task row has `total_float_days > 0` in F012 `schedule_results`; `reassign_to { resource_id, remaining_hours }` for up to three active resources sharing a required skill with `remaining_hours ≥ over_hours` in the period, ordered by `remaining_hours` descending then `resource_id`.
- Authorization: `resource-viewer` reads all rows; a user without `resource-viewer` receives only their own resource row and an empty conflicts page for other resources; foreign-tenant `resource_id` or conflict id → 404 `not_found`; cost fields never appear in these DTOs.
- Dependencies: F033 `resources`, `allocations`, capacity and `capacity.computed.v1`, the `resource-admin`/`resource-viewer` roles; F012 `schedule_results` for float; F004 job transport and outbox.
- Feature flag: `F034_FEATURE` gates the two routes and the detector registration; the migration (T134) runs regardless.
- Rollback: unregister `conflict_detector` from `services/worker/src/registry.rs` and disable `F034_FEATURE`; `workload_conflicts` is rebuildable by replaying `capacity.computed.v1`.

## TDD

- Failing test first: `testing/features/F034/api/workload_tests.rs::workload_rows_carry_utilization_and_status`, `::utilization_is_null_when_available_is_zero`, `::workload_range_over_182_days_is_invalid`, `::workload_over_500_resources_is_invalid`, `::workload_row_reports_stale_when_source_event_queued`, `::non_viewer_sees_only_own_workload_row`; `testing/features/F034/api/conflict_tests.rs::capacity_event_opens_conflict_with_over_hours`, `::conflict_detection_is_idempotent_per_source_version`, `::resolved_period_sets_resolved_at_and_stops_publishing`, `::conflict_lists_shift_and_reassign_suggestions`, `::reassign_candidates_capped_at_three_by_remaining_hours`, `::foreign_tenant_conflict_is_not_found`
- Fixtures/mocks: `testing/fixtures/workload.rs` (Ana over-allocated 22 h against 16 h available in the week of 2026-10-12, `Design API` with 4 days of float, Ben with a matching skill and 12 h remaining, tenant B twin); in-process job runner; in-memory outbox recorder; fixed clock `2026-09-03T00:00:00Z`
- Targeted command: `cargo xtask test-feature F034`
- Full command: `cargo xtask test-all`

## Exit criteria

- [ ] Tests above written before implementation and observed failing
- [ ] Routes mounted in `services/api/src/router.rs`; detector registered in `services/worker/src/registry.rs` behind `F034_FEATURE`; OpenAPI regenerated without drift
- [ ] Owned-path, 500-line, lint, and security gates pass
- [ ] `conflict_detection_ms` and dead-letter behavior observed in the harness
- [ ] Handoff evidence recorded in S067
- [ ] `finished_at` recorded
