---
id: T174
type: task
status: planned
parent_epic: E000
parent_feature: F044
parent_story: S087
depends_on: [T173]
owned_paths: [automation/xtask/src/release.rs, testing/features/F044/api/**, testing/features/F044/database/**]
feature_flag: F044_FEATURE
branch: t174-migration-safety
started_at: null
finished_at: null
---

# T174 — Migration safety

## Identity

- Parent story: `S087` Contract drift
- Owner: platform
- Branch: `t174-migration-safety`
- Decision references: `docs/architecture-decisions.md` section 2; `docs/capability-contracts.md` row F044

## Objective

Implement `check-migrations` with naming, pairing, ownership, header, ordering, immutability, destructive-statement, and down-completeness checks by static analysis of `services/api/migrations/`.

## Specification

- Owned paths: `automation/xtask/src/release.rs` (`Migration`, `MigrationHeader`, `StatementKind`, `sql::classify`, `load_migrations`, `check_migration_names`, `check_migration_order`, `check_migration_safety`, `check_migrations`)
- Contract/input: files matching `^(\d{14})_([a-z0-9-]+)_([a-z0-9_]+)\.(up|down)\.sql$`; header line 1 `-- opshub: feature=<id> module=<m> reversible=true|false destructive=none|<kinds>`; `--base REF` default `origin/main` then `main`; catalog rows for module ownership; tickets for the `Expand/contract:` bullet
- Output/behavior: `migration.name`, `migration.down_missing`, `migration.module_not_owned`, `migration.header`, `migration.order` (duplicate or non-increasing timestamp, or older than the newest on base), `migration.mutated` (content differs from `git show <base>:<path>`), `migration.destructive` (kinds `DROP TABLE`, `DROP COLUMN`, `ALTER COLUMN TYPE`, `TRUNCATE`, `ADD COLUMN NOT NULL` without `DEFAULT`, `CREATE INDEX` without `CONCURRENTLY` on a pre-existing table) unless declared in the header and justified in the ticket, `migration.down_incomplete` (a table, index, or type created in `up` not mentioned in `down`), `migration.unclassified` (warning in JSON); tokenizer strips `--` and `/* */` comments and skips string literals; table existence tracked across migrations in timestamp order; an absent migrations directory prints `skipped` and passes
- Dependencies: T173 catalog parser
- Feature flag: `F044_FEATURE`
- Data access (decision 2.1): `services/api/migrations/*.sql` is read as text only. The checker never executes a statement, never opens a database connection, and takes no `sqlx` dependency; it owns no table and adds no repository.

## TDD

- Failing test first: `testing/features/F044/api/migration_tests.rs::migration_without_down_reported`, `::bad_filename_reported`, `::module_not_owned_by_any_feature_reported`, `::missing_header_reported`, `::duplicate_timestamp_reported`, `::branch_migration_older_than_main_reported`, `::mutated_main_migration_reported`, `::drop_column_without_declaration_is_destructive`, `::declared_and_justified_destructive_passes`, `::index_without_concurrently_on_existing_table_flagged`, `::down_missing_created_index_is_incomplete`, `testing/features/F044/database/sql_tests.rs::classifier_ignores_comments_and_strings`, `::table_existence_tracked_in_timestamp_order`
- Targeted command: `cargo xtask test-feature F044`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/features/F044/fixtures/migrations` with a scratch repository whose `origin/main` holds two migrations and whose branch adds valid, older, mutated, and destructive ones

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] `check-migrations` dispatched from `main()` through `release.rs`; the old filename-only check removed
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S087
- [ ] `finished_at` recorded
