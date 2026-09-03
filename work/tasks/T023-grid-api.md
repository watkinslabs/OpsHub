---
id: T023
type: task
status: planned
parent_epic: E002
parent_feature: F006
parent_story: S012
depends_on: [T022]
owned_paths: [crates/domain/src/sheets/**, services/api/src/sheets/**, testing/features/F006/api/**, testing/features/F006/performance/**]
feature_flag: F006_FEATURE
branch: t023-grid-api
started_at: null
finished_at: null
---

# T023 — Grid API

## Identity

- Parent story: `S012` Create/update row
- Owner: platform
- Branch: `t023-grid-api`
- Decision references: `docs/architecture-decisions.md` sections 2–3; `docs/capability-contracts.md` row F006

## Objective

Implement row and group services and the seven row routes, including fractional positioning, moves, soft delete/restore, and the paged row list that the grid and board consume.

## Specification

- Owned paths: `crates/domain/src/sheets/{row.rs, position.rs, service_rows.rs, service_groups.rs}`, `services/api/src/sheets/{handlers_row.rs, handlers_group.rs}`
- Contract/input: `CreateRowRequest { group_id?, after_row_id?, cells: Map<ColumnId, Value> }`, `UpdateRowRequest { cells }`, `MoveRowRequest { group_id?, after_row_id? }`, list query `{ cursor?, limit? ≤ 500, group_id? }`.
- Output/behavior: routes `GET/POST /api/v1/sheets/{id}/rows`, `GET/PATCH/DELETE /api/v1/rows/{id}`, `POST /api/v1/rows/{id}/restore`, `POST /api/v1/rows/{id}/move` return `RowResponse { id, sheet_id, group_id, position, version, cells: { column_id: { raw, display, validation } }, created_at, updated_at, deleted_at }`; `position.rs` implements fractional index generation and rebalancing when any key in a group exceeds 64 chars; group delete moves rows to the default group; events `row.created.v1`, `row.updated.v1`, `row.deleted.v1`, `row.restored.v1`, `row.moved.v1`.
- Dependencies: T022 sheet service and router; F007 will later validate typed cells, so this task validates only that keys are column IDs of the sheet.
- Feature flag: `F006_FEATURE`

## TDD

- Failing test first: `testing/features/F006/api/row_tests.rs::row_create_assigns_position`, `::row_list_pages_by_position`, `::row_move_between_groups_emits_event`, `::row_move_rebalances_long_keys`, `::group_delete_moves_rows_to_default`, `::row_cross_tenant_not_found`; `testing/features/F006/performance/row_list_bench.rs::row_list_100k_p95`
- Targeted command: `cargo xtask test-feature F006`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: seeded 3-group/50-row sheet; 100,000-row generator with fixed seed

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] p95 targets from NFR-F006-01 met in the performance lane
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S012
- [ ] `finished_at` recorded
