---
id: S049
type: story
status: planned
parent_epic: E005
parent_feature: F025
depends_on: [F025]
owned_paths: [crates/domain/src/report_exports/**, crates/persistence/src/report_exports/**, services/api/src/report_exports/**, services/worker/src/report_exports/**, services/api/migrations/*_report_exports_*.sql, testing/features/F025/api/**, testing/features/F025/database/**, testing/features/F025/performance/**]
feature_flag: F025_FEATURE
branch: s049-source-drill-through
started_at: null
finished_at: null
---

# S049 — Source drill-through

## Identity

- Parent feature: `F025` Export/drill-through
- Owner: platform
- Branch: `s049-source-drill-through`
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 6, 7; `docs/capability-contracts.md` row F025

## Vertical slice

As a report viewer, I want to open the source records behind a report group, a KPI tile, or a chart point and see honestly which of them I am not allowed to open, so that a dashboard number can be checked without leaving the review or leaking rows the permission model hides.

## Requirements

- **SR-S049-01:** `GET /api/v1/reports/{id}/drill/{row_id}` resolves a snapshot `row_id` to `DrillResult` with one entry per report source alias carrying `sheet_id`, `source_row_id`, `access`, `deep_link`, and `cells`; an unknown row returns `404 not_found` and `?snapshot_id=` pins a retained snapshot (covers FR-F025-01).
- **SR-S049-02:** The same route accepts `row_id = group:<base64url>` encoded by `DrillKey` from `widget_id`, dimension values, filters, and `snapshot_id`, pages contributing rows by `cursor` and `limit` 1..200 with `total` capped at 5,000, rejects a tampered tag with `400 invalid`, and returns `409 conflict` with `reason: "snapshot_expired"` and the current `snapshot_id` when the pinned snapshot is gone (FR-F025-02).
- **SR-S049-03:** Resolution runs under the caller's F021 `ViewerScope`: unreadable source sheets are marked `denied` with no cells and no deep link and listed in `restricted_sources`, hidden columns are stripped and listed in `hidden_columns`, and `meta.aggregate_scope` and `meta.hidden_row_count` are returned when the report's `aggregate_policy` is `owner` (FR-F025-03, NFR-F025-02).
- **SR-S049-04:** Every drill publishes `drill-through.opened.v1` with `report_id`, `snapshot_id`, `target_kind`, `widget_id`, `source_count`, `denied_count`, `returned_row_count`, and `scope_key`, and writes the `report.drill-through` audit row (FR-F025-04).
- **SR-S049-05:** The migration creates `report_exports` with its typed option and error columns, plus the ordered child tables `report_export_columns` and `report_export_widgets`, with the check constraints and the claim, sweep, and `error_code` indexes from ticket section 4, so the export story writes against a stable schema (FR-F025-09, FR-F025-12).
- **SR-S049-06:** `ReportExportRepository` in `crates/persistence/src/report_exports/` owns all three tables and exposes `create_if_absent`, `get_for_actor`, `page_for_actor`, `claim_next_queued`, `update_progress`, `complete`, `fail`, `claim_expired`, `count_running_for_tenant`, and `count_requests_since`; the `report-exports.render` worker consumer, Chromium pool wrapper, and nightly expiry sweep are registered behind `F025_FEATURE` with the 120 s and 180 s render timeouts, 3 retries, and dead letter on the fourth failure, and reach the tables only through those named queries — no SQL string, `sqlx::query*` call, or connection lives in the domain, API, or worker module (FR-F025-09, FR-F025-12, NFR-F025-04).
- **SR-S049-07:** Share-link actors from F036 may drill under their guest scope but every export route returns `403 denied`; foreign-tenant report and export ids return `404 not_found` on drill, status, and download (NFR-F025-02).
- **SR-S049-08:** Row drill responds under 400 ms p95 and group drill under 900 ms p95 over the 100,000-row "Portfolio status" snapshot, with source rows fetched through one batched F006/F007 repository read per readable sheet and no read issued for denied sheets (NFR-F025-01).

## Surfaces

- Rust service/API: `crates/domain/src/report_exports/{mod.rs, drill.rs, drill_key.rs, job.rs, errors.rs, service.rs}` depending on repository traits only; `services/api/src/report_exports/{mod.rs, routes.rs, handlers_drill.rs, dto.rs}`
- Persistence: `crates/persistence/src/report_exports/{mod.rs, report_export_repository.rs}` holding every SQL statement for `report_exports`, `report_export_columns`, and `report_export_widgets`, with creation running as one `UnitOfWork` over the row, its child rows, and the outbox event
- Worker: `services/worker/src/report_exports/{mod.rs, render_job.rs, browser.rs, expiry_job.rs}` registered behind the flag, calling `ReportExportRepository` for every claim, progress, completion, failure, and expiry write
- Data/migration: `services/api/migrations/<ts>_report_exports_create_tables.sql` and `.down.sql` creating `report_exports`, `report_export_columns`, and `report_export_widgets` with the checks and indexes from ticket section 4, the down migration dropping all three
- Events/audit: `drill-through.opened.v1` through the F004 outbox; audit rows `report.drill-through`
- Mocks/fixtures: `testing/fixtures/report_exports.rs` (100,000-row snapshot, restricted "Risks" sheet, hidden `Budget.margin` column, share-link guest, owner-policy report variant)

## TDD harness

- Test path: `testing/features/F025/{api,database,performance}/`
- Feature flag: `F025_FEATURE`
- Targeted command: `cargo xtask test-feature F025`
- Full command: `cargo xtask test-all`
- First failing tests: `drill_row_returns_sources_with_deep_links`, `drill_group_key_pages_contributing_rows`, `drill_group_tampered_key_rejected`, `drill_expired_snapshot_returns_conflict`, `drill_denies_restricted_sheet_without_query`, `drill_owner_policy_reports_hidden_row_count`, `drill_publishes_opened_event_and_audit`, `share_link_guest_may_drill_but_not_export`

## Exit criteria

- [ ] Requirement tests SR-S049-01 through SR-S049-08 written first and failing
- [ ] Tasks T097 and T098 complete and wired through `services/api` router and `services/worker` registry
- [ ] Unit, API, database, permission, and performance tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/report_exports/routes.rs` mounted in `services/api/src/router.rs` (`/api/v1/reports/{id}/drill`, `/api/v1/report-exports`); `services/worker/src/report_exports/render_job.rs` and `expiry_job.rs` registered in `services/worker/src/registry.rs`
- [ ] Handoff evidence recorded in the F025 ticket
