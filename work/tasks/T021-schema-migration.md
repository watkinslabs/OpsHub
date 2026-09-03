---
id: T021
type: task
status: planned
parent_epic: E002
parent_feature: F006
parent_story: S011
depends_on: [S011]
owned_paths: [services/api/migrations/*_sheets_*.sql, crates/domain/src/sheets/**, testing/features/F006/database/**]
feature_flag: F006_FEATURE
branch: t021-schema-migration
started_at: null
finished_at: null
---

# T021 — Schema migration

## Identity

- Parent story: `S011` Create sheet
- Owner: platform
- Branch: `t021-schema-migration`
- Decision references: `docs/architecture-decisions.md` section 2; `docs/capability-contracts.md` row F006

## Objective

Create the `sheets`, `sheet_groups`, `rows`, and `cells` tables with constraints, indexes, and rollback so S011 and S012 services have a verified schema.

## Specification

- Owned paths: `services/api/migrations/<ts>_sheets_create_tables.sql`, `services/api/migrations/<ts>_sheets_create_tables.down.sql`, `crates/domain/src/sheets/schema.rs` (typed column names)
- Contract/input: DDL per F006 ticket section 4 PostgreSQL: four tables, tenant/UUIDv7/version/audit/soft-delete columns, unique name index per folder, one default group per sheet partial unique index, foreign keys with `on delete restrict`, `rows(sheet_id, position)` partial index, `cells` primary key `(row_id, column_id)`.
- Output/behavior: `sqlx migrate run` applies cleanly on an empty database and on a database with F005 tables; `sqlx migrate revert` drops the tables; `cargo xtask check-migrations` reports forward compatibility and rollback metadata.
- Dependencies: F005 tables `workspaces` and `folders` exist for foreign keys.
- Feature flag: `F006_FEATURE` (migration runs regardless; API routes are gated)
- Large-table note: no existing data; future column additions must be additive and nullable.

## TDD

- Failing test first: `testing/features/F006/database/migration_tests.rs::sheets_tables_exist_with_constraints`, `::duplicate_name_same_folder_rejected`, `::second_default_group_rejected`, `::rollback_drops_tables`
- Targeted command: `cargo xtask test-feature F006`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: schema-per-worker database from `testing/harness/db.rs`; no external mocks

## Exit criteria

- [ ] Tests written before the migration and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S011
- [ ] `finished_at` recorded
