---
id: T039
type: task
status: planned
parent_epic: E002
parent_feature: F010
parent_story: S020
depends_on: [T038]
owned_paths: [crates/domain/src/dataio/**, services/api/src/dataio/**, services/worker/src/dataio/**, apps/web/src/features/dataio/**, testing/features/F010/frontend/**, testing/features/F010/e2e/**, testing/features/F010/accessibility/**]
feature_flag: F010_FEATURE
branch: t039-export-worker
started_at: null
finished_at: null
---

## Decision references

- Architecture: `docs/architecture-decisions.md` sections 2, 3, 4, 5, 6, 7
- Capability contract: `docs/capability-contracts.md` row F010

# T039 — Export worker

## Identity

- Parent story: `S020` CSV/XLSX jobs
- Owner: platform
- Branch: `t039-export-worker`
- Decision references: `docs/architecture-decisions.md` sections 2–7; `docs/capability-contracts.md` row F010

## Objective

Implement permission-filtered CSV, XLSX, and PDF export jobs with signed downloads and expiry, and build the search palette, results page, import wizard, status panel, and export dialog wired to the real API.

## Specification

- Owned paths: `crates/domain/src/dataio/export/{mod.rs, service.rs, csv_writer.rs, xlsx_writer.rs, pdf_writer.rs, permission_filter.rs}`, `services/api/src/dataio/handlers_export.rs`, `services/worker/src/dataio/{export_job.rs, expiry_sweep.rs}`, `apps/web/src/features/dataio/{SearchCommandPalette.tsx, SearchResultsPage.tsx, SearchResultGroup.tsx, ImportWizard.tsx, ImportUploadStep.tsx, ImportMappingStep.tsx, ImportPreviewTable.tsx, ImportReportPanel.tsx, ImportStatusPanel.tsx, ExportDialog.tsx, ExportStatusToast.tsx, api.ts, hooks.ts, routes.ts}`
- Contract/input: `CreateExportRequest { source_kind: sheet|view, source_id, format: csv|xlsx|pdf, filter?, columns? }`; worker payload `ExportJobMessage { export_id, tenant_id, requested_by, correlation_id }`; generated `DataIoApi` client; route params `workspaceId`, `sheetId`; palette shortcut `Ctrl+K`.
- Output/behavior: `POST /api/v1/exports` validates the requested columns against readable columns, writes them as ordered `export_job_columns` rows and the filter as ordered `export_job_filters` rows through `ExportJobRepository`, and returns `202 { job_id }`; the worker streams rows through `permission_filter` (drops denied columns and unreadable rows for `requested_by`), writes CSV (UTF-8 with BOM, RFC 4180 quoting), XLSX (streamed sheet with typed cells and frozen header), or PDF (paginated table, repeated header row, footer with sheet name, exporter, timestamp, horizontal page groups for wide sheets), uploads to `tenant_id/exports/<job_id>.<ext>`, records `storage_key`, `checksum`, `row_count`, `expires_at = now + 7 days`, emits `export.completed.v1`; `GET /api/v1/exports/{id}` returns status; `GET /api/v1/exports/{id}/download` returns `302` to a 15-minute signed URL for the requester or a tenant-admin, `409 conflict` while not completed, `404 not_found` after expiry, and writes an `export.download` audit event; `expiry_sweep` deletes expired objects hourly. UI: palette with grouped results and highlighted snippets, results page with kind filters and cursor paging, wizard steps upload, map, preview, dry run, commit with a report panel and 2 s status polling, export dialog with format and column choices and a toast linking to download; states loading, empty, error with `correlation_id`, denied, stale, offline, success; import entry hidden for viewers; telemetry events from ticket section 4.
- Dependencies: T038 import routes and job lifecycle; `ExportJobRepository` in `crates/persistence/src/dataio/`, which holds every statement the export path issues; F004 object storage client and signed URL helper; F013 view filter read for `source_kind = view`; F005 workspace shell for navigation.
- Feature flag: `F010_FEATURE` read through the flag hook; routes and job handlers are not registered when off.

## TDD

- Failing test first: `testing/features/F010/frontend/SearchCommandPalette.test.tsx::opens_with_ctrl_k_and_groups_results`, `ImportWizard.test.tsx::dry_run_report_then_commit_polls_status`, `::hides_import_for_viewer`, `ExportDialog.test.tsx::requests_export_and_shows_download_toast`; `testing/features/F010/e2e/dataio.spec.ts::search_and_open_row`, `::import_wizard_dry_run_then_commit`, `::export_pdf_and_download`; `testing/features/F010/accessibility/dataio.a11y.spec.ts::palette_wizard_dialog_have_no_serious_axe_violations`; `testing/features/F010/api/export_tests.rs::export_excludes_denied_columns`, `::export_download_requires_requester_or_admin`, `::export_download_conflict_while_running`, `::export_expired_not_found`
- Targeted command: `cargo xtask test-feature F010`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: MSW handlers from the seeded `Plan` sheet and job fixtures; Playwright against the real API with MinIO; PDF output checked with a text-extraction assertion on header repeat

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Component, E2E, accessibility, and export API lanes pass
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S020
- [ ] `finished_at` recorded
