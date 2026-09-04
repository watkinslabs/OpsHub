---
id: S120
type: story
status: planned
parent_epic: E008
parent_feature: F060
depends_on: [F060]
owned_paths: [crates/domain/src/formatting/**, crates/persistence/src/formatting/**, services/api/src/formatting/**, services/worker/src/formatting/**, apps/web/src/features/formatting/**, testing/features/F060/**]
feature_flag: F060_FEATURE
branch: s120-visual-states
started_at: null
finished_at: null
---

# S120 — Visual states

## Identity

- Parent feature: `F060` Conditional formatting
- Owner: platform
- Branch: `s120-visual-states`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 6, 9; `docs/capability-contracts.md` row F060

## Vertical slice

As a sheet reader, I want every row and cell to carry a resolved visual state that is computed the same way on every read, refreshed when the underlying data changes, explainable rule by rule, and readable without colour, so that I can trust what the sheet is telling me and find out why it is telling me that.

## Requirements

- **SR-S120-01:** Resolution is deterministic: matching rules apply in scope-then-position order, each writes its own set properties over earlier ones, a cell-target state always overrides a row-target state for the same property, `stop_if_true` ends the row, disabled rules are skipped, and the result carries `applied_rule_ids` in order plus `winning_rule_id` per property (covers FR-F060-07).
- **SR-S120-02:** `include=formatting` on the F006 row list, the F008 changes feed, and the F013 view rows attaches `formatting` per row computed inside the same request from the compiled rule set against already permission-filtered cells; each handler loads its rules through `FormattingRuleRepository::load_compiled_rule_set` and its cached matches through `FormattingStateRepository::list_states_for_rows` and issues no SQL of its own (FR-F060-09).
- **SR-S120-03:** Rules containing a formula leaf, referencing a `formula` column, or living on a sheet over 20,000 rows are `materialized` and recomputed by the `formatting.materialize` worker from `cell.updated.v1`, `cells.bulk-updated.v1`, `rows.bulk-updated.v1`, `row.created.v1`, `row.deleted.v1`, `formula.recalculated.v1`, and `formatting-rule.updated.v1`, upserting `formatting_states` with `matched` and `source_change_version` through `FormattingStateRepository::upsert_state_batch`; the cache row records the match only, and the painted properties come from the rule's typed `fill_token`, `text_color_token`, `icon`, `badge_text`, and `formatting_rule_text_styles` rows at fold time (FR-F060-10, NFR-F060-04).
- **SR-S120-04:** A materialized state is served only when `source_change_version` is at least the row's last change version; otherwise the read evaluates that rule inline, serves the fresh state, and enqueues a repair, and inline evaluation and the cached-match fold produce identical `FormatState` objects for the same inputs because both read the same rule format columns (FR-F060-11).
- **SR-S120-05:** `POST /api/v1/sheets/{sheet_id}/formatting/evaluate` returns resolved states for up to 200 rows without persisting, accepts an unsaved draft rule for the editor preview, and with `explain: true` returns per rule `matched`, `leaf_results`, and `skipped_reason` for the `Why is this row highlighted?` popover (FR-F060-12).
- **SR-S120-06:** Evaluation never widens visibility and never fails a read: a leaf over a column the actor cannot read is unmatched and its rule id lands in `hidden_inputs`, a cell with F035 `status = error` matches only `is_error`, and exceeding the 150 ms page budget returns the page with `degraded = true` and `reason = "budget"` while the evaluate route returns `unavailable` (FR-F060-13, NFR-F060-02).
- **SR-S120-07:** The grid applies a row state as CSS custom properties on the row element with per-cell overrides, renders the legend of enabled rules, offers the `Colour and icon` or `Icon only` signal mode persisted per user, exposes `aria-describedby` naming the applied rules on every formatted row, and drops the newly-matched flash under `prefers-reduced-motion` (FR-F060-15, NFR-F060-03).
- **SR-S120-08:** Performance gates hold: a 100-rule set compiles in under 5 ms and is cached per `(sheet_id, rules_version)`, 100 rules over 500 rows evaluate in under 25 ms p95 and add at most 10% to the view row-page p95, 100,000-row materialization finishes in under 90 s, and the 500-row viewport paints with no frame over 16 ms (NFR-F060-01).
- **SR-S120-09:** Observability holds: `formatting_eval_duration_ms{path}`, `formatting_rules_evaluated_total`, `formatting_states_stale_total`, and `formatting_degraded_total{reason}` are exported and every evaluation span carries `tenant_id`, `sheet_id`, `view_id`, `rules_version`, and `correlation_id` (NFR-F060-04).

## Surfaces

- Infrastructure/container: the `formatting.materialize` and `formatting.repair` jobs registered on the F004 job transport with per-sheet concurrency 1 and batches of 500 rows
- Data access: `crates/persistence/src/formatting/{rule_repository.rs, state_repository.rs}` hold every SQL statement for this slice — the evaluator, `read_hook.rs`, `handlers_evaluate.rs`, `materialize.rs`, and `repair.rs` reach rules through `FormattingRuleRepository` (`load_compiled_rule_set`, `list_rules_referencing_column`, `disable_rules_referencing_column`), cached matches through `FormattingStateRepository` (`list_states_for_rows`, `upsert_state_batch`, `list_stale_rows`, `delete_states_for_rule`), and rows and cells through the F006 `RowRepository`; no `sqlx::query*` call appears in the grid handler, the evaluate handler, or the worker jobs, and each 500-row materialization batch commits in one `UnitOfWork` (decision section 2.1)
- Rust service/API: `crates/domain/src/formatting/{evaluate.rs, state.rs, explain.rs, budget.rs}`; `services/api/src/formatting/{handlers_evaluate.rs, read_hook.rs}` registering `FormattingEvaluator` on the shared `RowReadContext`; `services/worker/src/formatting/{mod.rs, materialize.rs, repair.rs}`
- Data/migration: reads `formatting_rules` with its `formatting_rule_conditions`, `formatting_rule_target_columns`, and `formatting_rule_text_styles` children, reads and writes `formatting_states`, and reads `sheets.formatting_rules_version`, all created by S119; no additional migration
- React/UI: `apps/web/src/features/formatting/{useRowFormatting.ts, FormattingLegend.tsx, WhyFormattedPopover.tsx, SignalModeSwitch.tsx, formatState.css}` consumed by the F008 `VirtualGrid` row and cell renderers
- Mocks/fixtures: `testing/fixtures/formatting.rs` 100,000-row generator, the 6 seeded exception rows, recorded F035 recalculation events, and the token-contrast table read from `apps/web/src/design/tokens.css`; harness lanes under `testing/features/F060/{api,e2e,accessibility,performance}/`

## TDD harness

- Test path: `testing/features/F060/{api,e2e,accessibility,performance}/`
- Feature flag: `F060_FEATURE`
- Targeted command: `cargo xtask test-feature F060`
- Full command: `cargo xtask test-all`
- First failing tests: `later_rule_overrides_fill_only`, `cell_target_overrides_row_target`, `stop_if_true_halts_evaluation`, `row_read_attaches_formatting_when_included`, `materialized_state_refreshed_on_formula_recalculated`, `stale_state_falls_back_to_inline_evaluation`, `hidden_column_leaf_is_unmatched_and_reported`, `budget_exceeded_returns_degraded_page`, `explain_lists_leaf_results_in_order`

## Exit criteria

- [ ] Requirement tests SR-S120-01 through SR-S120-09 written first and failing
- [ ] Tasks T239 and T240 complete and wired through the row read handlers and the worker registry
- [ ] Unit, API, E2E, accessibility, and performance tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/formatting/read_hook.rs` registered in `services/api/src/router.rs` state and called by the F006, F008, and F013 row read handlers through `RowReadContext`; `services/worker/src/formatting/materialize.rs` registered in `services/worker/src/registry.rs`
- [ ] Inline and materialized states proven identical over the 5,000-row equivalence test
- [ ] Handoff evidence recorded in the F060 ticket
