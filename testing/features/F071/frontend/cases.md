# F071 frontend cases

File: `testing/features/F071/frontend/{MigrationListPage.test.tsx,MigrationUploadPanel.test.tsx,ColumnReviewTable.test.tsx,TypeOverrideSelect.test.tsx,IssuePanel.test.tsx,CommitConfirmDialog.test.tsx,CommitProgressPanel.test.tsx}`. Vitest with MSW. Flag `F071_FEATURE`.

- `review_table_lists_inferred_type_and_confidence` — FR-F071-08: each row shows source header, 5 sample values, inferred type, and the confidence chip with its numeric value.
- `confidence_is_text_and_icon_not_colour_alone` — NFR-F071-03: `High`, `Medium`, and `Low` render as text with a labelled icon; removing colour leaves the meaning intact.
- `type_override_offers_only_the_twelve_types` — FR-F071-09: the select lists exactly the twelve F007 types and reveals per-type settings fields for `currency`, `select`, and `datetime`.
- `override_stays_local_until_commit` — FR-F071-09: changing three types issues no request until `Create everything` is pressed, then sends all three in one body.
- `ambiguous_column_flagged_until_decided` — FR-F071-06: an `ambiguous` row shows a warning icon with a title and keeps commit disabled.
- `issues_grouped_by_severity_with_counts` — FR-F071-15: `Blocking`, `Warning`, and `Information` headings carry counts and each issue shows tab, source reference, and message.
- `waiving_last_blocking_issue_enables_commit` — FR-F071-03: waiving the final blocking issue enables `Create everything`.
- `dialog_states_tabs_rows_folder_and_accepted_ambiguities` — FR-F071-09: the confirm dialog names 12 tabs, 4,310 rows, folder `Delivery`, and 2 accepted ambiguities.
- `override_error_returns_message_to_offending_row` — FR-F071-09: a `400` with `field_errors.column_overrides` attaches the message to those rows and scrolls to the first.
- `conflict_renders_already_committing_surface` — FR-F071-09: a `409` shows that this migration is already being created, with no retry button.
- `progress_panel_announces_each_committed_tab` — FR-F071-10, NFR-F071-03: each tab moving to `committed` updates the polite live region with its name and row count.
- `failed_tab_states_its_sheet_was_removed` — FR-F071-11: a `failed` tab shows its reason and states that its sheet was removed.
- `completion_links_to_first_created_sheet` — FR-F071-16: `completed` renders a link built from `first_sheet_id`.
- `upload_panel_rejects_unsupported_container_before_request` — FR-F071-02: choosing a `.docx` shows the unsupported-source message without calling the API.
- `viewer_sees_denied_surface_on_migration_route` — FR-F071-16: a viewer loading the review route sees the denied surface and no entry point in the workspace tree.
- `error_banner_shows_correlation_id` — NFR-F071-04: a `500` renders the banner with `correlation_id` and retry.
- `offline_disables_upload_and_commit` — FR-F071-16: the offline badge disables both actions while the preview stays readable.
- `stale_preview_refetches_on_version_change` — FR-F071-08: a changed `version` shows the stale banner and refetches.

Evidence: Vitest JUnit under `testing/evidence/F071/frontend/`.
