# F060 api cases

File: `testing/features/F060/api/{rule_tests.rs,compile_tests.rs,evaluate_tests.rs,materialize_tests.rs,read_hook_tests.rs,negative_tests.rs}`. Flag `F060_FEATURE`.

- `create_rule_returns_position_and_version` — FR-F060-01: create against `Delivery plan` → UUIDv7 id, fractional position after the last sheet-scoped rule, `version` 1, `materialized: false`.
- `rule_limit_rejects_hundred_first_rule` — FR-F060-01: 100 rules seeded, the next create → 400 `invalid` with `field_errors.sheet_id = "rule_limit"` and no row written.
- `condition_rejects_operator_type_mismatch` — FR-F060-02: `before` on the `Status` select column → 400 with `field_errors.condition` naming leaf index 0.
- `formula_leaf_must_be_boolean` — FR-F060-02: `{ formula: "Budget * 2" }` parses to number → 400 `NonBooleanFormula`; `Variance > 0` accepted.
- `condition_rejects_twenty_first_leaf` — FR-F060-02: 21 leaves and depth 5 both rejected with the offending index.
- `target_cells_rejects_foreign_column` — FR-F060-03: a column id from another sheet → 400 with `field_errors.target.column_ids`.
- `format_without_non_color_signal_rejected` — FR-F060-04: `fill: format.red` alone → 400 `needs_non_color_signal`; adding `icon: alert-triangle` succeeds.
- `unknown_color_token_rejected` — FR-F060-04: `fill: "#ff0000"` → 400 with `field_errors.format.fill`.
- `rule_list_orders_sheet_scope_before_view_scope` — FR-F060-05: mixed set returns sheet rules by position then view rules by position; `enabled=false` filter returns only the disabled rule.
- `reorder_across_scope_rejected` — FR-F060-06: sheet rule after a view rule → 400 `scope_mismatch`; a valid reorder publishes `formatting-rule.updated.v1` with `change_kind: reordered`.
- `later_rule_overrides_fill_only` — FR-F060-07: `Mine` (blue, badge) then `Late` (red, icon) → fill red, badge kept from `Mine`, `winning_rule_id` per property.
- `cell_target_overrides_row_target` — FR-F060-03, FR-F060-07: a cell rule at position 1 beats a row rule at position 5 on the `Budget` column only.
- `stop_if_true_halts_evaluation` — FR-F060-07: the third rule never appears in `applied_rule_ids` when the second sets `stop_if_true`.
- `disabled_rule_is_skipped` — FR-F060-07: disabling a matching rule removes it from `applied_rule_ids` on the next read.
- `evaluation_is_stable_across_repeat_runs` — FR-F060-07: the same row evaluated 100 times yields byte-identical state.
- `view_scoped_rule_absent_from_other_view` — FR-F060-08: `At risk` read applies both rules, `All work` read applies only the sheet rule; deleting `At risk` soft-deletes its rule.
- `row_read_attaches_formatting_when_included` — FR-F060-09: `include=formatting` on the F006 rows, F008 changes, and F013 view rows returns the `formatting` object; omitting it returns rows without the field.
- `materialized_flag_resolved_at_write` — FR-F060-10: a formula-leaf rule and a rule on a 20,001-row sheet are `materialized: true`; a plain date rule on a 50-row sheet is false.
- `materialized_state_refreshed_on_formula_recalculated` — FR-F060-10: patching `Budget` and replaying `formula.recalculated.v1` upserts `formatting_states` with the new `source_change_version`.
- `materialize_idempotent_per_source_change_version` — NFR-F060-04: replaying the same event writes no second row and leaves `evaluated_at` unchanged.
- `stale_state_falls_back_to_inline_evaluation` — FR-F060-11: a state one version behind is ignored, the fresh value is served, and a repair is enqueued; `formatting_states_stale_total` increments.
- `inline_and_materialized_states_match_over_five_thousand_rows` — FR-F060-11: both paths produce identical state objects for 5,000 rows.
- `evaluate_returns_draft_preview_without_persisting` — FR-F060-12: a draft rule over 10 rows returns states and writes no `formatting_rules` row.
- `explain_lists_leaf_results_in_order` — FR-F060-12: `explain: true` returns `matched`, `leaf_results`, and `skipped_reason` per rule for one row.
- `hidden_column_leaf_is_unmatched_and_reported` — FR-F060-13, NFR-F060-02: the actor denied `Budget` gets the rule id in `hidden_inputs` and no state, and no `Budget` value appears in the response.
- `formula_error_cell_matches_only_is_error` — FR-F060-13: a `#CYCLE` cell matches `is_error` and fails `gt`, `eq`, and `is_empty` without erroring the read.
- `budget_exceeded_returns_degraded_page` — FR-F060-13: 100 formula rules over 500 rows past 150 ms → page with `degraded: true`, `reason: "budget"`; the evaluate route returns 503 `unavailable`; `formatting_degraded_total` increments.
- `stale_version_patch_conflicts` — FR-F060-14: `If-Match` on an old version → 409 with the current version and no write.
- `delete_publishes_deleted_event_and_soft_deletes` — FR-F060-14: `DELETE` → `deleted_at` set, `formatting-rule.deleted.v1` published, rule absent from the list.
- `viewer_cannot_create_or_reorder_rule` — FR-F060-14: sheet-viewer POST, PATCH, DELETE, and reorder → 403 `denied`; list and evaluate → 200.
- `foreign_tenant_rule_not_found` — NFR-F060-02: tenant B rule, sheet, and view ids → 404 on every route.
- `rule_mutation_bumps_formatting_rules_version` — FR-F060-07, NFR-F060-01: each mutation increments `sheets.formatting_rules_version` exactly once and writes an audit row.
- `compiled_set_cached_until_rules_version_changes` — NFR-F060-01: two reads compile once; a mutation forces a recompile.
- `column_delete_disables_referencing_rules` — FR-F060-10: `column.deleted.v1` for `Owner` disables the rules referencing it and marks `field_errors.condition = "missing_column"`.

Evidence: JUnit output, outbox recordings, and metric snapshots under `testing/evidence/F060/api/`.
