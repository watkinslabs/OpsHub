# F035 api cases

File: `testing/features/F035/api/{parser_tests.rs,functions_tests.rs,evaluate_tests.rs,recalc_tests.rs,cross_sheet_tests.rs}`. Flag `F035_FEATURE`.

- `parse_returns_ast_and_references` — FR-F035-01: `=SUM([Estimate])*IF([Priority]="High",1.5,1)` → node_count 9, two references with stable column ids, functions_used `[SUM, IF]`.
- `parse_reports_position_on_syntax_error` — FR-F035-01: `=SUM(` → 200 with `errors[0].code = invalid`, `position = 6`, `expected = ")"`.
- `parse_respects_operator_precedence` — FR-F035-02: `=2+3*4^2` evaluates to 50; `=-2^2` evaluates to -4; `="a"&1+1` evaluates to `a2`.
- `parse_rejects_over_10000_nodes` — FR-F035-03: generated expression with 10,001 nodes → 400 `invalid`, `field_errors.expression = too_large`.
- `parse_rejects_unsupported_function` — FR-F035-03: `=FOO(1)` → 400 `invalid`, `field_errors.expression = unsupported_function:FOO`.
- `canonical_form_survives_column_rename` — FR-F035-02: rename `Estimate` to `Effort` in F007; stored canonical unchanged; pretty print shows `[Effort]`.
- `functions_catalog_matches_registry` — FR-F035-04: GET functions returns every registry entry with group, params, returns, example; no extra entries.
- `arithmetic_group_matches_expected_values` — FR-F035-05: `SUM AVG MIN MAX COUNT COUNTIF SUMIF ROUND ABS MOD` against 30 fixture expressions.
- `text_group_handles_unicode_and_blank` — FR-F035-05: `LEN("héllo")` = 5, `LEFT(blank,2)` = "", `SUBSTITUTE` replaces all occurrences.
- `datetime_group_uses_injected_clock` — FR-F035-05, NFR-F035-02: `TODAY()` = 2026-09-03, `DATEADD`, `DATEDIFF`, `NETWORKDAYS` over a weekend boundary.
- `aggregation_over_children_sums_hierarchy` — FR-F035-05: `SUM(CHILDREN([Estimate]))` on a 3-level parent equals the fixture total; `DESCENDANTS` includes grandchildren.
- `lookup_group_index_match_vlookup` — FR-F035-05: `INDEX/MATCH` and `VLOOKUP` into `Rates` return the rate for a key; missing key → `missing_reference`.
- `division_by_zero_is_type_mismatch` — FR-F035-05: `=1/0` → status error, `type_mismatch`; `IFERROR(1/0, 0)` → 0.
- `evaluate_preview_type_mismatch` — FR-F035-07: `=LEN(5)` on row 1 → `{ status: error, error_code: type_mismatch }`, nothing persisted.
- `evaluate_preview_times_out_within_budget` — FR-F035-11: pathological nested `NETWORKDAYS` loop → `timeout` within 2,100 ms wall clock.
- `set_formula_rewrites_dependencies_and_emits_event` — FR-F035-06: PUT formula → `formula_definitions` row, edges replaced, `formula.updated.v1`, full-column results `pending` then `ok`.
- `set_formula_null_clears_results` — FR-F035-06: `expression: null` deletes definition, edges, and results.
- `set_formula_stale_version_conflicts` — FR-F035-06: `If-Match` behind column version → 409 with `current_version`.
- `cycle_rejected_at_definition_time` — FR-F035-10: A→B then B→A → 400 `cycle:<A>,<B>`; no definition written for B.
- `cycle_through_cross_sheet_detected_at_recalc` — FR-F035-10: cycle closed by a linked sheet change → cells `cycle`, `formula.failed.v1`.
- `incremental_recalc_touches_only_dependents` — FR-F035-09: edit one child → exactly the parent `Total` and `Weighted` cells recomputed; unrelated columns untouched.
- `recalc_runs_in_topological_order` — FR-F035-09: chain A→B→C recomputes A, then B, then C; three `formula.recalculated.v1` events in order.
- `timeout_marks_remaining_cells` — FR-F035-11: budget exhausted mid-column → remaining rows `timeout`, `batch_id` set, `formula.failed.v1` reason timeout.
- `replayed_event_is_idempotent` — NFR-F035-04: same `cell.updated.v1` delivered twice → one recalculation, results unchanged.
- `recalculate_route_rate_limits_second_job` — FR-F035-14: first POST → 202 under 2 s; second while active → 429 `rate_limited`.
- `cross_sheet_unreadable_yields_missing_reference` — FR-F035-12: viewer without `Rates` access reads `RateLookup` → `missing_reference`, never a value.
- `cross_sheet_foreign_tenant_not_found_at_definition` — FR-F035-12, FR-F035-16: `{sheet:<tenant B id>}` in PUT → 404 `not_found`.
- `formula_graph_reports_depth_and_cycle` — FR-F035-13: graph for `Plan` → nodes for 3 columns and `Rates`, depth 2, `has_cycle` false; after cycle injection true.
- `viewer_mutation_denied` — FR-F035-16: viewer PUT formula and POST recalculate → 403 `denied`; parse and evaluate allowed.
- `cross_tenant_ids_not_found` — FR-F035-16: tenant B ids on every route → 404.
- `recalc_span_carries_ids_and_metrics` — NFR-F035-04: span has `tenant_id`, `sheet_id`, `column_id`, `correlation_id`; metrics counters increment.

Evidence: JUnit output and request logs under `testing/evidence/F035/api/`.
