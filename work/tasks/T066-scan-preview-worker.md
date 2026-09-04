---
id: T066
type: task
status: planned
parent_epic: E004
parent_feature: F017
parent_story: S033
depends_on: [T065]
owned_paths: [crates/domain/src/files/**, crates/persistence/src/files/**, services/worker/src/files/**, testing/features/F017/api/**, testing/features/F017/performance/**, testing/features/F017/requirements/**]
feature_flag: F017_FEATURE
branch: t066-scan-preview-worker
started_at: null
finished_at: null
---

# T066 — Scan/preview worker

## Identity

- Parent story: `S033` Attachments
- Owner: platform
- Branch: `t066-scan-preview-worker`
- Decision references: `docs/architecture-decisions.md` sections 5, 7; `docs/capability-contracts.md` row F017

## Objective

Implement the `scan_file`, `render_preview`, and upload-ticket sweeper worker jobs so every completed upload is ClamAV-scanned and checksum-verified before download and clean images and PDFs get thumbnails.

## Specification

- Owned paths: `crates/domain/src/files/{scanner.rs, preview.rs}`, `crates/persistence/src/files/{file_repository.rs, file_scan_repository.rs, upload_ticket_repository.rs}`, `services/worker/src/files/{mod.rs, scan_job.rs, preview_job.rs, ticket_sweeper.rs}`
- Contract/input: JetStream job subjects `files.scan` with payload `{ tenant_id, file_id, version, correlation_id }`, `files.preview` with the same payload, and a cron `files.sweep_tickets` every hour; `ClamScanner` trait `{ scan_stream(reader) -> ScanResult { Clean | Infected { signature } | Error } }` implemented over the `clamd` INSTREAM socket at `OPSHUB_CLAMD_ADDR`; `ObjectStore` from T065.
- Output/behavior: `scan_file` loads the version through `FileRepository::get`, returns early when `scan_state != pending` (idempotent), streams the object through `clamd` with a 120 s timeout while hashing SHA-256; clean and matching checksum → `FileRepository::set_scan_state(file_id, version, clean)`, a `FileScanRepository::insert` row with `duration_ms` and `signature_db_version`, `file.scanned.v1`, enqueue `files.preview`; infected or mismatched → `copy_object` to `quarantine/<key>`, `delete_object(key)`, `set_scan_state(..., quarantined)`, a scan row carrying `signature`, `file.quarantined.v1`; scanner error → retry with backoff 5 s, 25 s, 125 s, 625 s, 3125 s then dead-letter with state left `pending`; `render_preview` produces 320 px WebP for `image/*` and 1,024 px first-page WebP for `application/pdf` under `previews/<file_id>/<version>.webp` with a 30 s timeout and sets `preview_state` to `ready`, `unsupported`, or `failed` through `FileRepository`; `ticket_sweeper` calls `UploadTicketRepository::claim_expired_tickets(now, limit)` hourly and deletes the orphan objects for the claimed rows — no inline `DELETE` in the job; the jobs hold no SQL and reach every table through `crates/persistence/src/files/`; a `find_pending_scans(limit)` sweep re-enqueues versions left `pending`; metrics `file_scan_duration_seconds`, `file_quarantined_total`, `file_preview_failures_total`.
- Dependencies: T065 tables, repositories, and store; F004 worker job registry, retry policy, dead letters, metrics exporter; `clamd` service from compose.
- Feature flag: `F017_FEATURE` gates job registration in `services/worker/src/jobs.rs`.

## TDD

- Failing test first: `testing/features/F017/api/scan_tests.rs::scan_clean_sets_state_and_publishes`, `::scan_eicar_quarantines_file`, `::scan_checksum_mismatch_quarantines`, `::scan_replay_is_noop_when_not_pending`, `::scan_error_dead_letters_after_five_attempts`, `::preview_image_and_pdf_ready`, `::preview_unsupported_type_marked`, `::sweeper_claims_expired_tickets_via_repository`; `testing/features/F017/performance/scan_bench.rs::scan_250mb_within_120s`
- Targeted command: `cargo xtask test-feature F017`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `ClamScanner` stub keyed by EICAR content and a failing variant; MinIO harness; embedded JetStream from `testing/harness/nats.rs`; fixed clock

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Jobs registered in `services/worker/src/jobs.rs` behind the flag; dead-letter path verified
- [ ] `cargo xtask check-persistence` passes: no SQL in `services/worker/src/files/`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S033
- [ ] `finished_at` recorded
