---
id: T138
type: task
status: planned
parent_epic: E002
parent_feature: F035
parent_story: S069
depends_on: [T137]
owned_paths: [crates/domain/src/formulas/**, services/api/src/formulas/**, testing/features/F035/api/**, testing/features/F035/requirements/**]
feature_flag: F035_FEATURE
branch: t138-function-library
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 9
- Capability contract: `docs/capability-contracts.md` row F035

# T138 — Function library

## Identity

- Parent story: `S069` Parser and evaluation
- Owner: platform
- Branch: `t138-function-library`
- Decision references: `docs/architecture-decisions.md` sections 2–4, 9; `docs/capability-contracts.md` row F035

## Objective

Implement the typed value model, the function registry and the eight function groups, the budgeted evaluator, and the parse, evaluate, and functions routes.

## Specification

- Owned paths: `crates/domain/src/formulas/{value.rs, eval.rs, budget.rs, functions/mod.rs, functions/registry.rs, functions/arithmetic.rs, functions/comparison.rs, functions/conditional.rs, functions/text.rs, functions/datetime.rs, functions/lookup.rs, functions/aggregation.rs, functions/cross_sheet.rs}`, `services/api/src/formulas/{mod.rs, routes.rs, handlers_parse.rs, handlers_functions.rs, dto.rs}`
- Contract/input: `FunctionSpec { name, group: FunctionGroup, params: Vec<ParamSpec { name, ty: ValueType, variadic }>, returns: ValueType, example }`; `Evaluator::eval(&Ast, &RowContext, &Budget) -> Value`; `RowContext` provides `cell(column_id)`, `children(column_id)`, `parent(column_id)`, `lookup(sheet_id, column_id, key)` through a trait implemented by S070 and by the in-memory test context; `Budget { cpu_ms: 2000, max_depth: 256 }`; `Clock` trait injected for `TODAY`/`NOW`.
- Output/behavior: functions `SUM AVG MIN MAX COUNT COUNTIF SUMIF ROUND ABS MOD IF IFERROR AND OR NOT ISBLANK CONCAT LEFT RIGHT MID LEN UPPER LOWER TRIM FIND SUBSTITUTE TEXT VALUE TODAY NOW DATE YEAR MONTH DAY WEEKDAY DATEADD DATEDIFF NETWORKDAYS INDEX MATCH VLOOKUP CHILDREN PARENT ANCESTORS DESCENDANTS LOOKUP`; coercion rules: number to text through `TEXT`, text to number only through `VALUE`, blank counts as 0 in arithmetic and empty string in text, division by zero returns `Value::Error(TypeMismatch)`; budget exhaustion returns `Value::Error(Timeout)`; routes `POST /api/v1/formulas/parse`, `POST /api/v1/formulas/evaluate`, `GET /api/v1/formulas/functions` return `ParseResponse`, `EvaluateResponse`, `FunctionCatalogResponse` with error mapping from ticket section 4; the catalog is rendered from the registry at startup and cached.
- Dependencies: T137 parser and AST; F003 `authz::require(actor, Permission::SheetView, sheet)`.
- Feature flag: `F035_FEATURE` gates router mounting.

## TDD

- Failing test first: `testing/features/F035/api/functions_tests.rs::arithmetic_group_matches_expected_values`, `::text_group_handles_unicode_and_blank`, `::datetime_group_uses_injected_clock`, `::aggregation_over_children_sums_hierarchy`, `::lookup_group_index_match_vlookup`, `::division_by_zero_is_type_mismatch`, `::functions_catalog_matches_registry`; `testing/features/F035/api/evaluate_tests.rs::evaluate_preview_type_mismatch`, `::evaluate_preview_times_out_within_budget`, `::parse_rejects_unsupported_function`
- Targeted command: `cargo xtask test-feature F035`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: in-memory `RowContext` built from `testing/fixtures/formulas.rs` (`Plan` 200 rows, 3 levels; `Rates` 20 rows); fixed clock `2026-09-03T00:00:00Z`

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Router mounted in `services/api/src/router.rs` behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass (each function group file ≤ 500 lines)
- [ ] Handoff evidence recorded in S069
- [ ] `finished_at` recorded
