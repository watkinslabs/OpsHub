# F025 e2e cases

File: `testing/features/F025/e2e/export_drill.spec.ts`. Playwright against the seeded tenant with the deterministic render stub. Flag `F025_FEATURE`.

- `drill_from_chart_point_to_source_rows` — FR-F025-02, FR-F025-13: Dana opens "Weekly review", presses `Enter` on the bar "Dana", the panel lists 7 risk rows with their project source, and `Open row` lands on the sheet with the row selected.
- `drill_shows_denied_rows_for_restricted_viewer` — FR-F025-03: Lee drills the same point and sees "No access" rows and the footer note about rows counted but not visible.
- `export_report_csv_and_download` — FR-F025-05, FR-F025-08: Dana exports "Portfolio status" to CSV, the toast links to the download, and the saved file has no `Budget.margin` column.
- `export_dashboard_pdf_with_refresh` — FR-F025-06: Dana exports "Weekly review" to PDF with `Refresh first`, the export center shows 4 pages, and the denied widget appears as a title-only tile.
- `retry_failed_export_from_center` — FR-F025-12: a render forced to fail shows `render_timeout` with `Retry`; the retry completes and the row offers `Download`.
- `viewer_cannot_export_dashboard` — FR-F025-05: Lee sees the disabled `Export` button and a direct POST from the console returns the denied page state.

Evidence: Playwright traces, downloaded files, and render stub logs under `testing/evidence/F025/e2e/`.
