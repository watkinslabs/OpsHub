---
id: T179
type: task
status: planned
parent_epic: E004
parent_feature: F045
parent_story: S090
depends_on: [T178]
owned_paths: [apps/web/src/features/documents/**, testing/features/F045/frontend/**, testing/features/F045/accessibility/**]
feature_flag: F045_FEATURE
branch: t179-document-editor-versioning
started_at: null
finished_at: null
---

# T179 — Document editor/versioning

## Identity

- Parent story: `S090` Sharing and permissions
- Owner: platform
- Branch: `t179-document-editor-versioning`
- Decision references: `docs/architecture-decisions.md` sections 5, 6; `docs/capability-contracts.md` row F045

## Objective

Build the document library page with the folder tree, document list, search box, move and trash views, and the document page with a revision-saving editor and revision history wired to the real documents API.

## Specification

- Owned paths: `apps/web/src/features/documents/{DocumentLibraryPage.tsx, FolderTree.tsx, DocumentList.tsx, SearchBox.tsx, NewNodeDialog.tsx, MoveDialog.tsx, TrashView.tsx, DocumentPage.tsx, DocumentEditor.tsx, RevisionHistoryPanel.tsx, api.ts, hooks.ts, routes.ts}`
- Contract/input: generated `DocumentsApi` client; route params `workspaceId`, `documentId`; query `folder`, `view=trash`, `q`.
- Output/behavior: `FolderTree` renders `role="tree"` with arrow-key navigation, `F2` rename, and lazy child loading per folder; `DocumentList` pages children and shows `effective_role`; `SearchBox` debounces `q` at 300 ms and renders snippets; `MoveDialog` picks a target folder and rolls back the optimistic move on `invalid` or `conflict` with the reason inline; `TrashView` lists deleted nodes and restores subtrees; `DocumentEditor` downloads the current revision through the presigned URL, edits an in-memory Automerge document, saves with `Ctrl+S` or `Save revision` posting `If-Match: <current_revision>`, and on `conflict` shows the stale banner and disables save until reload; `RevisionHistoryPanel` pages revisions newest first and offers `Restore as new revision`; states: loading skeletons, empty call to action, error banner with correlation ID, read-only affordances below `document-editor`, not-found page, offline badge; telemetry `document_created`, `document_opened`, `document_moved`, `revision_saved`, `document_restored`.
- Dependencies: T178 routes; F005 workspace shell for the `Documents` sidebar entry; F017 presigned URL download helper.
- Feature flag: `F045_FEATURE` read through the flag hook; routes are not registered when off.

## TDD

- Failing test first: `testing/features/F045/frontend/FolderTree.test.tsx::folder_tree_keyboard_navigation`, `::folder_tree_lazy_loads_children`; `DocumentEditor.test.tsx::save_posts_revision_with_if_match`, `::stale_revision_shows_banner_and_disables_save`; `RevisionHistoryPanel.test.tsx::restore_as_new_revision_calls_api`; `MoveDialog.test.tsx::cycle_error_rolls_back_move`; `testing/features/F045/accessibility/documents.a11y.spec.ts::library_and_editor_have_no_serious_axe_violations`
- Targeted command: `cargo xtask test-feature F045`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: MSW handlers from the seeded tree fixture with three revisions per document; blob URL stub for presigned downloads

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Component and accessibility lanes pass
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S090
- [ ] `finished_at` recorded
