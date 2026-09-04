---
id: T089
type: task
status: planned
parent_epic: E005
parent_feature: F023
parent_story: S045
depends_on: [S045]
owned_paths: [services/api/migrations/*_dashboards_*.sql, crates/domain/src/dashboards/**, crates/persistence/src/dashboards/**, testing/features/F023/database/**, testing/features/F023/api/**]
feature_flag: F023_FEATURE
branch: t089-dashboard-schema
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3
- Capability contract: `docs/capability-contracts.md` row F023

# T089 — Dashboard schema

## Identity

- Parent story: `S045` Widget layout
- Owner: platform
- Branch: `t089-dashboard-schema`
- Decision references: `docs/architecture-decisions.md` sections 2, 3; `docs/capability-contracts.md` row F023

## Objective

Create the `dashboards`, `dashboard_widgets`, `dashboard_widget_sources`, `dashboard_widget_columns`, `widget_cache`, and `widget_cache_sources` tables, the `DashboardRepository` and `DashboardWidgetRepository` shells that own them, and the typed `Dashboard`, `DashboardWidget`, and `GridLayout` model with the grid validator so widget placement is verified before any resolver runs.

## Specification

- Owned paths: `services/api/migrations/<ts>_dashboards_create_tables.sql`, `services/api/migrations/<ts>_dashboards_create_tables.down.sql`, `crates/domain/src/dashboards/{mod.rs, dashboard.rs, widget.rs, grid.rs, errors.rs, schema.rs}`, `crates/persistence/src/dashboards/{mod.rs, dashboard_repository.rs, dashboard_widget_repository.rs}`
- Contract/input: `GridLayout { columns: 12, row_height_px: 80 }` persisted as `grid_columns`/`row_height_px`, `GridPosition { x, y, w, h }`, `WidgetKind` with the twelve variants, `DashboardRefreshPolicy { mode: manual|interval|on_open, interval_minutes }` persisted as `refresh_mode`/`refresh_interval_minutes`, `SourceRef { source_kind, source_id, role }` persisted as `dashboard_widget_sources`, ordered `column_refs[]` persisted as `dashboard_widget_columns`, `ReplaceWidgetsRequest.widgets[]` with ≤ 40 entries.
- Output/behavior: DDL per ticket section 4 with position check constraints, kind check, `grid_columns`/`row_height_px`/`refresh_mode`/`refresh_interval_minutes` checks and the interval-requires-minutes check, unique name partial index, `unique (widget_id, source_kind, source_id, role)`, `dashboard_widget_columns` primary key `(widget_id, column_ref)` with `unique (widget_id, position)`, `widget_cache(widget_id, scope_key)` primary key, every `on delete cascade` including `widget_cache_sources` to `widget_cache`, and the five indexes; `DashboardRepository` and `DashboardWidgetRepository` implement the shared `Repository` contract over these tables so no SQL leaves `crates/persistence`; `grid::validate(widgets) -> Result<(), Vec<FieldError>>` rejects `w`/`h` outside 1..12, `x + w > 12`, negative coordinates, pairwise overlaps (O(n²) over ≤ 40), and more than 40 widgets, each error naming `widgets[i].position`; `grid::diff(existing, incoming) -> WidgetDiff { added, removed, moved, reconfigured }` for audit and cache retention; `sqlx migrate revert` drops the six tables.
- Dependencies: F005 `folders` and F021 `reports` for foreign keys; F017 `files` referenced by `dashboard_widget_sources` rows of kind `file`.
- Feature flag: `F023_FEATURE` (migration runs regardless; routes are gated)
- Large-table note: `widget_cache` payloads up to 256 KB each; scheduler scans use `(scope_key, computed_at)` and never load payloads.

## TDD

- Failing test first: `testing/features/F023/database/migration_tests.rs::dashboards_tables_exist_with_constraints`, `::widget_position_out_of_range_rejected`, `::widget_cache_cascades_on_widget_delete`, `::widget_sources_and_columns_cascade_on_widget_delete`, `::cache_sources_cascade_on_cache_delete`, `::refresh_interval_required_for_interval_mode`, `::rollback_drops_dashboard_tables`; `testing/features/F023/api/grid_tests.rs::widgets_overlap_rejected`, `::widgets_exceeding_forty_rejected`, `::widget_diff_reports_moved_and_reconfigured`
- Targeted command: `cargo xtask test-feature F023`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: schema-per-worker database from `testing/harness/db.rs`; property strategy generating random non-overlapping layouts

## Exit criteria

- [ ] Tests written before the migration and validator and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S045
- [ ] `finished_at` recorded
