---
id: S020
type: story
status: planned
parent_epic: E002
parent_feature: F010
depends_on: [S019]
owned_paths: [crates/domain/src/dataio/**, services/api/src/dataio/**, services/worker/src/dataio/**, apps/web/src/features/dataio/**, testing/features/F010/**]
feature_flag: F010_FEATURE
branch: s020-csv-xlsx-jobs
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 5, 6, 7, 9
- Capability contract: `docs/capability-contracts.md` row F010

# S020 — CSV/XLSX jobs

## Identity

- Parent feature: `F010` Search/import/export
- Owner: platform
- Branch: `s020-csv-xlsx-jobs`
- Decision references: `docs/architecture-decisions.md` sections 2–7, 9; `docs/capability-contracts.md` row F010

## Vertical slice

As a sheet editor, I want to commit a previewed import in resumable chunks with a chosen duplicate strategy, cancel it if needed, and export a sheet or view to CSV, XLSX, or PDF that respects my permissions, and I want the search palette, import wizard, and export dialog in the web app, so that data moves in and out of OpsHub safely at 100,000-row scale.

Story split: S019 delivered the index, search route, and import creation, preview, and dry run. This story owns the real commit path with cursor resume and cancel, the export jobs and download, and all F010 UI (T039, T040).

## Requirements

- **SR-S020-01:** `POST /api/v1/imports/{id}/commit` with `dry_run: false` is acknowledged in under 2 s and the worker writes 1,000-row chunks through the F008 bulk row service with `Idempotency-Key = <import_id>:<chunk_index>`, advancing `cursor` per chunk and emitting `import.started.v1` and `import.completed.v1` (covers FR-F010-08).
- **SR-S020-02:** A worker killed between chunks leaves status `committing` with a valid `cursor`; the next claim resumes and every `import_rows.target_row_id` is set exactly once (FR-F010-09, NFR-F010-04).
- **SR-S020-03:** `skip`, `update`, and `append` strategies behave per FR-F010-10; `update` uses `If-Match` and reports rows changed during the import as conflicts in the report.
- **SR-S020-04:** `POST /api/v1/imports/{id}/cancel` stops after the current chunk, keeps written rows, emits `import.failed.v1` with `reason = cancelled`, and returns `409 conflict` on terminal jobs; three worker failures dead-letter the job as `failed` (FR-F010-11, FR-F010-12).
- **SR-S020-05:** `POST /api/v1/exports` queues a job acknowledged in under 2 s; the worker writes CSV, XLSX, or PDF with hidden and denied columns and rows excluded, records `storage_key`, `checksum`, `row_count`, `requested_by`, and emits `export.completed.v1` (FR-F010-13, FR-F010-14).
- **SR-S020-06:** `GET /api/v1/exports/{id}/download` redirects to a 15-minute signed URL for the requester or a tenant-admin, returns `409 conflict` while running, `404 not_found` after the 7-day expiry, and writes an `export.download` audit event (FR-F010-15).
- **SR-S020-07:** `SearchCommandPalette`, `SearchResultsPage`, `ImportWizard`, `ImportStatusPanel`, and `ExportDialog` render loading, empty, error, denied, stale, offline, and success states, hide import for viewers, and poll job status every 2 s (FR-F010-16, NFR-F010-03).
- **SR-S020-08:** A 100,000-row import completes in under 10 minutes and a 100,000-row CSV export in under 60 s on the fixture generator (NFR-F010-01).

## Surfaces

- Infrastructure/container: none beyond S019
- Rust service/API: `crates/domain/src/dataio/{import/chunker.rs, import/commit.rs, export/service.rs, export/csv_writer.rs, export/xlsx_writer.rs, export/pdf_writer.rs, export/permission_filter.rs, fixtures.rs}`; `services/api/src/dataio/{handlers_export.rs, handlers_import_commit.rs}`; `services/worker/src/dataio/{import_job.rs, export_job.rs, expiry_sweep.rs}`
- Data/migration: none new; uses tables from S019
- React/UI: `apps/web/src/features/dataio/{SearchCommandPalette.tsx, SearchResultsPage.tsx, SearchResultGroup.tsx, ImportWizard.tsx, ImportUploadStep.tsx, ImportMappingStep.tsx, ImportPreviewTable.tsx, ImportReportPanel.tsx, ImportStatusPanel.tsx, ExportDialog.tsx, ExportStatusToast.tsx, api.ts, hooks.ts, routes.ts}`
- Mocks/fixtures: 100,000-row CSV generator with fixed seed; worker kill switch between chunks; MSW handlers for component tests; Playwright against a seeded tenant with MinIO

## TDD harness

- Test path: `testing/features/F010/{api,frontend,e2e,accessibility,performance}/`
- Feature flag: `F010_FEATURE`
- Targeted command: `cargo xtask test-feature F010`
- Full command: `cargo xtask test-all`
- First failing tests: `import_commit_writes_chunks_with_idempotency_keys`, `import_resumes_after_worker_kill_without_duplicates`, `import_update_strategy_patches_matched_rows`, `import_cancel_stops_after_current_chunk`, `export_excludes_denied_columns`, `export_download_requires_requester_or_admin`, `import_wizard_dry_run_then_commit`, `import_100k_rows_under_10_minutes`

## Exit criteria

- [ ] Requirement tests SR-S020-01 through SR-S020-08 written first and failing
- [ ] Tasks T039 and T040 complete; UI wired to real API through generated client
- [ ] Unit, API, React, E2E, accessibility, permission, and performance tests pass
- [ ] Production call path named: `services/worker/src/dataio/import_job.rs` and `export_job.rs` registered in `services/worker/src/jobs.rs`; `apps/web/src/features/dataio/ImportWizard.tsx` mounted at `/w/:workspaceId/sheets/:sheetId/import`
- [ ] Handoff evidence recorded in the F010 ticket
