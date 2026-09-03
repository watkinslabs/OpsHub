---
id: T139
type: task
status: planned
parent_epic: E002
parent_feature: F035
parent_story: S070
depends_on: [T138]
owned_paths: [crates/domain/src/formulas/**, services/api/src/formulas/**, testing/features/F035/api/**, testing/features/F035/performance/**]
feature_flag: F035_FEATURE
branch: t139-incremental-recalculation
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 7, 9
- Capability contract: `docs/capability-contracts.md` row F035

# T139 — Incremental recalculation

## Identity

- Parent story: `S070` Dependency graph and recalculation
- Owner: platform
- Branch: `t139-incremental-recalculation`
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 7, 9; `docs/capability-contracts.md` row F035

## Objective

Implement the dependency graph, the set-formula and recalculate routes, the outbox consumer that plans and runs incremental recalculation in topological order, and the timeout and idempotency handling for result batches.

## Specification

- Owned paths: `crates/domain/src/formulas/{graph.rs, recalc.rs, consumer.rs, service.rs, results_repo.rs}`, `services/api/src/formulas/{handlers_column.rs, handlers_recalculate.rs}`
- Contract/input: `SetFormulaRequest { expression: Option<String>, result_type: ResultType }` with `If-Match` column version; `DependencyGraph::{add_edges(column_id, edges), would_cycle(column_id, edges) -> Option<Vec<ColumnId>>, dependents_of(sheet_id, column_id), topo_order(set)}`; consumer subscriptions `cell.updated.v1`, `cells.bulk-updated.v1`, `rows.bulk-updated.v1`, `row.reparented.v1`, `link.updated.v1`, `rollup.recomputed.v1`; `RecalcPlan { batch_id, columns: Vec<(ColumnId, RowSet)>, source_version }`.
- Output/behavior: `PUT /api/v1/columns/{id}/formula` stores the definition, replaces edges in one transaction, rejects cycles with `400 invalid` and `field_errors.expression = "cycle:<ids>"`, schedules a full column recalculation, emits `formula.updated.v1`; `POST /api/v1/sheets/{sheet_id}/recalculate` returns `202 { job_id }` in under 2 s and `429 rate_limited` while a job is active for the sheet; `run_plan` evaluates rows in 5,000-row chunks per column under the 2,000 ms CPU budget, writes `formula_results` with `status`, `error_code`, `batch_id`, `source_version`, marks remaining cells `timeout` when the budget is exhausted, emits `formula.recalculated.v1` per column and `formula.failed.v1` on cycle or timeout; a replayed event with an already-applied `source_version` is a no-op; events for the same `(sheet_id, column_id)` are coalesced with a 250 ms debounce.
- Dependencies: T138 evaluator; F004 outbox consumer registration; F006 cell read path returns `formula_results` inside `validation`; F009 `row_hierarchy` for `CHILDREN`/`PARENT` row sets.
- Feature flag: `F035_FEATURE` gates both routes and consumer registration.

## TDD

- Failing test first: `testing/features/F035/api/recalc_tests.rs::set_formula_rewrites_dependencies_and_emits_event`, `::cycle_rejected_at_definition_time`, `::incremental_recalc_touches_only_dependents`, `::recalc_runs_in_topological_order`, `::timeout_marks_remaining_cells`, `::replayed_event_is_idempotent`, `::recalculate_route_rate_limits_second_job`; `testing/features/F035/performance/recalc_bench.rs::incremental_recalc_100k_p95`, `::full_recalc_100k_under_60s`
- Targeted command: `cargo xtask test-feature F035`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: in-memory outbox recorder and consumer harness; 100,000-row generator with 10 formula columns and fixed seed

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] p95 and budget targets from NFR-F035-01 met in the performance lane
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S070
- [ ] `finished_at` recorded
