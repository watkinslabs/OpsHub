---
id: T081
type: task
status: planned
parent_epic: E005
parent_feature: F021
parent_story: S041
depends_on: [S041]
owned_paths: [services/api/migrations/*_reports_*.sql, crates/domain/src/reports/**, crates/persistence/src/reports/**, testing/features/F021/database/**, testing/features/F021/api/**]
feature_flag: F021_FEATURE
branch: t081-report-query-model
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3
- Capability contract: `docs/capability-contracts.md` row F021

# T081 — Report query model

## Identity

- Parent story: `S041` Source selection
- Owner: platform
- Branch: `t081-report-query-model`
- Decision references: `docs/architecture-decisions.md` sections 2, 3; `docs/capability-contracts.md` row F021

## Objective

Define the typed `ReportDefinition` model, its validator, and the `reports` schema migration so every later task compiles, stores, and refreshes reports against a verified structure.

## Specification

- Owned paths: `services/api/migrations/<ts>_reports_create_tables.sql`, `services/api/migrations/<ts>_reports_create_tables.down.sql`, `crates/domain/src/reports/{mod.rs, report.rs, definition.rs, validate.rs, snapshot.rs, errors.rs, schema.rs}` (repository traits, no SQL), `crates/persistence/src/reports/{mod.rs, report_repository.rs, report_snapshot_repository.rs}`
- Contract/input: `ReportDefinition { sources: Vec<ReportSource>, joins: Vec<ReportJoin>, filters: FilterNode, group_by: Vec<GroupLevel>, aggregates: Vec<AggregateSpec>, calculated_fields: Vec<CalculatedField>, sorts: Vec<SortSpec> }` deserialized from a request body ≤ 256 KB and persisted as rows, never as a `jsonb` column; `RefreshPolicy { mode, interval_minutes, timezone }` mapped to `reports.refresh_mode`, `refresh_interval_minutes`, `refresh_timezone`; `AggregatePolicy::{Viewer, Owner}`; column metadata from F007 for type checks; F035 `formulas::parse` for calculated fields.
- Output/behavior: `validate_definition(def, sheets: &SheetCatalog) -> Result<ValidatedDefinition, Vec<FieldError>>` enforces alias regex `^[a-z][a-z0-9_]{0,31}$`, unique aliases, 1..20 sources, 0..19 joins forming a tree from `sources[0]`, join type compatibility (`link` to row id, matching scalar types), operator/type matrix for 13 operators, depth ≤ 4, ≤ 50 predicates, ≤ 3 group levels, ≤ 20 aggregates with `sum`/`avg` on numeric types only, ≤ 25 calculated fields parsed without cycles under 10,000 AST nodes; each failure is a `FieldError { path, code, message }`. DDL creates `reports`, `report_sources`, `report_source_columns`, `report_joins`, `report_filters`, `report_group_by`, `report_aggregates`, `report_calculated_fields`, `report_snapshots`, `report_snapshot_sources`, `report_snapshot_rows`, `report_snapshot_row_sources` with the unique name partial index, `(report_id, alias)` and `(report_id, position)` uniqueness, `(report_id, lower(label))` uniqueness on aggregates and calculated fields, the `refresh_mode`/`refresh_interval_minutes` check, the `report_group_by` level range, the join `kind` and `left_source_id <> right_source_id` checks, single-active-snapshot partial index, `report_sources(sheet_id)` and `report_source_columns(column_id)` indexes, the scheduler index `reports(refresh_mode, refresh_interval_minutes) where deleted_at is null`, and the `report_snapshot_rows(snapshot_id, seq)` and `report_snapshot_row_sources(snapshot_id, seq, source_id)` primary keys; `sqlx migrate revert` drops all twelve tables. `ReportRepository` and `ReportSnapshotRepository` own these tables and expose `load_definition`, `replace_definition`, `list_reports_using_sheet`, `list_reports_using_column`, `page_reports`, `claim_refresh`, `find_active_run`, `latest_succeeded`, `page_snapshot_rows`, `mark_snapshots_stale`, `prune_snapshots`; `replace_definition` writes all eight definition tables plus the stale marking in one `UnitOfWork`.
- Dependencies: F006/F007 tables `sheets`, `columns` for foreign keys and column types; F035 parser crate.
- Feature flag: `F021_FEATURE` (migration runs regardless; routes are gated)
- Large-table note: `report_snapshot_rows` grows to 300,000 rows per report (3 snapshots × 100,000); retention deletes by `snapshot_id` in batches of 10,000 through `prune_snapshots`, and `report_snapshot_row_sources` cascades from the row it belongs to.

## TDD

- Failing test first: `testing/features/F021/database/migration_tests.rs::reports_tables_exist_with_constraints`, `::duplicate_report_name_same_folder_rejected`, `::second_active_snapshot_rejected`, `::rollback_drops_report_tables`, `::report_definition_round_trips_through_repository`; `testing/features/F021/api/definition_tests.rs::alias_regex_enforced`, `::join_cycle_rejected`, `::join_type_mismatch_rejected`, `::calculated_field_parse_error_names_field`
- Targeted command: `cargo xtask test-feature F021`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: schema-per-worker database from `testing/harness/db.rs`; `SheetCatalog` fixture with "Projects", "Risks", "Budget" column types; real F035 parser

## Exit criteria

- [ ] Tests written before the migration and validator and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S041
- [ ] `finished_at` recorded
