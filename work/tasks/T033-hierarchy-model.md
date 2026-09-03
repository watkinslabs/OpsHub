---
id: T033
type: task
status: planned
parent_epic: E002
parent_feature: F009
parent_story: S017
depends_on: [S017]
owned_paths: [services/api/migrations/*_links_*.sql, crates/domain/src/links/**, testing/features/F009/database/**]
feature_flag: F009_FEATURE
branch: t033-hierarchy-model
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 9
- Capability contract: `docs/capability-contracts.md` row F009

# T033 — Hierarchy model

## Identity

- Parent story: `S017` Parent/child rows
- Owner: platform
- Branch: `t033-hierarchy-model`
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 9; `docs/capability-contracts.md` row F009

## Objective

Create the `row_hierarchy`, `cell_links`, and `rollup_rules` tables with constraints, trigger, indexes, and rollback, and implement the pure hierarchy model (path rewrite, depth check, cycle check, subtree ordering) that the services build on.

## Specification

- Owned paths: `services/api/migrations/<ts>_links_create_tables.sql`, `services/api/migrations/<ts>_links_create_tables.down.sql`, `crates/domain/src/links/{mod.rs, schema.rs, hierarchy.rs, errors.rs}`
- Contract/input: DDL per F009 ticket section 4 PostgreSQL: `row_hierarchy` keyed by `row_id` with `depth` check 0–20, unique `(sheet_id, path)`, trigger `row_hierarchy_same_sheet` rejecting a parent from another sheet; `cell_links` with enum checks and partial unique index on `(source_row_id, source_column_id) where deleted_at is null`; `rollup_rules` with function check and unique `column_id`; indexes from ticket section 4. Model API: `Hierarchy::indent_target(row, siblings) -> Result<ParentRef, HierarchyError>`, `Hierarchy::outdent_target(row) -> Result<PlacementAfterParent, HierarchyError>`, `rewrite_subtree(rows, new_parent_path) -> Vec<PathUpdate>`, `check_depth(subtree, new_root_depth) -> Result<(), HierarchyError::DepthExceeded>`, `is_descendant(candidate, of) -> bool` using `path` prefix.
- Output/behavior: `sqlx migrate run` applies on an empty database and on one with F006 and F007 tables; `sqlx migrate revert` drops the three tables and the trigger; `cargo xtask check-migrations` passes; the model is pure (no database access) and returns `NoPreviousSibling`, `AlreadyRoot`, `DepthExceeded`, and `Cycle` for the cases in FR-F009-03.
- Dependencies: F006 `rows` and F007 `columns` tables for foreign keys.
- Feature flag: `F009_FEATURE` (migration runs regardless; routes are gated)
- Large-table note: `row_hierarchy` has one row per sheet row (up to 100,000 per sheet); `path` uses `text_pattern_ops` so subtree scans are index range scans.

## TDD

- Failing test first: `testing/features/F009/database/migration_tests.rs::links_tables_exist_with_constraints`, `::depth_over_20_rejected_by_check`, `::parent_from_other_sheet_rejected_by_trigger`, `::second_active_link_per_cell_rejected`, `::duplicate_rollup_rule_per_column_rejected`, `::subtree_scan_uses_path_index`, `::rollback_drops_tables`; `testing/features/F009/database/hierarchy_model_tests.rs::rewrite_subtree_paths`, `::is_descendant_by_path_prefix`
- Targeted command: `cargo xtask test-feature F009`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: schema-per-worker database from `testing/harness/db.rs`; in-memory row list builders for model tests

## Exit criteria

- [ ] Tests written before the migration and model and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S017
- [ ] `finished_at` recorded
