---
id: T221
type: task
status: planned
parent_epic: E008
parent_feature: F056
parent_story: S111
depends_on: [S111]
owned_paths: [services/api/migrations/*_pivots_*.sql, crates/domain/src/pivots/**, crates/persistence/src/pivots/**, testing/features/F056/database/**, testing/features/F056/api/**]
feature_flag: F056_FEATURE
branch: t221-pivot-query-engine
started_at: null
finished_at: null
---

# T221 — Pivot query engine

## Identity

- Parent story: `S111` Pivot configuration
- Owner: platform
- Branch: `t221-pivot-query-engine`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3; `docs/capability-contracts.md` row F056

## Objective

Create the `pivots` and `pivot_outputs` schema with its normalized definition child tables, the `PivotRepository` that owns them, and the domain aggregation engine that folds permission-filtered source rows into dimension/measure cells.

## Specification

- Owned paths: `services/api/migrations/<ts>_pivots_create_tables.sql`, `services/api/migrations/<ts>_pivots_create_tables.down.sql`, `crates/domain/src/pivots/{mod.rs, pivot.rs, dimension.rs, measure.rs, aggregate.rs, errors.rs, schema.rs}`, `crates/persistence/src/pivots/{mod.rs, pivot_repository.rs, definition_rows.rs}`
- Contract/input: `Pivot` definition per F056 ticket section 4; `aggregate::fold(source: impl Stream<Item = VisibleRow>, def: &Pivot, tz: Tz) -> Result<FoldResult, PivotError>` where `VisibleRow` comes from `reports::query_rows_for_actor` pages of 5,000.
- Output/behavior: DDL creates `pivots`, `pivot_outputs`, and the five child tables `pivot_row_dimensions`, `pivot_column_dimensions`, `pivot_measures`, `pivot_filters`, and `pivot_output_source_versions` exactly as in ticket section 4 — cascading foreign keys to the parent, composite primary keys on `(pivot_id, position)` / `(output_id, source_id)`, `position` bounds enforcing 3 row dimensions, 2 column dimensions, 10 measures and 50 filter clauses, unique `(pivot_id, column_id)` per dimension axis and `(pivot_id, column_id, aggregate)` per measure, closed-enum checks on `bucket`, `aggregate`, `format`, `operator`, `source_kind`, `filter_match`, `refresh_policy`, `status`, and `error_code`, foreign keys on `workspace_id`, `created_by`, `updated_by`, and `requested_by`, plus `pivots_tenant_workspace_name_idx`, `pivot_outputs_one_active_idx`, and the ticket's definition-load, column-usage, and staleness indexes; `fold` returns `FoldResult { cells: Vec<OutputCell>, row_count, source_versions }`, truncates dates per `DateBucket` in `tz`, uses `rust_decimal` for `sum`/`avg`, and fails with `SourceTooLarge` past 100,000 rows or 50,000 cells.
- Data access: `crates/persistence/src/pivots/pivot_repository.rs` implements `PivotRepository` over `pivots` and the four definition child tables with `find_with_definition`, `list_for_workspace`, `find_by_source`, `claim_name`, `list_due_for_refresh`, and `replace_row_dimensions`/`replace_column_dimensions`/`replace_measures`/`replace_filters`; `definition_rows.rs` maps child rows to and from `Vec<Dimension>`, `Vec<Measure>`, and the filter set by `position`. Each `replace_*` runs as one delete-of-removed-positions plus upsert inside the caller's `UnitOfWork` and refuses an empty row-dimension or measure set. `aggregate.rs` and every other file under `crates/domain/src/pivots/` take loaded values and hold no `sqlx::query*` call or connection (decision section 2.1).
- Dependencies: F021 `query_rows_for_actor`; F007 column type metadata for validation; F049 tenant timezone lookup.
- Feature flag: `F056_FEATURE` (migration runs regardless; routes are gated)
- Large-table note: `pivot_outputs.cells` stays jsonb as the verbatim rebuildable output grid served by `PivotOutputRepository::load_cells` and rebuilt by the `pivots.compute` job, capped at 50,000 cells per output; definition and source-version child rows are narrow and bounded per parent; future columns must be additive and nullable.

## TDD

- Failing test first: `testing/features/F056/database/migration_tests.rs::pivot_tables_exist_with_constraints`, `::four_row_dimensions_rejected`, `::duplicate_column_on_row_axis_rejected`, `::duplicate_measure_column_and_aggregate_rejected`, `::invalid_bucket_value_rejected`, `::deleting_pivot_cascades_definition_rows`, `::second_active_output_rejected`, `::rollback_drops_tables_children_first`; `testing/features/F056/api/aggregate_tests.rs::aggregate_excludes_hidden_rows`, `::aggregate_month_bucket_uses_tenant_timezone`, `::aggregate_count_distinct_and_decimal_sum`, `::aggregate_source_too_large`, `::repository_round_trips_definition_in_position_order`
- Targeted command: `cargo xtask test-feature F056`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: schema-per-worker database from `testing/harness/db.rs`; `testing/fixtures/pivots.rs` 2,000-row sheet and report hiding 300 rows

## Exit criteria

- [ ] Tests written before the migration and engine and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; `cargo xtask check-migrations` passes
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S111
- [ ] `finished_at` recorded
