---
id: T038
type: task
status: planned
parent_epic: E002
parent_feature: F010
parent_story: S019
depends_on: [T037]
owned_paths: [crates/domain/src/dataio/**, services/api/src/dataio/**, services/worker/src/dataio/**, testing/features/F010/api/**, testing/features/F010/requirements/**]
feature_flag: F010_FEATURE
branch: t038-import-worker
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 5, 7, 9
- Capability contract: `docs/capability-contracts.md` row F010

# T038 — Import worker

## Identity

- Parent story: `S019` Search
- Owner: platform
- Branch: `t038-import-worker`
- Decision references: `docs/architecture-decisions.md` sections 2–5, 7, 9; `docs/capability-contracts.md` row F010

## Objective

Implement CSV and XLSX parsing, type detection, mapping, duplicate matching, and the import job lifecycle through creation, preview, dry run, chunked resumable commit, and cancel, including the worker job handler and the four import routes.

## Specification

- Owned paths: `crates/domain/src/dataio/import/{mod.rs, parser_csv.rs, parser_xlsx.rs, type_detect.rs, mapping.rs, dedupe.rs, service.rs, chunker.rs, commit.rs}`, `services/api/src/dataio/{handlers_import.rs, handlers_import_commit.rs}`, `services/worker/src/dataio/import_job.rs`
- Contract/input: `CreateImportRequest { sheet_id, file_id, format: csv|xlsx, has_header }`; `PreviewImportRequest { mapping?: Vec<MappingEntry { source_column, target: ColumnId | NewColumn { label, type } , coercion }>, key_column_id?, duplicate_strategy?: skip|update|append }` stored as one `import_column_mappings` row per source column; `CommitImportRequest { dry_run: bool }`; worker job payload `ImportJobMessage { import_id, tenant_id, correlation_id }`; `ChunkCursor { chunk_index, last_row_number }`.
- Output/behavior: routes `POST /api/v1/imports`, `GET /api/v1/imports/{id}`, `POST /api/v1/imports/{id}/preview`, `POST /api/v1/imports/{id}/commit`, `POST /api/v1/imports/{id}/cancel` return `ImportJobResponse` and `PreviewImportResponse { sample_rows (50), detected_types, proposed_mapping, duplicates }`; parsers stream rows and stop with `invalid` past 100,000 rows or 50 MB; `type_detect` samples up to 1,000 rows per column and chooses the narrowest type (`boolean`, `number`, `currency`, `date`, `datetime`, `select` when ≤ 50 distinct values, else `text`); dry run runs the F007 validation engine over every row and writes `import_rows`, one `import_row_errors` row per failure, and the `valid_rows`, `invalid_rows`, and `duplicate_rows` counts on the job, with no sheet writes; the API report is those counts plus the first 100 error rows; real commit is acknowledged `202` and the worker writes 1,000-row chunks through the F008 bulk row service with `Idempotency-Key = <import_id>:<chunk_index>`, applies `skip|update|append`, advances `cursor_chunk_index` and `cursor_row_number` in the same transaction as each chunk result through `ImportJobRepository::advance_cursor`, resumes from them on `claim_resumable_job`, emits `import.started.v1` and `import.completed.v1`, dead-letters after three failures with `import.failed.v1`; cancel flips status after the running chunk and emits `import.failed.v1` with `reason = cancelled`; every transition writes an audit event.
- Dependencies: T037 tables and the `crates/persistence/src/dataio/` repositories; F008 `grid::bulk_upsert_rows` over the F006 repositories; F007 `columns::validate_cells`; F017 file read stream by `file_id`; F004 job runs, retry, dead letters. The parsers, the service, the chunker, and the worker handler hold no SQL (decision 2.1).
- Feature flag: `F010_FEATURE` gates routes and job handler registration.

## TDD

- Failing test first: `testing/features/F010/api/import_tests.rs::import_create_rejects_oversize_file`, `::import_preview_detects_types_and_duplicates`, `::import_mapping_rows_replaced_per_source_column`, `::import_dry_run_report_reads_error_rows`, `::import_dry_run_writes_no_rows`, `::import_commit_writes_chunks_with_idempotency_keys`, `::import_resumes_after_worker_kill_without_duplicates`, `::import_update_strategy_patches_matched_rows`, `::import_skip_strategy_marks_rows_skipped`, `::import_cancel_stops_after_current_chunk`, `::import_dead_letters_after_three_failures`, `::import_viewer_denied`, `::import_cross_tenant_not_found`
- Targeted command: `cargo xtask test-feature F010`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `plan.csv` (1,000 rows, 20 invalid), `plan.xlsx`, malformed `broken.xlsx`; worker kill switch between chunks from `testing/harness/worker.rs`; stubbed F017 file fixture; in-memory outbox recorder

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Routes mounted in `services/api/src/dataio/routes.rs`; job handler registered in `services/worker/src/jobs.rs`; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S019
- [ ] `finished_at` recorded
