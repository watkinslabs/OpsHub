---
id: T098
type: task
status: planned
parent_epic: E005
parent_feature: F025
parent_story: S049
depends_on: [S049]
owned_paths: [crates/domain/src/report_exports/**, services/worker/src/report_exports/**, services/api/src/report_exports/**, testing/features/F025/api/**, testing/features/F025/performance/**]
feature_flag: F025_FEATURE
branch: t098-export-worker
started_at: null
finished_at: null
---

# T098 — Export worker

## Identity

- Parent story: `S049` Source drill-through
- Owner: platform
- Branch: `t098-export-worker`
- Decision references: `docs/architecture-decisions.md` sections 4, 7, 9; `docs/capability-contracts.md` row F025

## Objective

Implement export creation, the render worker and its four renderers, progress and retry handling, signed downloads with audit, and the nightly expiry sweep.

## Specification

- Owned paths: `crates/domain/src/report_exports/{export.rs, options.rs, limits.rs, render/{mod.rs, csv.rs, xlsx.rs, pdf.rs, png.rs}}`, `services/worker/src/report_exports/{mod.rs, render_job.rs, browser.rs, expiry_job.rs}`, `services/api/src/report_exports/{handlers_export.rs, handlers_download.rs}`
- Contract/input: `POST /api/v1/reports/{id}/exports` `{ format: csv|xlsx|pdf, snapshot_id?, columns?, filter?, include_group_headers?, include_aggregates?, timezone, locale?, page? }`; `POST /api/v1/dashboards/{id}/exports` `{ format: pdf|png, widget_ids?, timezone, page?, refresh }`; `GET /api/v1/report-exports/{id}`; `GET /api/v1/report-exports/{id}/download`; job subject `report-exports.render` carrying `{ export_id, tenant_id, run_id }`.
- Output/behavior: creation validates format per source kind, requires `resource-exporter` plus `read` and an `Idempotency-Key`, stores `scope_key`, returns `202 { export_id, status, expires_at }` under 500 ms, publishes `report-export.requested.v1`, and returns the existing row for a repeated key; `render_job.rs` claims a `queued` row using the `status, created_at` partial index, sets `running` with `run_id`, rebuilds the scope and aborts on `scope_key` mismatch, dispatches to the renderer, writes bytes to `{tenant_id}/report-exports/{export_id}/.tmp-{run_id}` and moves to `{slug}.{ext}` on success, records `storage_key`, `checksum`, `byte_size`, `row_count`, `page_count`, `partial`, `expires_at` (completion plus 7 days), sets `completed`, and publishes `report-export.completed.v1`; `progress_pct` is written every 5 s or 10,000 rows; timeouts are 120 s for `csv` and `xlsx` and 180 s for `pdf` and `png`, with 3 retries and a dead letter plus `report-export.failed.v1` and a typed `error.code` on the fourth attempt; limits from FR-F025-11 are checked at creation and again while streaming; `browser.rs` drives the headless Chromium pool against the internal print route with a short-lived service token bound to `scope_key`; download signs a 15-minute URL, returns `409` while pending, `404` when failed or expired, `403` for a non-requester who is not `tenant-admin`, and writes the `report-export.download` audit row; `expiry_job.rs` runs nightly, deletes objects past `expires_at`, sets `expired`, and writes `report-export.expire`.
- Dependencies: T097 schema and domain module; F021 `read_rows` paging for CSV and XLSX; F023 widget cache and refresh for dashboard renders; F010 object-storage and signed-download conventions; F049 formatter for locale and timezone output; F004 job runtime, dead letters, and outbox.
- Feature flag: `F025_FEATURE` gates the export routes and the render and expiry jobs.

## TDD

- Failing test first: `testing/features/F025/api/export_tests.rs::create_report_export_returns_queued_job`, `::duplicate_idempotency_key_returns_same_export`, `::pdf_without_page_setup_rejected`, `::csv_omits_hidden_column_bytes`, `::xlsx_types_number_and_date_cells`, `::dashboard_pdf_renders_denied_widget_as_no_access`, `::render_scope_key_mismatch_aborts_job`, `::row_cap_fails_with_limit_exceeded`, `::render_timeout_retries_three_times_then_dead_letters`, `::download_before_completion_returns_conflict`, `::download_after_expiry_returns_not_found`, `::non_requester_download_denied_and_audited`, `::expiry_sweep_deletes_object_and_marks_expired`; `testing/features/F025/performance/export_bench.rs::csv_250k_rows_under_120s`, `::dashboard_pdf_twelve_widgets_under_45s`
- Targeted command: `cargo xtask test-feature F025`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/report_exports.rs`; JetStream stub for `report-exports.render`; MinIO prefix per worker with an injectable failing sink; deterministic PDF and PNG stub asserting the print route URL and service token scope; fixed clock and idempotency keys

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Export routes and both jobs registered behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S049
- [ ] `finished_at` recorded
