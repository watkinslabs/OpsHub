---
id: S050
type: story
status: planned
parent_epic: E005
parent_feature: F025
depends_on: [F025]
owned_paths: [crates/domain/src/report_exports/**, services/api/src/report_exports/**, services/worker/src/report_exports/**, apps/web/src/features/report-exports/**, testing/features/F025/frontend/**, testing/features/F025/e2e/**, testing/features/F025/accessibility/**]
feature_flag: F025_FEATURE
branch: s050-pdf-csv-export
started_at: null
finished_at: null
---

# S050 — PDF/CSV export

## Identity

- Parent feature: `F025` Export/drill-through
- Owner: platform
- Branch: `s050-pdf-csv-export`
- Decision references: `docs/architecture-decisions.md` sections 2, 4, 7, 9; `docs/capability-contracts.md` row F025

## Vertical slice

As a report exporter, I want to send a report to CSV, XLSX, or PDF and a dashboard to PDF or PNG, watch the job progress, and download a file that contains exactly what I am allowed to read and expires afterwards, so that a shared export is safe to hand to someone else and its origin is on record.

## Requirements

- **SR-S050-01:** `POST /api/v1/reports/{id}/exports` validates format, columns, timezone, and page setup, requires `resource-exporter` plus `read` and an `Idempotency-Key`, creates a `queued` row with the caller's `scope_key`, returns `202 { export_id, status, expires_at }` under 500 ms, and publishes `report-export.requested.v1`; a repeat of the same key returns the existing `export_id` (covers FR-F025-05, FR-F025-12).
- **SR-S050-02:** `POST /api/v1/dashboards/{id}/exports` renders the caller's view of the dashboard, optionally refreshing first and waiting up to 120 s for widgets to reach `fresh`, rendering `denied` widgets as a title-only "No access" tile and still-`computing` widgets as "Not available" with `partial: true` (FR-F025-06).
- **SR-S050-03:** The render job streams CSV with a BOM and RFC 4180 quoting, XLSX with a frozen typed header, PDF with repeated headers, group headers, optional aggregate rows, and a footer naming report, exporter, snapshot time, and page `n of m`, and PNG at 1440×1024 at device pixel ratio 2, updating `progress_pct` every 5 s or 10,000 rows and publishing `report-export.completed.v1` (FR-F025-09, FR-F025-10).
- **SR-S050-04:** Limits are enforced: 250,000 rows for CSV and XLSX, 20,000 rows or 200 pages for PDF, 200 MB per output, 200 columns, 20 requests per actor per hour, and 3 concurrent renders per tenant, failing with `limit_exceeded` or returning `429 rate_limited` with `Retry-After` (FR-F025-11).
- **SR-S050-05:** `GET /api/v1/report-exports/{id}` reports status, progress, counts, size, `partial`, and typed errors, and `GET /api/v1/report-exports/{id}/download` returns a 15-minute signed `302` when `completed`, `409 conflict` while `queued` or `running`, `404 not_found` when failed or past `expires_at`, `403 denied` for anyone but the requester or a `tenant-admin`, and writes the `report-export.download` audit row (FR-F025-07, FR-F025-08).
- **SR-S050-06:** Exported bytes are produced under the requester's `scope_key`, so hidden columns and restricted source rows never reach any format, and a `scope_key` mismatch between the stored row and the render context aborts the job (NFR-F025-02).
- **SR-S050-07:** The web app ships `DrillPanel`, `ExportDialog`, and the export center at `/exports` with loading, empty, error, denied, and success states, 2 s status polling that stops at a terminal status, a completion toast linking to the download, and `Retry` on failed rows (FR-F025-13).
- **SR-S050-08:** Panel, dialog, and export center pass axe with zero serious or critical violations, trap and restore focus, announce progress through a polite live region, and mark denied rows with text plus a labelled icon; generated PDFs carry a document title, table header tagging, and reading order (NFR-F025-03).

## Surfaces

- Rust service/API: `crates/domain/src/report_exports/{export.rs, options.rs, limits.rs, render/{mod.rs, csv.rs, xlsx.rs, pdf.rs, png.rs}}`; `services/api/src/report_exports/{handlers_export.rs, handlers_download.rs, dto.rs}`
- Worker: `services/worker/src/report_exports/render_job.rs` renderer dispatch, progress writes, temporary-key upload and move, retry and dead-letter handling
- Object storage: `{tenant_id}/report-exports/{export_id}/{slug}.{ext}` with server-side encryption and 15-minute signed URLs, following the F010 download conventions
- React/UI: `apps/web/src/features/report-exports/{DrillPanel.tsx, DrillSourceList.tsx, DrillFooter.tsx, ExportDialog.tsx, ExportFormatPicker.tsx, ExportColumnPicker.tsx, PageSetupFields.tsx, ExportCenterPage.tsx, ExportRow.tsx, ExportProgressBar.tsx, api.ts, hooks.ts, routes.ts}`
- Mocks/fixtures: `testing/fixtures/report_exports.rs`; MinIO prefix per worker with an injectable failing sink; deterministic PDF and PNG render stub asserting the print route and service token scope

## TDD harness

- Test path: `testing/features/F025/{api,frontend,e2e,accessibility,performance}/`
- Feature flag: `F025_FEATURE`
- Targeted command: `cargo xtask test-feature F025`
- Full command: `cargo xtask test-all`
- First failing tests: `create_report_export_returns_queued_job`, `duplicate_idempotency_key_returns_same_export`, `csv_omits_hidden_column_bytes`, `dashboard_pdf_renders_denied_widget_as_no_access`, `download_before_completion_returns_conflict`, `download_after_expiry_returns_not_found`, `viewer_without_exporter_role_denied`, `export_dialog_requires_page_setup_for_pdf`

## Exit criteria

- [ ] Requirement tests SR-S050-01 through SR-S050-08 written first and failing
- [ ] Tasks T099 and T100 complete and wired through the web router and the export routes
- [ ] API, React, E2E, permission-negative, accessibility, and performance tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/report_exports/handlers_export.rs` and `handlers_download.rs` mounted through `services/api/src/router.rs`; `apps/web/src/features/report-exports/routes.ts` registered in `apps/web/src/app/routes.tsx` and the report and dashboard toolbars
- [ ] Handoff evidence recorded in the F025 ticket
