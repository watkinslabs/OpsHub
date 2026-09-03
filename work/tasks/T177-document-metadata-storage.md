---
id: T177
type: task
status: planned
parent_epic: E004
parent_feature: F045
parent_story: S089
depends_on: [S089]
owned_paths: [services/api/migrations/*_documents_*.sql, crates/domain/src/documents/**, services/api/src/documents/**, testing/features/F045/database/**, testing/features/F045/api/**]
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

Create the `documents`, `document_revisions`, and `document_search` schema and the node and revision services so documents can be created, updated, trashed, restored, and versioned with immutable object-storage revisions.

## Specification

- Owned paths: `services/api/migrations/<ts>_documents_create_tables.sql`, `services/api/migrations/<ts>_documents_create_tables.down.sql`, `crates/domain/src/documents/{mod.rs, node.rs, revision.rs, errors.rs, service.rs, schema.rs}`, `services/api/src/documents/{mod.rs, routes.rs, handlers_node.rs, handlers_revision.rs, dto.rs}`
- Contract/input: DDL per F045 ticket section 4: three tables with tenant, UUIDv7, version, audit, and soft-delete columns, `depth <= 32` check, sibling title partial unique index, `(document_id, revision)` unique index, GIN indexes on `path` and `tsv`, `documents_path_check` trigger; requests `CreateDocumentRequest`, `UpdateDocumentRequest`, `AddRevisionRequest` with `Idempotency-Key` and `If-Match`.
- Output/behavior: routes `GET/POST /api/v1/documents`, `GET/PATCH/DELETE /api/v1/documents/{id}`, `POST /api/v1/documents/{id}/restore`, `GET/POST /api/v1/documents/{id}/revisions`, `GET /api/v1/documents/{id}/revisions/{rev}` return `DocumentResponse`, `RevisionResponse`, and `RevisionDownloadResponse`; `add_revision` locks the document row, writes the object through the F017 `ObjectStore`, records the SHA-256 checksum, and aborts the transaction on a failed put; `get_revision_download` verifies the checksum and returns a 15-minute presigned URL; subtree delete and restore batch 1,000 nodes per statement; events `document.created.v1`, `document.updated.v1`, `document.deleted.v1`, `document.restored.v1`, `document.revision-added.v1`; `sqlx migrate revert` drops the tables and trigger.
- Dependencies: F005 `workspaces` table; F017 storage client and presigned URL helper; F003 authz and audit writer; F004 outbox writer.
- Feature flag: `F045_FEATURE` gates router mounting; migration runs regardless.
- Large-table note: no existing data; future columns must be additive and nullable.

## TDD

- Failing test first: `testing/features/F045/database/migration_tests.rs::documents_tables_exist_with_constraints`, `::sibling_title_duplicate_rejected`, `::revision_number_unique_per_document`, `::depth_over_32_rejected`, `::rollback_drops_tables`; `testing/features/F045/api/document_tests.rs::document_create_returns_version_one_and_path`, `::document_restore_subtree_keeps_ids`; `testing/features/F045/api/revision_tests.rs::revision_stale_if_match_conflicts`, `::revision_failed_put_rolls_back_metadata`, `::revision_download_verifies_checksum`
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
