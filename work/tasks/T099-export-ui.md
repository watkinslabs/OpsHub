---
id: T099
type: task
status: planned
parent_epic: E005
parent_feature: F025
parent_story: S050
depends_on: [S050]
owned_paths: [apps/web/src/features/report-exports/**, testing/features/F025/frontend/**, testing/features/F025/e2e/**]
feature_flag: F025_FEATURE
branch: t099-export-ui
started_at: null
finished_at: null
---

# T099 — Export UI

## Identity

- Parent story: `S050` PDF/CSV export
- Owner: platform
- Branch: `t099-export-ui`
- Decision references: `docs/architecture-decisions.md` sections 3, 6; `docs/capability-contracts.md` row F025

## Objective

Build the drill panel, the export dialog, and the export center, wire them to the drill and export routes, and cover every state including denied, partial, failed, and expired.

## Specification

- Owned paths: `apps/web/src/features/report-exports/{DrillPanel.tsx, DrillSourceList.tsx, DrillDeniedRow.tsx, DrillFooter.tsx, ExportDialog.tsx, ExportFormatPicker.tsx, ExportColumnPicker.tsx, PageSetupFields.tsx, ExportCenterPage.tsx, ExportRow.tsx, ExportProgressBar.tsx, useDrillTarget.ts, api.ts, hooks.ts, routes.ts}`
- Contract/input: generated `ReportExportsApi` with `drill`, `createReportExport`, `createDashboardExport`, `getExport`, `downloadExport`; the drill panel is opened with a `DrillTarget` built from a report group row, a chart point, or a KPI tile and mirrored into the `drill` query parameter so a reload restores it.
- Output/behavior: `DrillPanel` is a focus-trapped side sheet listing sources with `Open row` deep links, `DrillDeniedRow` showing "No access" as text plus a labelled `Lock` icon, `DrillFooter` stating `total`, `returned`, and `hidden_row_count` with the owner-aggregate note, cursor paging with `Load more`, empty state "No records you can open", and `409 snapshot_expired` shown as "This snapshot has been replaced" with `Reload`; `ExportDialog` picks format per source kind, columns (max 200), timezone, locale, and page setup shown only for `pdf`, disables submit for an actor without `resource-exporter` with a tooltip naming the role, sends an `Idempotency-Key` per submission, and renders `field_errors` inline; `ExportCenterPage` at `/exports` and `/exports/:exportId` lists this actor's exports with format, status, determinate progress from `progress_pct`, `partial` badge, `Download`, and `Retry`, polling `['export', id]` every 2 s and stopping at `completed`, `failed`, or `expired`; a completion toast links to the download; error rows show `error.code` and `correlation_id`; telemetry events `drill_opened`, `drill_row_opened`, `export_requested`, `export_completed`, `export_downloaded`, `export_retried`.
- Dependencies: T097 drill route and T098 export routes; F023 dashboard and F021 report toolbars for the entry points; F024 chart point context menu for the chart entry; design tokens and Lucide icon set.
- Feature flag: `F025_FEATURE` hides the drill entry points, the export buttons, and the `/exports` route when off.

## TDD

- Failing test first: `testing/features/F025/frontend/DrillPanel.test.tsx::lists_sources_with_open_row_links`, `::denied_source_renders_no_access_without_link`, `::footer_states_hidden_row_count_for_owner_policy`, `::expired_snapshot_offers_reload`; `testing/features/F025/frontend/ExportDialog.test.tsx::export_dialog_requires_page_setup_for_pdf`, `::disables_submit_without_exporter_role`, `::sends_idempotency_key_once_per_submit`; `testing/features/F025/frontend/ExportRow.test.tsx::shows_progress_then_download_link`, `::failed_row_shows_error_code_and_retry`; `testing/features/F025/e2e/export_drill.spec.ts::drill_from_chart_point_to_source_rows`, `::export_report_csv_and_download`, `::export_dashboard_pdf_with_refresh`
- Targeted command: `cargo xtask test-feature F025`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: Vitest with MSW fixtures for drill row, drill group, denied source, queued/running/completed/failed/expired exports; Playwright against the seeded tenant with the deterministic render stub

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Routes registered in `apps/web/src/app/routes.tsx` and entry points added to the report and dashboard toolbars behind the flag
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S050
- [ ] `finished_at` recorded
