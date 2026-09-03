# F045 e2e cases

File: `testing/features/F045/e2e/documents.spec.ts`. Playwright against seeded tenant. Flag `F045_FEATURE`.

- `create_folder_document_save_revision` — FR-F045-01, FR-F045-07, FR-F045-14: editor creates folder "Runbooks", document "Deploy checklist", types a body, presses `Ctrl+S`, history panel shows revision 2 with author and time; reload shows the saved body.
- `move_search_trash_restore` — FR-F045-03, FR-F045-05, FR-F045-06: editor moves the document to "Archive 2025", searches `deploy` and sees a snippet, trashes the folder, opens trash, restores, and the document URL still works.
- `sibling_title_clash_shows_field_error` — FR-F045-02: second "Runbooks" in the same folder shows the inline title error.
- `concurrent_save_shows_stale_banner` — FR-F045-07: second session saves a revision; first session's save shows the stale banner and reload recovers the newer body.
- `viewer_is_read_only` — FR-F045-14: viewer login sees tree, list, and document without create, move, trash, or save controls.
- `link_principal_sees_only_granted_folder` — FR-F045-11: opening the share link shows "Runbooks" contents only, no workspace breadcrumb, and direct navigation to a "Finance" document shows not-found.
- `denied_folder_hidden_from_member` — FR-F045-10: member with explicit deny on "Finance" does not see it in the tree; direct URL shows not-found.
- `keyboard_only_library` — NFR-F045-03: no mouse; tree navigated with arrows, document opened with Enter, revision saved with `Ctrl+S`, live region announces the save.

Evidence: Playwright traces and videos under `testing/evidence/F045/e2e/`.
