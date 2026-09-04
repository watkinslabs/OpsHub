---
id: T137
type: task
status: planned
parent_epic: E002
parent_feature: F035
parent_story: S069
depends_on: [S069]
owned_paths: [crates/domain/src/formulas/**, services/api/migrations/*_formulas_*.sql, testing/features/F035/database/**, testing/features/F035/api/**]
feature_flag: F035_FEATURE
branch: t137-parser-ast
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 9
- Capability contract: `docs/capability-contracts.md` row F035

# T137 — Parser/AST

## Identity

- Parent story: `S069` Parser and evaluation
- Owner: platform
- Branch: `t137-parser-ast`
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 9; `docs/capability-contracts.md` row F035

## Objective

Implement the lexer, Pratt parser, arena AST with the 10,000-node limit, canonical stable-ID serialization, and the formula tables migration so every later formula feature works on one verified expression model.

## Specification

- Owned paths: `crates/domain/src/formulas/{mod.rs, lexer.rs, parser.rs, ast.rs, canonical.rs, errors.rs, schema.rs}`, `crates/persistence/src/formulas/{mod.rs, definition_repository.rs, dependency_repository.rs, result_repository.rs}`, `services/api/migrations/<ts>_formulas_create_tables.sql`, `services/api/migrations/<ts>_formulas_create_tables.down.sql`
- Contract/input: `parse(source: &str, resolver: &dyn LabelResolver) -> Result<ParsedFormula, FormulaError>` where `ParsedFormula { ast: Ast, node_count: usize, references: Vec<Reference>, functions_used: Vec<FunctionId>, canonical: String }`; tokens: numbers (`1`, `1.5`, `1e3`), strings (`"..."` with `""` escape), booleans, date literals `DATE(2026,9,3)` handled as calls, operators `+ - * / ^ % & = <> < <= > >=`, `[Label]`, `[Label]@row`, `{col:uuid}`, `{sheet:uuid}!{col:uuid}`, identifiers followed by `(`.
- Output/behavior: precedence `^` > unary `-` > `* / %` > `+ -` > `&` > comparisons; syntax errors carry 1-based `position` and `expected`; node count is checked while building and stops at 10,001 with `FormulaError::TooLarge`; argument count over 64 is `FormulaError::TooManyArguments`; `canonical.rs` rewrites labels to stable IDs via the resolver and pretty-prints back with current labels; migration creates `formula_definitions`, `formula_dependencies`, `formula_results` with the check constraints, unique `column_id`, cascade, and indexes from ticket section 4, and each of the three tables gets exactly one data access class — `FormulaDefinitionRepository`, `FormulaDependencyRepository`, `FormulaResultRepository` in `crates/persistence/src/formulas/` implementing the shared `Repository` contract (decision 2.1), so `crates/domain/src/formulas/` and the migration tests hold no SQL string or `sqlx::query*` call; `formula_definitions.ast` and `formula_results.value` stay `jsonb` as a compiled expression payload and one typed cell value, with the queried facets in typed columns and `formula_dependencies` rows.
- Dependencies: F007 `columns` table for the `LabelResolver` fixture; F006 `rows`/`cells` for foreign keys.
- Feature flag: `F035_FEATURE` (migration runs regardless; routes are gated)
- Large-table note: `formula_results` is expected to reach 1,000,000 rows per large sheet; the primary key `(row_id, column_id)` is the only required index at creation.

## TDD

- Failing test first: `testing/features/F035/api/parser_tests.rs::parse_returns_ast_and_references`, `::parse_reports_position_on_syntax_error`, `::parse_rejects_over_10000_nodes`, `::parse_respects_operator_precedence`, `::canonical_form_survives_column_rename`; `testing/features/F035/database/migration_tests.rs::formula_tables_exist_with_constraints`, `::node_count_over_limit_rejected_by_check`, `::rollback_drops_tables`
- Targeted command: `cargo xtask test-feature F035`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: in-memory `LabelResolver` mapping `Estimate`, `Priority`, `Rate` to fixed column IDs; schema-per-worker database from `testing/harness/db.rs`

## Exit criteria

- [ ] Tests written before the parser and migration and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S069
- [ ] `finished_at` recorded
