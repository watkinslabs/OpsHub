---
id: T237
type: task
status: planned
parent_epic: E008
parent_feature: F060
parent_story: S119
depends_on: [S119]
owned_paths: [crates/domain/src/formatting/**, services/api/src/formatting/**, services/api/migrations/*_formatting_*.sql, testing/features/F060/api/**, testing/features/F060/database/**]
feature_flag: F060_FEATURE
branch: t237-rule-engine
started_at: null
finished_at: null
---

# T237 — Rule engine

## Identity

- Parent story: `S119` Formatting rules
- Owner: platform
- Branch: `t237-rule-engine`
- Decision references: `docs/architecture-decisions.md` sections 2, 3; `docs/capability-contracts.md` row F060

## Objective

Create the `formatting` schema and implement the rule aggregate: condition and target validation against F007 column types and the F035 parser, the format token set with the non-colour-signal constraint, fractional ordering per scope, the compiled rule-set cache keyed by `sheets.formatting_rules_version`, and the five rule routes with their events and audit records.

## Specification

- Owned paths: `services/api/migrations/<ts>_formatting_create_tables.sql` and `.down.sql`, `crates/domain/src/formatting/{mod.rs, rule.rs, condition.rs, target.rs, format.rs, compile.rs, errors.rs, service.rs}`, `services/api/src/formatting/{mod.rs, routes.rs, handlers_rules.rs, dto.rs}`
- Contract/input: `CreateRuleRequest { sheet_id, view_id?, name, condition, target, format, stop_if_true?, enabled? }`, `UpdateRuleRequest` (same fields, all optional, `If-Match` on `version`), `ReorderRuleRequest { after_rule_id }`, list query `{ view_id?, enabled?, cursor?, limit? }`; `condition` is `and`/`or`/`{ column_id, op, value }`/`{ formula }`; `target` is `{ kind: "row" }` or `{ kind: "cells", column_ids }`; `format` is `{ fill, text_color, text_style, icon, badge_text }`.
- Output/behavior: routes `GET /api/v1/sheets/{sheet_id}/formatting-rules`, `POST /api/v1/formatting-rules`, `PATCH /api/v1/formatting-rules/{id}`, `DELETE /api/v1/formatting-rules/{id}`, `POST /api/v1/formatting-rules/{id}/reorder`. Limits enforced: 100 rules per sheet, 20 leaves, depth 4, 50 target columns, 200 formula AST nodes, name 120 chars, badge 12 chars. `format` with `fill` or `text_color` and no `text_style`, `icon`, or `badge_text` is rejected as `needs_non_color_signal`. Ordering is a fractional index unique per `(sheet_id, coalesce(view_id, zero uuid))`, rebalanced when any key exceeds 64 chars; reorder is scope-bound. `materialized` is computed at write time from the condition (formula leaf or `formula` column reference) and the sheet row count over 20,000. Every mutation increments `sheets.formatting_rules_version` in the same transaction, publishes `formatting-rule.updated.v1` with `change_kind` or `formatting-rule.deleted.v1` through the outbox, and writes an `audit_events` row. `compile.rs` produces `CompiledRuleSet` cached per `(tenant_id, sheet_id, rules_version)` with 5-minute idle expiry. Errors map `RuleLimit`, `UnknownColumn`, `OperatorTypeMismatch`, `ColorOnlyFormat`, `ScopeMismatch`, `NonBooleanFormula` to `400 invalid`, `StaleVersion` to `409 conflict`, `NotFound` to `404 not_found`, denial to `403 denied`. DDL for `formatting_rules`, `formatting_states`, the `sheets.formatting_rules_version` column, and the five indexes from ticket section 4.
- Dependencies: F007 column types and operator table; F035 parser for the formula leaf; F013 `views` for the `view_id` foreign key and cascade; F003 `Permission::SheetEditor` and `Permission::SheetViewer`; F004 outbox and idempotency store.
- Feature flag: `F060_FEATURE` gates the routes; the migration runs regardless.

## TDD

- Failing test first: `testing/features/F060/api/rule_tests.rs::create_rule_returns_position_and_version`, `::rule_limit_rejects_hundred_first_rule`, `::condition_rejects_operator_type_mismatch`, `::formula_leaf_must_be_boolean`, `::condition_rejects_twenty_first_leaf`, `::format_without_non_color_signal_rejected`, `::unknown_color_token_rejected`, `::reorder_across_scope_rejected`, `::stale_version_patch_conflicts`, `::viewer_cannot_create_or_reorder_rule`, `::foreign_tenant_rule_not_found`, `::rule_mutation_bumps_formatting_rules_version`, `::rule_mutation_publishes_updated_event_with_change_kind`; `testing/features/F060/api/compile_tests.rs::compiled_set_cached_until_rules_version_changes`, `::position_rebalances_past_sixty_four_chars`; `testing/features/F060/database/migration_tests.rs::formatting_tables_exist_with_constraints`, `::position_unique_per_scope`, `::states_cascade_on_rule_delete`, `::rollback_drops_formatting_objects`
- Targeted command: `cargo xtask test-feature F060`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/formatting.rs` `Delivery plan` sheet with `Status`, `Due date`, `Owner`, `Budget`, and `Variance` columns, two saved views, the 100-rule set, a sheet-editor and a sheet-viewer, tenant B; in-memory outbox recorder; fixed clock `2026-09-03T00:00:00Z`

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; routes registered behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S119
- [ ] `finished_at` recorded
