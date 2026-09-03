---
id: S017
type: story
status: planned
parent_epic: E002
parent_feature: F009
depends_on: [F007]
owned_paths: [crates/domain/src/links/**, services/api/src/links/**, services/api/migrations/*_links_*.sql, testing/features/F009/**]
feature_flag: F009_FEATURE
branch: s017-parent-child-rows
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 9
- Capability contract: `docs/capability-contracts.md` row F009

# S017 — Parent/child rows

## Identity

- Parent feature: `F009` Hierarchy and links
- Owner: platform
- Branch: `s017-parent-child-rows`
- Decision references: `docs/architecture-decisions.md` sections 2–4, 9; `docs/capability-contracts.md` row F009

## Vertical slice

As a sheet editor, I want to indent and outdent rows into a parent/child tree, list a row's children, and have deletes and restores cascade through the subtree, so that work breakdown structure exists as stable, event-emitting records before roll-ups and links are layered on.

## Requirements

- **SR-S017-01:** `POST /api/v1/rows/{id}/indent` nests the row under the previous visible sibling, rewrites `path` and `depth` for the row and its descendants, requires `If-Match`, and emits `row.reparented.v1` (covers FR-F009-01).
- **SR-S017-02:** `POST /api/v1/rows/{id}/outdent` places the row after its parent at the parent's depth with descendants; outdenting a root returns `400 invalid` with `field_errors.row_id = "already_root"` (FR-F009-02).
- **SR-S017-03:** Indent returns `400 invalid` with `no_previous_sibling`, `depth_exceeded` (depth over 20 anywhere in the moved subtree), or `cycle` (target is self or a descendant) (FR-F009-03).
- **SR-S017-04:** `GET /api/v1/rows/{id}/children` returns direct children by `child_position` with cursor paging, and `depth=all` returns the subtree in `path` order with `depth` and `has_children`, excluding soft-deleted rows (FR-F009-04).
- **SR-S017-05:** Deleting a parent through the F006 row service cascades to descendants in one transaction; restore cascades back; restoring a child under a deleted parent returns `409 conflict` (FR-F009-05).
- **SR-S017-06:** The `cell_links` and `rollup_rules` tables are created in the same migration as `row_hierarchy` with all constraints from ticket section 4 so S018 needs no schema change (FR-F009-06, FR-F009-09).
- **SR-S017-07:** A viewer receives `403 denied` on indent and outdent; a foreign-tenant row ID returns `404 not_found`; every mutation writes an audit event and an outbox event (FR-F009-14, FR-F009-16).
- **SR-S017-08:** Subtree list of 10,000 descendants meets NFR-F009-01 using the `path` index.

## Surfaces

- Infrastructure/container: none beyond F004 baseline
- Rust service/API: `crates/domain/src/links/{mod.rs, hierarchy.rs, hierarchy_service.rs, hierarchy_reader.rs, errors.rs, schema.rs}`; `services/api/src/links/{mod.rs, routes.rs, handlers_hierarchy.rs, dto.rs}`
- Data/migration: `services/api/migrations/<ts>_links_create_tables.sql` creating `row_hierarchy`, `cell_links`, `rollup_rules` with the trigger, partial unique index, and indexes from ticket section 4
- React/UI: none in this story (S018 and T036 cover UI)
- Mocks/fixtures: `testing/fixtures/links.rs` tenant A editor/viewer, sheet `Plan` with a 3-level 60-row tree, tenant B sheet `Foreign`; in-memory outbox recorder

## TDD harness

- Test path: `testing/features/F009/api/`, `testing/features/F009/database/`, and `testing/features/F009/performance/`
- Feature flag: `F009_FEATURE`
- Targeted command: `cargo xtask test-feature F009`
- Full command: `cargo xtask test-all`
- First failing tests: `indent_nests_under_previous_sibling`, `indent_moves_descendants_and_rewrites_paths`, `indent_rejects_depth_over_20`, `outdent_root_is_invalid`, `children_depth_all_returns_path_order`, `delete_parent_cascades_and_restore_reverses`, `hierarchy_cross_tenant_not_found`

## Exit criteria

- [ ] Requirement tests SR-S017-01 through SR-S017-08 written first and failing
- [ ] Tasks T033 and T034 complete and wired through `services/api` router
- [ ] Unit, API, database, permission, and performance tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/links/routes.rs` mounted in `services/api/src/router.rs`
- [ ] Handoff evidence recorded in the F009 ticket
