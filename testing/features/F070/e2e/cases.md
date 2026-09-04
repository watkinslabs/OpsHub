# F070 e2e cases

File: `testing/features/F070/e2e/trash.spec.ts`. Playwright against the seeded tenant with the worker running. Flag `F070_FEATURE`.

- `delete_sheet_and_restore_it` — FR-F070-01, FR-F070-06, FR-F070-12: an editor deletes `Cutover plan`, opens `Trash`, sees it at the top with `30 days left`, restores it, and finds the sheet and its 40 rows back in `Northfield Delivery / Migration`.
- `restore_parent_then_child` — FR-F070-07: with folder `Procurement` and sheet `Vendor scorecard` both deleted, restoring the sheet shows the blocked reason naming the folder; restoring the folder clears the block and the sheet then restores.
- `editor_cannot_purge` — FR-F070-10: an editor opens the row menu and finds `Purge` disabled with the reason; the API call issued directly returns 403 and the entry survives the reload.
- `compliance_admin_purges_one_item` — FR-F070-10: a compliance administrator retypes the title, confirms, sees the row disappear and the audit entry appear, and a reload does not bring it back.
- `held_document_refuses_purge` — FR-F070-09: purging the document under an active legal hold shows the hold name and leaves it listed; releasing the hold then allows the purge.
- `member_sees_only_what_they_could_read` — FR-F070-02, FR-F070-11: a member with no access to `Procurement` opens `Trash` and sees neither its entries nor their titles, and a direct link to one lands on the not-found page.
- `restored_item_reappears_without_reload` — FR-F070-12: after a restore the owning sheet list updates from the invalidated query key rather than a page refresh.

Evidence: Playwright traces, worker logs and audit extracts under `testing/evidence/F070/e2e/`.
