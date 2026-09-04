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

Create the `sheets`, `sheet_settings`, `sheet_groups`, `rows`, and `cells` tables with their triggers, constraints, indexes, and rollback so the `crates/persistence/src/sheets/` repositories that S011 and S012 build on have a verified schema.

## Specification

- Owned paths: `services/api/migrations/<ts>_sheets_create_tables.sql`, `services/api/migrations/<ts>_sheets_create_tables.down.sql`, `crates/domain/src/sheets/schema.rs` (typed column names)
- Contract/input: DDL per F006 ticket section 4 PostgreSQL — five tables with tenant/UUIDv7/version/audit/soft-delete columns: `sheets`; `sheet_settings(sheet_id uuid primary key references sheets(id) on delete cascade, tenant_id uuid not null, row_numbering text not null default 'none' check (row_numbering in ('none','sequential','custom')), default_view text not null default 'grid' check (default_view in ('grid','board')), board_lane_column_id uuid, updated_by uuid, updated_at timestamptz not null)` with an insert trigger on `sheets` creating exactly one row; `sheet_groups`; `rows(position text not null)`; `cells(tenant_id, row_id, column_id, raw jsonb, display text, validation_state text not null default 'valid' check (validation_state in ('valid','invalid','pending')), validation_code text, validation_message text, updated_at, primary key (row_id, column_id))`. Constraints and indexes: `sheets_tenant_folder_name_idx`, one `is_default` group per sheet partial unique index, foreign keys with `on delete restrict`, `rows(sheet_id, position) where deleted_at is null`, `rows(tenant_id, id)`, `cells(row_id)`, `cells(column_id, validation_state) where validation_state <> 'valid'`, `sheets(tenant_id, workspace_id, updated_at desc)`. `cells.raw` stays `jsonb` as the user-defined typed cell value only; `board_lane_column_id` gains its foreign key to `columns(id)` in F007.
- Output/behavior: `sqlx migrate run` applies cleanly on an empty database and on a database with F005 tables; `sqlx migrate revert` drops the five tables and the settings trigger; every table created here is reached only through `SheetRepository`, `SheetGroupRepository`, `RowRepository`, and `CellRepository` in `crates/persistence/src/sheets/`, and the database lane asserts the schema through those repositories rather than embedding SQL in services or handlers (decision 2.1); `cargo xtask check-migrations` reports forward compatibility and rollback metadata.
- Dependencies: F005 tables `workspaces` and `folders` exist for foreign keys.
- Feature flag: `F006_FEATURE` (migration runs regardless; API routes are gated)
- Large-table note: no existing data; future column additions must be additive and nullable.

## TDD

- Failing test first: `testing/features/F006/database/migration_tests.rs::sheets_tables_exist_with_constraints`, `::duplicate_name_same_folder_rejected`, `::second_default_group_rejected`, `::sheet_settings_row_created_by_trigger`, `::sheet_settings_rejects_unknown_default_view`, `::cell_validation_state_check_rejects_unknown_value`, `::rollback_drops_tables`
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
