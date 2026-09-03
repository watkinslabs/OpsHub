---
id: S019
type: story
status: planned
parent_epic: E002
parent_feature: F010
depends_on: [F008, F004]
owned_paths: [crates/domain/src/dataio/**, services/api/src/dataio/**, services/worker/src/dataio/**, services/api/migrations/*_dataio_*.sql, testing/features/F010/**]
feature_flag: F010_FEATURE
branch: s019-search
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 7, 9
- Capability contract: `docs/capability-contracts.md` row F010

# S019 — Search

## Identity

- Parent feature: `F010` Search/import/export
- Owner: platform
- Branch: `s019-search`
- Decision references: `docs/architecture-decisions.md` sections 2–4, 7, 9; `docs/capability-contracts.md` row F010

## Vertical slice

As a sheet viewer, I want to search my tenant's sheets, rows, comment metadata, and attachment metadata and see only what I can read, and as a sheet editor I want to create an import job, preview its mapping, and dry-run it before anything is written, so that finding and staging data is safe before the commit path in S020.

Story split: this story owns the search index, search route, and the import job creation, preview, and dry-run stages (T037, T038). S020 owns the real commit with resumable chunks, cancel, and the export jobs (T039, T040).

## Requirements

- **SR-S019-01:** `GET /api/v1/search` returns ranked hits with `kind`, `entity_id`, `sheet_id`, `title`, highlighted `snippet`, and an opaque cursor; `q` 1–256 chars, `limit` 1–100, empty `q` returns `400 invalid` (covers FR-F010-01).
- **SR-S019-02:** Every hit is re-checked against the actor's ACL before return; rows on unreadable sheets and foreign-tenant documents never appear, and a foreign `sheet_id` filter yields an empty page (FR-F010-02, NFR-F010-02).
- **SR-S019-03:** The indexer in `services/worker/src/dataio/index_consumer.rs` upserts `search_documents` from the twelve listed sheet, row, cell, comment, and file events, drops stale versions, removes soft-deleted sources, and emits `search.indexed.v1` (FR-F010-03, FR-F010-04).
- **SR-S019-04:** Comment and attachment documents carry metadata only (200-char comment prefix, author, filename, MIME, size); file bodies are never read by the indexer (FR-F010-04).
- **SR-S019-05:** `POST /api/v1/imports` creates a `created` job for a CSV or XLSX `file_id` up to 50 MB and 100,000 rows; oversize or unparseable files return `400 invalid` with `field_errors.file_id` (FR-F010-05).
- **SR-S019-06:** `POST /api/v1/imports/{id}/preview` returns 50 sample rows, detected types, a proposed mapping with coercion rules, and duplicate matches on `key_column_id`, moving the job to `previewed` (FR-F010-06).
- **SR-S019-07:** `POST /api/v1/imports/{id}/commit` with `dry_run: true` validates all rows through the F007 engine, stores `import_rows` and the `report`, sets status `dry_run`, and writes zero sheet rows (FR-F010-07).
- **SR-S019-08:** Index lag from outbox event to searchable document is under 5 s p95 and search p95 is under 500 ms on the 1,000,000-document fixture (NFR-F010-01).

## Surfaces

- Infrastructure/container: MinIO bucket prefix per test worker from F004 compose baseline
- Rust service/API: `crates/domain/src/dataio/{mod.rs, errors.rs, search/indexer.rs, search/query.rs, search/acl_filter.rs, import/parser_csv.rs, import/parser_xlsx.rs, import/type_detect.rs, import/mapping.rs, import/dedupe.rs, import/service.rs}`; `services/api/src/dataio/{mod.rs, routes.rs, handlers_search.rs, handlers_import.rs, dto.rs}`; `services/worker/src/dataio/{mod.rs, index_consumer.rs}`
- Data/migration: `services/api/migrations/<ts>_dataio_create_tables.sql` creating `search_documents`, `import_jobs`, `import_rows`, `export_jobs` with the constraints and indexes from ticket section 4
- React/UI: none in this story (S020 and T039 cover the palette, wizard, and export UI)
- Mocks/fixtures: `testing/fixtures/dataio.rs` tenants A and B, `Plan` and restricted `Payroll` sheets, seeded comments and attachment metadata, `plan.csv` and `plan.xlsx`; in-memory outbox recorder; stubbed F017 file fixture

## TDD harness

- Test path: `testing/features/F010/api/` and `testing/features/F010/database/`
- Feature flag: `F010_FEATURE`
- Targeted command: `cargo xtask test-feature F010`
- Full command: `cargo xtask test-all`
- First failing tests: `search_returns_ranked_hits_with_snippets`, `search_omits_unreadable_sheet_rows`, `search_cross_tenant_returns_empty`, `indexer_upserts_and_ignores_stale_version`, `indexer_never_reads_file_bodies`, `import_create_rejects_oversize_file`, `import_preview_detects_types_and_duplicates`, `import_dry_run_writes_no_rows`

## Exit criteria

- [ ] Requirement tests SR-S019-01 through SR-S019-08 written first and failing
- [ ] Tasks T037 and T038 complete and wired through `services/api` router and worker consumer registry
- [ ] Unit, API, database, permission tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/dataio/routes.rs` mounted in `services/api/src/router.rs`; `services/worker/src/dataio/index_consumer.rs` registered in `services/worker/src/consumers.rs`
- [ ] Handoff evidence recorded in the F010 ticket
