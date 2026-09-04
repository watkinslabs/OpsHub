---
id: T177
type: task
status: planned
parent_epic: E004
parent_feature: F045
parent_story: S089
depends_on: [S089]
owned_paths: [services/api/migrations/*_documents_*.sql, crates/domain/src/documents/**, crates/persistence/src/documents/**, services/api/src/documents/**, testing/features/F045/database/**, testing/features/F045/api/**]
feature_flag: F045_FEATURE
branch: t177-document-metadata-storage
started_at: null
finished_at: null
---

# T177 — Document metadata/storage

## Identity

- Parent story: `S089` Document library
- Owner: platform
- Branch: `t177-document-metadata-storage`
- Decision references: `docs/architecture-decisions.md` sections 2, 5; `docs/capability-contracts.md` row F045

## Objective

Create the `documents`, `document_ancestors`, `document_revisions`, and `document_search` schema, the repositories in `crates/persistence/src/documents/`, and the node and revision use cases so documents can be created, updated, trashed, restored, and versioned with immutable object-storage revisions.

## Specification

- Owned paths: `services/api/migrations/<ts>_documents_create_tables.sql`, `services/api/migrations/<ts>_documents_create_tables.down.sql`, `crates/persistence/src/documents/{mod.rs, document_repository.rs, document_revision_repository.rs, document_search_repository.rs}`, `crates/domain/src/documents/{mod.rs, node.rs, revision.rs, errors.rs, service.rs, repository.rs}` (repository traits only, no SQL), `services/api/src/documents/{mod.rs, routes.rs, handlers_node.rs, handlers_revision.rs, dto.rs}`
- Contract/input: DDL per F045 ticket section 4: four tables with tenant, UUIDv7, version, audit, and soft-delete columns, `documents` plus the `document_ancestors` closure table (`primary key (document_id, ancestor_id)`, `distance >= 1`, both foreign keys `on delete cascade`), `depth <= 32` check, sibling title partial unique index, `(document_id, revision)` unique index, `document_ancestors(ancestor_id, distance)` and `document_ancestors(tenant_id, ancestor_id)` b-trees, GIN index on `tsv`; requests `CreateDocumentRequest`, `UpdateDocumentRequest`, `AddRevisionRequest` with `Idempotency-Key` and `If-Match`.
- Output/behavior: routes `GET/POST /api/v1/documents`, `GET/PATCH/DELETE /api/v1/documents/{id}`, `POST /api/v1/documents/{id}/restore`, `GET/POST /api/v1/documents/{id}/revisions`, `GET /api/v1/documents/{id}/revisions/{rev}` return `DocumentResponse`, `RevisionResponse`, and `RevisionDownloadResponse`; `create_node` writes the `documents` row and its `document_ancestors` rows and sets `depth = count(document_ancestors)` in one `UnitOfWork`; `add_revision` takes the row lock through `DocumentRevisionRepository::lock_for_revision` (`select ... for update`, still serializing concurrent revision writers), assigns `next_revision` as `current_revision + 1`, writes the object through the F017 `ObjectStore` adapter, records the SHA-256 checksum, and aborts the transaction on a failed put, with the revision row, `current_revision` bump, `document_search` upsert, and outbox enqueue in one `UnitOfWork`; `get_revision_download` verifies the checksum and returns a 15-minute presigned URL; `soft_delete_subtree` and restore batch 1,000 nodes per statement, selecting descendants by `document_ancestors.ancestor_id`; no SQL string, `sqlx::query*` call, or connection exists in `crates/domain/src/documents` or `services/api/src/documents`; events `document.created.v1`, `document.updated.v1`, `document.deleted.v1`, `document.restored.v1`, `document.revision-added.v1`; `sqlx migrate revert` drops all four tables.
- Dependencies: F005 `workspaces` table; F017 storage client and presigned URL helper; F003 authz and audit writer; F004 outbox writer.
- Feature flag: `F045_FEATURE` gates router mounting; migration runs regardless.
- Large-table note: no existing data; future columns must be additive and nullable.

## TDD

- Failing test first: `testing/features/F045/database/migration_tests.rs::documents_tables_exist_with_constraints`, `::sibling_title_duplicate_rejected`, `::revision_number_unique_per_document`, `::document_ancestors_distance_check_rejects_zero`, `::depth_over_32_rejected`, `::rollback_drops_four_tables`; `testing/features/F045/api/document_tests.rs::document_create_writes_ancestor_rows_and_depth`, `::document_restore_subtree_keeps_ids`; `testing/features/F045/api/revision_tests.rs::revision_stale_if_match_conflicts`, `::revision_failed_put_rolls_back_metadata`, `::revision_download_verifies_checksum`, `::lock_for_revision_serializes_concurrent_writers`
- Targeted command: `cargo xtask test-feature F045`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: schema-per-worker database from `testing/harness/db.rs`; in-memory `ObjectStore` with a failing-put mode; in-memory outbox recorder

## Exit criteria

- [ ] Tests written before the migration and services and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; router mounted in `services/api/src/router.rs` behind the flag
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S089
- [ ] `finished_at` recorded
