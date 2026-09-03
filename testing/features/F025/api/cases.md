# F025 api cases

File: `testing/features/F025/api/{drill_tests.rs,export_tests.rs,download_tests.rs,render_tests.rs,permission_tests.rs,scope_bytes_tests.rs}`. Flag `F025_FEATURE`.

- `drill_row_returns_sources_with_deep_links` — FR-F025-01: snapshot row → Projects and Risks sources with `source_row_id` and `/w/{workspace}/sheets/{sheet}?row=` links.
- `drill_row_unknown_id_returns_not_found` — FR-F025-01: row absent from the latest snapshot → 404 `not_found`.
- `drill_group_key_pages_contributing_rows` — FR-F025-02: 7-row group key returns 5 then 2 rows by cursor with `total` 7.
- `drill_group_tampered_key_rejected` — FR-F025-02: flipped tag byte → 400 `invalid` and no snapshot read.
- `drill_expired_snapshot_returns_conflict` — FR-F025-02: key pinned to a rotated-out snapshot → 409 with `reason: "snapshot_expired"` and the current `snapshot_id`.
- `drill_denies_restricted_sheet_without_query` — FR-F025-03: viewer without read on Risks → `access: denied`, no cells, and the query log shows no Risks row query.
- `drill_strips_hidden_columns` — FR-F025-03: `Budget.margin` absent from `cells` and listed in `hidden_columns`.
- `drill_owner_policy_reports_hidden_row_count` — FR-F025-03: owner-policy report → `aggregate_scope: "owner"` and `hidden_row_count` 1.
- `drill_publishes_opened_event_and_audit` — FR-F025-04: outbox holds `drill-through.opened.v1` with `denied_count`; audit holds `report.drill-through`.
- `create_report_export_returns_queued_job` — FR-F025-05: 202 with `export_id`, `expires_at`, `queued` row carrying `scope_key`, `report-export.requested.v1` published.
- `pdf_without_page_setup_rejected` — FR-F025-05: `format: pdf` with no `page` → 400 `invalid` naming `page`; `page` with `csv` → 400.
- `duplicate_idempotency_key_returns_same_export` — FR-F025-12: second POST with the same key → the first `export_id` and one row.
- `dashboard_pdf_renders_denied_widget_as_no_access` — FR-F025-06: widget resolving `denied` renders a title-only tile and no payload text in the PDF.
- `dashboard_export_refresh_waits_then_marks_partial` — FR-F025-06: a widget still `computing` after the wait → "Not available" and `partial: true`.
- `render_writes_checksum_and_moves_temp_object` — FR-F025-09: temporary key absent after success, `storage_key`, `checksum`, `byte_size`, `row_count` recorded, `report-export.completed.v1` published.
- `render_reports_progress_during_stream` — FR-F025-09: 50,000-row CSV records at least 5 increasing `progress_pct` values.
- `csv_bytes_exclude_hidden_column` — NFR-F025-02: downloaded CSV has no `Budget.margin` header and none of its values.
- `xlsx_types_number_and_date_cells` — FR-F025-10: numeric and date columns are typed cells, header row frozen, group headers present when requested.
- `pdf_text_excludes_restricted_rows` — NFR-F025-02: extracted PDF text has no Risks row the requester cannot read; footer names report, exporter, snapshot time, and page `n of m`.
- `render_scope_key_mismatch_aborts_job` — NFR-F025-02: stored `scope_key` differing from the rebuilt scope → job aborted, status `failed` with `internal`, no object written.
- `row_cap_fails_with_limit_exceeded` — FR-F025-11: 250,001-row report → `failed` with `error.code: "limit_exceeded"` naming the cap.
- `hourly_rate_limit_returns_retry_after` — FR-F025-11: 21st request in an hour → 429 `rate_limited` with `Retry-After`; 4th concurrent render → 429.
- `render_timeout_retries_three_times_then_dead_letters` — FR-F025-12: stub stalling past 180 s → 3 retries, `failed` with `render_timeout`, `report-export.failed.v1`, dead letter.
- `download_before_completion_returns_conflict` — FR-F025-08: `running` export → 409 with the current status.
- `download_after_expiry_returns_not_found` — FR-F025-08: clock past `expires_at` → 404 and no signed URL minted.
- `download_signs_url_for_fifteen_minutes_and_audits` — FR-F025-08: 302 to a URL expiring in 900 s and a `report-export.download` audit row.
- `viewer_without_exporter_role_denied_on_both_creators` — FR-F025-05, FR-F025-06: report-viewer without `resource-exporter` → 403 on both POSTs and no row created.
- `share_link_guest_may_drill_but_not_export` — NFR-F025-02: guest drill succeeds under guest scope; guest export → 403 `denied`.
- `non_requester_download_denied_and_audited` — FR-F025-08: another member → 403; `tenant-admin` → 302.
- `foreign_tenant_export_status_not_found` — NFR-F025-02: tenant B export id → 404 on status and download; tenant B report → 404 on drill.
- `expiry_sweep_deletes_object_and_marks_expired` — FR-F025-12: nightly sweep removes the object, sets `expired`, writes `report-export.expire`.

Evidence: JUnit output, outbox dumps, and downloaded artifacts under `testing/evidence/F025/api/`.
