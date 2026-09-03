# F045 frontend cases

File: `testing/features/F045/frontend/{FolderTree.test.tsx,DocumentList.test.tsx,DocumentEditor.test.tsx,RevisionHistoryPanel.test.tsx,MoveDialog.test.tsx,TrashView.test.tsx}`. Vitest with MSW. Flag `F045_FEATURE`.

- `folder_tree_keyboard_navigation` — FR-F045-14, NFR-F045-03: Down moves focus, Right expands "Runbooks", Left collapses, Enter opens the selected doc.
- `folder_tree_lazy_loads_children` — FR-F045-06: expanding a folder fetches `['documents', workspaceId, folderId, cursor]` once and renders 25 children.
- `folder_tree_rename_with_f2` — FR-F045-04: `F2` opens inline rename, Enter calls `updateDocument` with `If-Match`.
- `document_list_shows_loading_empty_error` — FR-F045-14: pending query shows skeleton; empty folder shows `New document` call to action; 500 shows banner with `correlation_id` and retry.
- `document_list_hides_controls_for_viewer` — FR-F045-14: `effective_role: viewer` hides new, move, trash controls and shows `Read only`.
- `search_box_debounces_and_renders_snippets` — FR-F045-06: typing `deploy` issues one request after 300 ms and renders highlighted snippets.
- `save_posts_revision_with_if_match` — FR-F045-07: `Ctrl+S` posts the Automerge binary with `If-Match: 3` and emits `revision_saved`.
- `stale_revision_shows_banner_and_disables_save` — FR-F045-07: 409 `conflict` shows `This document has a newer revision`, save disabled until reload.
- `editor_offline_is_read_only` — FR-F045-14: `navigator.onLine=false` shows offline badge and disables editing and save.
- `restore_as_new_revision_calls_api` — FR-F045-09: choosing revision 2 and `Restore as new revision` posts its body as revision 4 and announces via live region.
- `cycle_error_rolls_back_move` — FR-F045-03: `moveDocument` 400 `parent_id=cycle` returns the node to its original folder and shows the reason inline.
- `trash_view_restores_subtree` — FR-F045-05: restore on a deleted folder calls `restoreDocument`, removes it from trash, and emits `document_restored`.
- `not_found_page_for_non_member` — FR-F045-14: 404 on `['document', id]` renders the not-found page.

Evidence: Vitest JUnit under `testing/evidence/F045/frontend/`.
