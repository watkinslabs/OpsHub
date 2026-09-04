---
id: T121
type: task
status: planned
parent_epic: E007
parent_feature: F031
parent_story: S061
depends_on: [S061]
owned_paths: [services/api/migrations/*_portfolios_*.sql, crates/domain/src/portfolios/**, crates/persistence/src/portfolios/**, testing/features/F031/database/**]
feature_flag: F031_FEATURE
branch: t121-portfolio-schema
started_at: null
finished_at: null
---

# T121 — Portfolio schema

## Identity

- Parent story: `S061` Portfolio setup
- Owner: platform
- Branch: `t121-portfolio-schema`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1; `docs/capability-contracts.md` row F031

## Objective

Create the `portfolios`, `portfolio_projects`, and `portfolio_rollups` tables with constraints, indexes, and rollback so the portfolio service and the refresh worker have a verified schema.

## Specification

- Owned paths: `services/api/migrations/<ts>_portfolios_create_tables.sql`, `services/api/migrations/<ts>_portfolios_create_tables.down.sql`, `crates/domain/src/portfolios/schema.rs` (typed column names), `crates/persistence/src/portfolios/{mod.rs, portfolio_repository.rs, rollup_repository.rs}` (the only place F031 SQL exists, per decision section 2.1)
- Contract/input: DDL per F031 ticket section 4 PostgreSQL: `portfolios` with tenant/UUIDv7/version/audit/soft-delete columns, `refresh_policy` check constraint (`manual`, `scheduled`), `stale_after_seconds` check 60–86,400, `rollup_state` default `never`; `portfolio_projects` with composite primary key `(portfolio_id, project_sheet_id)` and foreign keys to `portfolios(id)` and `sheets(id)` with `on delete restrict`; `portfolio_measure_mappings(portfolio_id, measure, column_id)` with primary key `(portfolio_id, measure)` and a `measure` check over the six measure names; `portfolio_rollups` with unique `(portfolio_id, requested_version)`; `portfolio_rollup_rows` with unique `(rollup_id, project_sheet_id)`, typed measure and `*_state` columns, and typed `sheet_version`/`baseline_id` in place of the former `source_versions`; `portfolio_rollup_totals` with primary key `(rollup_id, measure, bucket)`. No array column and no `jsonb` column is created.
- Output/behavior: `sqlx migrate run` applies cleanly on an empty database and on a database with F006 and F015 tables; `sqlx migrate revert` drops the six tables and indexes, children before parents; `cargo xtask check-migrations` reports forward compatibility and rollback metadata; unique partial name index blocks case-insensitive duplicates while `deleted_at is null`.
- Dependencies: F006 `sheets` and F015 `provisioning_runs` tables exist for foreign keys and project validation.
- Feature flag: `F031_FEATURE` (migration runs regardless; API routes and worker job are gated)
- Data access: `PortfolioRepository` (owns `portfolios`, `portfolio_projects`, `portfolio_measure_mappings`) and `PortfolioRollupRepository` (owns `portfolio_rollups`, `portfolio_rollup_rows`, `portfolio_rollup_totals`) are the only classes that write these tables; the domain service, handlers, and worker job depend on their traits (decision section 2.1).
- Large-table note: `portfolio_rollup_rows` is bounded to 500 rows per snapshot and three snapshots per portfolio, so a portfolio holds at most 1,500 rows; future columns must be additive and nullable.

## TDD

- Failing test first: `testing/features/F031/database/migration_tests.rs::portfolio_tables_exist_with_constraints`, `::duplicate_portfolio_name_rejected`, `::refresh_policy_check_rejects_unknown_value`, `::membership_requires_existing_sheet`, `::snapshot_unique_per_requested_version`, `::rollup_row_unique_per_project_per_snapshot`, `::measure_mapping_rejects_unknown_measure`, `::measure_state_check_rejects_unknown_state`, `::rollback_drops_tables`
- Targeted command: `cargo xtask test-feature F031`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: schema-per-worker database from `testing/harness/db.rs`; F006 and F015 migrations applied first; no external mocks

## Exit criteria

- [ ] Tests written before the migration and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S061
- [ ] `finished_at` recorded
