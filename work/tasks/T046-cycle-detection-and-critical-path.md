---
id: T046
type: task
status: planned
parent_epic: E003
parent_feature: F012
parent_story: S023
depends_on: [T045]
owned_paths: [crates/domain/src/dependencies/**, services/api/src/dependencies/**, testing/features/F012/api/**, testing/features/F012/requirements/**, testing/features/F012/performance/**]
feature_flag: F012_FEATURE
branch: t046-cycle-detection-and-critical-path
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 9
- Capability contract: `docs/capability-contracts.md` row F012

# T046 — Cycle detection and critical path

## Identity

- Parent story: `S023` Dependency links
- Owner: platform
- Branch: `t046-cycle-detection-and-critical-path`
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 9; `docs/capability-contracts.md` row F012

## Objective

Implement the sheet dependency graph with cycle detection on create and update, the forward/backward pass critical-path calculation over working days, parent roll-up, milestone handling, persisted `schedule_results`, and the critical-path route.

## Specification

- Owned paths: `crates/domain/src/dependencies/{graph.rs, cycle.rs, critical_path.rs, rollup.rs, recompute.rs}`, `services/api/src/dependencies/handlers_critical_path.rs`, `services/api/src/dependencies/consumers.rs`
- Contract/input: `SheetGraph::load(sheet_id)` builds nodes from rows with the F011 `sheet_schedule_settings` start, end, and duration columns and edges from `row_dependencies`; `detect_cycle(graph, candidate_edge) -> Result<(), CyclePath>` uses Kahn topological sort and, on failure, DFS to return the cycle in traversal order; `compute_critical_path(graph, calendar, exceptions, timezone) -> Vec<ScheduleResult>` applies constraints `FS: start ≥ pred.finish + lag`, `SS: start ≥ pred.start + lag`, `FF: finish ≥ pred.finish + lag`, `SF: finish ≥ pred.start + lag` with `add_working_days`/`add_working_hours` and float via `working_days_between`.
- Output/behavior: `POST/PATCH` dependency now call the real `CycleChecker`, returning `400 invalid` with `field_errors.successor_row_id = "cycle"` and `details.cycle_path`; `GET /api/v1/sheets/{sheet_id}/critical-path` returns `CriticalPathResponse { schedule_version, computed_at, rows }` and upserts `schedule_results`; parents get min start/max finish of descendants and are rejected as link endpoints; zero-duration rows are milestones; a consumer on `row.updated.v1`, `cell.updated.v1`, `row.reparented.v1` recomputes the sheet, debounced 500 ms, within a 2 s budget; metrics `dependencies_cycle_rejections_total`, `critical_path_duration_ms`.
- Dependencies: T045 tables and routes; F011 `crates/domain/src/schedules/working_time.rs`; F009 `GET /api/v1/rows/{id}/children` hierarchy data via the domain crate.
- Feature flag: `F012_FEATURE`

## TDD

- Failing test first: `testing/features/F012/api/critical_path_tests.rs::dependency_cycle_rejected_with_path`, `::dependency_cycle_check_serialized_per_sheet`, `::critical_path_marks_zero_float_rows`, `::critical_path_respects_each_link_kind`, `::critical_path_negative_lag_leads_successor`, `::critical_path_hours_lag_uses_working_window`, `::critical_path_skips_calendar_exceptions`, `::critical_path_rolls_up_parent_rows`, `::critical_path_milestone_zero_duration`, `::critical_path_unscheduled_sheet_invalid`; `testing/features/F012/performance/critical_path_bench.rs::critical_path_10k_p95`
- Targeted command: `cargo xtask test-feature F012`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: seeded 12-row schedule with parent, milestone, and holiday; 10,000-row/20,000-link generator with fixed seed; F011 calendar fixtures used directly

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] p95 target from NFR-F012-01 for critical path met in the performance lane
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S023
- [ ] `finished_at` recorded
