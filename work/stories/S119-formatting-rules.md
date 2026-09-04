---
id: S119
type: story
status: planned
parent_epic: E008
parent_feature: F060
depends_on: [F060]
owned_paths: [crates/domain/src/formatting/**, crates/persistence/src/formatting/**, services/api/src/formatting/**, apps/web/src/features/formatting/**, services/api/migrations/*_formatting_*.sql, testing/features/F060/**]
feature_flag: F060_FEATURE
branch: s119-formatting-rules
started_at: null
finished_at: null
---

# S119 — Formatting rules

## Identity

- Parent feature: `F060` Conditional formatting
- Owner: platform
- Branch: `s119-formatting-rules`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 6; `docs/capability-contracts.md` row F060

## Vertical slice

As a sheet editor, I want to author ordered conditional-formatting rules with typed conditions, row or cell targets, and formats that always carry a non-colour signal, scoped either to the whole sheet or to one saved view, so that the rule set is a durable, explainable, permission-checked contract before anything is painted on screen.

## Requirements

- **SR-S119-01:** `POST /api/v1/formatting-rules` creates a rule with `sheet_id`, optional `view_id`, `name`, `condition`, `target`, `format`, `stop_if_true`, and `enabled`, returning a UUIDv7 `id`, a fractional `position` at the end of its scope, `version` 1, and the resolved `materialized` flag; `FormattingRuleRepository::insert` writes the rule row, one `formatting_rule_conditions` row per AST node, one ordered `formatting_rule_target_columns` row per targeted column, and one `formatting_rule_text_styles` row per style in a single `UnitOfWork`, and the request and response keep their nested JSON shape; the 101st non-deleted rule on a sheet returns `invalid` with `field_errors.sheet_id = "rule_limit"` (covers FR-F060-01).
- **SR-S119-02:** The condition AST validates every leaf against the F007 column type using the F013 operator set, accepts a formula leaf only when the F035 parser reports `result_type = boolean` and at most 200 AST nodes, and rejects more than 20 leaves, more than 4 levels of nesting, or an unknown column with `field_errors.condition` naming the leaf index; the validated tree is persisted as `formatting_rule_conditions` rows carrying `parent_id`, `position`, `node_kind`, and a real `column_id` foreign key, and is reassembled into the same AST on read (FR-F060-02).
- **SR-S119-03:** `target` accepts `{ kind: "row" }` or `{ kind: "cells", column_ids }` with 1 to 50 columns of the same sheet, and `format` accepts only the seven colour tokens, the three text styles, the six icons, and a badge of at most 12 characters, rejecting a fill or text colour with no icon, badge, or text style as `needs_non_color_signal`; the target is stored as `formatting_rules.target_kind` plus ordered `formatting_rule_target_columns` rows and the format as the `fill_token`, `text_color_token`, `icon`, and `badge_text` columns plus `formatting_rule_text_styles` rows, each closed enum held by a `check` constraint (FR-F060-03, FR-F060-04, NFR-F060-03).
- **SR-S119-04:** `GET /api/v1/sheets/{sheet_id}/formatting-rules` returns rules ordered by scope rank then `position` with `view_id` and `enabled` filters, and `POST /api/v1/formatting-rules/{id}/reorder` moves a rule only within its own scope, rejecting a cross-scope target with `field_errors.after_rule_id = "scope_mismatch"` (FR-F060-05, FR-F060-06).
- **SR-S119-05:** A rule with `view_id = null` applies to every read of the sheet and a view-scoped rule applies only through that view and is layered after all sheet-scoped rules; `view_id` must belong to `sheet_id`, and deleting the view soft-deletes its rules (FR-F060-08).
- **SR-S119-06:** `PATCH` requires `If-Match` on `version` and publishes `formatting-rule.updated.v1` with `change_kind` in `created|updated|reordered|enabled|disabled`; `DELETE` soft-deletes and publishes `formatting-rule.deleted.v1`; every mutation requires `sheet-editor` and `Idempotency-Key` and writes an audit row (FR-F060-14).
- **SR-S119-07:** A `sheet-viewer` may list rules but receives `denied` on create, update, delete, and reorder, and cross-tenant rule, sheet, or view IDs return `not_found` (FR-F060-14, NFR-F060-02).
- **SR-S119-08:** Every rule mutation increments `sheets.formatting_rules_version` through `SheetRepository::bump_formatting_rules_version` inside the same `UnitOfWork` transaction as the rule and child rows so the compiled rule-set cache key changes exactly once per mutation (FR-F060-07, NFR-F060-01).
- **SR-S119-09:** The `Conditional formatting` panel lists rules in evaluation order with scope chips, supports drag and `Alt+ArrowUp`/`Alt+ArrowDown` reordering with a live-region announcement, opens the rule editor with condition builder, target picker, format picker, and 10-row preview, and renders read-only for viewers (FR-F060-15, NFR-F060-03).

## Surfaces

- Infrastructure/container: none new; the rule set cache is a per-process cache sized 500 sheets with a 5-minute idle expiry
- Data access: `crates/persistence/src/formatting/{mod.rs, rule_repository.rs, condition_repository.rs, state_repository.rs}` hold every SQL statement for this slice — `FormattingRuleRepository` owns `formatting_rules`, `formatting_rule_conditions`, `formatting_rule_target_columns`, and `formatting_rule_text_styles`, `FormattingStateRepository` owns `formatting_states`, and the `sheets` version bump goes through the F006 `SheetRepository`; `crates/domain/src/formatting` and the `services/api/src/formatting` handlers depend on the repository traits and contain no `sqlx::query*` call (decision section 2.1)
- Rust service/API: `crates/domain/src/formatting/{mod.rs, rule.rs, condition.rs, target.rs, format.rs, compile.rs, errors.rs, service.rs}`; `services/api/src/formatting/{mod.rs, routes.rs, handlers_rules.rs, dto.rs}`
- Data/migration: `services/api/migrations/<ts>_formatting_create_tables.sql` creating `formatting_rules`, `formatting_rule_conditions`, `formatting_rule_target_columns`, `formatting_rule_text_styles`, and `formatting_states`, and adding `sheets.formatting_rules_version` per ticket section 4
- React/UI: `apps/web/src/features/formatting/{FormattingPanel.tsx, RuleList.tsx, RuleListItem.tsx, RuleEditor.tsx, ConditionBuilder.tsx, ConditionLeafRow.tsx, FormulaConditionTab.tsx, TargetPicker.tsx, FormatPicker.tsx, RulePreviewTable.tsx, api.ts, hooks.ts}`
- Mocks/fixtures: `testing/fixtures/formatting.rs` with the `Delivery plan` sheet, its five typed columns, two saved views, and the 10-rule and 100-rule sets; harness lanes under `testing/features/F060/{api,database,frontend}/`

## TDD harness

- Test path: `testing/features/F060/{api,database,frontend}/`
- Feature flag: `F060_FEATURE`
- Targeted command: `cargo xtask test-feature F060`
- Full command: `cargo xtask test-all`
- First failing tests: `create_rule_returns_position_and_version`, `rule_limit_rejects_hundred_first_rule`, `condition_rejects_operator_type_mismatch`, `formula_leaf_must_be_boolean`, `format_without_non_color_signal_rejected`, `reorder_across_scope_rejected`, `view_scoped_rule_absent_from_other_view`, `viewer_cannot_create_or_reorder_rule`, `rule_mutation_bumps_formatting_rules_version`, `condition_tree_round_trips_through_child_rows`, `target_columns_keep_picker_order`

## Exit criteria

- [ ] Requirement tests SR-S119-01 through SR-S119-09 written first and failing
- [ ] Tasks T237 and T238 complete and wired through the API router and the sheet header slot
- [ ] Unit, API, database, React, and permission tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/formatting/routes.rs` mounted in `services/api/src/router.rs` (`/api/v1/formatting-rules`, `/api/v1/sheets/{sheet_id}/formatting-rules`); `apps/web/src/features/formatting/FormattingPanel.tsx` mounted in the F006 `SheetPage` header slot
- [ ] Handoff evidence recorded in the F060 ticket
