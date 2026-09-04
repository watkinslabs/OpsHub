---
id: T034
type: task
status: planned
parent_epic: E002
parent_feature: F009
parent_story: S017
depends_on: [T033]
owned_paths: [crates/domain/src/links/**, services/api/src/links/**, testing/features/F009/api/**, testing/features/F009/requirements/**, testing/features/F009/performance/**]
feature_flag: F009_FEATURE
branch: t034-link-model
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 9
- Capability contract: `docs/capability-contracts.md` row F009

# T034 — Link model

## Identity

- Parent story: `S017` Parent/child rows
- Owner: platform
- Branch: `t034-link-model`
- Decision references: `docs/architecture-decisions.md` sections 2–4, 9; `docs/capability-contracts.md` row F009

## Objective

Implement the hierarchy service and the three hierarchy routes, the cascade hooks into the F006 row service, the `HierarchyReader` used by F035, and the `CellLink` domain model with its type-compatibility rules so S018 can add link routes without touching the model.

## Specification

- Owned paths: `crates/domain/src/links/{hierarchy_service.rs, hierarchy_reader.rs, cascade.rs, link.rs}`, `services/api/src/links/{mod.rs, routes.rs, handlers_hierarchy.rs, dto.rs}`
- Contract/input: `indent_row(ctx, row_id, if_match)`, `outdent_row(ctx, row_id, if_match)`, `list_children(ctx, row_id, ChildrenQuery { cursor, limit ≤ 500, depth: Direct|All })`; `HierarchyReader::{children(row_id), parent(row_id), ancestors(row_id), descendants(row_id)}` trait for F035; `cascade_delete_subtree(tx, row_id)` and `cascade_restore_subtree(tx, row_id)` called by the F006 row service; `CellLink::validate(source_column: &Column, target_column: &Column) -> Result<(), LinkError>` checking `link` source type and `accepted_types`, and `LinkType`/`SyncDirection` enums.
- Output/behavior: routes `POST /api/v1/rows/{id}/indent`, `POST /api/v1/rows/{id}/outdent`, `GET /api/v1/rows/{id}/children` return `ReparentResponse { row_id, parent_row_id, depth, path, version }` and `Page<ChildRowResponse { id, depth, has_children, position, version, cells }>`; path rewrites run in 5,000-row chunks inside one `UnitOfWork` through `RowHierarchyRepository`, so no handler or service statement touches the table directly; errors map per ticket section 4; events `row.reparented.v1` written to `outbox_events` with the mutation; audit rows `row.indent` and `row.outdent`; restore of a child under a deleted parent returns `409 conflict` with `field_errors.parent_row_id = "deleted"`.
- Dependencies: T033 schema, model, and `crates/persistence/src/links/` repositories; F003 `authz::require(actor, Permission::SheetEdit, sheet)`; F004 `OutboxRepository` writer; F006 row service hook points for cascade.
- Feature flag: `F009_FEATURE` gates router mounting; cascade hooks are no-ops when off.

## TDD

- Failing test first: `testing/features/F009/api/hierarchy_tests.rs::indent_nests_under_previous_sibling`, `::indent_moves_descendants_and_rewrites_paths`, `::indent_rejects_depth_over_20`, `::indent_rejects_first_row_in_group`, `::outdent_root_is_invalid`, `::children_depth_all_returns_path_order`, `::delete_parent_cascades_and_restore_reverses`, `::hierarchy_viewer_denied`, `::hierarchy_cross_tenant_not_found`; `testing/features/F009/performance/hierarchy_bench.rs::children_10k_descendants_p95`, `::indent_subtree_p95`
- Targeted command: `cargo xtask test-feature F009`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/links.rs` 3-level `Plan` tree; 10,000-descendant generator with fixed seed; in-memory outbox recorder

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Router mounted in `services/api/src/router.rs` behind the flag; OpenAPI regenerated without drift
- [ ] p95 targets from NFR-F009-01 for children and indent met
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S017
- [ ] `finished_at` recorded
