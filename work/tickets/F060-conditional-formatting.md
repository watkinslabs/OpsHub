---
id: F060
type: feature
status: planned
priority: P1
owner: platform
estimate: 3
target_milestone: M7
parent_epic: E008
depends_on: [F008, F035]
blocks: []
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/formatting/**, crates/persistence/src/formatting/**, services/api/src/formatting/**, services/worker/src/formatting/**, apps/web/src/features/formatting/**, services/api/migrations/*_formatting_*.sql, testing/features/F060/**]
feature_flag: F060_FEATURE
flag_default: off
branch: f060-conditional-formatting
started_at: null
finished_at: null
---

# F060 — Conditional formatting

## 1. Identity and dates

- Branch: `f060-conditional-formatting`
- Capability area: advanced modules (spec 5.1 low-level bullet "conditional formatting evaluates typed rules against current values and exposes deterministic visual states in every supported view")
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 6, 9; `docs/capability-contracts.md` row F060
- Module slug: `formatting`; aggregate: `formatting-rule`

## 2. Requirement specification

### Problem and user outcome

A 40,000-row delivery sheet hides its exceptions. People scan for late tasks, blocked owners, and budget overruns by reading every row, and today the only way to mark them is to type a status word by hand and keep it current. Teams want the sheet to mark itself: typed rules over the F007 column values and F035 formula results that paint rows and cells, in a fixed and explainable order, identically in the grid and in every saved view, without turning colour into the only way to read the data.

As a sheet editor, I want ordered conditional-formatting rules scoped to a sheet or to one view, with row or cell targets and a non-colour signal on every rule, so that exceptions are visible at a glance to every reader — including screen-reader and colour-blind users — and I can explain exactly which rule painted a given cell.

### Functional requirements

- **FR-F060-01:** An actor with `sheet-editor` on the sheet can create a rule with `POST /api/v1/formatting-rules` carrying `{ sheet_id, view_id?, name (1–120 chars), condition, target, format, stop_if_true?, enabled? }`; the response returns a UUIDv7 `id`, a fractional `position` after the last rule in the same scope, `version` 1, and the resolved `materialized` flag. A sheet holding 100 non-deleted rules (sheet-scoped plus view-scoped together) returns `invalid` with `field_errors.sheet_id = "rule_limit"` and writes nothing.
- **FR-F060-02:** `condition` is a typed AST of `and`/`or` groups over leaves `{ column_id, op, value }` reusing the F013 operator set per F007 column type (`eq`, `neq`, `contains`, `in`, `is_empty`, `is_not_empty`, `gt`, `lt`, `between`, `before`, `after`, `is_me`, `is_error`), plus a leaf kind `{ formula: "<expression>" }` parsed by the F035 parser and required to have `result_type = boolean` and at most 200 AST nodes. A condition holds at most 20 leaves and nests at most 4 levels; an unknown column ID, an operator invalid for the column type, a non-boolean formula, or an over-size condition returns `invalid` with `field_errors.condition` naming the offending leaf index. The AST is stored as one `formatting_rule_conditions` row per node — `parent_id` for the enclosing group, `position` for evaluation order within that group, `node_kind` in `and|or|leaf|formula`, a real `column_id` foreign key on leaves — so a leaf is joinable, constrainable and indexable; the request and response keep the nested JSON AST unchanged.
- **FR-F060-03:** `target` is either `{ kind: "row" }` or `{ kind: "cells", column_ids: [...] }` with 1 to 50 column IDs of the same sheet, stored as `formatting_rules.target_kind` plus one ordered `formatting_rule_target_columns` row per column so the picker order round-trips and each column is a foreign key; a cell target listing a deleted or foreign column returns `invalid` with `field_errors.target.column_ids`, and a duplicate column ID is rejected by the child table's primary key. Row targets produce a row state; cell targets produce a per-column state, and a cell state always overrides a row state for the same property regardless of rule order.
- **FR-F060-04:** `format` carries `fill`, `text_color` (both from the fixed token set `format.red`, `format.amber`, `format.green`, `format.blue`, `format.violet`, `format.slate`, `format.none` defined in `apps/web/src/design/tokens.css`), `text_style` (any of `bold`, `italic`, `strikethrough`), `icon` (Lucide `alert-triangle`, `check-circle`, `clock`, `flag`, `circle-dot`, `octagon-x`), and `badge_text` (≤ 12 chars), stored as the typed columns `fill_token`, `text_color_token`, `icon`, `badge_text` on `formatting_rules` with `check` constraints over the token, style and icon enums, plus one `formatting_rule_text_styles` row per selected style; the request and response keep `format` as one JSON object with `text_style` as an array. A format that sets `fill` or `text_color` without at least one of `text_style`, `icon`, or `badge_text` returns `invalid` with `field_errors.format = "needs_non_color_signal"`; an unknown token returns `invalid` with `field_errors.format.fill`.
- **FR-F060-05:** `GET /api/v1/sheets/{sheet_id}/formatting-rules` returns every rule the actor can read, ordered by scope rank (sheet-scoped first, then view-scoped) and then ascending `position`, each with `condition`, `target`, `format`, `enabled`, `stop_if_true`, `materialized`, `version`, audit fields, and `last_evaluated_at`; `view_id` and `enabled` are supported filters. The response bodies are unchanged JSON: `FormattingRuleRepository::list_rules_for_sheet` reads the rule rows with their condition, target-column and text-style children in one query per scope and reassembles the nested `condition` AST, the `target.column_ids` array and the `format` object.
- **FR-F060-06:** `POST /api/v1/formatting-rules/{id}/reorder` with `{ after_rule_id | null }` moves a rule within its own scope only (a sheet-scoped rule can never be ordered among view-scoped rules and the reverse returns `invalid` with `field_errors.after_rule_id = "scope_mismatch"`), recomputes the fractional `position`, increments `version`, and publishes `formatting-rule.updated.v1` with `change_kind = "reordered"`.
- **FR-F060-07:** Resolution is deterministic: matching rules are applied in the FR-F060-05 order, each matching rule writes its own set properties over the properties written by earlier rules, `stop_if_true` ends evaluation of that row after the rule is applied, and disabled rules are skipped. The resolved state exposes `applied_rule_ids` in application order and `winning_rule_id` per property, so two evaluations of the same row and rule set always produce the identical state.
- **FR-F060-08:** A rule with `view_id = null` applies wherever the sheet is read (grid, board, and every saved view); a rule with a `view_id` applies only when rows are read through that F013 view and is layered after all sheet-scoped rules. Deleting the view soft-deletes its view-scoped rules; the `view_id` must belong to `sheet_id` or the create returns `invalid` with `field_errors.view_id`.
- **FR-F060-09:** Row reads evaluate on read. `GET /api/v1/sheets/{sheet_id}/rows` (F006), `GET /api/v1/sheets/{sheet_id}/changes` (F008), and `GET /api/v1/views/{id}/rows` (F013) accept `include=formatting` and attach `formatting: { row: FormatState, cells: { <column_id>: FormatState }, applied_rule_ids, hidden_inputs, degraded }` per row, computed from the compiled rule set of that sheet inside the same request against the already permission-filtered cells.
- **FR-F060-10:** Rules whose condition contains a formula leaf or references a column of type `formula`, and every rule on a sheet with more than 20,000 non-deleted rows, are marked `materialized = true` and evaluated on write: the worker `formatting.materialize` consumes `cell.updated.v1`, `cells.bulk-updated.v1`, `rows.bulk-updated.v1`, `row.created.v1`, `row.deleted.v1`, `formula.recalculated.v1`, and `formatting-rule.updated.v1` and upserts one `formatting_states` row per `(rule_id, row_id)` with `matched`, `source_change_version`, and `evaluated_at` through `FormattingStateRepository::upsert_state_batch`. The row records only whether that rule matched; the painted properties come from the rule's own typed format columns at fold time, so the cache never holds a second copy of a format that the rule can change.
- **FR-F060-11:** The read path uses a materialized state only when its `source_change_version` is greater than or equal to the row's last change version; otherwise it evaluates that rule inline, serves the fresh value, and enqueues a repair. Inline evaluation and a cached `matched` fold must produce identical `FormatState` objects for identical inputs, which holds because both fold the same typed format columns of the same rule in the same order.
- **FR-F060-12:** `POST /api/v1/sheets/{sheet_id}/formatting/evaluate` with `{ row_ids?: [...], rule?: <unsaved rule body>, view_id?, limit (1–200, default 50), explain? }` returns the resolved state per row without persisting anything, and with `explain: true` also returns per rule `{ rule_id | "draft", matched, leaf_results, skipped_reason }`; it is the rule-editor preview, the `Why is this row highlighted?` popover source, and the support tool.
- **FR-F060-13:** Evaluation never widens visibility and never fails a read: a leaf referencing a column the actor cannot read is treated as not matched and its rule ID is listed in `hidden_inputs`; a cell whose F035 result carries `status = error` matches only `is_error` and evaluates false for every other operator; when the per-page evaluation budget of 150 ms is exceeded the page is returned with `formatting.degraded = true` and `reason = "budget"` while `POST /formatting/evaluate` returns `unavailable`.
- **FR-F060-14:** `PATCH /api/v1/formatting-rules/{id}` (name, condition, target, format, enabled, stop_if_true) requires `If-Match` on `version` and publishes `formatting-rule.updated.v1` with `change_kind` in `created|updated|reordered|enabled|disabled`; `DELETE /api/v1/formatting-rules/{id}` soft-deletes and publishes `formatting-rule.deleted.v1`. All mutations require `sheet-editor`, an `Idempotency-Key`, and write an `audit_events` row; reads require `sheet-viewer`; cross-tenant IDs return `not_found`.
- **FR-F060-15:** The web app adds a `Conditional formatting` panel to the sheet header with an ordered rule list (drag or `Alt+ArrowUp`/`Alt+ArrowDown` to reorder), a rule editor with condition builder, target picker, format picker, and live preview of 10 rows, a legend listing every enabled rule as swatch plus icon plus name, a per-cell `Why is this row highlighted?` popover listing the applied rules in order, and a signal mode switch `Colour and icon` or `Icon only` that persists per user and is reflected in the `signals` query parameter.

### Non-functional requirements

- **NFR-F060-01 Performance:** compiling a 100-rule set takes under 5 ms and is cached per `(sheet_id, rules_version)`; evaluating 100 rules over a 500-row page takes under 25 ms p95 and adds at most 10% to the F013 row-page p95, keeping it under 550 ms; full materialization of 100,000 rows against 100 rules completes in under 90 s; the grid paints a 500-row viewport with formatting with no frame over 16 ms.
- **NFR-F060-02 Security/privacy:** formatting is computed after F003 row and cell permission filtering and can only ever hide a signal, never reveal a value; formula leaves run in the pure F035 evaluator with a 200 ms per-page budget and no I/O; rule bodies are audited, evaluated cell values are never logged; cross-tenant rule, sheet, and view IDs return `not_found`.
- **NFR-F060-03 Accessibility:** colour is never the only signal — the server rejects colour-only formats and the client renders icon, badge, or text style for every coloured state; every token pair holds at least 4.5:1 contrast for text on fill and 3:1 for icons, asserted by a token test; formatted rows carry `aria-describedby` naming the applied rules; the legend and the popover are keyboard reachable; `Icon only` mode drops all fills; `prefers-reduced-motion` removes the newly-matched flash; axe reports zero serious or critical violations.
- **NFR-F060-04 Reliability/observability:** materialization is idempotent per `(rule_id, row_id, source_change_version)` and resumable after restart; metrics `formatting_eval_duration_ms{path}`, `formatting_rules_evaluated_total`, `formatting_states_stale_total`, and `formatting_degraded_total{reason}` are exported; every evaluation span carries `tenant_id`, `sheet_id`, `view_id`, `rules_version`, and `correlation_id`.

### Scope

Included: rule CRUD with scope and ordering, typed condition AST over F007 column types and F035 formula predicates, row and cell targets, the format token set with the non-colour-signal constraint, deterministic precedence resolution, evaluate-on-read attachment to the F006, F008, and F013 row reads, evaluate-on-write materialization worker with staleness repair, the preview and explain endpoint, the rules panel, legend, explanation popover, and signal mode.

Excluded: formula parsing and recalculation itself (F035), saved-view definition, filters, and sharing (F013), grid rendering, editing, and virtualization (F008), column types and cell validation (F007), automation actions that change data on a condition (F018), report and dashboard styling (F021, F022), export of formatting to CSV or XLSX (F010), theming and design tokens themselves (F001), published and embedded view styling (F059).

## 3. UX specification

- Entry points: sheet header overflow menu `Conditional formatting` opens the panel at `/w/{workspace_id}/sheets/{sheet_id}?panel=formatting`; a view header shows the same panel with the `This view only` scope preselected; a formatted cell's context menu shows `Why is this row highlighted?`; `Shift+F` opens the legend from the grid.
- Primary flow: an editor opens the panel, clicks `New rule`, picks `Due date` `before` `today` and `Status` `neq` `Complete`, chooses target `Row`, fill `format.red` with icon `alert-triangle`, sees the 10-row preview repaint, saves, and the grid shows late rows immediately; they add a second rule `Owner is me` with `format.blue` and badge `Mine`, drag it above the first, and the preview shows the blue rule losing the fill to the later red rule while keeping its badge.
- Loading: the rule list shows three skeleton rows and the grid renders unformatted until the first evaluated page arrives. Empty: the panel shows `No rules yet` with `New rule` and one example. Error: an inline banner with `correlation_id` and `Retry`; a degraded page shows `Formatting paused for this page` with `Retry`. Success: toast `Rule saved` and a one-time flash on newly matched rows. Stale/conflict: saving with a stale `version` shows `This rule changed` with `Reload` and the field diff. Denied: viewers see the panel read-only with the legend and no `New rule`.
- Rule editor: name field, condition builder rows with column, operator, and typed value control from F007, `Add condition` and `Add group`, a formula tab with the F035 editor and boolean-result check, target radio group `Whole row` or `Selected columns` with a column multi-select, format controls as labelled swatch buttons with icon and badge pickers, `Stop evaluating later rules` checkbox, and a preview table of 10 rows from `POST /formatting/evaluate`.
- Precedence list: rules render as an ordered list with a visible number, keyboard reorder via `Alt+ArrowUp`/`Alt+ArrowDown`, a live region announcing `Moved Late tasks to position 2 of 5`, a `Sheet` or `View` scope chip, and a disabled state with reduced opacity plus the text `Disabled`.
- Explanation popover: lists the applied rules in order with each rule's name, matched leaves, and which property it won, plus `hidden_inputs` rendered as `Uses a column you cannot read`.
- Responsive: the panel becomes a full-screen sheet below 768 px; the legend collapses to a summary button below 640 px.
- Keyboard and screen reader: every formatted row exposes `aria-describedby` pointing to a visually hidden `Formatted by Late tasks, Mine`; icons carry `aria-hidden` and their meaning comes from the description; the signal mode switch is a labelled two-option radio group.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062); Lucide icons `Palette`, `ListOrdered`, `Eye`, `EyeOff`, `AlertTriangle`, `CircleHelp`; all fills, text colours, and focus rings from `apps/web/src/design/tokens.css`.

- Design: `design/artboards/Formatting.dc.html` on the canvas indexed by `design/canvas.json`. The ticket is the contract and the artboard is the picture; when they disagree the ticket wins.

## 4. Technical specification

### Rust backend

- Data access (decision section 2.1): `crates/persistence/src/formatting/` holds `FormattingRuleRepository` (owns `formatting_rules`, `formatting_rule_conditions`, `formatting_rule_target_columns`, `formatting_rule_text_styles`) and `FormattingStateRepository` (owns `formatting_states`). `sheets.formatting_rules_version` belongs to the F006 `SheetRepository`; the rule use cases bump it through `SheetRepository::bump_formatting_rules_version`, so no two classes write the same table. Named queries: `list_rules_for_sheet`, `load_compiled_rule_set`, `find_rule_for_update`, `count_active_rules_for_sheet`, `next_position_in_scope`, `reposition_within_scope`, `rebalance_scope_positions`, `replace_condition_tree`, `replace_target_columns`, `replace_text_styles`, `list_rules_referencing_column`, `disable_rules_referencing_column`, `detach_purged_column`, `soft_delete_rules_for_view`, and on states `list_states_for_rows`, `upsert_state_batch`, `delete_states_for_rule`, `list_stale_rows`, `count_stale_states`. There is no generic query entry point. Every use case, the compiler, the evaluator, the `services/api/src/formatting` handlers, the read hook called from the F006, F008, and F013 grid handlers, and the worker jobs depend on these traits and contain no SQL; a rule create, update, reorder, or delete writes the rule row, its condition tree, its target columns, its text styles, the audit row, the outbox row, and the `sheets` version bump inside one `UnitOfWork`, and a materialization batch of 500 upserts runs in one `UnitOfWork` per batch.
- Domain entities in `crates/domain/src/formatting/`: `FormattingRule { id, tenant_id, sheet_id, view_id: Option<ViewId>, name, position: FracIndex, enabled, stop_if_true, materialized, condition: Condition, target: Target, format: FormatSpec, rules_version_at_write, version, created/updated actor+time, deleted_at }`, `Condition::{ And(Vec<Condition>), Or(Vec<Condition>), Leaf { column_id, op: FormatOp, value }, Formula { expression, ast_node_count } }`, `Target::{ Row, Cells(Vec<ColumnId>) }`, `FormatSpec { fill: ColorToken, text_color: ColorToken, text_style: TextStyleSet, icon: Option<FormatIcon>, badge_text: Option<String> }`, `FormatState { fill, text_color, text_style, icon, badge_text, winners: BTreeMap<Property, RuleId> }`, `RowFormatting { row: FormatState, cells: BTreeMap<ColumnId, FormatState>, applied_rule_ids: Vec<RuleId>, hidden_inputs: Vec<RuleId>, degraded: bool }`.
- Use cases: `create_rule`, `update_rule`, `delete_rule`, `reorder_rule`, `list_rules`, `compile_rule_set`, `evaluate_rows`, `evaluate_draft`, `explain_row`, `materialize_rule`, `repair_stale_states`.
- `compile.rs` takes the rows returned by `FormattingRuleRepository::load_compiled_rule_set` (rule rows joined to their condition, target-column and text-style children, ordered by scope then `position` then `parent_id, position`) and turns that rule set into a `CompiledRuleSet { rules_version, ordered: Vec<CompiledRule>, referenced_columns: HashSet<ColumnId>, formula_programs }` cached in a per-process `moka` cache keyed `(tenant_id, sheet_id, rules_version)` with a 5-minute idle expiry and invalidated by `formatting-rule.updated.v1` and `formatting-rule.deleted.v1`.
- `evaluate.rs` walks the compiled set once per row against the F006 cell map handed in by the caller — the grid handler passes the rows it already loaded through the F006 `RowRepository`, and the worker loads them the same way, so the evaluator itself never touches a connection — reading `cells[column_id].raw` only (never `display`, so locale never changes matching), delegating formula leaves to the F035 evaluator with an injected clock, and folding matches into `FormatState` with the FR-F060-07 property-override and cell-over-row rules.
- API endpoints (`services/api/src/formatting/`): `GET /api/v1/sheets/{sheet_id}/formatting-rules`, `POST /api/v1/formatting-rules`, `PATCH /api/v1/formatting-rules/{id}`, `DELETE /api/v1/formatting-rules/{id}`, `POST /api/v1/formatting-rules/{id}/reorder`, `POST /api/v1/sheets/{sheet_id}/formatting/evaluate`. DTOs `CreateRuleRequest`, `UpdateRuleRequest`, `ReorderRuleRequest { after_rule_id }`, `EvaluateRequest { row_ids?, rule?, view_id?, limit, explain }`, `RuleResponse`, `Page<RuleResponse>`, `EvaluateResponse { rows: Vec<RowFormattingResponse>, explain: Option<Vec<RuleExplain>> }`.
- Read-path integration: `FormattingEvaluator` is registered in the API application state and called by the F006 row list, the F008 changes feed, and the F013 view rows handler through the shared `RowReadContext` extension when `include=formatting` is present; the evaluator receives rows after permission filtering and returns `RowFormatting` per row.
- Worker (`services/worker/src/formatting/`): `materialize.rs` consumes the FR-F060-10 event list, resolves affected `(rule_id, row_id)` pairs, and upserts `formatting_states` in batches of 500 with `source_change_version` from the triggering event through `FormattingStateRepository::upsert_state_batch`; `repair.rs` drains the stale-repair queue with per-sheet concurrency 1 using `list_stale_rows`. Both jobs hold no SQL of their own and reach rules, rows, and states only through the repositories.
- Events: `formatting-rule.updated.v1` with `{ rule_id, sheet_id, view_id, change_kind, rules_version, changed_fields, actor_id, correlation_id }` and `formatting-rule.deleted.v1` with `{ rule_id, sheet_id, view_id, rules_version, actor_id, correlation_id }`, both through the F004 outbox.
- Authorization: `sheet-editor` for create, update, delete, reorder; `sheet-viewer` for list and evaluate; a view-scoped rule additionally requires read access to that view; missing sheet access maps to `not_found`.
- Validation: name 1–120 chars, 100 rules per sheet, 20 leaves, depth 4, 50 target columns, 200 formula AST nodes, badge text 12 chars, tokens from the fixed enum, `view_id` belonging to `sheet_id`.
- Error mapping: `FormattingError::RuleLimit → 400 invalid`, `::UnknownColumn → 400 invalid`, `::OperatorTypeMismatch → 400 invalid`, `::ColorOnlyFormat → 400 invalid`, `::ScopeMismatch → 400 invalid`, `::NonBooleanFormula → 400 invalid`, `::StaleVersion → 409 conflict`, `::NotFound → 404 not_found`, `::BudgetExceeded → 503 unavailable`, `AuthzError::Denied → 403 denied`.

### PostgreSQL/SQLx

- Migration `*_formatting_*.sql` creates `formatting_rules(id uuid pk, tenant_id uuid not null, sheet_id uuid not null references sheets(id) on delete restrict, view_id uuid null references views(id) on delete cascade, name text not null check (length(name) between 1 and 120), position text not null, enabled bool not null default true, stop_if_true bool not null default false, materialized bool not null default false, target_kind text not null check (target_kind in ('row','cells')), fill_token text not null default 'format.none' check (fill_token in ('format.red','format.amber','format.green','format.blue','format.violet','format.slate','format.none')), text_color_token text not null default 'format.none' check (text_color_token in ('format.red','format.amber','format.green','format.blue','format.violet','format.slate','format.none')), icon text null check (icon in ('alert-triangle','check-circle','clock','flag','circle-dot','octagon-x')), badge_text text null check (length(badge_text) between 1 and 12), last_evaluated_at timestamptz, version bigint not null default 1, created_by, created_at, updated_by, updated_at, deleted_at)` and `formatting_states(tenant_id uuid not null, sheet_id uuid not null references sheets(id) on delete cascade, rule_id uuid not null references formatting_rules(id) on delete cascade, row_id uuid not null references rows(id) on delete cascade, matched bool not null, source_change_version bigint not null, evaluated_at timestamptz not null, primary key (rule_id, row_id))`, and adds `sheets.formatting_rules_version bigint not null default 0` through an additive `alter table`.
- Normalized sets (decision section 2, no array or AST-in-`jsonb` columns): `formatting_rule_conditions(id uuid pk, tenant_id uuid not null, rule_id uuid not null references formatting_rules(id) on delete cascade, parent_id uuid null references formatting_rule_conditions(id) on delete cascade, position smallint not null, node_kind text not null check (node_kind in ('and','or','leaf','formula')), column_id uuid null references columns(id) on delete restrict, op text null check (op in ('eq','neq','contains','in','is_empty','is_not_empty','gt','lt','between','before','after','is_me','is_error')), operand jsonb null, formula_expression text null, formula_ast_node_count smallint null, unique nulls not distinct (rule_id, parent_id, position), check ((node_kind in ('and','or') and column_id is null and op is null and formula_expression is null) or (node_kind = 'leaf' and column_id is not null and op is not null) or (node_kind = 'formula' and formula_expression is not null and formula_ast_node_count is not null)))` replaces `condition jsonb`: one row per AST node, `parent_id` for the enclosing group, `position` for the ordered repeating group, exactly one root row per rule with `parent_id is null`. `formatting_rule_target_columns(rule_id uuid not null references formatting_rules(id) on delete cascade, tenant_id uuid not null, column_id uuid not null references columns(id) on delete restrict, position smallint not null, primary key (rule_id, column_id), unique (rule_id, position))` replaces `target.column_ids` and keeps the picker order. `formatting_rule_text_styles(rule_id uuid not null references formatting_rules(id) on delete cascade, tenant_id uuid not null, style text not null check (style in ('bold','italic','strikethrough')), primary key (rule_id, style))` replaces the `text_style` set inside `format jsonb`. `CreateRuleRequest`, `UpdateRuleRequest`, `RuleResponse`, and the evaluate DTOs keep the nested `condition` AST, the `target.column_ids` array, and the `format` object with its `text_style` array, so no externally visible shape changes; `FormattingRuleRepository` fans a saved rule out to rows (delete of removed rows, then `insert ... on conflict do update`) and reassembles the JSON on read, inside the rule's `UnitOfWork` transaction. Rule precedence and reorder semantics are unchanged: order still comes from scope rank then the fractional `position` on `formatting_rules`, never from a child table.
- `jsonb` audit: `formatting_rule_conditions.operand` stays `jsonb` — it is one typed F007 cell value (select option, date, person, currency, or a `between` pair) compared by the evaluator against the cell's own `raw` payload, never filtered, joined, sorted, or constrained on by the product; a check requires it non-null exactly for the operators that take an operand. `formatting_rules.condition`, `target`, and `format` are gone: the product parses, validates, orders, and evaluates all three and joins conditions and targets to `columns`, so they are tables and typed columns. `formatting_states.state` is gone: a matched rule's painted properties are its own typed format columns, so caching a second copy would let the cache disagree with the rule. `formatting_states` itself remains the only derived, rebuildable structure in the module — it serves `FormattingStateRepository::list_states_for_rows`, the batched read behind `include=formatting` for materialized rules on sheets over 20,000 rows, and it is rebuilt by the `formatting.materialize` worker from the FR-F060-10 events, by `formatting.repair` from `list_stale_rows`, and, for any row it is missing or stale for, by inline evaluation on the read request itself, so no read ever depends on it. No other `jsonb` column exists in this module.
- Invariants: `position` is a fractional index ordered under collation `C` and unique per `(sheet_id, coalesce(view_id, '00000000-0000-0000-0000-000000000000'))` among non-deleted rules; `count_active_rules_for_sheet` caps a sheet at 100 non-deleted rules under the rule row lock taken by the `UnitOfWork`; `name` non-empty by check; `target_kind = 'cells'` requires between 1 and 50 `formatting_rule_target_columns` rows and `target_kind = 'row'` requires none, asserted by `FormattingRuleRepository::replace_target_columns`; `formatting_rule_conditions` holds exactly one root per rule, at most 20 rows with `node_kind in ('leaf','formula')`, and at most 4 levels of nesting, with the depth and leaf counts enforced by the repository as it writes the tree; a colour-carrying rule needs at least one `formatting_rule_text_styles` row, a non-null `icon`, or a non-null `badge_text`; every child row carries the parent's `tenant_id`; `sheets.formatting_rules_version` increments once per rule mutation inside the write transaction and is the cache key.
- Indexes: `formatting_rules(tenant_id, sheet_id, position) where deleted_at is null`, `formatting_rules(view_id) where view_id is not null and deleted_at is null`, `formatting_rule_conditions(rule_id, parent_id, position)` for tree reassembly in evaluation order, `formatting_rule_conditions(column_id) where column_id is not null` and `formatting_rule_target_columns(column_id)` for the F007 column-deletion lookup — these replace the GIN index on the former `condition jsonb`, `formatting_rule_text_styles(rule_id)`, `formatting_states(sheet_id, row_id)`, `formatting_states(rule_id, source_change_version)`.
- Column deletion interaction: F007 deleting a column emits `column.deleted.v1`; the materialize worker calls `FormattingRuleRepository::disable_rules_referencing_column`, which joins `formatting_rule_conditions(column_id)` and `formatting_rule_target_columns(column_id)` instead of scanning JSON, disables every rule that references it, sets `field_errors.condition = "missing_column"` in the rule response, and leaves the rule editable so the owner can repair it. F007 soft-deletes columns, so the `on delete restrict` foreign keys never block that; the F027 purge calls `detach_purged_column`, which deletes the condition and target rows of those already-disabled rules before the column row goes.
- Audit events: `formatting-rule.create`, `formatting-rule.update`, `formatting-rule.delete`, `formatting-rule.reorder`, `formatting-rule.enable`, `formatting-rule.disable`, written by the base repository contract with field-level diffs of `condition`, `target`, and `format` computed from the JSON the repository reassembles before and after the write, so the audit trail keeps the shape reviewers already read.
- Retention/deletion: soft-deleted rules are purged by the F027 sweep after the tenant retention window and their condition, target-column, text-style, and `formatting_states` rows cascade; deleting a sheet cascades states through `rows`; rollback drops `formatting_states`, `formatting_rule_conditions`, `formatting_rule_target_columns`, `formatting_rule_text_styles`, then `formatting_rules`, children before parents, and removes the added `sheets` column.

### React/TypeScript

- Routes: none new; `apps/web/src/features/formatting/` mounts into the F006 `SheetPage` header slot and the F008 `VirtualGrid` row and cell renderers. Components `FormattingPanel`, `RuleList`, `RuleListItem`, `RuleEditor`, `ConditionBuilder`, `ConditionLeafRow`, `FormulaConditionTab`, `TargetPicker`, `FormatPicker`, `RulePreviewTable`, `FormattingLegend`, `WhyFormattedPopover`, `SignalModeSwitch`, `useRowFormatting`.
- Rendering: a row's `FormatState` is applied as CSS custom properties (`--fmt-fill`, `--fmt-text`, `--fmt-icon`) on the row element and per-cell overrides on the cell element, so a viewport repaint never re-lays-out the virtual grid; `Icon only` mode sets `--fmt-fill: transparent` at the grid root.
- State: TanStack Query keys `['formatting-rules', sheetId, viewId]`, `['formatting-evaluate', sheetId, draftHash]`; row formatting rides along the existing `['sheet-rows', ...]` and `['view-rows', ...]` payloads and is invalidated by the `rules_version` returned in `formatting-rule.updated.v1` over the F046 live channel.
- API client: generated `FormattingApi` with `listRules`, `createRule`, `updateRule`, `deleteRule`, `reorderRule`, `evaluate`.
- Telemetry: `formatting_rule_created`, `formatting_rule_reordered`, `formatting_rule_disabled`, `formatting_preview_run`, `formatting_explain_opened`, `formatting_signal_mode_changed` with `sheet_id`, `view_id`, and `rule_count`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F060-01 through FR-F060-15 in `testing/features/F060/requirements/cases.md`
- [ ] Failure/edge-case tests: colour-only format rejected, 101st rule rejected, cross-scope reorder rejected, non-boolean formula rejected, condition over a deleted column disables the rule, formula error cell matches only `is_error`, evaluation budget exceeded returns a degraded page
- [ ] Permission-negative and tenant-isolation tests: viewer cannot create or reorder, hidden column leaf is dropped into `hidden_inputs` without leaking the value, foreign-tenant rule and view IDs return `not_found`
- [ ] Rust unit tests: `crates/domain/src/formatting/` precedence folding, cell-over-row override, `stop_if_true`, compile cache invalidation by `rules_version`, fractional position rebalance
- [ ] API contract/integration tests: every route above with success and each error code, plus `include=formatting` on the F006, F008, and F013 row reads
- [ ] Database migration/constraint tests: unique position per scope, `formatting_rule_conditions` ordinal unique per `(rule_id, parent_id)` and node-kind check, condition and target-column foreign keys to `columns`, duplicate target column rejected, duplicate text style rejected, cascade from rule and row deletion, view cascade, rollback in child-before-parent order
- [ ] React component tests: `RuleEditor`, `ConditionBuilder`, `RuleList` keyboard reorder, `FormattingLegend`, `WhyFormattedPopover`, `SignalModeSwitch`
- [ ] Browser E2E tests: create two rules, reorder them, watch the grid repaint, open the explanation popover, switch to `Icon only`, edit a cell and see the state change
- [ ] Accessibility tests: axe on the panel, editor, and formatted grid; colour-only rejection; contrast of every token pair; `aria-describedby` naming applied rules; reduced-motion flash removal
- [ ] Performance/load tests: 100 rules over 500 rows under 25 ms, 100,000-row materialization under 90 s, viewport paint frames under 16 ms

### Fast fanout configuration

- Test harness path: `testing/features/F060/`
- Feature flag: `F060_FEATURE`
- Fixture/seed factory: `testing/fixtures/formatting.rs` builds tenant A and B, a sheet-editor and a sheet-viewer, a sheet `Delivery plan` with `Status` (select), `Due date` (date), `Owner` (person), `Budget` (currency), and `Variance` (formula) columns, 50 seeded rows with 6 known exceptions, two saved views, a 10-rule and a 100-rule rule set, and a 100,000-row generator
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, UTC, fixed fractional position seeds so rule order is stable across runs
- Mock/stub contracts: the real F035 evaluator with the injected fixed clock; the F003 authz engine with fixture bindings; outbox publisher recorded in memory; a token-contrast table loaded from `apps/web/src/design/tokens.css`
- Parallel isolation: one schema per test worker, tenant ID per test, per-worker cache instance so `rules_version` invalidation is not shared
- Targeted command: `cargo xtask test-feature F060`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F060/`

## 6. Acceptance criteria

```gherkin
Feature: Conditional formatting rules and visual states

Scenario: Later rule wins the fill and stop_if_true ends evaluation
  Given sheet-scoped rules "Mine" at position 1 with fill format.blue and badge "Mine"
  And "Late" at position 2 with fill format.red, icon alert-triangle, and stop_if_true true
  And a third rule "Blocked" at position 3 with fill format.amber
  When a row owned by the actor and past its due date is read with include=formatting
  Then the row state has fill format.red, icon alert-triangle, and badge "Mine"
  And applied_rule_ids is the ordered pair of the Mine and Late rule ids without the Blocked rule

Scenario: View-scoped rule stays inside its view
  Given a sheet-scoped rule and a rule scoped to view "At risk"
  When rows are read through view "At risk" and then through view "All work"
  Then the At risk read applies both rules and the All work read applies only the sheet-scoped rule

Scenario: Colour alone is rejected
  Given an editor creating a rule with fill format.red and no icon, badge, or text style
  When they POST /api/v1/formatting-rules
  Then the response is 400 invalid with field_errors.format needs_non_color_signal and no rule is written

Scenario: A formula rule is materialized on write and read back identically
  Given a materialized rule whose condition is the formula predicate Variance greater than 0
  When an editor patches a Budget cell and the recalculation publishes formula.recalculated.v1
  Then formatting_states for that row is upserted with the new source_change_version
  And the next row read returns the same state that inline evaluation of that row produces

Scenario: Viewer cannot change rules
  Given a sheet-viewer on the sheet
  When they POST a reorder for an existing rule
  Then the response is 403 denied and the rule position is unchanged
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F008 (cell edit events, changes feed, virtual grid render path), F035 (parser, boolean evaluation, formula result status and error codes); reads F006 rows and cells, F007 column types and operators, F013 views for view scope; decisions sections 2, 3, 6, 9; contracts row F060
- Blocks: none
- Conflicts with: none (disjoint owned paths; the F006, F008, and F013 read handlers gain the `include=formatting` parameter through the shared `RowReadContext` extension rather than edits inside those modules)
- External dependencies: none
- Risks and mitigations: per-row evaluation could slow every sheet read, mitigated by the compiled cached rule set, the 150 ms page budget with a degraded response, and the p95 gate in the performance lane; materialized states could drift from live data, mitigated by `source_change_version` staleness checks, inline fallback, the repair queue, and an equivalence test asserting inline and materialized states match over 5,000 rows; colour-coded meaning could be invisible to colour-blind and screen-reader users, mitigated by the server-side non-colour-signal constraint, the contrast token test, `aria-describedby`, and `Icon only` mode; rules referencing a deleted column could break reads, mitigated by disabling those rules on `column.deleted.v1` and surfacing a repair message.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F008 and F035 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F060/`
- [ ] Migration file name and owned paths claimed
- [ ] `RowReadContext` extension point available in the F006, F008, and F013 row read handlers
- [ ] Format colour tokens present in `apps/web/src/design/tokens.css` with recorded contrast ratios

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for every rule mutation and reorder
- [ ] Inline and materialized evaluation proven identical over the 5,000-row equivalence test
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F060_FEATURE`, run down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Sheet editors can add up to 100 ordered conditional-formatting rules per sheet, scoped to the whole sheet or to one saved view, targeting whole rows or selected columns, with conditions over typed columns and formula predicates; every coloured rule also carries an icon, badge, or text style, so formatting is readable without colour, and a `Why is this row highlighted?` popover explains which rule painted a cell.
- Migration adds `formatting_rules`, its `formatting_rule_conditions`, `formatting_rule_target_columns`, and `formatting_rule_text_styles` child tables, and `formatting_states`, plus a `formatting_rules_version` column on `sheets`; rollback drops them. Feature is off by default behind `F060_FEATURE`.
