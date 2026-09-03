---
id: S033
type: story
status: planned
parent_epic: E004
parent_feature: F017
depends_on: [F006, F004]
owned_paths: [crates/domain/src/files/**, services/api/src/files/**, services/worker/src/files/**, services/api/migrations/*_files_*.sql, testing/features/F017/**]
feature_flag: F017_FEATURE
branch: s033-attachments
started_at: null
finished_at: null
---

# S033 — Attachments

## Identity

- Parent feature: `F017` Files and proofing
- Owner: platform
- Branch: `s033-attachments`
- Decision references: `docs/architecture-decisions.md` sections 2–5, 7; `docs/capability-contracts.md` row F017

## Vertical slice

As a sheet editor, I want to upload a file to a row through a presigned S3 URL, have it virus-scanned and checksummed before anyone can download it, and see a preview thumbnail, so that attachments are safe and stored outside the transactional database.

## Requirements

- **SR-S033-01:** `POST /api/v1/files/uploads` validates the tenant MIME allowlist and size limit, writes a `file_upload_tickets` row, and returns a presigned PUT URL that expires in 15 minutes (covers FR-F017-01, FR-F017-02).
- **SR-S033-02:** `PUT /api/v1/files/uploads/{id}/complete` calls `head_object`, rejects a missing object with `409 conflict`, creates `files` and `file_versions` rows with `scan_state = pending`, publishes `file.uploaded.v1`, and enqueues `scan_file` (FR-F017-03).
- **SR-S033-03:** Worker job `scan_file` streams the object to `clamd`, recomputes SHA-256, sets `clean` and publishes `file.scanned.v1`, or moves the object to `quarantine/`, sets `quarantined`, records the signature in `file_scans`, and publishes `file.quarantined.v1` (FR-F017-04).
- **SR-S033-04:** `GET /api/v1/files/{id}/download` returns `302` to a 15-minute presigned GET only for `clean` versions; `pending` returns `409 conflict` and `quarantined` returns `403 denied` (FR-F017-05).
- **SR-S033-05:** Worker job `render_preview` writes a WebP thumbnail for images and a first-page render for PDFs and sets `preview_state`; unsupported types report `unsupported` (FR-F017-07).
- **SR-S033-06:** `GET /api/v1/files/{id}` and `GET /api/v1/{target_kind}/{target_id}/files` return metadata, versions, scan and preview state, cursor paging with `limit` ≤ 100, and `scan_state` filter (FR-F017-06, FR-F017-10).
- **SR-S033-07:** Every mutation checks `Idempotency-Key`, writes an audit row, and enqueues its outbox event; viewers receive `403 denied` and foreign tenants `404 not_found`; jobs are idempotent by `(file_id, version)` and dead-letter after 5 attempts (FR-F017-15, NFR-F017-04).

## Surfaces

- Infrastructure/container: MinIO and `clamd` services from `infra/compose.yml` (F004 baseline); bucket `opshub-files` created by the worker on startup
- Rust service/API: `crates/domain/src/files/{file.rs, version.rs, upload.rs, store.rs, scanner.rs, allowlist.rs, errors.rs, service.rs}`; `services/api/src/files/{routes.rs, handlers_upload.rs, handlers_file.rs, dto.rs}`; `services/worker/src/files/{scan_job.rs, preview_job.rs, ticket_sweeper.rs}`
- Data/migration: `services/api/migrations/<ts>_files_create_tables.sql` creating `files`, `file_versions`, `file_scans`, `proofs`, `proof_decisions`, `file_upload_tickets` with constraints and indexes from ticket section 4
- React/UI: none in this story (S034 covers the file tab, version drawer, and proof panel)
- Mocks/fixtures: `testing/fixtures/files.rs` tenant, row, editor, viewer, foreign tenant, clean PDF, PNG, EICAR file; MinIO harness bucket prefix per worker; `ClamScanner` stub keyed by content

## TDD harness

- Test path: `testing/features/F017/api/`, `testing/features/F017/database/`, `testing/features/F017/performance/`
- Feature flag: `F017_FEATURE`
- Targeted command: `cargo xtask test-feature F017`
- Full command: `cargo xtask test-all`
- First failing tests: `upload_start_returns_presigned_put`, `upload_mime_not_allowed_invalid`, `upload_complete_missing_object_conflicts`, `scan_eicar_quarantines_file`, `download_pending_conflicts`, `download_quarantined_denied`, `upload_viewer_denied`

## Exit criteria

- [ ] Requirement tests SR-S033-01 through SR-S033-07 written first and failing
- [ ] Tasks T065 and T066 complete and wired through `services/api` router and `services/worker` job registry
- [ ] Unit, API, worker, database, permission, and performance tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/files/routes.rs` mounted in `services/api/src/router.rs`; `services/worker/src/files/scan_job.rs` registered in `services/worker/src/jobs.rs`
- [ ] Handoff evidence recorded in the F017 ticket
