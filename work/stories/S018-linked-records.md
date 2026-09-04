---
id: S018
type: story
status: planned
parent_epic: E002
parent_feature: F009
depends_on: [S017]
owned_paths: [crates/domain/src/links/**, services/api/src/links/**, apps/web/src/features/links/**, testing/features/F009/**]
feature_flag: F009_FEATURE
branch: s018-linked-records
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 6, 9
- Capability contract: `docs/capability-contracts.md` row F009

# S018 — Linked records

## Identity

- Parent feature: `F009` Hierarchy and links
- Owner: platform
- Branch: `s018-linked-records`
- Decision references: `docs/architecture-decisions.md` sections 2–4, 6, 9; `docs/capability-contracts.md` row F009

## Vertical slice

As a sheet editor, I want parent cells to roll up their children with a rule I choose and link cells to rows in other sheets by stable ID, with broken targets flagged and everything visible in the grid, so that summaries and references stay current without copying values.

## Requirements

- **SR-S018-01:** `PUT /api/v1/columns/{id}/rollup` stores or clears a `rollup_rules` row after checking the function/type matrix, `status_priority` for `any|all` on select, and `weight_column_id` for `weighted_percent` (covers FR-F009-06).
- **SR-S018-02:** The outbox consumer recomputes only ancestors of changed rows for affected columns on row, cell, bulk, reparent, delete, and restore events, writes parent cells with `validation.state = valid`, keeps `pending` during compute, rejects direct edits with `rolled_up`, and emits `rollup.recomputed.v1` per column (FR-F009-07, FR-F009-08).
- **SR-S018-03:** `POST /api/v1/links` checks source `link` column, target `sheet-viewer` access, target row existence, and `accepted_types`, copies the target value into the source display, and emits `link.created.v1`; `PATCH` and `DELETE` re-check and emit `link.updated.v1` or `link.deleted.v1` (FR-F009-09, FR-F009-11).
- **SR-S018-04:** `GET /api/v1/links` filters and pages, returning `target_sheet_name` and `target_primary_value` only for readable targets and `target_redacted: true` otherwise (FR-F009-10).
- **SR-S018-05:** Target row or sheet deletion, column deletion, or incompatible type change sets `status = broken` and the source cell `validation.state = invalid` with code `broken_link`; restore reverses it (FR-F009-12).
- **SR-S018-06:** `pull`/`both` copies target `cell.updated.v1` values into the source display; `push`/`both` writes the target through the F008 service and returns `403 denied` without target edit rights (FR-F009-13).
- **SR-S018-07:** `HierarchyControls`, `ChildRowsOutline`, `LinkedCellRenderer`, `LinkPicker`, and `RollupRuleEditor` render loading, empty, error, denied, pending, broken, and conflict states with treegrid semantics and keyboard indent (FR-F009-15, NFR-F009-03).
- **SR-S018-08:** Cross-tenant and unreadable targets return `404 not_found`; viewers get `403 denied` on link and rollup mutations; a 5,000-row roll-up recompute completes under 5 s (FR-F009-14, NFR-F009-01).

## Surfaces

- Infrastructure/container: none
- Rust service/API: `crates/domain/src/links/{link.rs, link_service.rs, rollup.rs, rollup_service.rs, consumer.rs, sync.rs}`; `services/api/src/links/{handlers_links.rs, handlers_rollup.rs}`; links go through `CellLinkRepository` and rules through `RollupRuleRepository` (which owns `rollup_rules`, `rollup_rule_status_priorities`, and `rollup_rule_filters`) in `crates/persistence/src/links/`, recomputed cells through the F006 `CellRepository` and their validation rows through the F007 `CellValidationStateRepository`; the services, consumers, and tests hold no SQL (decision 2.1)
- Data/migration: none new; uses `cell_links`, `rollup_rules`, `rollup_rule_status_priorities`, and `rollup_rule_filters` from S017 through those repositories
- React/UI: `apps/web/src/features/links/{HierarchyControls.tsx, IndentGuide.tsx, ChildRowsOutline.tsx, LinkPicker.tsx, LinkedCellRenderer.tsx, BrokenLinkBadge.tsx, RollupRuleEditor.tsx, RollupCellRenderer.tsx, api.ts, hooks.ts}`
- Mocks/fixtures: `Plan` tree with `Cost` and `Status` columns, `Vendors` sheet with 20 rows, tenant B `Foreign`; 5,000-row tree generator for performance lane; MSW handlers for component tests

## TDD harness

- Test path: `testing/features/F009/{api,frontend,e2e,accessibility,performance}/`
- Feature flag: `F009_FEATURE`
- Targeted command: `cargo xtask test-feature F009`
- Full command: `cargo xtask test-all`
- First failing tests: `rollup_sum_recomputes_ancestors_only`, `rollup_parent_cell_rejects_direct_edit`, `link_create_requires_target_read_access`, `link_target_delete_marks_broken`, `link_push_sync_denied_without_target_edit`, `linked_cell_shows_broken_state`, `rollup_recompute_5000_rows_under_5s`

## Exit criteria

- [ ] Requirement tests SR-S018-01 through SR-S018-08 written first and failing
- [ ] Tasks T035 and T036 complete; UI wired to real API through generated client
- [ ] Unit, API, React, E2E, accessibility, permission, and performance tests pass
- [ ] Production call path named: `crates/domain/src/links/consumer.rs` registered in `services/api/src/outbox_consumers.rs` and `apps/web/src/features/links/HierarchyControls.tsx` mounted in the F008 `VirtualGrid` row toolbar
- [ ] Handoff evidence recorded in the F009 ticket
