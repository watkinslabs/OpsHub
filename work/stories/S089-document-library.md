---
id: S089
type: story
status: planned
parent_epic: E004
parent_feature: F045
depends_on: [F005, F017, F036]
owned_paths: [crates/domain/src/documents/**, crates/persistence/src/documents/**, services/api/src/documents/**, services/api/migrations/*_documents_*.sql, testing/features/F045/**]
feature_flag: F045_FEATURE
branch: s089-document-library
started_at: null
finished_at: null
---

# S089 — Document library

## Identity

- Parent feature: `F045` Documents/folders
- Owner: platform
- Branch: `s089-document-library`
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 5; `docs/capability-contracts.md` row F045

## Vertical slice

As a workspace editor, I want to create folders and documents in a tree, move and rename them, trash and restore whole subtrees, save immutable revisions, and find documents by full-text search, so that my team has a governed library before any sharing or live-editing surface exists.

## Requirements

- **SR-S089-01:** `POST /api/v1/documents` with `{ workspace_id, parent_id?, kind, title, body_base64? }` inserts the `documents` row through `DocumentRepository`, writes its `document_ancestors` rows and `depth` in the same `UnitOfWork`, stores revision 1 for a `doc`, and returns `DocumentResponse` with version 1 (covers FR-F045-01).
- **SR-S089-02:** Case-insensitive sibling title clash returns `409 conflict` with `field_errors.title = "taken"` (FR-F045-02).
- **SR-S089-03:** `POST /api/v1/documents/{id}/move` rejects self or descendant targets with `field_errors.parent_id = "cycle"` via `DocumentRepository::is_descendant_of` plus the `parent_id <> id` check and depth above 32 with `"too_deep"`, rewrites `document_ancestors` and `depth` for every node in the moved subtree through `move_subtree` in one `UnitOfWork`, and emits `document.moved.v1` (FR-F045-03).
- **SR-S089-04:** `PATCH /api/v1/documents/{id}` updates `title`, `archived`, and `search_visibility` under `If-Match`; stale returns `409 conflict` with `current_version` (FR-F045-04).
- **SR-S089-05:** `DELETE` soft-deletes the subtree through `soft_delete_subtree`, which selects descendants by `document_ancestors.ancestor_id`; `POST /restore` restores it with original IDs and re-parents an orphaned child to root with `restored_to_root: true` (FR-F045-05).
- **SR-S089-06:** `GET /api/v1/documents` lists children with cursor paging, `limit` ≤ 100, `kind`, `deleted`, `archived` filters, and `q` full-text search with snippets from `document_search` via `DocumentRepository::list_children` and `DocumentSearchRepository::search` (FR-F045-06).
- **SR-S089-07:** `POST /api/v1/documents/{id}/revisions` with `If-Match: <current_revision>` takes the `select ... for update` row lock through `DocumentRevisionRepository::lock_for_revision` so concurrent writers stay serialized, writes the object, records SHA-256 checksum and size, increments `current_revision`, and publishes `document.revision-added.v1`; stale returns `409` (FR-F045-07).
- **SR-S089-08:** `GET .../revisions` pages newest first and `GET .../revisions/{rev}` returns a presigned URL valid 15 minutes after verifying the checksum (FR-F045-08, FR-F045-09).
- **SR-S089-09:** Every mutation checks `Idempotency-Key`, writes an audit event, and enqueues the matching outbox event; foreign-tenant actors receive `404 not_found` (FR-F045-13).
- **SR-S089-10:** No SQL string, `sqlx::query*` call, or connection exists in `crates/domain/src/documents` or `services/api/src/documents`; every table read or written by this story goes through `DocumentRepository`, `DocumentRevisionRepository`, or `DocumentSearchRepository` (decision 2.1).

## Surfaces

- Infrastructure/container: MinIO bucket from the F004 compose baseline; no new services
- Rust service/API: `crates/domain/src/documents/{node.rs, revision.rs, tree.rs, search.rs, errors.rs, service.rs}` (repository traits only, no SQL); `crates/persistence/src/documents/{mod.rs, document_repository.rs, document_revision_repository.rs, document_search_repository.rs}`; `services/api/src/documents/{routes.rs, handlers_node.rs, handlers_revision.rs, dto.rs}`
- Data/migration: `services/api/migrations/<ts>_documents_create_tables.sql` creating `documents`, `document_ancestors`, `document_revisions`, `document_search` with the indexes from ticket section 4
- React/UI: none in this story (S090 and T179 cover UI)
- Mocks/fixtures: `testing/fixtures/documents.rs` tenant, workspace, editor, viewer, foreign-tenant builders and the 4-folder/25-document seeded tree; in-memory `ObjectStore`; in-memory outbox recorder

## TDD harness

- Test path: `testing/features/F045/api/` and `testing/features/F045/database/`
- Feature flag: `F045_FEATURE`
- Targeted command: `cargo xtask test-feature F045`
- Full command: `cargo xtask test-all`
- First failing tests: `document_create_writes_ancestor_rows_and_depth`, `document_sibling_title_conflicts`, `document_move_into_descendant_rejected`, `move_subtree_rewrites_ancestor_rows`, `document_restore_subtree_keeps_ids`, `revision_stale_if_match_conflicts`, `document_search_returns_snippets`

## Exit criteria

- [ ] Requirement tests SR-S089-01 through SR-S089-10 written first and failing
- [ ] Tasks T177 and T178 complete and wired through `services/api` router
- [ ] Unit, API, database, and permission tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/documents/routes.rs` mounted in `services/api/src/router.rs`
- [ ] Handoff evidence recorded in the F045 ticket
