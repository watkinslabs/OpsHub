---
id: T239
type: task
status: planned
parent_epic: E008
parent_feature: F060
parent_story: S120
depends_on: [S120]
owned_paths: [crates/domain/src/formatting/**, crates/persistence/src/formatting/**, services/api/src/formatting/**, services/worker/src/formatting/**, apps/web/src/features/formatting/**, testing/features/F060/e2e/**]
feature_flag: F060_FEATURE
branch: t239-evaluation-path
started_at: null
finished_at: null
---

# T239 — Evaluation path

## Identity

- Parent story: `S120` Visual states
- Owner: platform
- Branch: `t239-evaluation-path`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 6, 9; `docs/capability-contracts.md` row F060

## Objective

Implement the deterministic evaluator and both evaluation paths: on-read attachment of `formatting` to the F006, F008, and F013 row reads plus the evaluate and explain route, and on-write materialization of formula-backed and large-sheet rules into `formatting_states` with staleness fallback and repair, together with the grid rendering, legend, explanation popover, and signal mode.

## Specification

- Owned paths: `crates/domain/src/formatting/{evaluate.rs, state.rs, explain.rs, budget.rs}`, `crates/persistence/src/formatting/{rule_repository.rs, state_repository.rs}`, `services/api/src/formatting/{handlers_evaluate.rs, read_hook.rs}`, `services/worker/src/formatting/{mod.rs, materialize.rs, repair.rs}`, `apps/web/src/features/formatting/{useRowFormatting.ts, FormattingLegend.tsx, WhyFormattedPopover.tsx, SignalModeSwitch.tsx, formatState.css}`
- Contract/input: `EvaluateRequest { row_ids?, rule?, view_id?, limit (1–200, default 50), explain? }` on `POST /api/v1/sheets/{sheet_id}/formatting/evaluate`; the `include=formatting` query parameter on `GET /api/v1/sheets/{sheet_id}/rows`, `GET /api/v1/sheets/{sheet_id}/changes`, and `GET /api/v1/views/{id}/rows`; worker input is the event set `cell.updated.v1`, `cells.bulk-updated.v1`, `rows.bulk-updated.v1`, `row.created.v1`, `row.deleted.v1`, `formula.recalculated.v1`, `formatting-rule.updated.v1`, and `column.deleted.v1`.
- Output/behavior: `evaluate.rs` folds the compiled rule set over each row's F006 cell map reading `cells[column_id].raw` only, delegating formula leaves to the F035 evaluator with the injected clock, applying properties in scope-then-position order with cell targets overriding row targets and `stop_if_true` halting the row, and emitting `RowFormatting { row, cells, applied_rule_ids, hidden_inputs, degraded }` with `winners` per property. `read_hook.rs` registers `FormattingEvaluator` on the shared `RowReadContext` so the three read handlers attach `formatting` after permission filtering. A leaf over an unreadable column is unmatched and its rule id is added to `hidden_inputs`; a cell with F035 `status = error` matches only `is_error`; exceeding the 150 ms page budget in `budget.rs` returns the page with `degraded = true, reason = "budget"` while the evaluate route returns `503 unavailable`. `materialize.rs` resolves affected `(rule_id, row_id)` pairs from each event, upserts `formatting_states` with `matched` and `source_change_version` in batches of 500, is idempotent per `(rule_id, row_id, source_change_version)`, and on `column.deleted.v1` disables every rule referencing the column by joining `formatting_rule_conditions(column_id)` and `formatting_rule_target_columns(column_id)`; `repair.rs` drains stale rows with per-sheet concurrency 1. The read path serves a materialized state only when `source_change_version` is at least the row's last change version and otherwise evaluates inline and enqueues a repair. `explain.rs` returns per rule `matched`, `leaf_results`, and `skipped_reason`. The web layer applies states as `--fmt-fill`, `--fmt-text`, and `--fmt-icon` custom properties on the F008 row and cell elements, renders `FormattingLegend` (opened with `Shift+F`), `WhyFormattedPopover` listing applied rules in order and rendering `hidden_inputs` as `Uses a column you cannot read`, and `SignalModeSwitch` whose `Icon only` mode sets `--fmt-fill: transparent` at the grid root and is mirrored in the `signals` query parameter; formatted rows carry `aria-describedby` naming the applied rules and the newly-matched flash is removed under `prefers-reduced-motion`. Metrics `formatting_eval_duration_ms{path}`, `formatting_rules_evaluated_total`, `formatting_states_stale_total`, and `formatting_degraded_total{reason}` are exported and spans carry `tenant_id`, `sheet_id`, `view_id`, `rules_version`, and `correlation_id`.
- Data access: `evaluate.rs`, `state.rs`, `explain.rs`, `budget.rs`, `read_hook.rs`, `handlers_evaluate.rs`, `materialize.rs`, and `repair.rs` hold no SQL. Rules and their condition, target-column, and text-style rows load through `FormattingRuleRepository::load_compiled_rule_set`, column-deletion repair through `list_rules_referencing_column` and `disable_rules_referencing_column`, cached matches through `FormattingStateRepository::{list_states_for_rows, upsert_state_batch, list_stale_rows, delete_states_for_rule}`, and rows and cells through the F006 `RowRepository`; the evaluator is handed already-loaded cell maps and never opens a connection, and each 500-row materialization batch and each repair drain commits in one `UnitOfWork` (decision section 2.1). A served cached row supplies `matched` only; the painted properties come from the rule's typed format columns and `formatting_rule_text_styles` rows, which is why the inline and cached folds cannot diverge.
- Dependencies: T237 for the rule aggregate, its child tables, the compiled rule set, and the `formatting_states` table; F008 changes feed and `VirtualGrid` renderers; F013 view rows handler; F035 evaluator and recalculation events; F003 permission filtering; F004 job transport and metrics.
- Feature flag: `F060_FEATURE` gates the read hook, the evaluate route, and the worker jobs; with the flag off the reads omit the `formatting` field entirely.

## TDD

- Failing test first: `testing/features/F060/api/evaluate_tests.rs::later_rule_overrides_fill_only`, `::cell_target_overrides_row_target`, `::stop_if_true_halts_evaluation`, `::disabled_rule_is_skipped`, `::row_read_attaches_formatting_when_included`, `::view_scoped_rule_absent_from_other_view`, `::hidden_column_leaf_is_unmatched_and_reported`, `::formula_error_cell_matches_only_is_error`, `::budget_exceeded_returns_degraded_page`, `::explain_lists_leaf_results_in_order`; `testing/features/F060/api/materialize_tests.rs::materialized_state_refreshed_on_formula_recalculated`, `::materialize_idempotent_per_source_change_version`, `::stale_state_falls_back_to_inline_evaluation`, `::inline_and_materialized_states_match_over_five_thousand_rows`, `::column_delete_disables_referencing_rules`, `::rule_format_change_repaints_cached_matches_without_rewriting_states`; `testing/features/F060/e2e/formatting.spec.ts::grid_repaints_after_rule_reorder`, `::why_formatted_popover_lists_rules_in_order`, `::icon_only_mode_drops_fills`
- Targeted command: `cargo xtask test-feature F060`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/formatting.rs` with the 6 seeded exception rows, the 5,000-row equivalence set, recorded `formula.recalculated.v1` payloads, a permission fixture hiding the `Budget` column from one actor, and a budget-forcing rule set of 100 formula rules; fixed clock `2026-09-03T00:00:00Z`

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] `read_hook.rs` registered in the API state and called by the F006, F008, and F013 row read handlers; `materialize.rs` and `repair.rs` registered in `services/worker/src/registry.rs`
- [ ] Inline and materialized states proven identical over the 5,000-row equivalence test
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S120
- [ ] `finished_at` recorded
