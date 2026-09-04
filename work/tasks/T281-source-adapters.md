---
id: T281
type: task
status: planned
parent_epic: E003
parent_feature: F071
parent_story: S141
depends_on: [S141]
owned_paths: [crates/domain/src/migration/**, crates/persistence/src/migration/**, services/api/src/migration/**, services/worker/src/migration/**, services/api/migrations/*_migration_*.sql, testing/features/F071/api/**, testing/features/F071/database/**]
feature_flag: F071_FEATURE
branch: t281-source-adapters
started_at: null
finished_at: null
---

# T281 — Source adapters

## Identity

- Parent story: `S141` Source parsing
- Owner: platform
- Branch: `t281-source-adapters`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 5, 9; `docs/capability-contracts.md` row F071

## Objective

Create the `migration` schema and implement the four source readers, the container and limit guards, the type inference engine with confidence, the create and read routes, and the analysis job that stages a complete dry run without creating anything in the workspace.

## Specification

- Owned paths: `services/api/migrations/<ts>_migration_create_tables.sql` and `.down.sql`, `crates/domain/src/migration/{mod.rs, errors.rs, limits.rs, issues.rs, service.rs, sources/{mod.rs, detect.rs, xlsx_reader.rs, zip_container.rs, airtable_csv.rs, smartsheet_export.rs}, infer/{mod.rs, sampler.rs, candidates.rs, confidence.rs, options.rs}}`, `crates/persistence/src/migration/{mod.rs, migration_repository.rs, sheet_repository.rs, column_map_repository.rs, issue_repository.rs}`, `services/api/src/migration/{mod.rs, routes.rs, handlers_create.rs, handlers_read.rs, dto.rs}`, `services/worker/src/migration/{mod.rs, analyze_job.rs}`
- Contract/input: `CreateMigrationRequest { file_id, source_kind, target_folder_id, name? }`; list query `{ cursor?, limit?, status?, source_kind? }`; the stored source object at `tenant_id/migrations/<migration_id>/source`.
- Output/behavior: routes `POST /api/v1/migrations`, `GET /api/v1/migrations`, `GET /api/v1/migrations/{id}`. `detect.rs` chooses the reader from `source_kind` and the container magic bytes and rejects a mismatch with `unsupported_source`. `zip_container.rs` rejects an entry whose normalised path escapes the extraction root and stops at the 500 MB uncompressed ceiling before writing anything. `xlsx_reader.rs` streams SpreadsheetML rows with the shared-strings table read once, exposing cell value, number format, formula text, and outline level; `airtable_csv.rs` reads one CSV per table; `smartsheet_export.rs` maps one bundled Excel export per sheet. `sampler.rs` takes the first 500 non-empty cells plus a stride over the remainder seeded by `source_index`, capped at 2,000; `candidates.rs` scores the twelve F007 types; `confidence.rs` applies the 0.95 and 0.80 thresholds and the fixed precedence and marks `ambiguous`; `options.rs` stages select options at 50 distinct values, 20 % of `row_count`, and 60 chars. Header detection, proposed-name deduplication, and primary-column choice write `migration_sheets`; inference writes `migration_column_maps`; every gap writes a `migration_issues` row with `kind`, `severity`, tab, source reference, and message. `analyze_job.rs` claims through `claim_analyzable`, writes the whole plan in one `UnitOfWork`, sets `ready` with `blocking_issue_count`, and dead-letters after three attempts with `migration.failed.v1`. `GET /api/v1/migrations/{id}` composes the preview and parses up to 20 sample rows per tab on demand. DDL for `migrations`, `migration_sheets`, `migration_column_maps`, and `migration_issues` with the check constraints, unique keys, and indexes from ticket section 4.
- Data access: the readers, inference, handlers, and `analyze_job.rs` hold no SQL; every read and write goes through `MigrationRepository`, `MigrationSheetRepository`, `MigrationColumnMapRepository`, and `MigrationIssueRepository` in `crates/persistence/src/migration/` using the named queries `claim_analyzable`, `replace_column_maps`, `count_blocking_issues`, and `list_preview_page`, with no generic query escape hatch, and the analysis write commits in one `UnitOfWork` (decision section 2.1).
- Dependencies: F007 column types, settings, and options as the inference target; F010 object-storage job conventions and its xlsx and CSV parsing primitives; F017 for the scanned `file_id`; F004 for the worker, quota, and dead letters; F003 for `sheet-editor` on the destination folder.
- Feature flag: `F071_FEATURE` gates the routes and the analysis job; the migration runs regardless.

## TDD

- Failing test first: `testing/features/F071/api/source_tests.rs::detect_rejects_container_mismatched_to_source_kind`, `::zip_entry_escaping_root_rejected`, `::zip_expansion_limit_rejected_before_extraction`, `::macro_workbook_accepted_and_recorded_without_execution`, `::airtable_zip_reads_one_table_per_csv`; `testing/features/F071/api/inference_tests.rs::inference_assigns_twelve_types_with_confidence`, `::ambiguous_number_duration_column_marked_ambiguous`, `::low_confidence_column_falls_back_to_text_with_samples`, `::select_inferred_only_within_cardinality_rule`, `::person_column_requires_resolvable_tenant_users`, `::currency_column_stages_iso_code`, `::repeat_analysis_produces_identical_plan`; `testing/features/F071/api/analyze_tests.rs::analysis_creates_no_sheet_in_target_folder`, `::header_detection_falls_back_to_generated_names`, `::preview_returns_sheets_columns_samples_and_issues`, `::fourth_concurrent_migration_rate_limited`, `::viewer_cannot_create_migration`, `::foreign_tenant_migration_not_found`; `testing/features/F071/database/migration_tests.rs::migration_tables_exist_with_constraints`, `::column_map_unique_per_sheet_and_index`, `::issue_kind_check_rejects_unknown_kind`, `::sheets_cascade_on_migration_delete`, `::rollback_drops_migration_tables`
- Targeted command: `cargo xtask test-feature F071`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/migration.rs`; workbook and archive generators in `testing/harness/workbooks/`; F017 file API stub with pre-scanned fixtures; fixed clock `2026-09-03T00:00:00Z`

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; routes and job registered behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S141
- [ ] `finished_at` recorded
