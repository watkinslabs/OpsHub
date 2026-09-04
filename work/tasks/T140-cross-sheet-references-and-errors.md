---
id: T140
type: task
status: planned
parent_epic: E002
parent_feature: F035
parent_story: S070
depends_on: [T139]
owned_paths: [crates/domain/src/formulas/**, services/api/src/formulas/**, apps/web/src/features/formulas/**, testing/features/F035/frontend/**, testing/features/F035/e2e/**, testing/features/F035/accessibility/**]
feature_flag: F035_FEATURE
branch: t140-cross-sheet-references-and-errors
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 3, 4, 6, 9
- Capability contract: `docs/capability-contracts.md` row F035

# T140 — Cross-sheet references and errors

## Identity

- Parent story: `S070` Dependency graph and recalculation
- Owner: platform
- Branch: `t140-cross-sheet-references-and-errors`
- Decision references: `docs/architecture-decisions.md` sections 3, 4, 6, 9; `docs/capability-contracts.md` row F035

## Objective

Implement permission-checked cross-sheet reference resolution, the formula graph route, the five error states end to end, and the formula editor, cell badges, and graph panel in the web app.

## Specification

- Owned paths: `crates/domain/src/formulas/{cross_sheet.rs, graph_view.rs}`, `services/api/src/formulas/handlers_graph.rs`, `apps/web/src/features/formulas/{FormulaEditor.tsx, FormulaAutocomplete.tsx, ReferenceChips.tsx, FormulaPreviewRow.tsx, FormulaErrorPopover.tsx, FormulaCellBadge.tsx, FormulaGraphPanel.tsx, RecalculateButton.tsx, api.ts, hooks.ts, errorCodes.ts}`
- Contract/input: `{sheet:<sheet_id>}!{col:<column_id>}` and `LOOKUP({sheet}!{col}, key, {col})` references; `CrossSheetResolver::resolve(actor, sheet_id, column_id) -> Result<ColumnSnapshot, FormulaError::MissingReference>` applies the F003 ACL and tenant predicate and reads the target through the F007 `ColumnRepository` and F006 `CellRepository`, so `cross_sheet.rs`, `graph_view.rs` and `handlers_graph.rs` contain no SQL (decision 2.1) and the graph itself is read with `load_graph_for_sheet` on `FormulaDependencyRepository` and last-status fields from `FormulaResultRepository`; `GET /api/v1/sheets/{sheet_id}/formula-graph` returns `FormulaGraphResponse { nodes: [{ id, kind: column|sheet, label, depth, status, last_batch_id, last_duration_ms }], edges: [{ from, to, kind }], has_cycle }`; generated `FormulasApi` client; `errorCodes.ts` maps `invalid`, `missing_reference`, `type_mismatch`, `cycle`, `timeout` to badges `#INVALID`, `#REF`, `#TYPE`, `#CYCLE`, `#TIMEOUT` and messages.
- Output/behavior: definition time requires `sheet-viewer` on every referenced sheet (`404 not_found` otherwise, so unreadable sheets are not confirmed to exist); evaluation time yields `missing_reference` per cell for deleted, unreadable, or foreign-tenant targets and never reads across tenants; `FormulaEditor` is a labelled textbox with `aria-describedby` live error, combobox autocomplete fed by `['formula-functions']`, reference chips, debounced preview row from `evaluateFormula`, `Ctrl+Enter` save with `If-Match`, read-only mode for viewers, stale banner on `conflict`; `FormulaCellBadge` renders inside F008 grid cells for `status = error` and `pending` shimmer; `FormulaGraphPanel` lists nodes and edges with cycle highlight and a list layout under 640 px; `RecalculateButton` calls `recalculateSheet` and shows the `rate_limited` state; telemetry `formula_editor_opened`, `formula_saved`, `formula_parse_error`, `formula_recalculate_requested`, `formula_error_badge_opened`.
- Dependencies: T139 graph and recalculation; F007 `ColumnEditorDrawer` hosts the editor; F008 `VirtualGrid` renders the badge through a cell renderer slot.
- Feature flag: `F035_FEATURE` read through the flag hook; editor and badges are not rendered when off.

## TDD

- Failing test first: `testing/features/F035/api/cross_sheet_tests.rs::cross_sheet_unreadable_yields_missing_reference`, `::cross_sheet_foreign_tenant_not_found_at_definition`, `::formula_graph_reports_depth_and_cycle`; `testing/features/F035/frontend/FormulaEditor.test.tsx::shows_position_error_from_parse`, `::autocomplete_inserts_function`, `::viewer_sees_read_only_editor`; `FormulaCellBadge.test.tsx::renders_badge_per_error_code`; `testing/features/F035/e2e/formula.spec.ts::set_formula_edit_child_parent_updates`, `::cycle_rejected_in_editor`; `testing/features/F035/accessibility/formula.a11y.spec.ts::editor_and_badges_have_no_serious_axe_violations`
- Targeted command: `cargo xtask test-feature F035`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: MSW handlers from `testing/fixtures/formulas.rs` (`Plan`, `Rates`, viewer without `Rates` access); Playwright against the real API with a seeded tenant

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] API, component, E2E, and accessibility lanes pass
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S070
- [ ] `finished_at` recorded
