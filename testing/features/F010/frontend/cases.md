# F010 frontend cases

File: `testing/features/F010/frontend/{SearchCommandPalette.test.tsx,SearchResultsPage.test.tsx,ImportWizard.test.tsx,ImportStatusPanel.test.tsx,ExportDialog.test.tsx}`. Vitest with MSW. Flag `F010_FEATURE`.

- `opens_with_ctrl_k_and_groups_results` — FR-F010-16: `Ctrl+K` opens the palette; results grouped as Sheets, Rows, Comments, Attachments with highlighted snippets.
- `palette_enter_opens_row_and_emits_telemetry` — FR-F010-16: `Enter` on a row hit navigates to the grid URL and emits `search_result_opened`.
- `results_page_shows_empty_state` — FR-F010-16: zero hits render `No results for "zzz"` with kind filter hints.
- `results_page_shows_error_with_correlation_id` — NFR-F010-04: 500 response renders banner containing `correlation_id` and retry.
- `wizard_upload_rejects_oversize_file_locally` — FR-F010-05: 51 MB file blocked before upload with an inline message.
- `wizard_mapping_step_uses_detected_types` — FR-F010-06: preview response fills mapping selects with detected types and duplicate count.
- `dry_run_report_then_commit_polls_status` — FR-F010-07, FR-F010-08: dry run shows `980 valid, 20 invalid`; commit shows progress polled every 2 s until `completed`.
- `hides_import_for_viewer` — FR-F010-16: viewer role has no `Import from file` menu entry; direct route renders denied state.
- `status_panel_shows_cancel_and_failed_states` — FR-F010-11, FR-F010-12: `cancelled` shows kept row count; `failed` shows dead-letter reason.
- `requests_export_and_shows_download_toast` — FR-F010-13, FR-F010-15: choosing PDF queues job; toast appears with `Download` when `completed`.
- `export_dialog_lists_only_readable_columns` — FR-F010-14: denied `Salary` column absent from the column picker.
- `offline_disables_import_and_export` — FR-F010-16: `navigator.onLine=false` disables actions and shows offline badge; palette shows recent cached results.
- `stale_job_version_reconciles` — FR-F010-12: server `version` ahead of cached → panel refetches and shows the newer status.

Evidence: Vitest JUnit under `testing/evidence/F010/frontend/`.
