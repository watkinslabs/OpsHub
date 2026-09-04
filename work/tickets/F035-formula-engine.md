---
id: F035
type: feature
status: planned
priority: P0
owner: platform
estimate: 13
target_milestone: M1
parent_epic: E002
depends_on: [F007, F009]
blocks: [F018, F021, F039, F053, F060]
conflicts_with: []
parallel_safe: true
owned_paths: [crates/persistence/src/formulas/**, crates/domain/src/formulas/**, services/api/src/formulas/**, apps/web/src/features/formulas/**, services/api/migrations/*_formulas_*.sql, testing/features/F035/**]
feature_flag: F035_FEATURE
flag_default: off
branch: f035-formula-engine
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 6, 9
- Capability contract: `docs/capability-contracts.md` row F035

# F035 — Formula engine

## 1. Identity and dates

- Branch: `f035-formula-engine`
- Capability area: core work record engine (spec 5.2 DATA-02, DATA-03, low-level formula bullets; section 4 Column `formula` type and stable-ID rule; section 10 formula decision: function groups of 5.2, 10,000-AST-node limit, 2-second evaluation budget, cycle detection, explicit unsupported-function errors)
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 6, 9; `docs/capability-contracts.md` row F035
- Module slug: `formulas`; aggregate: `formula`

## 2. Requirement specification

### Problem and user outcome

Teams model derived values (totals, due-date offsets, status text, lookups into other sheets) but today every derived value must be typed by hand and drifts from its inputs. They need a formula column that is parsed once, recalculated only when an input changes, protected against cycles and runaway evaluation, and that reports why a cell failed instead of showing a blank.

As a sheet editor, I want to write `=SUM([Estimate]) * IF([Priority] = "High", 1.5, 1)` on a column and see every row compute and stay current as cells, hierarchy, and linked sheets change, so that my sheet is a live model rather than a snapshot.

### Functional requirements

- **FR-F035-01:** `POST /api/v1/formulas/parse` accepts `{ sheet_id, expression }` and returns `{ ast, node_count, references: [{ sheet_id, column_id, row_scope }], functions_used, errors }`; a syntax error returns `200` with `errors[0].code = "invalid"`, a 1-based `position`, and the expected token, never a `400`.
- **FR-F035-02:** The parser accepts arithmetic (`+ - * / ^ %`), comparison (`= <> < <= > >=`), string concatenation (`&`), parentheses, numeric, string, boolean, and date literals, column references `[Label]` and `[Label]@row`, stable references `{col:<column_id>}` and `{sheet:<sheet_id>}!{col:<column_id>}`, and function calls with up to 64 arguments; identifiers are case-insensitive and stored in canonical form with stable IDs so column renames never change the stored formula.
- **FR-F035-03:** An expression whose AST exceeds 10,000 nodes is rejected with error code `invalid` and `field_errors.expression = "too_large"`; an unknown function name returns `invalid` with `field_errors.expression = "unsupported_function:<NAME>"`.
- **FR-F035-04:** `GET /api/v1/formulas/functions` lists every supported function with `name`, `group` (`arithmetic`, `comparison`, `conditional`, `text`, `datetime`, `lookup`, `aggregation`, `cross_sheet`), argument signature, return type, and one example; the list is the single source for the editor autocomplete and is identical to the evaluator registry.
- **FR-F035-05:** The function library implements at least: `SUM AVG MIN MAX COUNT COUNTIF SUMIF ROUND ABS MOD`, `IF IFERROR AND OR NOT ISBLANK`, `CONCAT LEFT RIGHT MID LEN UPPER LOWER TRIM FIND SUBSTITUTE TEXT VALUE`, `TODAY NOW DATE YEAR MONTH DAY WEEKDAY DATEADD DATEDIFF NETWORKDAYS`, `INDEX MATCH VLOOKUP`, `CHILDREN PARENT ANCESTORS DESCENDANTS`, and cross-sheet `LOOKUP({sheet}!{col}, key, {col})`; each function declares typed parameters and returns `type mismatch` when given an incompatible argument.
- **FR-F035-06:** `PUT /api/v1/columns/{id}/formula` with `{ expression, result_type: number|text|boolean|date|datetime|duration|currency }` on a column of type `formula` stores a `formula_definitions` row, rewrites the dependency graph, schedules a full column recalculation, emits `formula.updated.v1`, and requires `If-Match` on the column version; a body of `{ expression: null }` removes the formula and clears results.
- **FR-F035-07:** `POST /api/v1/formulas/evaluate` accepts `{ sheet_id, expression, row_id? }` and returns `{ value, display, status, error_code? }` for that single row without persisting, applying the same 2 s budget; it is the preview used by the editor and by F039.
- **FR-F035-08:** Every formula result is stored in `formula_results` with `value` (typed JSON), `display`, `status` (`ok`, `error`, `pending`), and `error_code` one of `invalid`, `missing_reference`, `type_mismatch`, `cycle`, `timeout`; the cell read path from F006 returns these fields inside the cell `validation` object so grids and reports never see a blank for a failed formula.
- **FR-F035-09:** The dependency graph (`formula_dependencies`) records column-to-column and column-to-sheet edges; a `cell.updated.v1`, `cells.bulk-updated.v1`, `rows.bulk-updated.v1`, `row.reparented.v1`, `link.updated.v1`, or `rollup.recomputed.v1` event triggers recalculation of only the transitively dependent formula cells, in topological order, and emits one `formula.recalculated.v1` per affected column with `cell_count` and `duration_ms`.
- **FR-F035-10:** Introducing an edge that closes a cycle (including self-reference and cycles through cross-sheet references or roll-up columns) is rejected at `PUT /formula` time with `invalid` and `field_errors.expression = "cycle:<column_id>,<column_id>,..."`; a cycle discovered at recalculation time (because a linked sheet changed) marks every cell on the cycle `status = error, error_code = cycle` and emits `formula.failed.v1`.
- **FR-F035-11:** Evaluation of one recalculation batch is bounded to 2,000 ms of CPU per column; when exceeded the remaining cells of that column are set to `error_code = timeout`, the batch is recorded in `formula_results.batch_id`, and `formula.failed.v1` is emitted with `reason = timeout`.
- **FR-F035-12:** Cross-sheet references resolve by stable `sheet_id` and `column_id`; the referencing actor needs `sheet-viewer` on the target sheet at definition time, and at evaluation time a target the reading tenant cannot see or that was deleted yields `missing_reference` for that cell only, never an exception or a value from another tenant.
- **FR-F035-13:** `GET /api/v1/sheets/{sheet_id}/formula-graph` returns nodes (formula columns and referenced sheets) and edges with `depth`, `has_cycle`, and last recalculation status so users and support can explain a slow or failing sheet.
- **FR-F035-14:** `POST /api/v1/sheets/{sheet_id}/recalculate` forces a full recalculation of every formula column in the sheet as an acknowledged job (`202` with `job_id` in under 2 s), rate-limited to one active job per sheet (`rate_limited` otherwise).
- **FR-F035-15:** The formula editor in the web app shows live parse errors with position, function autocomplete from the functions route, referenced columns as chips, a per-row preview from the evaluate route, and error-code badges in cells with a tooltip that names the failing reference or function.
- **FR-F035-16:** A viewer or commenter can read formula results and open the read-only formula view but receives `denied` on `PUT /formula` and `POST /recalculate`; cross-tenant IDs on any route return `not_found`.

### Non-functional requirements

- **NFR-F035-01 Performance:** parse of a 1,000-node expression completes in under 20 ms; incremental recalculation after a single-cell edit on a 100,000-row sheet with 10 formula columns completes within 2,000 ms; a full sheet recalculation of 100,000 rows and 10 columns completes within 60 s in the outbox consumer path and never blocks the editing request.
- **NFR-F035-02 Security/privacy:** the evaluator is pure (no I/O, no clock other than the injected fixed clock, no string-to-code paths); cross-sheet reads apply the target sheet ACL and tenant predicate; formula text is audited but result values are not logged.
- **NFR-F035-03 Accessibility:** the formula editor is a labelled textbox with `aria-describedby` for live errors, autocomplete uses the combobox pattern, and error badges in cells are announced with their error code; no serious axe violations.
- **NFR-F035-04 Reliability/observability:** recalculation is idempotent per `(column_id, source_version)`; metrics `formula_recalc_duration_ms`, `formula_recalc_cells`, `formula_timeouts_total`, and `formula_cycles_total` are exported; every recalculation span carries `tenant_id`, `sheet_id`, `column_id`, and `correlation_id` of the triggering event.

### Scope

Included: lexer, parser, AST, canonical stable-ID serialization, function registry and library for the eight groups, typed evaluator, dependency graph, incremental and full recalculation, cycle and timeout handling, error codes, cross-sheet references, formula graph route, formula editor and cell error badges.

Excluded: automation expression evaluation (F018 reuses the parser), report calculated fields (F021), assisted formula generation (F039), conditional-formatting rules (F060), working-calendar-aware date math beyond `NETWORKDAYS` on the tenant default calendar (F011), array formulas and user-defined functions (non-goal: full Excel compatibility).

## 3. UX specification

- Entry points: column header menu `Set formula` on a `formula` column (F007 editor drawer hosts the `FormulaEditor` panel); cell error badge click opens `FormulaErrorPopover`; sheet menu `Recalculate all` and `Formula graph`.
- Primary flow: open a formula column, type `=SUM(CHILDREN([Estimate]))`, autocomplete offers `SUM`, `SUMIF`; chips show referenced columns; the preview row shows `12`; press `Save`; the column shows `pending` shimmer per cell then values; editing a child estimate updates the parent within 2 s.
- Loading: shimmer on cells with `status = pending`; Empty: column with no formula shows `Set formula` placeholder; Error: cells show a badge `#INVALID`, `#REF`, `#TYPE`, `#CYCLE`, `#TIMEOUT` mapped from the error codes, and the editor shows the parser message with a caret at `position`; Success: toast `Formula saved, recalculating 4,200 cells`; Stale/conflict: saving with a stale column version shows the reload banner; Denied: editor opens read-only with an explanation for viewers.
- Permission-denied: `Set formula` hidden for viewers and commenters; cross-sheet picker lists only sheets the actor can read.
- Responsive: the editor panel becomes a bottom sheet under 768 px; the formula graph renders as a list under 640 px.
- Keyboard: `Ctrl+Space` opens autocomplete, arrows and `Enter` pick, `Escape` closes, `Ctrl+Enter` saves; focus returns to the column header after save; motion respects `prefers-reduced-motion`.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062); Lucide icons `Sigma`, `FunctionSquare`, `AlertTriangle`, `RefreshCw`, `GitBranch`; error colors from `apps/web/src/design/tokens.css` with 4.5:1 contrast.

- Design: `design/artboards/FormulaEditor.dc.html` on the canvas indexed by `design/canvas.json`. The ticket is the contract and the artboard is the picture; when they disagree the ticket wins.

## 4. Technical specification

Canonical contract: `docs/capability-contracts.md` row F035.

### Rust backend

- Domain entities in `crates/domain/src/formulas/`: `FormulaDefinition { id, tenant_id, sheet_id, column_id, expression_source, expression_canonical, ast: Ast, node_count, result_type: ResultType, version, created/updated actor+time }`, `Ast` (arena of `Node { kind: NodeKind, children: Range }` with `NodeKind::{Literal, ColumnRef{column_id, scope}, SheetRef{sheet_id, column_id}, Call{function_id, argc}, Binary(Op), Unary(Op)}`), `Dependency { from_column_id, to_sheet_id, to_column_id, kind: Cell|Children|Parent|CrossSheet }`, `FormulaResult { row_id, column_id, value: Value, display, status: ResultStatus, error_code: Option<FormulaError>, batch_id, source_version }`, `Value::{Number(f64), Text, Bool, Date, DateTime, Duration, Currency{amount, code}, Blank, Error(FormulaError)}`.
- Modules: `lexer.rs`, `parser.rs` (Pratt parser, node limit enforced during build), `canonical.rs` (label to stable-ID rewrite and pretty printer), `functions/{mod.rs, registry.rs, arithmetic.rs, comparison.rs, conditional.rs, text.rs, datetime.rs, lookup.rs, aggregation.rs, cross_sheet.rs}`, `eval.rs` (`Evaluator::eval(&Ast, &RowContext, &Budget) -> Value`), `graph.rs` (`DependencyGraph` with `add_edges`, `would_cycle`, `dependents_of`, `topo_order`), `recalc.rs` (`plan_incremental(event) -> RecalcPlan`, `run_plan(plan, budget)`), `service.rs`, `errors.rs`.
- Data access (decision 2.1): `FormulaDefinitionRepository` (`formula_definitions`), `FormulaDependencyRepository` (`formula_dependencies`), and `FormulaResultRepository` (`formula_results`) in `crates/persistence/src/formulas/`; the recalculated cell values that reach the grid are written through the F006 `CellRepository`, and `row_hierarchy` is read through the F009 `RowHierarchyRepository` behind `HierarchyReader`, so no table gains a second writer. The use cases below, `recalc.rs`, and the outbox consumer depend on those repository traits and the shared `UnitOfWork`; `crates/domain/src/formulas/` and `services/api/src/formulas/` contain no SQL, and the graph load, the reverse-dependency walk, and the batched result write are named repository queries (`dependents_of_column`, `load_graph_for_sheet`, `upsert_results_batch`).
- Use cases: `parse_formula`, `evaluate_preview`, `set_column_formula`, `clear_column_formula`, `list_functions`, `get_formula_graph`, `request_full_recalculation`, `handle_change_event` (outbox consumer that calls `plan_incremental`).
- API endpoints (`services/api/src/formulas/`): `POST /api/v1/formulas/parse`, `POST /api/v1/formulas/evaluate`, `PUT /api/v1/columns/{id}/formula`, `GET /api/v1/sheets/{sheet_id}/formula-graph`, `POST /api/v1/sheets/{sheet_id}/recalculate`, `GET /api/v1/formulas/functions`. DTOs `ParseRequest`, `ParseResponse`, `EvaluateRequest`, `EvaluateResponse`, `SetFormulaRequest`, `FormulaResponse`, `FormulaGraphResponse`, `RecalculateResponse { job_id, status }`, `FunctionCatalogResponse`.
- Events: `formula.updated.v1` (aggregate `column_id`, `changed_fields: [expression, result_type]`), `formula.recalculated.v1` (`column_id`, `cell_count`, `duration_ms`, `batch_id`), `formula.failed.v1` (`column_id`, `reason: cycle|timeout|missing_reference`, `cell_count`); all through the outbox with the contract envelope.
- Authorization: `sheet-editor` on the owning sheet for `PUT /formula` and `POST /recalculate`; `sheet-viewer` for parse, evaluate, functions, and graph; cross-sheet references additionally require `sheet-viewer` on each referenced sheet; missing access maps to `not_found`.
- Validation: expression 1–8,000 chars, `node_count ≤ 10,000`, argument count ≤ 64, `result_type` must be a formula-compatible column type; `Budget { cpu_ms: 2000, max_depth: 256 }`.
- Error mapping: `FormulaError::Syntax → 200 parse response with errors`, `FormulaError::TooLarge | Unsupported | Cycle → 400 invalid with field_errors.expression`, `StaleVersion → 409 conflict`, `RecalcInProgress → 429 rate_limited`, `NotFound → 404 not_found`, `AuthzError::Denied → 403 denied`.

### PostgreSQL/SQLx

- Migration `*_formulas_*.sql` creates `formula_definitions(id uuid pk, tenant_id uuid not null, sheet_id uuid not null, column_id uuid not null, expression_source text not null, expression_canonical text not null, ast jsonb not null, node_count int not null check (node_count <= 10000), result_type text not null, version bigint not null default 1, created_by, created_at, updated_by, updated_at)`, `formula_dependencies(tenant_id, from_column_id uuid, to_sheet_id uuid, to_column_id uuid, kind text, primary key (from_column_id, to_sheet_id, to_column_id, kind))`, `formula_results(tenant_id, row_id uuid, column_id uuid, value jsonb, display text, status text not null check (status in ('ok','error','pending')), error_code text check (error_code in ('invalid','missing_reference','type_mismatch','cycle','timeout')), batch_id uuid, source_version bigint, computed_at timestamptz, primary key (row_id, column_id))`.
- `formula_definitions.ast` stays `jsonb`: it is the compiled payload of one user-authored expression, written and read whole by the evaluator, and every part of it the product queries — the referenced sheets and columns — is already projected into `formula_dependencies` rows with real keys, so nothing filters, joins, or constrains on a key inside the blob (decision 2). `formula_results.value` is a single typed cell value for the same reason as `cells.raw`; the queried facets (`status`, `error_code`, `source_version`, `batch_id`) are typed columns beside it.
- Invariants: unique `formula_definitions(column_id)`; `formula_dependencies.from_column_id` foreign key to `formula_definitions(column_id) on delete cascade`; `formula_results` rows are deleted when the definition is removed; `error_code` is null exactly when `status <> 'error'` (check constraint).
- Indexes: `formula_dependencies(to_sheet_id, to_column_id)` for reverse lookup, `formula_results(column_id, status)` for error counts, `formula_definitions(tenant_id, sheet_id)`.
- Audit events: `formula.set`, `formula.clear`, `formula.recalculate_requested` with the canonical expression diff; results are not audited.
- Retention/deletion: results follow the row soft-delete (hidden, not removed); rollback drops the three tables and the `formula` type remains a shell column in F007.

### React/TypeScript

- Routes: none new; components mount inside the F007 column drawer and the F008 grid. Components in `apps/web/src/features/formulas/`: `FormulaEditor`, `FormulaAutocomplete`, `ReferenceChips`, `FormulaPreviewRow`, `FormulaErrorPopover`, `FormulaCellBadge`, `FormulaGraphPanel`, `RecalculateButton`.
- State: TanStack Query keys `['formula-functions']`, `['formula', columnId]`, `['formula-graph', sheetId]`, `['formula-preview', sheetId, expressionHash, rowId]` (debounced 300 ms); the `set formula` mutation invalidates `['formula', columnId]`, `['grid-rows', sheetId]`, and `['formula-graph', sheetId]`.
- API client: generated `FormulasApi` with `parseFormula`, `evaluateFormula`, `setColumnFormula`, `getFormulaGraph`, `recalculateSheet`, `listFunctions`.
- Optimistic updates: none; cells show `pending` until `formula.recalculated.v1` arrives through the F046 patch channel or a refetch of `['grid-rows', sheetId]`.
- Telemetry: `formula_editor_opened`, `formula_saved`, `formula_parse_error`, `formula_recalculate_requested`, `formula_error_badge_opened` with `sheet_id`, `column_id`, `error_code`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F035-01 through FR-F035-16 in `testing/features/F035/requirements/cases.md`
- [ ] Failure/edge-case tests: 10,001-node expression, unsupported function, self-reference, three-column cycle through a cross-sheet reference, timeout on a pathological `NETWORKDAYS` loop, deleted target sheet, renamed column keeps formula, division by zero returns `type_mismatch`
- [ ] Permission-negative and tenant-isolation tests: viewer `PUT /formula` denied, cross-tenant column `not_found`, cross-sheet reference into an unreadable sheet yields `missing_reference` and never a value
- [ ] Rust unit tests: `crates/domain/src/formulas/` lexer, parser precedence, canonical round-trip, each function group, graph cycle detection, topological order
- [ ] API contract/integration tests: every route above with success and each error code
- [ ] Database migration/constraint tests: node-count check, status/error_code check, cascade on definition delete, rollback
- [ ] React component tests: `FormulaEditor` autocomplete and errors, `FormulaCellBadge`, `FormulaGraphPanel`
- [ ] Browser E2E tests: set formula, edit input cell, observe recalculated parent, cycle rejected in editor, recalculate all
- [ ] Accessibility tests: axe on editor and badges, combobox keyboard flow, error announcement
- [ ] Performance/load tests: parse 1,000 nodes < 20 ms, incremental recalc < 2 s on 100k rows, full recalc < 60 s

### Fast fanout configuration

- Test harness path: `testing/features/F035/`
- Feature flag: `F035_FEATURE`
- Fixture/seed factory: `testing/fixtures/formulas.rs` builds a tenant, editor, viewer, foreign tenant, sheet `Plan` with 200 rows and a 3-level hierarchy, sheet `Rates` with 20 rows, and formula columns `Total`, `Weighted`, `RateLookup`
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z` injected into `TODAY`/`NOW`, UTC
- Mock/stub contracts: in-memory outbox recorder; event consumer driven directly by tests; authz uses the real F003 engine with fixture bindings
- Parallel isolation: one schema per test worker, tenant ID per test
- Targeted command: `cargo xtask test-feature F035`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F035/`

## 6. Acceptance criteria

```gherkin
Feature: Formula engine

Scenario: Parent total recalculates after a child edit
  Given column "Total" on sheet "Plan" has formula =SUM(CHILDREN([Estimate]))
  When an editor changes a child row's Estimate from 3 to 5
  Then the parent's Total shows the new sum within 2 seconds
  And formula.recalculated.v1 is in the outbox with cell_count 1

Scenario: Cycle is rejected at definition time
  Given column "A" references column "B"
  When an editor sets formula =[A]+1 on column "B"
  Then the response is 400 invalid with field_errors.expression starting with "cycle:"
  And no formula_definitions row is written for "B"

Scenario: Cross-sheet reference into an unreadable sheet
  Given a formula on "Plan" that looks up sheet "Rates"
  And the tenant's viewer cannot read "Rates"
  When results are read by that viewer
  Then affected cells show status error with error_code missing_reference

Scenario: Viewer cannot set a formula
  Given a viewer on sheet "Plan"
  When they PUT /api/v1/columns/{id}/formula
  Then the response is 403 denied and no event is published

Scenario: Oversized expression
  When an editor parses an expression with 10,001 AST nodes
  Then the response is 400 invalid with field_errors.expression "too_large"
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F007 (`formula` column type, cell validation object), F009 (hierarchy functions and roll-up events); decisions sections 2–4, 6, 9; contracts row F035
- Blocks: F018, F021, F039, F053, F060
- Conflicts with: none (disjoint owned paths)
- External dependencies: none
- Risks and mitigations: recalculation storms on bulk edits are coalesced per `(sheet_id, column_id)` with a 250 ms debounce in the consumer; f64 rounding differences versus spreadsheet expectations are handled by `ROUND` semantics documented in the function catalog and by currency values carrying integer minor units; memory for 100k-row batches is bounded by streaming rows in 5,000-row chunks.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F007 and F009 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F035/`
- [ ] Migration file name and owned paths claimed
- [ ] Fixture factory `testing/fixtures/formulas.rs` and schema-per-worker isolation available in `testing/harness/`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for every mutation
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F035_FEATURE`, run down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Formula columns evaluate the arithmetic, comparison, conditional, text, date/time, lookup, aggregation, and cross-sheet function groups with incremental recalculation and explicit `#INVALID`, `#REF`, `#TYPE`, `#CYCLE`, and `#TIMEOUT` states.
- Migration adds `formula_definitions`, `formula_dependencies`, and `formula_results`; rollback drops them. Feature is off by default behind `F035_FEATURE`.
