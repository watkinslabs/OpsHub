---
id: S090
type: story
status: planned
parent_epic: E004
parent_feature: F045
depends_on: [S089]
owned_paths: [crates/domain/src/documents/**, crates/persistence/src/documents/**, services/api/src/documents/**, apps/web/src/features/documents/**, testing/features/F045/**]
feature_flag: F045_FEATURE
branch: s090-sharing-and-permissions
started_at: null
finished_at: null
---

# S090 — Sharing and permissions

## Identity

- Parent feature: `F045` Documents/folders
- Owner: platform
- Branch: `s090-sharing-and-permissions`
- Decision references: `docs/architecture-decisions.md` sections 4, 5, 6; `docs/capability-contracts.md` row F045

## Vertical slice

As a document owner, I want access to my folders and documents to follow the inherited share model with explicit denies, guests and links limited to what they were granted, and a library UI that reflects each person's effective role, so that written knowledge is shared safely without leaking the rest of the workspace.

## Requirements

- **SR-S090-01:** `resolve_effective_access` loads the node's `document_ancestors` rows through `DocumentRepository`, walks them root-to-leaf (`distance` descending) against F036 `share_grants`, returns the highest granted role, and returns `denied` when any level carries an explicit deny; every `DocumentResponse` carries `effective_role`, and `path` is those ancestor IDs in the same order (FR-F045-10).
- **SR-S090-02:** A guest or link principal receives `403 denied` on `GET /api/v1/documents` without `parent_id`, can list and read only nodes under a granted folder, and receives `403 denied` on every mutation route (FR-F045-11).
- **SR-S090-03:** A link principal receives `429 rate_limited` on the 61st request within one minute for the same link token, with `Retry-After` set (FR-F045-11, NFR-F045-02).
- **SR-S090-04:** Nodes with `search_visibility = hidden` and nodes reachable only through a link are excluded from tenant-wide `q` results unless the workspace setting `link_search_discoverable` is true (FR-F045-12).
- **SR-S090-05:** A member with an explicit deny on a folder receives `404 not_found` for that folder and every descendant, including revision routes (FR-F045-10, FR-F045-13).
- **SR-S090-06:** `DocumentLibraryPage`, `FolderTree`, `DocumentList`, `DocumentPage`, `DocumentEditor`, `RevisionHistoryPanel`, `MoveDialog`, and `TrashView` render from the API, hide mutation affordances below `document-editor`, and show loading, empty, error, denied, stale, and offline states (FR-F045-14, NFR-F045-03).
- **SR-S090-07:** The 10,000-child listing, 1 MB revision save, and 100,000-document search meet NFR-F045-01, listing and search driven through `DocumentRepository::list_children` and `DocumentSearchRepository::search` with the `document_ancestors(ancestor_id, distance)` and `document_search` GIN indexes.
- **SR-S090-08:** The access walk and rate-limit code reach PostgreSQL only through the repository traits: no SQL string, `sqlx::query*` call, or connection exists in `crates/domain/src/documents` or `services/api/src/documents`, and the access tests drive the repository traits rather than raw queries (decision 2.1).

## Surfaces

- Infrastructure/container: none
- Rust service/API: `crates/domain/src/documents/{access.rs, principal.rs}`; `crates/persistence/src/documents/{document_repository.rs, document_search_repository.rs}` supplying the ancestor and search queries; `services/api/src/documents/{authz.rs, rate_limit.rs}`
- Data/migration: none new; reads `documents` and `document_ancestors` through `DocumentRepository` and F036 `share_grants` and `share_links` through their own repositories
- React/UI: `apps/web/src/features/documents/{DocumentLibraryPage.tsx, FolderTree.tsx, DocumentList.tsx, DocumentPage.tsx, DocumentEditor.tsx, RevisionHistoryPanel.tsx, MoveDialog.tsx, TrashView.tsx, NewNodeDialog.tsx, SearchBox.tsx, api.ts, hooks.ts, routes.ts}`
- Mocks/fixtures: guest and link principal fixtures with grants on one folder and a deny on another; 10,000-child and 100,000-document generators for the performance lane; MSW handlers for component tests

## TDD harness

- Test path: `testing/features/F045/{api,frontend,e2e,accessibility,performance}/`
- Feature flag: `F045_FEATURE`
- Targeted command: `cargo xtask test-feature F045`
- Full command: `cargo xtask test-all`
- First failing tests: `explicit_deny_hides_descendants`, `effective_access_walks_ancestor_rows`, `link_principal_cannot_list_root`, `link_principal_rate_limited_after_60`, `hidden_nodes_excluded_from_search`, `folder_tree_keyboard_navigation`, `document_list_10k_children_p95`

## Exit criteria

- [ ] Requirement tests SR-S090-01 through SR-S090-08 written first and failing
- [ ] Tasks T179 and T180 complete; UI wired to the real API through the generated client
- [ ] Unit, API, React, E2E, accessibility, permission, and performance tests pass
- [ ] Production call path named: `apps/web/src/features/documents/DocumentLibraryPage.tsx` mounted at `/w/:workspaceId/documents`
- [ ] Handoff evidence recorded in the F045 ticket
