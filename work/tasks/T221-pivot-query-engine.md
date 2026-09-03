---
id: T221
type: task
status: planned
parent_epic: E008
parent_feature: F056
parent_story: S111
depends_on: [S111]
owned_paths: [services/api/migrations/*_pivots_*.sql, crates/domain/src/pivots/**, testing/features/F056/database/**, testing/features/F056/api/**]
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
- Decision references: `docs/architecture-decisions.md` sections 2, 3; `docs/capability-contracts.md` row F056

## Objective

Create the `pivots` and `pivot_outputs` schema and the domain aggregation engine that folds permission-filtered source rows into dimension/measure cells.

## Specification

- Owned paths: `services/api/migrations/<ts>_pivots_create_tables.sql`, `services/api/migrations/<ts>_pivots_create_tables.down.sql`, `crates/domain/src/pivots/{mod.rs, pivot.rs, dimension.rs, measure.rs, aggregate.rs, errors.rs, schema.rs}`
- Contract/input: `Pivot` definition per F056 ticket section 4; `aggregate::fold(source: impl Stream<Item = VisibleRow>, def: &Pivot, tz: Tz) -> Result<FoldResult, PivotError>` where `VisibleRow` comes from `reports::query_rows_for_actor` pages of 5,000.
- Output/behavior: DDL creates both tables with check constraints on dimension and measure counts, `pivots_tenant_workspace_name_idx`, `pivot_outputs_one_active_idx`, and the three indexes in the ticket; `fold` returns `FoldResult { cells: Vec<OutputCell>, row_count, source_versions }`, truncates dates per `DateBucket` in `tz`, uses `rust_decimal` for `sum`/`avg`, and fails with `SourceTooLarge` past 100,000 rows or 50,000 cells.
- Dependencies: F021 `query_rows_for_actor`; F007 column type metadata for validation; F049 tenant timezone lookup.
- Feature flag: `F056_FEATURE` (migration runs regardless; routes are gated)
- Large-table note: `pivot_outputs.cells` is jsonb and capped at 50,000 cells per output; future columns must be additive and nullable.

## TDD

- Failing test first: `testing/features/F056/database/migration_tests.rs::pivot_tables_exist_with_constraints`, `::four_row_dimensions_rejected`, `::second_active_output_rejected`, `::rollback_drops_tables`; `testing/features/F056/api/aggregate_tests.rs::aggregate_excludes_hidden_rows`, `::aggregate_month_bucket_uses_tenant_timezone`, `::aggregate_count_distinct_and_decimal_sum`, `::aggregate_source_too_large`
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
