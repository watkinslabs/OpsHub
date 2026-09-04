---
id: T238
type: task
status: planned
parent_epic: E008
parent_feature: F060
parent_story: S119
depends_on: [S119]
owned_paths: [apps/web/src/features/formatting/**, testing/features/F060/frontend/**]
feature_flag: F060_FEATURE
branch: t238-formatting-ui
started_at: null
finished_at: null
---

# T238 — Formatting UI

## Identity

- Parent story: `S119` Formatting rules
- Owner: platform
- Branch: `t238-formatting-ui`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 6, 9; `docs/capability-contracts.md` row F060

## Objective

Build the `Conditional formatting` panel: the ordered rule list with scope chips and keyboard reordering, the rule editor with condition builder, formula tab, target picker, and format picker that enforces a non-colour signal before submit, and the live 10-row preview driven by the evaluate route.

## Specification

- Owned paths: `apps/web/src/features/formatting/{FormattingPanel.tsx, RuleList.tsx, RuleListItem.tsx, RuleEditor.tsx, ConditionBuilder.tsx, ConditionLeafRow.tsx, FormulaConditionTab.tsx, TargetPicker.tsx, FormatPicker.tsx, RulePreviewTable.tsx, api.ts, hooks.ts, index.ts}`
- Contract/input: generated `FormattingApi` with `listRules`, `createRule`, `updateRule`, `deleteRule`, `reorderRule`, and `evaluate`; query keys `['formatting-rules', sheetId, viewId]` and `['formatting-evaluate', sheetId, draftHash]`; the panel opens from the F006 `SheetPage` header slot at `?panel=formatting` and reads the F007 column list for the condition builder.
- Output/behavior: the rule list renders rules in evaluation order with a visible position number, a `Sheet` or `View` scope chip, an enable toggle, and reordering by drag or `Alt+ArrowUp`/`Alt+ArrowDown` with a live region announcing `Moved Late tasks to position 2 of 5`; `reorderRule` is optimistic and rolls back to the server order on `conflict`. The editor builds the condition AST with typed value controls per F007 column type, offers a formula tab that blocks submit until the parse reports a boolean result, a target radio group with a column multi-select capped at 50, and a format picker whose colour swatches are the seven tokens and which disables `Save` with the message `Add an icon, badge, or text style so colour is not the only signal` until a non-colour signal is chosen. `RulePreviewTable` debounces 300 ms and calls `evaluate` with the draft rule for 10 rows, showing the resolved swatch, icon, and badge per row. States: skeleton list while loading, `No rules yet` empty state with one example, error banner with `correlation_id` and `Retry`, `Rule saved` toast, `This rule changed` stale banner with `Reload` and the field diff, and a read-only panel without `New rule` for viewers. Telemetry events `formatting_rule_created`, `formatting_rule_reordered`, `formatting_rule_disabled`, and `formatting_preview_run`.
- Dependencies: F008 `VirtualGrid` header slot for mounting; F007 column metadata hook for operators and value editors; F035 formula editor component reused inside the formula tab; design tokens in `apps/web/src/design/tokens.css`.
- Feature flag: `F060_FEATURE` gates the panel entry point; with the flag off the header menu item is absent.

## TDD

- Failing test first: `testing/features/F060/frontend/RuleEditor.test.tsx::blocks_save_until_non_color_signal_chosen`, `::formula_tab_blocks_save_on_non_boolean_result`, `::target_picker_caps_column_selection_at_fifty`; `testing/features/F060/frontend/ConditionBuilder.test.tsx::offers_only_operators_valid_for_column_type`, `::reports_leaf_index_from_field_errors`; `testing/features/F060/frontend/RuleList.test.tsx::keyboard_reorder_announces_new_position`, `::optimistic_reorder_rolls_back_on_conflict`, `::viewer_sees_read_only_panel`; `testing/features/F060/frontend/RulePreviewTable.test.tsx::debounced_preview_renders_ten_rows`, `::preview_error_shows_retry_with_correlation_id`
- Targeted command: `cargo xtask test-feature F060`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: Vitest with MSW handlers for the six F060 routes plus the F007 column list, seeded from `testing/features/F060/frontend/fixtures/rules.json` (10 rules across both scopes, one disabled, one formula rule) and the `Delivery plan` column set; `prefers-reduced-motion` and viewport variants driven from the test setup

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Panel mounted in the F006 `SheetPage` header slot behind the flag and reachable from the view header
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S119
- [ ] `finished_at` recorded
