---
id: S141
type: story
status: planned
parent_epic: E003
parent_feature: F071
depends_on: [F007, F010]
owned_paths: [crates/domain/src/migration/**, crates/persistence/src/migration/**, services/api/src/migration/**, services/worker/src/migration/**, services/api/migrations/*_migration_*.sql, testing/features/F071/**]
feature_flag: F071_FEATURE
branch: s141-source-parsing
started_at: null
finished_at: null
---

# S141 — Source parsing

## Identity

- Parent feature: `F071` Migration import
- Owner: platform
- Branch: `s141-source-parsing`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 3, 5, 7, 9; `docs/capability-contracts.md` row F071

## Vertical slice

As a sheet editor, I want to upload a workbook exported from Excel, Google Sheets, Smartsheet, or Airtable and get back a complete dry run — every tab, every column with an inferred type and a confidence number, every sample value, and every thing that could not be brought over — so that I can judge the whole move before a single sheet exists.

## Requirements

- **SR-S141-01:** `POST /api/v1/migrations` validates `source_kind`, the F017-scanned `file_id`, and `sheet-editor` on `target_folder_id`, writes the `migrations` row in `analyzing`, and enqueues the analysis job; the container must be `.xlsx` for `excel` and `google-sheets` and `.zip` for `smartsheet` and `airtable`, and anything else returns `field_errors.file_id = "unsupported_source"`. No sheet, column, row, view, or link is created by this route (covers FR-F071-01, FR-F071-02).
- **SR-S141-02:** The container reader enforces 200 MB compressed, 500 MB uncompressed, 50 tabs, 400 columns per tab, 100,000 rows per tab, 500,000 rows per migration, and 3 concurrent migrations per tenant, rejects a zip entry whose path escapes the extraction root, and accepts a macro workbook without executing the macro project (FR-F071-03, FR-F071-15, NFR-F071-02).
- **SR-S141-03:** The four readers produce one common `SourceTab` stream — `xlsx_reader.rs` for OOXML including Google Sheets and Smartsheet exports, `airtable_csv.rs` for one CSV per table, `zip_container.rs` for the bundles — streaming rows rather than materialising the workbook, and none of them opens a network socket to Microsoft, Google, Smartsheet, or Airtable (FR-F071-02, NFR-F071-01, NFR-F071-02).
- **SR-S141-04:** Header detection, proposed sheet naming with folder deduplication, and primary-column selection write one `migration_sheets` row per tab with `row_count`, `column_count`, and `header_row_number`, and a tab with no qualifying header row raises `no_header_row` (FR-F071-04).
- **SR-S141-05:** Inference writes one `migration_column_maps` row per source column with `inferred_type` from the twelve F007 types, `confidence`, `state`, and staged settings, using a stride sampler seeded by `source_index` so two analyses of the same file agree exactly (FR-F071-05, NFR-F071-05).
- **SR-S141-06:** The confidence rule, the precedence order, the fallback to `text`, and the per-type rules for `select`, `person`, `currency`, `duration`, `date`, and `datetime` behave as specified, and every ambiguity writes an `ambiguous_type` or `ambiguous_date_order` issue naming the candidates (FR-F071-06, FR-F071-07).
- **SR-S141-07:** `GET /api/v1/migrations/{id}` returns the whole preview — sheets, column maps, up to 5 sample values per column, up to 20 sample rows per tab parsed on demand from object storage, issues, and `committed_sheet_count: 0` — and `GET /api/v1/migrations` pages by cursor and filters by `status` and `source_kind` (FR-F071-08, NFR-F071-01).
- **SR-S141-08:** `migration_issues` rows carry `kind`, `severity`, the tab, a source reference, and a message in the user's terms for every dropped conditional format, unsupported formula function, cross-workbook reference, oversized attachment, unresolved person, and capped row or column (FR-F071-15).
- **SR-S141-09:** A viewer or commenter is denied on create and read, a foreign-tenant `file_id`, `target_folder_id`, or migration id returns `not_found`, and a fourth concurrent migration returns `rate_limited` (FR-F071-16, NFR-F071-02).

## Surfaces

- Infrastructure/container: source file and extracted entries under the tenant's own object-storage prefix `tenant_id/migrations/<migration_id>/`; analysis runs on the F004 worker under the per-tenant job quota
- Data access: `crates/persistence/src/migration/{mod.rs, migration_repository.rs, sheet_repository.rs, column_map_repository.rs, issue_repository.rs}` hold every SQL statement for this slice, with the named queries `claim_analyzable`, `replace_column_maps`, `count_blocking_issues`, and `list_preview_page`; the readers, inference, handlers, and `services/worker/src/migration/analyze_job.rs` depend on the repository traits and contain no `sqlx::query*` call or connection, and the analysis result is written in one `UnitOfWork` (decision section 2.1)
- Rust service/API: `crates/domain/src/migration/{mod.rs, errors.rs, limits.rs, issues.rs, service.rs, sources/{xlsx_reader.rs, zip_container.rs, airtable_csv.rs, smartsheet_export.rs, detect.rs}, infer/{sampler.rs, candidates.rs, confidence.rs, options.rs}}`; `services/api/src/migration/{routes.rs, handlers_create.rs, handlers_read.rs, dto.rs}`; `services/worker/src/migration/{mod.rs, analyze_job.rs}`
- Data/migration: `services/api/migrations/<ts>_migration_create_tables.sql` creating `migrations`, `migration_sheets`, `migration_column_maps`, and `migration_issues` with the check constraints, unique keys, and indexes from ticket section 4
- React/UI: none in this slice; the review screen ships in S142
- Mocks/fixtures: `testing/fixtures/migration.rs`; workbook and archive generators in `testing/harness/workbooks/` for `q3-delivery.xlsx`, `smartsheet-export.zip`, `airtable-base.zip`, a 50-tab workbook, a 120,000-row tab, and an over-expanding zip; fixed clock

## TDD harness

- Test path: `testing/features/F071/{api,database}/`
- Feature flag: `F071_FEATURE`
- Targeted command: `cargo xtask test-feature F071`
- Full command: `cargo xtask test-all`
- First failing tests: `create_migration_rejects_unsupported_container`, `analysis_creates_no_sheet_in_target_folder`, `zip_expansion_limit_rejected_before_extraction`, `header_detection_falls_back_to_generated_names`, `inference_assigns_twelve_types_with_confidence`, `ambiguous_number_duration_column_marked_ambiguous`, `select_inferred_only_within_cardinality_rule`, `preview_returns_sheets_columns_samples_and_issues`, `viewer_cannot_create_migration`

## Exit criteria

- [ ] Requirement tests SR-S141-01 through SR-S141-09 written first and failing
- [ ] Tasks T281 and T282 complete and wired through the `services/api` router and the `services/worker` registry
- [ ] Unit, API, database, and permission tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/migration/routes.rs` mounted in `services/api/src/router.rs` (`/api/v1/migrations`); `services/worker/src/migration/analyze_job.rs` registered in `services/worker/src/registry.rs`
- [ ] Handoff evidence recorded in the F071 ticket
