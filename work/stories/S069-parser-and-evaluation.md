---
id: S069
type: story
status: planned
parent_epic: E002
parent_feature: F035
depends_on: [F007, F009]
owned_paths: [crates/domain/src/formulas/**, services/api/src/formulas/**, services/api/migrations/*_formulas_*.sql, testing/features/F035/**]
feature_flag: F035_FEATURE
branch: s069-parser-and-evaluation
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 9
- Capability contract: `docs/capability-contracts.md` row F035

# S069 — Parser and evaluation

## Identity

- Parent feature: `F035` Formula engine
- Owner: platform
- Branch: `s069-parser-and-evaluation`
- Decision references: `docs/architecture-decisions.md` sections 2–4, 9; `docs/capability-contracts.md` row F035

## Vertical slice

As a sheet editor, I want to parse and preview a formula against one row and see either a typed value or a precise error, so that I can trust an expression before it is attached to a column and recalculated across the sheet.

## Requirements

- **SR-S069-01:** `POST /api/v1/formulas/parse` returns the AST, `node_count`, stable-ID `references`, `functions_used`, and syntax errors with 1-based `position` and `code = invalid` (covers FR-F035-01, FR-F035-02).
- **SR-S069-02:** Expressions over 10,000 AST nodes and unknown function names are rejected with `400 invalid` and `field_errors.expression` values `too_large` and `unsupported_function:<NAME>` (FR-F035-03).
- **SR-S069-03:** `GET /api/v1/formulas/functions` is generated from the same registry the evaluator uses and lists every function in the eight groups with signature, return type, and example (FR-F035-04, FR-F035-05).
- **SR-S069-04:** `POST /api/v1/formulas/evaluate` evaluates one row under `Budget { cpu_ms: 2000, max_depth: 256 }` and returns `{ value, display, status, error_code }` with `type_mismatch`, `missing_reference`, `invalid`, or `timeout` where applicable (FR-F035-07, FR-F035-08).
- **SR-S069-05:** Column labels in source text are rewritten to `{col:<column_id>}` in `expression_canonical`, and the pretty printer renders current labels, so a rename in F007 leaves the stored formula valid (FR-F035-02).
- **SR-S069-06:** The evaluator is pure and injects a fixed clock; `TODAY()` and `NOW()` in tests return `2026-09-03` (NFR-F035-02).
- **SR-S069-07:** A viewer can call parse, evaluate, and functions; a foreign-tenant `sheet_id` returns `404 not_found` (FR-F035-16).

## Surfaces

- Infrastructure/container: none beyond F004 baseline
- Rust service/API: `crates/domain/src/formulas/{mod.rs, lexer.rs, parser.rs, ast.rs, canonical.rs, eval.rs, value.rs, errors.rs, functions/*.rs}`; `services/api/src/formulas/{mod.rs, routes.rs, handlers_parse.rs, handlers_functions.rs, dto.rs}`. The lexer, parser, evaluator and handlers are pure of SQL (decision 2.1); the only table access is through `FormulaDefinitionRepository` in `crates/persistence/src/formulas/`, which the parse and evaluate use cases call to load an existing definition.
- Data/migration: `services/api/migrations/<ts>_formulas_create_tables.sql` creating `formula_definitions`, `formula_dependencies`, `formula_results` with the constraints from ticket section 4 (tables are created here, populated by S070). Each table gets exactly one data access class in `crates/persistence/src/formulas/` — `FormulaDefinitionRepository`, `FormulaDependencyRepository`, `FormulaResultRepository` — implementing the shared `Repository` contract; `formula_definitions.ast` and `formula_results.value` stay `jsonb` because they are a compiled expression payload and one typed cell value, with every queried facet in typed columns and `formula_dependencies` rows.
- React/UI: none in this story (S070 and T140 cover the editor and badges)
- Mocks/fixtures: `testing/fixtures/formulas.rs` sheets `Plan` and `Rates`; fixed clock; in-memory outbox recorder

## TDD harness

- Test path: `testing/features/F035/api/` and `testing/features/F035/database/`
- Feature flag: `F035_FEATURE`
- Targeted command: `cargo xtask test-feature F035`
- Full command: `cargo xtask test-all`
- First failing tests: `parse_returns_ast_and_references`, `parse_reports_position_on_syntax_error`, `parse_rejects_over_10000_nodes`, `parse_rejects_unsupported_function`, `evaluate_preview_type_mismatch`, `functions_catalog_matches_registry`, `canonical_form_survives_column_rename`

## Exit criteria

- [ ] Requirement tests SR-S069-01 through SR-S069-07 written first and failing
- [ ] Tasks T137 and T138 complete and wired through `services/api` router
- [ ] Unit, API, database, permission tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/formulas/routes.rs` mounted in `services/api/src/router.rs`
- [ ] Handoff evidence recorded in the F035 ticket
