# F071 e2e cases

File: `testing/features/F071/e2e/migration.spec.ts`. Playwright against a seeded tenant with generated workbooks; no external product is contacted. Flag `F071_FEATURE`.

- `upload_review_override_commit_opens_created_sheet` — FR-F071-01, FR-F071-08, FR-F071-09, FR-F071-10, FR-F071-16: the editor uploads `q3-delivery.xlsx`, waits out `Analysing 12 tabs`, changes `Owner` from `text` to `person`, waives the conditional-format issue, presses `Create everything`, watches every tab reach `committed`, and opens the first created sheet to find its typed columns and its row count.
- `committed_sheet_shows_hierarchy_and_link_chip` — FR-F071-13, FR-F071-14: the committed `Tasks` sheet shows indented rows to depth 3 and a link chip on `Owner rate` pointing at the `Rates` sheet created from the same workbook.
- `grid_view_arrives_with_filter_and_sorts` — FR-F071-12: the committed `Milestones` sheet opens on a `grid` view carrying the AutoFilter conditions and 5 of the source's 6 sorts, with the truncation issue still listed on the migration.
- `blocking_issue_holds_the_commit_until_waived` — FR-F071-03: the 120,000-row tab shows a blocking `row_cap_exceeded`, `Create everything` is disabled, waiving it enables the commit and the sheet lands with 100,000 rows.
- `ambiguous_column_must_be_decided_before_commit` — FR-F071-06, FR-F071-09: the `1:30` column is flagged ambiguous, commit is refused, choosing `duration` clears it and the commit proceeds.
- `commit_resumes_after_worker_restart` — FR-F071-11: the worker is restarted mid-commit; the progress panel continues from the same tab and the finished sheet holds no duplicate rows.
- `delete_abandoned_migration_leaves_folder_unchanged` — FR-F071-11: after two tabs are committed the editor deletes the migration and the `Delivery` folder shows exactly the sheets it held before.
- `viewer_cannot_reach_migrations` — FR-F071-16: a viewer visits the migration route and sees the denied surface with no entry point in the workspace tree.

Evidence: Playwright traces, screenshots, and worker logs under `testing/evidence/F071/e2e/`.
