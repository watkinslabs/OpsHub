# F010 e2e cases

File: `testing/features/F010/e2e/{dataio.spec.ts,dataio_recovery.spec.ts}`. Playwright against seeded tenant with MinIO. Flag `F010_FEATURE`.

- `search_and_open_row` — FR-F010-01, FR-F010-02, FR-F010-16: viewer presses `Ctrl+K`, types "kickoff", sees the `Plan` row and no `Payroll` row, presses `Enter`, lands on the grid with the row focused.
- `import_wizard_dry_run_then_commit` — FR-F010-06, FR-F010-07, FR-F010-08: editor uploads `plan.csv`, accepts detected mapping, picks key `Task ID` and strategy `update`, runs dry run (`980 valid, 20 invalid`), commits, watches progress, grid shows 980 new or updated rows.
- `import_duplicate_skip_strategy` — FR-F010-10: second import of the same file with `skip` reports 980 skipped and changes nothing.
- `cancel_import_keeps_written_rows` — FR-F010-11: editor cancels a 5,000-row import mid-way; status panel shows `cancelled` with rows kept; grid row count matches `processed_rows`.
- `dead_lettered_import_shows_failure_reason` — FR-F010-12: harness forces three worker failures; panel shows `failed` with the dead-letter reason and a retry hint.
- `export_pdf_and_download` — FR-F010-13, FR-F010-14, FR-F010-15: editor exports `Plan` to PDF, toast shows `Download`, downloaded file has repeated headers and no denied column; audit log lists `export.download`.
- `viewer_cannot_import` — FR-F010-16: viewer sees no import entry; opening the import URL shows the denied state.
- `non_requester_download_denied` — FR-F010-15: another editor opens the download link → denied explanation.
- `search_reflects_edit_within_5s` — NFR-F010-01: editor renames a row; search for the new text finds it within 5 s.

Evidence: Playwright traces and videos under `testing/evidence/F010/e2e/`.
