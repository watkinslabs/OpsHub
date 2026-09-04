---
id: T025
type: task
status: planned
parent_epic: E002
parent_feature: F007
parent_story: S013
depends_on: [S013]
owned_paths: [services/api/migrations/*_columns_*.sql, crates/domain/src/columns/**, testing/features/F007/database/**]
feature_flag: F007_FEATURE
branch: t025-column-types
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` section 2
- Capability contract: `docs/capability-contracts.md` row F007

# T025 — Column types

## Identity

- Parent story: `S013` Column lifecycle
- Owner: platform
- Branch: `t025-column-types`
- Decision references: `docs/architecture-decisions.md` section 2; `docs/capability-contracts.md` row F007

## Objective

Create the `columns`, `column_options`, and `cell_validation_states` tables plus the `ColumnType` enum, settings model, and conversion matrix so the column service has a verified schema and typed domain model.

## Specification

- Owned paths: `services/api/migrations/<ts>_columns_create_tables.sql`, `services/api/migrations/<ts>_columns_create_tables.down.sql`, `crates/domain/src/columns/{mod.rs, column.rs, types.rs, settings.rs, conversion.rs, position.rs, schema.rs}`
- Contract/input: DDL per F007 ticket section 4 PostgreSQL: five tables with tenant/UUIDv7/version/audit/soft-delete columns, `type` check constraint over the twelve type names, `columns_sheet_label_idx` partial unique index, `columns_sheet_primary_idx` partial unique index, `width` check 40–1,000; `column_settings(column_id primary key references columns(id) on delete cascade, tenant_id, precision check 0–8, currency_code, display_format, multi, time_zone, updated_by, updated_at)` created per column by trigger, replacing the dropped `columns.settings jsonb`; `column_validation_rules(tenant_id, column_id references columns(id) on delete cascade, rule check over the seven rule names, min_number, max_number, min_datetime, max_datetime, pattern, message, created_by, created_at, primary key (column_id, rule))` with a per-rule check requiring exactly the bound columns that rule uses, replacing the dropped `columns.validation jsonb`; `cell_validation_states` primary key `(row_id, column_id)` with `state` check, populated from F006's `cells.validation_state`, `validation_code`, and `validation_message` before those three columns are dropped as a declared destructive statement; index `column_validation_rules(tenant_id, rule)`; additive nullable `cells.normalized jsonb`.
- Output/behavior: `sqlx migrate run` applies cleanly on a database with F006 tables; `sqlx migrate revert` drops the five tables and the `cells.normalized` column and restores the three `cells.validation_*` columns with their rows; `ColumnType` exposes `parse(&str)`, `as_str()`, and `default_settings()`; `conversion::allowed(from, to) -> bool` matches the ticket matrix; `position.rs` reuses the F006 fractional index algorithm for column order; `schema.rs` names are consumed by `ColumnRepository`, `ColumnOptionRepository`, and `CellValidationStateRepository` in `crates/persistence/src/columns/`, which hold every query against these tables; `cargo xtask check-migrations` reports rollback metadata and `cargo xtask check-persistence` passes.
- Dependencies: F006 tables `sheets`, `rows`, `cells` exist for foreign keys and the additive column.
- Feature flag: `F007_FEATURE` (migration runs regardless; API routes are gated)
- Large-table note: `cells.normalized` is added without a default so the migration does not rewrite existing cell rows.

## TDD

- Failing test first: `testing/features/F007/database/migration_tests.rs::columns_tables_exist_with_constraints`, `::duplicate_label_same_sheet_rejected`, `::second_primary_column_rejected`, `::unknown_type_rejected_by_check`, `::column_settings_row_created_by_trigger`, `::validation_rule_duplicate_name_rejected`, `::validation_rule_missing_bound_rejected_by_check`, `::cell_validation_states_backfilled_from_cells_columns`, `::rollback_drops_tables_and_normalized_column`; `crates/domain/src/columns/conversion.rs` unit test `conversion_matrix_matches_ticket`
- Targeted command: `cargo xtask test-feature F007`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: schema-per-worker database from `testing/harness/db.rs`; no external mocks

## Exit criteria

- [ ] Tests written before the migration and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18 with F006 data present
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S013
- [ ] `finished_at` recorded
