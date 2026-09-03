# F030 e2e cases

File: `testing/features/F030/e2e/{syncs.spec.ts,conflicts.spec.ts,files.spec.ts}`. Playwright against a seeded tenant with mock connector servers. Flag `F030_FEATURE`.

- `build_jira_sync_and_first_run` — FR-F030-02, FR-F030-05, FR-F030-16, FR-F030-21: an admin creates a Jira sync on project `OPS` against `Delivery board`, maps `summary`, `status` with `value_map`, and `duedate` with `date_tz`, previews five records, activates, runs, and sees `read 412 · created 412` in the run history.
- `resolve_conflict_from_queue` — FR-F030-13, FR-F030-14: a row and its issue both change; the run reports `conflicted 3`; the admin opens the conflict queue, uses `Keep external` on two and `Merge` on one, and the sheet shows the chosen values with the conflicts marked resolved.
- `replay_failed_run_from_history` — FR-F030-10, FR-F030-12: the mock fails 40 of 500 records; the run shows `partial`; `Dry-run replay` reports 40 would-update and writes nothing; the mock is repaired and `Replay failed only` updates exactly those 40.
- `resume_after_worker_restart` — FR-F030-09, NFR-F030-04: a 1,200-record run is interrupted mid-page; after restart the history shows one run reading 1,200 records with no duplicate rows on the sheet.
- `salesforce_sync_creates_and_marks_deleted` — FR-F030-17, FR-F030-15: an Opportunity sync creates rows, then a `getDeleted` response sets the `Deleted in CRM` checkbox without removing the row.
- `box_folder_attaches_files_and_rejects_scan_failure` — FR-F030-18: a Box folder binding attaches 19 files to matching rows and shows the EICAR sample as a rejected record with `scan_rejected`.
- `member_cannot_open_syncs` — FR-F030-20: a member visiting `/admin/syncs` sees the denied page.

Evidence: Playwright traces and mock connector logs under `testing/evidence/F030/e2e/`.
