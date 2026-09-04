---
id: F045
type: feature
status: planned
priority: P2
owner: platform
estimate: 5
target_milestone: M3
parent_epic: E004
depends_on: [F005, F017, F036]
blocks: [F046, F047]
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/documents/**, crates/persistence/src/documents/**, services/api/src/documents/**, apps/web/src/features/documents/**, services/api/migrations/*_documents_*.sql, testing/features/F045/**]
feature_flag: F045_FEATURE
flag_default: off
branch: f045-documents-folders
started_at: null
finished_at: null
---

# F045 — Documents/folders

## 1. Identity and dates

- Branch: `f045-documents-folders`
- Capability area: documents, folders, and sharing (spec 5.4a DOC-01, DOC-02; 5.4b COLLAB-03; section 4 record rules; section 10 link expiry and guest scoping)
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 5; `docs/capability-contracts.md` row F045
- Aggregate: `document`
- Module slug: `documents`

## 2. Requirement specification

### Problem and user outcome

Teams keep specifications, runbooks, and meeting notes next to their work, but OpsHub has no document surface. They need a folder tree inside a workspace, rich-text documents with an immutable revision history, search across titles and bodies, trash with restore, and sharing that respects the same inherited access model as the rest of the platform. F046 builds live co-editing on top of the revision store this feature creates, and F047 exposes documents as MCP resources.

As a workspace editor, I want to create folders and documents, move them around, save named revisions, find them by search, and share them with scoped people or links, so that my team's written knowledge lives beside its work records under one permission model.

### Functional requirements

- **FR-F045-01:** An actor with the `document-editor` role can `POST /api/v1/documents` with `{ workspace_id, parent_id?, kind: "folder"|"doc", title, body_base64? }`; the response returns a UUIDv7 `id`, `version` 1, `current_revision` 1 for a `doc` (0 for a folder), and `path` (ancestor IDs read from `document_ancestors` ordered by `distance` descending, root first).
- **FR-F045-02:** Titles are unique among non-deleted siblings under the same `parent_id` (case-insensitive, 1–255 chars); a duplicate returns `409 conflict` with `field_errors.title = "taken"`.
- **FR-F045-03:** `POST /api/v1/documents/{id}/move` with `{ parent_id, If-Match }` re-parents a folder or doc and rewrites the moved subtree's `document_ancestors` rows and `depth` values in the same transaction; a target that is the node itself or any descendant returns `400 invalid` with `field_errors.parent_id = "cycle"`, and a resulting depth above 32 returns `400 invalid` with `field_errors.parent_id = "too_deep"`.
- **FR-F045-04:** `PATCH /api/v1/documents/{id}` updates `title`, `archived` (true|false), and `search_visibility` (`inherit`|`hidden`) with `If-Match`; a stale version returns `409 conflict` with `current_version`.
- **FR-F045-05:** `DELETE /api/v1/documents/{id}` soft-deletes the node and every descendant in one transaction; `POST /api/v1/documents/{id}/restore` within the tenant retention window restores the node and descendants with their original IDs, and restoring a child whose parent is still deleted re-parents it to the workspace root with `restored_to_root: true`.
- **FR-F045-06:** `GET /api/v1/documents` lists children of `parent_id` (root when absent) with cursor pagination, `limit` up to 100, filter by `kind`, `deleted=true|false`, `archived`, and `q` (full-text on title and body), sorted by `title` or `updated_at`; `q` results carry a `snippet` and never include nodes the actor cannot read.
- **FR-F045-07:** `POST /api/v1/documents/{id}/revisions` with a body up to 20 MB and `If-Match: <current_revision>` stores the content in object storage, records `content_checksum` (SHA-256), `size_bytes`, and `storage_key`, increments `current_revision`, and publishes `document.revision-added.v1`; a stale `If-Match` returns `409 conflict` with `current_revision`.
- **FR-F045-08:** Revisions are immutable: there is no update or delete route for a revision, and `GET /api/v1/documents/{id}/revisions/{rev}` returns metadata plus a presigned download URL valid for 15 minutes; a checksum mismatch on read returns `503 unavailable` with code `unavailable` and raises a `document_checksum_mismatch` alert.
- **FR-F045-09:** `GET /api/v1/documents/{id}/revisions` pages revisions newest first with `limit` up to 100, each carrying `revision`, `author_id`, `created_at`, `size_bytes`, `content_checksum`, and optional `label` (≤ 120 chars) set at creation.
- **FR-F045-10:** Read access to a node is the union of grants on the node and its ancestors from F036 share grants, evaluated root-to-leaf where an explicit deny at any level wins; the effective role is returned as `effective_role` on every read.
- **FR-F045-11:** A guest or link principal from F036 can read only nodes explicitly granted or beneath a granted folder, never sees `GET /api/v1/documents` root listings of the workspace, and receives `429 rate_limited` after 60 requests per minute per link token.
- **FR-F045-12:** Nodes with `search_visibility = hidden`, and every node reached only through a share link, are excluded from tenant-wide `q` results unless the workspace setting `link_search_discoverable` is true.
- **FR-F045-13:** Every mutation requires `Idempotency-Key`, writes an `audit_events` row with actor, action, and diff, and publishes the matching `document.*.v1` event through the outbox; cross-tenant access by ID returns `404 not_found`.
- **FR-F045-14:** The web app renders a folder tree with a document list, opens a document in an editor that saves revisions, shows revision history with restore-as-new-revision, and offers move and trash views; viewers see read-only affordances and non-members see not-found.

### Non-functional requirements

- **NFR-F045-01 Performance:** listing a page of 100 children in a folder holding 10,000 nodes responds in under 500 ms p95; saving a 1 MB revision responds in under 800 ms p95; a `q` search over 100,000 documents responds in under 500 ms p95 (spec section 6).
- **NFR-F045-02 Security/privacy:** every query carries a `tenant_id` predicate; access is evaluated in the service layer with the inheritance walk; guest and link principals are tested for root-listing exclusion, write denial, and rate limiting; share links expire within 30 days.
- **NFR-F045-03 Accessibility:** the folder tree uses `role="tree"` with arrow-key navigation, the editor and dialogs pass axe with no serious violations, and revision restore is announced through a live region.
- **NFR-F045-04 Reliability/observability:** spans carry `tenant_id`, `document_id`, `revision`, and `correlation_id`; a revision write that fails object storage rolls back the metadata row; checksum verification on every read emits `document_checksum_verified_total`.

### Scope

Included: folder and document CRUD, move with cycle and depth checks, archive, soft delete and restore of subtrees, immutable revisions in object storage with checksums, revision listing and presigned download, full-text search index, inherited permission walk, guest and link scoping, search visibility, audit and outbox events, library and editor UI.

Excluded: live co-editing sessions, presence, and CRDT change replay (F046); creating share grants and link tokens (F036); comments on documents (F016); attachment upload pipeline and virus scanning (F017); MCP resource exposure (F047); retention purge (F027).

## 3. UX specification

- Entry points: workspace sidebar item `Documents`; route `/w/{workspace_id}/documents?folder={id}`; document route `/w/{workspace_id}/documents/{document_id}`; folder context menu `New folder`, `New document`, `Move`, `Archive`, `Trash`; trash view at `?view=trash`.
- Primary flow: open `Documents`, click `New folder`, name it `Runbooks`; inside it click `New document`, type a title, press Enter, the editor opens on revision 1; type body text, press `Ctrl+S` or click `Save revision`, the history panel shows revision 2 with author and time; open `Move`, pick `Archive 2025`, confirm, the tree updates; use the search box with `deploy`, the list shows matches with snippets.
- Loading: tree and list skeletons, editor skeleton while the presigned body downloads; Empty: `No documents yet` with `New document` call to action; Error: inline banner with `correlation_id` and retry; Success: toast on create, move, restore, and revision save; Stale/conflict: banner `This document has a newer revision` with `Reload` and `Save as new revision anyway` disabled until reload; Offline: editor read-only with an offline badge.
- Permission-denied: viewers and commenters see no create, move, trash, or save controls and an inline `Read only` label; link principals see only the granted subtree with no workspace breadcrumb; non-members get the not-found page.
- Responsive: tree collapses into a drawer under 768 px; editor toolbar wraps under 640 px; history panel becomes a bottom sheet.
- Keyboard: tree follows the ARIA tree pattern (Up/Down move, Right expands, Left collapses, Enter opens, `F2` renames); `Ctrl+S` saves a revision; `Escape` closes dialogs and returns focus; motion respects `prefers-reduced-motion`.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062); Lucide icons `Folder`, `FolderOpen`, `FileText`, `History`, `Move`, `Archive`, `Trash2`, `RotateCcw`, `Search`; spacing and color from `apps/web/src/design/tokens.css`.

## 4. Technical specification

### Rust backend

- Domain entities in `crates/domain/src/documents/`: `DocumentNode { id, tenant_id, workspace_id, parent_id: Option<DocumentId>, kind: NodeKind, title, archived: bool, search_visibility: SearchVisibility, current_revision: i64, depth: i16, version, created/updated actor+time, deleted_at }`, `NodeKind { Folder, Doc }`, `DocumentRevision { id, tenant_id, document_id, revision: i64, storage_key, content_checksum: [u8; 32], size_bytes, label: Option<String>, author_id, created_at }`, `DocumentAncestor { tenant_id, document_id, ancestor_id, distance: i16 }`, `EffectiveAccess { role: ShareRole, denied: bool, source_node_id }`.
- Persistence (`crates/persistence/src/documents/`): `DocumentRepository` owns `documents` and `document_ancestors`; `DocumentRevisionRepository` owns `document_revisions`; `DocumentSearchRepository` owns `document_search`. Each implements the shared `Repository` contract (`get`, `list` with cursor pagination, `insert`, `update` under an expected version, `soft_delete`, `restore`, `purge`) and adds named queries `list_children(parent_id, cursor)`, `list_subtree(document_id)`, `count_subtree(document_id)`, `is_descendant_of(candidate_id, ancestor_id)`, `move_subtree(document_id, new_parent_id)`, `lock_for_revision(document_id)`, `next_revision(document_id)`, `list_revisions(document_id, cursor)`, `get_revision(document_id, revision)`, `upsert_search(document_id, title, tsv, snippet)`, `search(tenant_id, workspace_id, query, cursor)`, `soft_delete_subtree(document_id)`; the tenant predicate, soft-delete filter, version check, audit row, and outbox enqueue come from the base contract. `lock_for_revision` carries the `select ... for update` on the document row that assigns `current_revision + 1` — the same row lock in the same transaction still serializes concurrent revision writers, only the SQL moved into `crates/persistence`. Adding a revision (revision row, `current_revision` bump, `document_search` upsert, outbox) and moving a subtree (parent change, ancestor rewrite for the whole moved subtree, depth recompute, audit) each run in one `UnitOfWork` that owns the transaction. Object-storage reads and writes stay in the F017 storage adapter, not in a repository. Per decision 2.1 the use cases below depend on these repository traits and contain no SQL: no SQL string, `sqlx::query*` call, or connection exists in `crates/domain/src/documents` or `services/api/src/documents`.
- Use cases: `create_node`, `rename_or_archive_node` (PATCH), `move_node`, `delete_subtree`, `restore_subtree`, `list_children`, `search_documents`, `add_revision`, `list_revisions`, `get_revision_download`, `resolve_effective_access`.
- API endpoints (`services/api/src/documents/`): `GET /api/v1/documents`, `POST /api/v1/documents`, `GET /api/v1/documents/{id}`, `PATCH /api/v1/documents/{id}`, `POST /api/v1/documents/{id}/move`, `DELETE /api/v1/documents/{id}`, `POST /api/v1/documents/{id}/restore`, `GET /api/v1/documents/{id}/revisions`, `POST /api/v1/documents/{id}/revisions`, `GET /api/v1/documents/{id}/revisions/{rev}`. DTOs: `CreateDocumentRequest`, `UpdateDocumentRequest`, `MoveDocumentRequest`, `AddRevisionRequest` (multipart or base64 body with `label?`), `DocumentResponse { id, workspace_id, parent_id, kind, title, archived, search_visibility, current_revision, path, effective_role, version, created_at, updated_at, deleted_at }`, `RevisionResponse`, `RevisionDownloadResponse { revision, download_url, expires_at, content_checksum }`, `Page<DocumentResponse>` with `snippet` on search hits.
- Events: `document.created.v1`, `document.updated.v1`, `document.moved.v1`, `document.deleted.v1`, `document.restored.v1`, `document.revision-added.v1`; payload per contract conventions with `changed_fields`; `document.moved.v1` carries `old_parent_id` and `new_parent_id`.
- Authorization: `document-editor` on the target node or an ancestor for mutations; `viewer` or higher for reads; `resolve_effective_access` walks the node's `document_ancestors` rows root-to-leaf (ordered by `distance` descending) against F036 `share_grants`, returning `denied` when any level carries an explicit deny; guest and link principals are recognized by `PrincipalKind::{Guest, Link}` in the gateway context and rejected from root listings.
- Storage: revisions written through the F017 storage client (`crates/storage::ObjectStore::put_immutable`) under key `tenants/{tenant_id}/documents/{document_id}/{revision}.bin`; the object put precedes the commit of the `UnitOfWork` holding the metadata insert, and a failed put aborts the transaction.
- Validation: title 1–255 chars; body ≤ 20 MB; `label` ≤ 120 chars; `limit` 1–100; `parent_id` must be a non-deleted folder in the same workspace; depth ≤ 32.
- Rate limiting: link principals are limited to 60 requests per minute per token via the F038 limiter keyed `link:{token_id}`.
- Error mapping: `DocumentError::TitleTaken → 409 conflict`, `DocumentError::Cycle → 400 invalid (parent_id=cycle)`, `DocumentError::TooDeep → 400 invalid (parent_id=too_deep)`, `DocumentError::StaleVersion | StaleRevision → 409 conflict`, `DocumentError::NotFound → 404 not_found`, `DocumentError::ChecksumMismatch → 503 unavailable`, `AuthzError::Denied → 403 denied`, `RateLimit → 429 rate_limited`, validation → `400 invalid` with `field_errors`.

### PostgreSQL/SQLx

- Migration `*_documents_*.sql` creates `documents(id uuid pk, tenant_id uuid not null, workspace_id uuid not null, parent_id uuid null references documents(id) on delete restrict, kind text not null check (kind in ('folder','doc')), title text not null, archived bool not null default false, search_visibility text not null default 'inherit', current_revision bigint not null default 0, depth smallint not null default 0 check (depth <= 32), version bigint not null default 1, created_by, created_at, updated_by, updated_at, deleted_at)`, `document_ancestors(tenant_id uuid not null, document_id uuid not null references documents(id) on delete cascade, ancestor_id uuid not null references documents(id) on delete cascade, distance smallint not null check (distance >= 1), created_by uuid not null, created_at timestamptz not null, primary key (document_id, ancestor_id))`, `document_revisions(id uuid pk, tenant_id, document_id uuid not null references documents(id) on delete restrict, revision bigint not null, storage_key text not null, content_checksum bytea not null, size_bytes bigint not null, label text, author_id uuid not null, created_at timestamptz not null)`, `document_search(tenant_id uuid not null, document_id uuid not null references documents(id) on delete cascade, tsv tsvector not null, title text not null, snippet text, updated_at timestamptz not null, primary key (tenant_id, document_id))`. The materialized `path uuid[]` is replaced by the `document_ancestors` closure table: one row per (node, ancestor) pair, `distance` 1 for the parent and increasing toward the root. No `jsonb` column exists in this feature; the only non-scalar column left is `document_search.tsv`, a derived search index rebuilt from the title and body, not a payload the product reads back.
- Invariants: unique partial index `documents_sibling_title_idx on (tenant_id, workspace_id, coalesce(parent_id, '00000000-0000-0000-0000-000000000000'), lower(title)) where deleted_at is null`; unique index `document_revisions_doc_rev_idx on (document_id, revision)`; `revision` assigned as `current_revision + 1` inside the same transaction under the `select ... for update` row lock taken by `DocumentRevisionRepository::lock_for_revision`; `depth = (select count(*) from document_ancestors where document_id = documents.id)`, maintained in the create and move transactions; a node's ancestor set is exactly its parent's ancestor set plus its parent, so `document_ancestors` has a row at `distance = 1` for every node with a non-null `parent_id`.
- Cycle prevention replaces the `documents_path_check` trigger with two checks inside the move transaction, rejecting exactly the same cycles: the new parent must not be a descendant of the moving node — no `document_ancestors` row exists with `document_id = new_parent_id and ancestor_id = moving_id` (`is_descendant_of`) — and `parent_id <> id` for the self-reference case, both mapping to `field_errors.parent_id = "cycle"`.
- Indexes: `documents(tenant_id, workspace_id, parent_id, lower(title)) where deleted_at is null`, `documents(tenant_id, workspace_id, updated_at desc)`, `document_ancestors(ancestor_id, distance)`, `document_ancestors(tenant_id, ancestor_id)`, `document_revisions(document_id, revision desc)`, `document_search using gin (tsv)`. The b-tree on `(ancestor_id, distance)` replaces the GIN index on `path`: "every descendant of X" is `where ancestor_id = X` — the same result set as the old `path @> array[X]`, now with declared foreign keys on both ends and with `distance` available for depth-ordered reads. Subtree soft delete, the affected-descendant count on move and delete audit events, and the ≤ 32 depth limit are unchanged.
- Search maintenance: `add_revision` and title changes call `DocumentSearchRepository::upsert_search` in the same transaction from the first 64 KB of extracted text; `tsv` uses the `simple` configuration plus the tenant locale configuration from F049 when present.
- Audit events: `document.create`, `document.update`, `document.move`, `document.delete`, `document.restore`, `document.revision.add` with field-level diffs and the affected descendant count on subtree operations.
- Retention/deletion: soft delete sets `deleted_at` on the subtree and leaves its `document_ancestors` rows intact so restore rebuilds the same tree; the F027 purge job removes metadata and object keys older than tenant retention; migration rollback drops the four tables `documents`, `document_ancestors`, `document_revisions`, and `document_search` (no data exists before this feature).

### React/TypeScript

- Routes: `/w/:workspaceId/documents`, `/w/:workspaceId/documents/:documentId` in `apps/web/src/features/documents/`; components `DocumentLibraryPage`, `FolderTree`, `DocumentList`, `DocumentPage`, `DocumentEditor`, `RevisionHistoryPanel`, `MoveDialog`, `TrashView`, `NewNodeDialog`, `SearchBox`.
- State: TanStack Query keys `['documents', workspaceId, folderId, cursor]`, `['document', id]`, `['document-revisions', id]`; mutations invalidate by key and update cached `version` and `current_revision`.
- API client: generated `DocumentsApi` with `listDocuments`, `createDocument`, `getDocument`, `updateDocument`, `moveDocument`, `deleteDocument`, `restoreDocument`, `listRevisions`, `addRevision`, `getRevisionDownload`.
- Editor: `DocumentEditor` loads the current revision through the presigned URL, edits an in-memory Automerge document, and posts the serialized binary as a new revision with `If-Match`; on `conflict` it shows the stale banner and disables save until reload; F046 replaces the save path with a live session behind its own flag.
- Optimistic updates: move applies locally in the tree and rolls back on `invalid` or `conflict` with the reason inline.
- Telemetry: `document_created`, `document_opened`, `document_moved`, `revision_saved`, `document_restored` with `document_id`, `kind`, and `revision`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F045-01 through FR-F045-14 in `testing/features/F045/requirements/cases.md`
- [ ] Failure/edge-case tests: sibling title clash, move into own descendant, depth 33, stale revision, checksum mismatch on read, restore child under deleted parent, 20 MB body limit
- [ ] Permission-negative and tenant-isolation tests: cross-tenant read returns `not_found`, viewer mutation returns `denied`, explicit deny on a folder hides its descendants, link principal cannot list root or write, link rate limit
- [ ] Rust unit tests: `crates/domain/src/documents/` ancestor-set and depth computation, access walk, checksum computation, error mapping
- [ ] Persistence tests: `crates/persistence/src/documents/` repository traits — `list_children`, `list_subtree`, `count_subtree`, `is_descendant_of`, `move_subtree` ancestor rewrite, `lock_for_revision` serializing two concurrent revision writers, `soft_delete_subtree`, `search`
- [ ] API contract/integration tests: every route above with success and each error code
- [ ] Database migration/constraint tests: sibling title index, revision uniqueness, `document_ancestors` primary key and `distance >= 1` check, cycle rejection in the move transaction, depth check, GIN search index, rollback of all four tables
- [ ] React component tests: `FolderTree`, `DocumentList`, `DocumentEditor`, `RevisionHistoryPanel`, `MoveDialog`, `TrashView` states
- [ ] Browser E2E tests: create folder and document, save revision, move, search, trash and restore, link principal scope
- [ ] Accessibility tests: axe on library and editor, tree keyboard pattern, dialog focus, live region on restore
- [ ] Performance/load tests: 10,000-child listing p95 under 500 ms, 1 MB revision save p95 under 800 ms, search over 100,000 documents p95 under 500 ms

### Fast fanout configuration

- Test harness path: `testing/features/F045/`
- Feature flag: `F045_FEATURE`
- Fixture/seed factory: `testing/fixtures/documents.rs` builds tenant, workspace, editor, viewer, guest, link principal, foreign tenant, and a seeded tree of 4 folders (depth 3) with 25 documents each carrying 3 revisions
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, UTC, fixed revision bodies with known SHA-256 values
- Mock/stub contracts: in-memory `ObjectStore` recording puts and serving presigned URLs; outbox publisher recorded in memory; authz uses the real F003 engine and F036 grant tables with fixture bindings
- Parallel isolation: one schema per test worker, tenant ID per test, object keys prefixed by test ID
- Targeted command: `cargo xtask test-feature F045`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F045/`

## 6. Acceptance criteria

```gherkin
Feature: Documents and folders

Scenario: Create a folder and a document with a first revision
  Given an editor in workspace "Ops"
  When they create folder "Runbooks" and document "Deploy checklist" inside it with a body
  Then the document has version 1, current_revision 1, depth 1, and a document_ancestors row for the folder at distance 1
  And events document.created.v1 and document.revision-added.v1 are in the outbox

Scenario: Move into own descendant is rejected
  Given folder "A" containing folder "B"
  When an editor moves "A" under "B"
  Then the response is 400 invalid with field_errors.parent_id "cycle" and no change is written

Scenario: Stale revision save is rejected
  Given document "Deploy checklist" at current_revision 3
  When an editor posts a revision with If-Match 2
  Then the response is 409 conflict with current_revision 3 and no object is stored

Scenario: Explicit deny hides a subtree
  Given a viewer granted the workspace and explicitly denied on folder "Finance"
  When they list the children of "Finance" or open a document inside it
  Then every response is 404 not_found

Scenario: Link principal cannot list the root
  Given a share link scoped to folder "Runbooks"
  When the link principal calls GET /api/v1/documents without parent_id
  Then the response is 403 denied, and listing "Runbooks" succeeds

Scenario: Trash and restore a subtree
  Given folder "Runbooks" with 3 documents
  When an editor deletes the folder and later restores it
  Then all four nodes return with their original ids and document.restored.v1 is published
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F005 (workspace and membership), F017 (object storage client, presigned URLs), F036 (share grants, guest identity, link tokens); decisions sections 2–5; contracts row F045
- Blocks: F046, F047
- Conflicts with: none (disjoint owned paths)
- External dependencies: S3-compatible object storage (MinIO locally)
- Risks and mitigations: a subtree delete or restore on a very wide folder can hold row locks for long, so subtree operations batch 1,000 nodes per statement through `list_subtree`, which reads `document_ancestors(ancestor_id, distance)`, and abort above 50,000 nodes with `invalid`; a wide move rewrites one `document_ancestors` row per descendant per ancestor level, so `move_subtree` is bounded by the same 50,000-node ceiling and the depth ≤ 32 limit; full-text upserts on every revision could slow saves, so the search upsert extracts only the first 64 KB of text; the access walk could become a hot path, so the effective role for an ancestor chain is cached per request in `EffectiveAccessCache`.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F005, F017, and F036 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F045/`
- [ ] Migration file name and owned paths claimed
- [ ] Fixture factory, in-memory object store, and schema-per-worker isolation available in `testing/harness/`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for every mutation
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F045_FEATURE`, run down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Users can organize folders and rich-text documents in a workspace, save immutable revisions, search titles and bodies, and share scoped subtrees with people or expiring links.
- Migration adds `documents`, `document_ancestors`, `document_revisions`, and `document_search`; rollback drops all four. Feature is off by default behind `F045_FEATURE`.
