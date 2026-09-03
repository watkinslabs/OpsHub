---
id: S070
type: story
status: planned
parent_epic: E002
parent_feature: F035
depends_on: [S069]
owned_paths: [crates/domain/src/formulas/**, services/api/src/formulas/**, apps/web/src/features/formulas/**, testing/features/F035/**]
feature_flag: F035_FEATURE
branch: s070-dependency-graph-and-recalculation
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 6, 9
- Capability contract: `docs/capability-contracts.md` row F035

# S070 — Dependency graph and recalculation

## Identity

- Parent feature: `F035` Formula engine
- Owner: platform
- Branch: `s070-dependency-graph-and-recalculation`
- Decision references: `docs/architecture-decisions.md` sections 2–4, 6, 9; `docs/capability-contracts.md` row F035

## Vertical slice

As a sheet editor, I want to attach a formula to a column and have only the affected cells recalculate when inputs, hierarchy, links, or other sheets change, with cycles and timeouts surfaced as cell errors, so that a large sheet stays correct and responsive.

## Requirements

- **SR-S070-01:** `PUT /api/v1/columns/{id}/formula` with `If-Match` stores `formula_definitions`, replaces `formula_dependencies` edges, schedules a full column recalculation, and emits `formula.updated.v1`; `{ expression: null }` clears the definition and results (FR-F035-06).
- **SR-S070-02:** Adding an edge that closes a cycle, including through cross-sheet references and roll-up columns, is rejected with `400 invalid` and `field_errors.expression = "cycle:<ids>"`; a cycle found during recalculation marks the cells `error/cycle` and emits `formula.failed.v1` (FR-F035-10).
- **SR-S070-03:** The outbox consumer maps `cell.updated.v1`, `cells.bulk-updated.v1`, `rows.bulk-updated.v1`, `row.reparented.v1`, `link.updated.v1`, and `rollup.recomputed.v1` to a `RecalcPlan` of transitively dependent cells in topological order and emits `formula.recalculated.v1` per column (FR-F035-09).
- **SR-S070-04:** A column batch exceeding 2,000 ms CPU marks remaining cells `timeout` and emits `formula.failed.v1` with `reason = timeout`; results carry `batch_id` and `source_version` so replays are idempotent (FR-F035-11, NFR-F035-04).
- **SR-S070-05:** Cross-sheet references resolve by `sheet_id` and `column_id`; unreadable or deleted targets produce `missing_reference` per cell and never a foreign value (FR-F035-12).
- **SR-S070-06:** `GET /api/v1/sheets/{sheet_id}/formula-graph` and `POST /api/v1/sheets/{sheet_id}/recalculate` expose the graph and force a full recalculation as an acknowledged job, one active per sheet (FR-F035-13, FR-F035-14).
- **SR-S070-07:** `FormulaEditor`, `FormulaCellBadge`, and `FormulaGraphPanel` show live parse errors, autocomplete, preview, error badges, and graph state with loading, empty, error, denied, and stale states (FR-F035-15, FR-F035-16, NFR-F035-03).
- **SR-S070-08:** Incremental recalculation after one cell edit on the 100,000-row fixture completes within 2,000 ms (NFR-F035-01).

## Surfaces

- Infrastructure/container: none
- Rust service/API: `crates/domain/src/formulas/{graph.rs, recalc.rs, consumer.rs, service.rs, functions/cross_sheet.rs}`; `services/api/src/formulas/{handlers_column.rs, handlers_graph.rs, handlers_recalculate.rs}`
- Data/migration: none new; uses tables from S069
- React/UI: `apps/web/src/features/formulas/{FormulaEditor.tsx, FormulaAutocomplete.tsx, ReferenceChips.tsx, FormulaPreviewRow.tsx, FormulaErrorPopover.tsx, FormulaCellBadge.tsx, FormulaGraphPanel.tsx, RecalculateButton.tsx, api.ts, hooks.ts}`
- Mocks/fixtures: `Plan` sheet with a 3-level hierarchy and `Rates` sheet; 100,000-row generator for performance lane; MSW handlers for component tests

## TDD harness

- Test path: `testing/features/F035/{api,database,frontend,e2e,accessibility,performance}/`
- Feature flag: `F035_FEATURE`
- Targeted command: `cargo xtask test-feature F035`
- Full command: `cargo xtask test-all`
- First failing tests: `set_formula_rewrites_dependencies_and_emits_event`, `cycle_rejected_at_definition_time`, `incremental_recalc_touches_only_dependents`, `timeout_marks_remaining_cells`, `cross_sheet_unreadable_yields_missing_reference`, `formula_editor_shows_position_error`, `incremental_recalc_100k_p95`

## Exit criteria

- [ ] Requirement tests SR-S070-01 through SR-S070-08 written first and failing
- [ ] Tasks T139 and T140 complete; UI wired to real API through generated client
- [ ] Unit, API, React, E2E, accessibility, permission, and performance tests pass
- [ ] Production call path named: `crates/domain/src/formulas/consumer.rs` registered in `services/api/src/outbox_consumers.rs` and `apps/web/src/features/formulas/FormulaEditor.tsx` mounted in the F007 `ColumnEditorDrawer`
- [ ] Handoff evidence recorded in the F035 ticket
