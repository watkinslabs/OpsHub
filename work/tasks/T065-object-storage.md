---
id: T065
type: task
status: planned
parent_epic: E004
parent_feature: F017
parent_story: S033
depends_on: [S033]
owned_paths: [services/api/migrations/*_files_*.sql, crates/domain/src/files/**, services/api/src/files/**, testing/features/F017/database/**, testing/features/F017/api/**]
feature_flag: F017_FEATURE
branch: t065-object-storage
started_at: null
finished_at: null
---

# T065 — Object storage

## Identity

- Parent story: `S033` Attachments
- Owner: platform
- Branch: `t065-object-storage`
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 5; `docs/capability-contracts.md` row F017

## Objective

Create the files schema, the S3 `ObjectStore` adapter, and the upload, complete, metadata, download, and list routes so files land in object storage with metadata and checksums in PostgreSQL.

## Specification

- Owned paths: `services/api/migrations/<ts>_files_create_tables.sql`, `services/api/migrations/<ts>_files_create_tables.down.sql`, `crates/domain/src/files/{mod.rs, file.rs, version.rs, upload.rs, store.rs, s3_store.rs, allowlist.rs, errors.rs, service.rs, schema.rs}`, `services/api/src/files/{mod.rs, routes.rs, handlers_upload.rs, handlers_file.rs, dto.rs}`
- Contract/input: DDL for `files`, `file_versions`, `file_scans`, `proofs`, `proof_decisions`, `file_upload_tickets` per F017 ticket section 4; `StartUploadRequest { target_kind, target_id, file_name, mime_type, size_bytes, sha256 }`, `CompleteUploadRequest { sha256 }`, list query `{ cursor?, limit?, scan_state?, sort? }`, download query `{ version? }`; `ObjectStore` trait `{ presign_put(key, ttl), presign_get(key, ttl), head_object(key), copy_object(from, to), get_stream(key), delete_object(key) }` with an S3 implementation configured from `OPSHUB_S3_ENDPOINT`, bucket, and secret-manager credentials; storage key `tenant/<tenant_id>/files/<file_id>/<version>`.
- Output/behavior: routes `POST /api/v1/files/uploads` (tenant allowlist and size checks, ticket row, 15-minute presigned PUT), `PUT /api/v1/files/uploads/{id}/complete` (`head_object` size check, `files` and `file_versions` insert with `scan_state = pending`, `file.uploaded.v1`, enqueue `scan_file`), `GET /api/v1/files/{id}` (`FileResponse` with versions and preview), `GET /api/v1/files/{id}/download` (`302` when clean, `409` pending, `403` quarantined, `file.download` audit), `GET /api/v1/{target_kind}/{target_id}/files` (`Page<FileResponse>`); errors per ticket section 4; `sqlx migrate revert` drops the six tables.
- Dependencies: F006 `rows` and `sheets` for target validation; F003 `authz::require(actor, Permission::Edit, target)`; F004 outbox writer, JetStream job enqueue, and secret manager; MinIO from compose.
- Feature flag: `F017_FEATURE` gates router mounting; migration runs regardless.

## TDD

- Failing test first: `testing/features/F017/database/migration_tests.rs::files_tables_exist_with_constraints`, `::scan_state_check_enforced`, `::rollback_drops_tables`; `testing/features/F017/api/upload_tests.rs::upload_start_returns_presigned_put`, `::upload_mime_not_allowed_invalid`, `::upload_size_over_limit_invalid`, `::upload_complete_missing_object_conflicts`, `::upload_complete_creates_pending_version`, `::upload_viewer_denied`, `::file_cross_tenant_not_found`; `testing/features/F017/api/download_tests.rs::download_pending_conflicts`, `::download_clean_redirects_with_expiry`
- Targeted command: `cargo xtask test-feature F017`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/files.rs` tenants A and B, editor, viewer; MinIO harness bucket prefix per worker; schema-per-worker database; in-memory outbox recorder

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; router mounted in `services/api/src/router.rs` behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S033
- [ ] `finished_at` recorded
