# F071 api cases

File: `testing/features/F071/api/{source_tests.rs,inference_tests.rs,analyze_tests.rs,plan_tests.rs,commit_tests.rs,negative_tests.rs}`. Flag `F071_FEATURE`.

- `detect_rejects_container_mismatched_to_source_kind` — FR-F071-02: `source_kind: airtable` with an `.xlsx` body → `400 invalid`, `field_errors.file_id = "unsupported_source"`.
- `macro_workbook_accepted_and_recorded_without_execution` — FR-F071-02: `.xlsm` fixture analyses normally, the macro project is never opened, one `macro_dropped` issue is written.
- `airtable_zip_reads_one_table_per_csv` — FR-F071-02: three CSVs → three `migration_sheets` rows named after their files.
- `zip_entry_escaping_root_rejected` — NFR-F071-02: an entry path leaving the extraction root aborts before any byte is written.
- `zip_expansion_limit_rejected_before_extraction` — FR-F071-03: uncompressed total past 500 MB → `field_errors.file_id = "expansion_limit"` with nothing extracted.
- `fifty_first_tab_rejected` — FR-F071-03: 51 tabs → `field_errors.file_id = "tab_limit"`.
- `row_cap_truncates_tab_with_blocking_issue` — FR-F071-03: a 120,000-row tab stages 100,000 rows and a blocking `row_cap_exceeded`; commit is refused until it is waived.
- `fourth_concurrent_migration_rate_limited` — FR-F071-03: three migrations in `analyzing` → the fourth returns `429 rate_limited` with `Retry-After`.
- `header_detection_falls_back_to_generated_names` — FR-F071-04: a tab whose first row is 40 % populated → `Column 1` upward and `no_header_row`.
- `proposed_name_deduplicated_against_folder` — FR-F071-04: destination already holds `Milestones` → proposed name `Milestones (2)`.
- `inference_assigns_twelve_types_with_confidence` — FR-F071-05: the twelve shaped columns each infer to their F007 type with confidence at or above 0.95.
- `sampler_caps_at_two_thousand_cells` — FR-F071-05, NFR-F071-01: a 100,000-row column reads 2,000 cells and no more.
- `ambiguous_number_duration_column_marked_ambiguous` — FR-F071-06: `1:30` values score above 0.80 as both → `duration` by precedence, `state: ambiguous`, `ambiguous_type` naming both.
- `low_confidence_column_falls_back_to_text_with_samples` — FR-F071-06: 0.72 best score → `text`, `ambiguous`, issue listing 5 failing values.
- `empty_column_is_text_at_zero_confidence` — FR-F071-06: all-empty column → `text`, `inferred`, confidence 0.
- `formula_never_inferred_from_values` — FR-F071-06: a computed-value column never infers `formula`.
- `select_inferred_only_within_cardinality_rule` — FR-F071-07: 12 distinct values over 300 rows → `select` with 12 staged options; 60 distinct → `text`.
- `person_column_requires_resolvable_tenant_users` — FR-F071-07: 9 of 10 emails resolve → `person` plus one `unresolved_person`; 5 of 10 → `text`.
- `currency_column_stages_iso_code` — FR-F071-07: `€` throughout → `currency` with `EUR`; mixed symbols → `text`.
- `ambiguous_date_order_defaults_to_iso_with_issue` — FR-F071-07: `03/04/2026` with no workbook locale → ISO order and `ambiguous_date_order`.
- `analysis_creates_no_sheet_in_target_folder` — FR-F071-01, FR-F071-08: after `ready` the folder tree is byte-identical to before.
- `preview_returns_sheets_columns_samples_and_issues` — FR-F071-08: 12 tabs, their column maps, 5 sample values each, 20 sample rows, every issue, `committed_sheet_count: 0`.
- `migration_list_filters_by_status_and_source_kind` — FR-F071-08: `status=ready&source_kind=excel` → one row; cursor paging over 40 migrations.
- `repeat_analysis_produces_identical_plan` — NFR-F071-05: re-analysing the same file yields identical sheet, column map, and issue content in the same order.
- `autofilter_becomes_grid_view_filter` — FR-F071-12: an AutoFilter on two columns → a `grid` view whose AST holds `eq` and `between`.
- `sixth_sort_truncated_with_issue` — FR-F071-12: 6 saved sorts → 5 `view_sorts` and `view_sorts_truncated`.
- `pivot_table_reported_as_unsupported_view_kind` — FR-F071-12: a pivot tab → `unsupported_view_kind` naming the tab and the source view.
- `resolvable_cross_tab_reference_staged_as_link` — FR-F071-13: a single-column reference into a tab with a unique key column → a `link` column map with the target tab recorded.
- `cross_workbook_reference_kept_as_text_with_issue` — FR-F071-13: a reference into another workbook → static text plus `cross_workbook_reference` naming the cell.
- `outline_depth_beyond_twenty_flattened_with_issue` — FR-F071-14: depth 23 → depth 20 plus `hierarchy_depth_exceeded`.
- `unsupported_formula_function_falls_back_to_value` — FR-F071-14: an unsupported function → its last computed value plus an issue naming the function and the cell.
- `attachment_over_size_cap_skipped` — FR-F071-15: a 30 MB embedded file → skipped with `attachment_over_size_cap` naming the file and its size; a 4 MB one uploads through F017.
- `override_revalidated_against_column_contract` — FR-F071-09: overriding to `select` with 60 options → `400 invalid` with `field_errors.column_overrides` and nothing created.
- `ambiguous_column_requires_override_or_acceptance` — FR-F071-09: commit without an override and without `accept_ambiguous` → `400 invalid` naming the column map.
- `unwaived_blocking_issue_refuses_commit` — FR-F071-03, FR-F071-09: a blocking issue → `400 invalid`; waived → `202`.
- `second_commit_returns_conflict` — FR-F071-09: commit on a `committing` migration → `409 conflict`.
- `tab_structure_failure_creates_nothing` — FR-F071-10: a column create failing mid-tab leaves no sheet, no column, and no view for that tab.
- `commit_resumes_from_cursor_without_duplicate_rows` — FR-F071-11: worker killed after chunk 2 of 5,000 rows → resumes at 2,000 and the sheet holds exactly 5,000 rows.
- `failed_tab_sheet_and_rows_soft_deleted` — FR-F071-11: three failures on tab 3 → tab `failed`, its sheet and rows soft-deleted, the other tabs committed.
- `link_pass_runs_after_all_tabs` — FR-F071-13: links are created only once every tab is committed, and a link failure records an issue without rolling a sheet back.
- `delete_removes_every_sheet_the_migration_created` — FR-F071-11: `DELETE` on a partly committed migration leaves the folder as it was and removes the source object.
- `commit_emits_started_and_completed_events` — FR-F071-10, NFR-F071-04: `migration.started.v1` then `migration.completed.v1` with `committed_sheet_count`, `committed_rows`, `issue_count`, and `first_sheet_id`.
- `dead_letter_after_three_attempts_emits_failed` — NFR-F071-04: a permanently failing source → `migration.failed.v1` with `reason: dead_letter` and a `job_runs` entry.
- `viewer_cannot_create_migration` — FR-F071-16: viewer POST → `403 denied`, no row written.
- `commenter_cannot_commit` — FR-F071-16: commenter commit → `403 denied`.
- `foreign_tenant_ids_not_found` — NFR-F071-02: tenant B `file_id`, `target_folder_id`, and migration id each → `404 not_found` on create, read, commit, and delete.
- `no_lane_opens_an_external_socket` — NFR-F071-02: the negative control fails if any code path on this feature dials a host outside the fixture.

Evidence: JUnit output and worker logs under `testing/evidence/F071/api/`.
