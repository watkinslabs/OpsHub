# F025 frontend cases

File: `testing/features/F025/frontend/{DrillPanel.test.tsx,DrillFooter.test.tsx,ExportDialog.test.tsx,ExportCenterPage.test.tsx,ExportRow.test.tsx}`. Vitest with MSW. Flag `F025_FEATURE`.

- `lists_sources_with_open_row_links` — FR-F025-01: each source renders alias, sheet name, and an `Open row` link to the deep link.
- `denied_source_renders_no_access_without_link` — FR-F025-03: `access: denied` renders "No access" text plus a labelled `Lock` icon and no link.
- `footer_states_hidden_row_count_for_owner_policy` — FR-F025-03: footer reads the total, returned count, and "1 row counted but not visible".
- `expired_snapshot_offers_reload` — FR-F025-02: 409 `snapshot_expired` renders "This snapshot has been replaced" with `Reload` targeting the current snapshot.
- `load_more_pages_group_rows` — FR-F025-02: `Load more` requests the next cursor and appends rows.
- `export_dialog_requires_page_setup_for_pdf` — FR-F025-05: choosing `pdf` reveals page size and orientation and blocks submit until both are set.
- `disables_submit_without_exporter_role` — FR-F025-05: an actor lacking `resource-exporter` sees a disabled `Export` with a tooltip naming the role.
- `sends_idempotency_key_once_per_submit` — FR-F025-12: double-click issues one request carrying a single `Idempotency-Key`.
- `column_picker_caps_at_two_hundred` — FR-F025-11: selecting a 201st column is blocked with the cap message.
- `shows_progress_then_download_link` — FR-F025-13: polling `queued` to `running` to `completed` shows the progress bar and then `Download` with size and page count.
- `failed_row_shows_error_code_and_retry` — FR-F025-12: `limit_exceeded` renders its sentence, the `correlation_id`, and `Retry`.
- `partial_export_shows_badge` — FR-F025-06: `partial: true` renders the badge explaining that some widgets were not available.
- `expired_row_hides_download` — FR-F025-08: `expired` replaces `Download` with "Link expired" and a re-export action.

Evidence: Vitest JUnit under `testing/evidence/F025/frontend/`.
