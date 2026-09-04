---
id: T035
type: task
status: planned
parent_epic: E002
parent_feature: F009
parent_story: S018
depends_on: [T034]
owned_paths: [crates/domain/src/links/**, services/api/src/links/**, testing/features/F009/api/**, testing/features/F009/performance/**]
feature_flag: F009_FEATURE
branch: t035-rollup-service
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 7, 9
- Capability contract: `docs/capability-contracts.md` row F009

# T035 — Rollup service

## Identity

- Parent story: `S018` Linked records
- Owner: platform
- Branch: `t035-rollup-service`
- Decision references: `docs/architecture-decisions.md` sections 2–4, 7, 9; `docs/capability-contracts.md` row F009

## Objective

Implement the roll-up rule route and recompute consumer, and the link service with its five routes, pull/push sync, and broken-link detection, all publishing the contract events.

## Specification

- Owned paths: `crates/domain/src/links/{rollup.rs, rollup_service.rs, link_service.rs, sync.rs, consumer.rs, results_writer.rs}`, `services/api/src/links/{handlers_links.rs, handlers_rollup.rs}`
- Contract/input: `SetRollupRequest { function: Option<RollupFunction>, source_column_id, weight_column_id?, status_priority?, filter? }` with `If-Match` column version, persisted as the `rollup_rules` row plus its `rollup_rule_status_priorities` rows (one per option, ordered by `position`) and at most one `rollup_rule_filters` row, replaced atomically with the rule; `CreateLinkRequest { source_row_id, source_column_id, target_sheet_id, target_row_id, target_column_id, link_type, sync_direction }`; `UpdateLinkRequest { target_row_id?, target_column_id?, link_type?, sync_direction? }`; list query `{ cursor?, limit?, source_row_id?, source_column_id?, target_sheet_id?, target_row_id?, status? }`; consumer subscriptions `row.updated.v1`, `cell.updated.v1`, `cells.bulk-updated.v1`, `rows.bulk-updated.v1`, `row.reparented.v1`, `row.deleted.v1`, `row.restored.v1`, `sheet.deleted.v1`, `sheet.restored.v1`, `column.deleted.v1`, `column.updated.v1`.
- Output/behavior: `PUT /api/v1/columns/{id}/rollup` validates the function/type matrix and emits `rollup.recomputed.v1` after the first full recompute; `recompute_rollups` walks ancestors of changed rows bottom-up, computes `sum|min|max|avg|count|any|all|first|last|weighted_percent` (status priority for `any|all`, weight column for `weighted_percent`), writes parent cells through the F008 cell writer over the F006 `CellRepository` and their `cell_validation_states` row with state `valid`, sets `pending` before compute, and coalesces events per `(sheet_id, column_id)` with a 250 ms debounce; direct edits to rolled-up cells are rejected with `field_errors.value = "rolled_up"`; routes `GET/POST /api/v1/links`, `PATCH/DELETE /api/v1/links/{id}` enforce source `sheet-editor`, target `sheet-viewer`, `accepted_types`, tenant isolation (`not_found`), redact unreadable targets in list, copy the target value on create, emit `link.created.v1`, `link.updated.v1`, `link.deleted.v1`; `sync.rs` handles pull (target `cell.updated.v1` to source display) and push (source edit to target through the F008 service, `403 denied` without target edit rights); broken-link detection sets `cell_links.status = broken` and the cell's `cell_validation_states` row to state `invalid` with code `broken_link`, and reverses on restore. All statements live in `crates/persistence/src/links/` behind `RollupRuleRepository` and `CellLinkRepository`; `results_writer.rs`, `consumer.rs`, and the handlers hold none (decision 2.1). Consumers are idempotent per `(aggregate_id, version)`.
- Dependencies: T034 hierarchy service and router; F007 column types, `column_options`, and `CellValidationStateRepository`; F008 cell write service over the F006 `CellRepository`; F004 outbox consumer registration.
- Feature flag: `F009_FEATURE` gates routes and consumer registration.

## TDD

- Failing test first: `testing/features/F009/api/rollup_tests.rs::rollup_sum_recomputes_ancestors_only`, `::rollup_any_uses_status_priority`, `::rollup_priority_rows_replaced_atomically`, `::rollup_filter_row_limits_source_rows`, `::rollup_weighted_percent_uses_weight_column`, `::rollup_parent_cell_rejects_direct_edit`, `::rollup_incompatible_function_invalid`, `::rollup_event_replay_is_idempotent`; `testing/features/F009/api/link_tests.rs::link_create_requires_target_read_access`, `::link_create_rejects_incompatible_type`, `::link_list_redacts_unreadable_targets`, `::link_target_delete_marks_broken`, `::link_pull_sync_copies_value`, `::link_push_sync_denied_without_target_edit`, `::link_cross_tenant_not_found`; `testing/features/F009/performance/rollup_bench.rs::rollup_recompute_5000_rows_under_5s`
- Targeted command: `cargo xtask test-feature F009`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `Plan` tree with `Cost`, `Status`, `Effort` columns; `Vendors` sheet; tenant B `Foreign`; in-memory outbox recorder and consumer harness; 5,000-row tree generator with fixed seed

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Consumer registered in `services/api/src/outbox_consumers.rs` behind the flag; OpenAPI regenerated without drift
- [ ] Roll-up recompute target from NFR-F009-01 met
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S018
- [ ] `finished_at` recorded
