---
id: F017
type: feature
status: planned
priority: P1
owner: platform
estimate: 8
target_milestone: M3
parent_epic: E004
depends_on: [F006, F004]
blocks: [F045, F057]
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/files/**, crates/persistence/src/files/**, services/api/src/files/**, services/worker/src/files/**, apps/web/src/features/files/**, services/api/migrations/*_files_*.sql, testing/features/F017/**]
feature_flag: F017_FEATURE
flag_default: off
branch: f017-files-and-proofing
started_at: null
finished_at: null
---

# F017 — Files and proofing

## 1. Identity and dates

- Branch: `f017-files-and-proofing`
- Capability area: collaboration and file service (spec 5.4b COLLAB-02, COLLAB-04; 5.1 WORK-02 attachments; section 4 File/FileVersion entity)
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 5, 7; `docs/capability-contracts.md` row F017
- Aggregate: `file`
- Module slug: `files`

## 2. Requirement specification

### Problem and user outcome

Work items reference specifications, screenshots, contracts, and design drafts that today live in chat threads and personal drives. Teams need attachments on rows and sheets that are safe to open, keep their history when replaced, can be previewed without downloading, and can be sent for a recorded approve or reject decision.

As a sheet editor, I want to attach a file to a row, know it has been virus-scanned before anyone downloads it, upload a new version without losing the old one, and ask reviewers for a decision, so that the artifacts behind our work are safe, traceable, and reviewable.

### Functional requirements

- **FR-F017-01:** An actor with `resource-editor` on the target can `POST /api/v1/files/uploads` with `{ target_kind, target_id, file_name, mime_type, size_bytes, sha256 }` where `target_kind` is `row`, `sheet`, `comment`, or `document`; the response returns `{ upload_id, put_url, expires_at, max_size_bytes }` with a presigned S3 PUT URL valid for 15 minutes.
- **FR-F017-02:** The tenant MIME allowlist defaults to `image/png`, `image/jpeg`, `image/gif`, `image/webp`, `application/pdf`, `text/csv`, `text/plain`, the Office document, spreadsheet, and presentation types, and `application/zip`; a MIME outside the allowlist or `size_bytes` above the tenant limit (default 250 MB, hard cap 2 GB) returns `400 invalid` with `field_errors.mime_type = "not_allowed"` or `field_errors.size_bytes = "too_large"`.
- **FR-F017-03:** `PUT /api/v1/files/uploads/{id}/complete` verifies the object exists in S3 with the declared size, records `files` and `file_versions` rows with `scan_state = pending` and the declared `sha256`, publishes `file.uploaded.v1`, and returns the file with version 1; a missing object returns `409 conflict` with code `conflict` and `field_errors.upload = "object_missing"`; an expired upload returns `410`-equivalent `not_found`.
- **FR-F017-04:** The worker job `scan_file` streams the object through ClamAV, recomputes SHA-256, and on a clean result with a matching checksum sets `scan_state = clean` and publishes `file.scanned.v1`; on a detection or checksum mismatch it sets `scan_state = quarantined`, moves the object to the `quarantine/` prefix, records `file_scans.signature`, and publishes `file.quarantined.v1`.
- **FR-F017-05:** `GET /api/v1/files/{id}/download` returns `302` to a presigned GET URL valid for 15 minutes only when the current version's `scan_state` is `clean`; `pending` returns `409 conflict` with `field_errors.scan_state = "pending"` and `quarantined` returns `403 denied` with `field_errors.scan_state = "quarantined"`; `?version=<n>` downloads a specific clean version.
- **FR-F017-06:** `GET /api/v1/files/{id}` returns `{ id, target, file_name, mime_type, size_bytes, sha256, current_version, scan_state, preview: { state, url? }, versions: [ { version, size_bytes, sha256, scan_state, created_by, created_at } ], proof?: ProofSummary, version, audit fields }`.
- **FR-F017-07:** The worker job `render_preview` produces, for clean files, a 320 px WebP thumbnail for images and a first-page 1,024 px WebP render for PDFs, stored under `previews/<file_id>/<version>.webp` and exposed through `preview.url` as a 15-minute presigned URL; unsupported types report `preview.state = unsupported`.
- **FR-F017-08:** `POST /api/v1/files/{id}/versions` accepts the same upload body as FR-F017-01, creates `file_versions` row `current_version + 1` after `complete`, keeps every earlier version downloadable, publishes `file.version-added.v1`, and requires `If-Match` on the file version.
- **FR-F017-09:** `DELETE /api/v1/files/{id}` soft-deletes the file and all versions, publishes `file.deleted.v1`, and hides it from `GET /api/v1/{target_kind}/{target_id}/files`; objects are purged from S3 only by the F027 retention job after the tenant window.
- **FR-F017-10:** `GET /api/v1/{target_kind}/{target_id}/files` lists non-deleted files for the target with cursor paging, `limit` 1–100, filter `scan_state`, and sort by `file_name` or `created_at`; the actor needs read access to the target.
- **FR-F017-11:** `POST /api/v1/files/{id}/proofs` with `{ reviewer_ids (1–20), due_at?, instructions? }` creates a `proofs` row in state `open` bound to the current version plus one `proof_reviewers` row per reviewer with `position` 1..n in request order, all in one transaction; a second open proof on the same file returns `409 conflict`; a duplicate reviewer or an empty list returns `400 invalid` with `field_errors.reviewer_ids`, and reviewers must have read access to the target or the call returns `400 invalid` with `field_errors.reviewer_ids`. The request and the `ProofResponse` keep a `reviewer_ids` array on the wire; the repository assembles it from `proof_reviewers` ordered by `position`.
- **FR-F017-12:** `POST /api/v1/proofs/{id}/decisions` with `{ decision: approved|rejected|changes_requested, reason? (required for rejected and changes_requested, ≤ 2,000 chars) }` by a reviewer with a `proof_reviewers` row records one `proof_decisions` row per reviewer (a repeat returns `409 conflict`); the proof becomes `approved` when every `proof_reviewers` row has an approving decision, `rejected` on the first rejection, and `changes_requested` on the first such decision, and each state change publishes `proof.decided.v1`; a non-reviewer receives `403 denied`.
- **FR-F017-13:** Uploading a new version to a file with an `open` proof closes that proof as `superseded` and publishes `proof.decided.v1` with `outcome = superseded`.
- **FR-F017-14:** The web app renders a `FileList` on the row drawer and sheet header with upload drop zone and progress, scan state badges, preview thumbnails, a version history drawer, and a proof panel where reviewers decide; download and preview controls are disabled until the scan is clean.
- **FR-F017-15:** Every mutation requires `Idempotency-Key`, writes an `audit_events` row, and publishes the matching `file.*.v1` or `proof.*.v1` event through the outbox; cross-tenant IDs return `404 not_found` and a viewer's mutation returns `403 denied`.

### Non-functional requirements

- **NFR-F017-01 Performance:** upload initiation and completion respond under 800 ms p95; file metadata and list reads respond under 500 ms p95; scan of a 250 MB file completes within 120 s and preview within 30 s p95; async job acknowledgement under 2 s (spec section 6).
- **NFR-F017-02 Security/privacy:** objects are stored under `tenant/<tenant_id>/files/<file_id>/<version>` with server-side encryption; presigned URLs expire in 15 minutes and are bound to a single object; quarantined objects are never served; ClamAV signatures are updated at least daily; checksums are verified on the server, never trusted from the client alone.
- **NFR-F017-03 Accessibility:** drop zone, progress, scan badges, version drawer, and proof panel pass axe with zero serious violations; upload is possible through a keyboard-triggered file input; scan completion and decisions are announced through a live region.
- **NFR-F017-04 Reliability/observability:** `scan_file` and `render_preview` are idempotent by `(file_id, version)`, retry with exponential backoff up to 5 attempts, and dead-letter with the file left in `pending`; metrics `file_scan_duration_seconds`, `file_quarantined_total`, `file_preview_failures_total`, and `file_upload_bytes_total` are exported; spans carry `tenant_id`, `file_id`, `version`, and `correlation_id`.

### Scope

Included: presigned upload and completion, per-proof reviewer rows, MIME and size allowlists, ClamAV scan, checksum verification, quarantine, expiring download URLs, previews for images and PDFs, versions, soft delete, per-target file list, proofs with reviewer decisions, file list and proof UI, audit and outbox events.

Excluded: comment body attachments UI (F016 references file IDs), document revisions (F045), DAM renditions and rights (F057), retention purge of objects (F027), form upload fields (F014 calls the upload routes), notification delivery for proof requests (F037 consumes `proof.decided.v1`), external file connectors (F030).

## 3. UX specification

- Entry points: row drawer tab `Files` at `/w/{workspace_id}/sheets/{sheet_id}?row={row_id}&tab=files`; sheet header icon `Paperclip`; file card menu `Versions` and `Request review`; reviewer inbox link `/files/{file_id}/proof` reached from the F037 notification.
- Primary flow: open a row, drop `spec.pdf` on the zone, progress bar reaches 100 %, card shows `Scanning`; within seconds the badge turns `Clean`, a thumbnail appears, `Download` enables; click `Request review`, pick two reviewers and a due date; each reviewer opens the proof panel, previews the PDF, clicks `Approve`; the card shows `Approved 2/2`.
- Loading: skeleton cards; Empty: `No files attached. Drop files here or browse.`; Error: banner with `correlation_id` and retry, per-file retry for failed uploads; Success: toast `spec.pdf uploaded`; Stale/conflict: version upload with stale `If-Match` shows `A newer version exists` with reload; Offline: drop zone disabled with offline badge.
- Permission-denied: viewers see cards without upload, delete, or version controls; a quarantined file shows a red `Quarantined` badge with the reason and no download for anyone; non-members see the not-found page.
- Responsive: cards become a single column under 640 px; the version drawer becomes full-screen under 768 px.
- Keyboard: `Enter` or `Space` on the drop zone opens the file picker; arrow keys move between cards; `Delete` prompts for delete; proof decisions are buttons in a labelled group; focus returns to the card after dialogs; motion respects `prefers-reduced-motion`.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062); Lucide `Paperclip`, `Upload`, `ShieldCheck`, `ShieldAlert`, `History`, `Download`, `CheckCircle2`, `XCircle`; tokens from `apps/web/src/design/tokens.css`.

- Design: `design/artboards/Proofing.dc.html` on the canvas indexed by `design/canvas.json`. The ticket is the contract and the artboard is the picture; when they disagree the ticket wins.

## 4. Technical specification

### Rust backend

- Domain entities in `crates/domain/src/files/`: `File { id, tenant_id, target: TargetRef, file_name, mime_type: Mime, current_version: i32, version, audit fields, deleted_at }`, `FileVersion { file_id, version: i32, storage_key, size_bytes, sha256: Checksum, scan_state: ScanState { Pending, Clean, Quarantined }, preview_state: PreviewState { Pending, Ready, Unsupported, Failed }, created_by, created_at }`, `FileScan { id, file_id, version, engine, signature_db_version, result, signature, scanned_at }`, `Proof { id, tenant_id, file_id, file_version, state: ProofState { Open, Approved, Rejected, ChangesRequested, Superseded }, due_at, instructions, version, audit fields }`, `ProofReviewer { id, proof_id, reviewer_id, position: i16, created_by, created_at }`, `ProofDecision { id, proof_id, reviewer_id, decision, reason, decided_at }`, `UploadTicket { id, tenant_id, file_id?, storage_key, declared: UploadDeclaration, expires_at }`.
- Use cases: `start_upload`, `complete_upload`, `get_file`, `sign_download`, `add_version`, `delete_file`, `list_files`, `create_proof`, `record_decision`, `supersede_proof`; worker jobs in `services/worker/src/files/`: `scan_file`, `render_preview`.
- API endpoints (`services/api/src/files/`): `POST /api/v1/files/uploads`, `PUT /api/v1/files/uploads/{id}/complete`, `GET /api/v1/files/{id}`, `GET /api/v1/files/{id}/download`, `POST /api/v1/files/{id}/versions`, `DELETE /api/v1/files/{id}`, `POST /api/v1/files/{id}/proofs`, `POST /api/v1/proofs/{id}/decisions`, `GET /api/v1/{target_kind}/{target_id}/files`. DTOs `StartUploadRequest`, `UploadTicketResponse`, `CompleteUploadRequest { sha256 }`, `FileResponse`, `FileVersionResponse`, `Page<FileResponse>`, `CreateProofRequest`, `ProofResponse`, `DecisionRequest`, `DownloadRedirect`.
- Events: `file.uploaded.v1`, `file.scanned.v1`, `file.quarantined.v1`, `file.version-added.v1`, `file.deleted.v1`, `proof.decided.v1`; payloads carry `file_id`, `version`, `target_kind`, `target_id`, and for proofs `proof_id`, `outcome`, `reviewer_id`.
- Persistence (`crates/persistence/src/files/`): `FileRepository` owns `files` and `file_versions`; `FileScanRepository` owns `file_scans`; `ProofRepository` owns `proofs`, `proof_reviewers`, and `proof_decisions`; `UploadTicketRepository` owns `file_upload_tickets`. Each implements the shared `Repository` contract (`get`, `list` with cursor pagination, `insert`, `update` under an expected version, `soft_delete`, `restore`, `purge`) and adds named queries `list_for_target(target_kind, target_id, cursor)`, `next_version(file_id)`, `find_pending_scans(limit)`, `set_scan_state(file_id, version, state)`, `find_open_proof(file_id)`, `list_reviewers(proof_id)`, `page_proofs_for_reviewer(reviewer_id, cursor)`, `record_decision(proof_id, reviewer_id, decision)`, and `claim_expired_tickets(now, limit)`; the tenant predicate, soft-delete filter, version check, audit row, and outbox enqueue come from the base contract. `list_reviewers` orders by `position` and supplies the `reviewer_ids` array the DTOs carry; `page_proofs_for_reviewer` rides the `proof_reviewers(tenant_id, reviewer_id)` index. Multi-table writes — completing an upload (version row, file row, ticket consumption) and deciding a proof (decision row plus the proof state transition) — run in one `UnitOfWork` that owns the transaction. The `scan_file` and `render_preview` jobs call `FileScanRepository` and `FileRepository` and hold no SQL, and the hourly expired-ticket sweep is `UploadTicketRepository::claim_expired_tickets`, not an inline `DELETE`. Object-storage access stays in the `ObjectStore` adapter and is not a repository concern. Per decision 2.1 the use cases above depend on these repository traits and contain no SQL: no SQL string, `sqlx::query*` call, or connection exists in `crates/domain/src/files`, `services/api/src/files`, or `services/worker/src/files`.
- Storage: `ObjectStore` trait in `crates/domain/src/files/store.rs` with the S3 implementation (MinIO locally) using presigned PUT/GET, `head_object`, `copy_object` to quarantine, and streaming `get_object` for the scanner; `ClamScanner` trait wraps the `clamd` INSTREAM protocol.
- Authorization: `resource-editor` on the target for upload, version, delete, and proof creation; target read for metadata, list, and download; a `proof_reviewers` row for the actor for decisions; explicit deny wins; unreadable targets map to `not_found`.
- Validation: `file_name` 1–255 chars without path separators, `mime_type` in tenant allowlist, `size_bytes` ≤ tenant limit, `sha256` 64 hex chars, `reviewer_ids` 1–20 unique on the wire and stored as `proof_reviewers` rows, `reason` ≤ 2,000 chars; idempotency for 24 hours; `If-Match` on version routes.
- Error mapping: `FileError::MimeNotAllowed → 400 invalid`, `FileError::TooLarge → 400 invalid`, `FileError::ObjectMissing → 409 conflict`, `FileError::ScanPending → 409 conflict`, `FileError::Quarantined → 403 denied`, `FileError::ProofAlreadyOpen → 409 conflict`, `FileError::DecisionExists → 409 conflict`, `FileError::NotReviewer → 403 denied`, `FileError::StaleVersion → 409 conflict`, `FileError::NotFound → 404 not_found`, `StoreError::Unavailable → 503 unavailable`.

### Interface

Exact shapes. Every field lists its JSON name, type, whether it is required, and the constraint that
makes it invalid. `T?` is nullable; a missing optional field and an explicit `null` mean the same
thing. Ids are UUIDv7 strings, timestamps are RFC 3339 UTC, `version` increments by one per write.
Unlisted fields are rejected with `400 invalid`. `Page<T>` and its opaque cursor are F028's; the
error envelope and the six codes are the shared ones.

**Upload flow.** Bytes never pass through the API. `POST /api/v1/files/uploads` validates the
declaration and returns a presigned S3 PUT URL; the browser PUTs the object directly to object
storage; `PUT /api/v1/files/uploads/{id}/complete` turns the ticket into `files` and `file_versions`
rows. There is no multipart request body on any route in this feature, and the API never accepts
file bytes.

**File states.** A version moves through exactly these, and every one is observable:

| Stage | States | Moves on |
|---|---|---|
| ticket | `open` → `consumed` \| `expired` | `complete` consumes it; the hourly sweep expires it after 15 minutes |
| `scan_state` | `pending` → `clean` \| `quarantined` | the `scan_file` worker; a dead-lettered scan leaves `pending`, never `clean` |
| `preview_state` | `pending` → `ready` \| `unsupported` \| `failed` | the `render_preview` worker, only after `clean` |
| file | live → soft-deleted → purged | `DELETE`, then the F027 retention job |
| proof | `open` → `approved` \| `rejected` \| `changes_requested` \| `superseded` | reviewer decisions, or a new file version |

`scan_state` gates download absolutely: `pending` is `409 conflict`, `quarantined` is `403 denied`,
and only `clean` yields a URL. `preview_state` gates nothing.

**`StartUploadRequest`** — `POST /api/v1/files/uploads`

| Field | Type | Required | Constraint |
|---|---|---|---|
| `target_kind` | `"row" \| "sheet" \| "comment" \| "document"` | yes | closed set, matching the `files.target_kind` check |
| `target_id` | uuid | yes | a live target of that kind the caller holds `resource-editor` on; unreadable → `404 not_found`, readable but not editable → `403 denied` |
| `file_name` | string | yes | 1–255 chars, no `/` or `\` and no `..` segment |
| `mime_type` | string | yes | in the tenant allowlist, else `400 invalid` with `field_errors.mime_type = "not_allowed"` |
| `size_bytes` | integer | yes | 1 to the tenant limit (default 250 MB, hard cap 2 GB), else `400 invalid` with `field_errors.size_bytes = "too_large"` |
| `sha256` | string | yes | 64 lowercase hex chars; a client claim, re-derived by the scanner and never trusted alone |

**`AddVersionRequest`** — `POST /api/v1/files/{id}/versions`: the same six fields, except
`target_kind` and `target_id`, which are rejected because the version inherits the file's target.
`If-Match: <file version>` is required.

**`UploadTicketResponse`**

| Field | Type | Notes |
|---|---|---|
| `upload_id` | uuid | pass to `complete` |
| `put_url` | string | presigned S3 PUT, valid 15 minutes, bound to one object key |
| `expires_at` | timestamp | when `put_url` and the ticket both die |
| `max_size_bytes` | integer | the tenant limit that was applied, so the client can fail fast |

**`CompleteUploadRequest`** — `PUT /api/v1/files/uploads/{id}/complete`: `{ sha256: string }`, the
64-hex digest of the bytes actually PUT. It must equal the ticket's declared `sha256`; a mismatch is
`400 invalid` with `field_errors.sha256`. `Idempotency-Key` is required; a replay returns the
original `FileResponse`.

**`FileVersionResponse`**

| Field | Type | Notes |
|---|---|---|
| `version` | integer | 1-based, dense |
| `size_bytes` | integer | the size verified against object storage, not the declaration |
| `sha256` | string | 64 hex chars; the scanner's recomputed digest once scanned, the declaration before that |
| `scan_state` | `"pending" \| "clean" \| "quarantined"` | |
| `preview_state` | `"pending" \| "ready" \| "unsupported" \| "failed"` | |
| `created_by` / `created_at` | uuid / timestamp | |

**`FileResponse`**

| Field | Type | Notes |
|---|---|---|
| `id` | uuid | |
| `target` | `{ kind, id }` | echoes `target_kind` and `target_id` |
| `file_name` / `mime_type` | string | |
| `size_bytes` / `sha256` | integer / string | of the current version |
| `current_version` | integer | |
| `scan_state` | `"pending" \| "clean" \| "quarantined"` | of the current version, mirrored here so a list needs no join on the client |
| `preview` | `{ state, url? }` | `url` is a 15-minute presigned GET, present only when `state` is `"ready"` |
| `versions` | FileVersionResponse[] | newest first, every version the file has |
| `proof` | ProofSummary? | present only while a proof exists on this file |
| `version` | integer | the aggregate version, `If-Match` for the next write |
| `created_at` / `updated_at` / `created_by` / `updated_by` | | |
| `deleted_at` | timestamp? | never present on a normal read; a soft-deleted file is `404 not_found` |

**`ProofSummary`**: `{ proof_id, state, file_version, due_at?, approved_count, reviewer_count }` — the
counts let a card render `Approved 2/2` without fetching the proof.

**`CreateProofRequest`** — `POST /api/v1/files/{id}/proofs`

| Field | Type | Required | Constraint |
|---|---|---|---|
| `reviewer_ids` | uuid[] | yes | 1–20 distinct live users of this tenant, each with read access to the file's target; empty, over 20, duplicated or lacking access → `400 invalid` with `field_errors.reviewer_ids`. Array order becomes `proof_reviewers.position` 1..n |
| `due_at` | timestamp? | no | must be in the future |
| `instructions` | string? | no | ≤ 2,000 chars |

The proof binds to the file's `current_version` at creation; a second `open` proof on the same file
is `409 conflict`.

**`ProofResponse`**: `{ id, file_id, file_version, state, due_at?, instructions?, reviewer_ids: uuid[], decisions: ProofDecisionResponse[], version, created_at, created_by }`. `reviewer_ids` is
assembled from `proof_reviewers` ordered by `position`, so it always round-trips the request order.

**`ProofDecisionResponse`**: `{ reviewer_id, decision, reason?, decided_at }` — one entry per reviewer
who has decided; reviewers who have not appear only in `reviewer_ids`.

**`DecisionRequest`** — `POST /api/v1/proofs/{id}/decisions`

| Field | Type | Required | Constraint |
|---|---|---|---|
| `decision` | `"approved" \| "rejected" \| "changes_requested"` | yes | closed set |
| `reason` | string? | conditional | required and 1–2,000 chars for `rejected` and `changes_requested`, optional for `approved` |

The caller must hold a `proof_reviewers` row on the proof, else `403 denied`; a second decision by
the same reviewer is `409 conflict`; a decision on a proof not in `open` is `409 conflict`.

**Markup on a proof.** F017 records a decision and its `reason` text and nothing more: there is no
annotation, coordinate, region or drawing payload on any route or table in this feature. Visual
markup over the rendered preview is not in scope here and belongs to a feature that declares its own
tables; a client must not smuggle it through `reason`, which is plain text.

**`DownloadRedirect`** — `GET /api/v1/files/{id}/download?version=<n>`: no response body. `302` with
`Location` set to a 15-minute presigned GET URL bound to that single object. `version` is optional
and defaults to `current_version`; it must name an existing version whose `scan_state` is `clean`.

**List route.** `GET /api/v1/{target_kind}/{target_id}/files` returns `Page<FileResponse>` with query
`{ scan_state?: "pending" \| "clean" \| "quarantined", sort?: "file_name" \| "created_at" (default "created_at" descending), cursor?: string, limit?: 1–100 (default 25) }`. `target_kind` in the path is
the same closed set. Soft-deleted files are excluded, and the caller needs read access to the target
or the route is `404 not_found`.

**Status codes**

| Code | Produced by |
|---|---|
| `200` | reads and `complete`; `201` on upload start, version add and proof create; `204` on delete; `302` on a ready download |
| `400 invalid` | MIME outside the allowlist, size over the tenant limit, a malformed `file_name` or `sha256`, a digest that disagrees with the ticket, `reviewer_ids` empty, over 20, duplicated or lacking target access, a missing `reason` on a non-approval, a `due_at` in the past |
| `403 denied` | a viewer starting an upload, adding a version, deleting, or creating a proof; a non-reviewer posting a decision; downloading a `quarantined` version, with `field_errors.scan_state = "quarantined"` |
| `404 not_found` | unknown, soft-deleted, foreign-tenant or invisible file, target, version, proof or upload ticket; an expired ticket, which is reported as `not_found` rather than `410` |
| `409 conflict` | the object is missing from storage at `complete` (`field_errors.upload = "object_missing"`); a download while `scan_state` is `pending` (`field_errors.scan_state = "pending"`); a second `open` proof; a repeat decision; a decision on a closed proof; a stale `If-Match` on a version add; a replayed `Idempotency-Key` with a different body |
| `429 rate_limited` | the shared per-actor request limit |
| `503 unavailable` | `StoreError::Unavailable` when object storage or `clamd` cannot be reached; the request is safe to retry and no state changed |

### Use case signatures

In `crates/domain/src/files/`. Each takes `ctx` carrying tenant, actor and correlation id, takes a
`UnitOfWork` for writes or a repository for reads — never a pool or a connection — and returns the
shared `DomainError`. Object storage and the scanner are reached only through the `ObjectStore` and
`ClamScanner` traits, which are arguments, not globals, so the evaluator of every rule stays testable
without S3.

```rust
fn start_upload(ctx: &Ctx, uow: &mut UnitOfWork, store: &dyn ObjectStore, req: StartUpload) -> Result<UploadTicket, DomainError>;
fn complete_upload(ctx: &Ctx, uow: &mut UnitOfWork, store: &dyn ObjectStore, ticket: UploadId, sha256: Checksum) -> Result<File, DomainError>;
fn add_version(ctx: &Ctx, uow: &mut UnitOfWork, store: &dyn ObjectStore, id: FileId, expected: Version, req: StartUpload) -> Result<UploadTicket, DomainError>;
fn get_file(ctx: &Ctx, repo: &FileRepository, proofs: &ProofRepository, id: FileId) -> Result<File, DomainError>;
fn list_files(ctx: &Ctx, repo: &FileRepository, target: TargetRef, filter: FileFilter, page: Cursor) -> Result<Page<File>, DomainError>;
fn sign_download(ctx: &Ctx, repo: &FileRepository, store: &dyn ObjectStore, id: FileId, version: Option<i32>) -> Result<SignedUrl, DomainError>;
fn delete_file(ctx: &Ctx, uow: &mut UnitOfWork, id: FileId, expected: Version) -> Result<(), DomainError>;
fn create_proof(ctx: &Ctx, uow: &mut UnitOfWork, id: FileId, req: CreateProof) -> Result<Proof, DomainError>;
fn record_decision(ctx: &Ctx, uow: &mut UnitOfWork, id: ProofId, req: Decision) -> Result<Proof, DomainError>;
fn supersede_proof(ctx: &Ctx, uow: &mut UnitOfWork, id: FileId, new_version: i32) -> Result<Option<Proof>, DomainError>;
fn scan_file(ctx: &Ctx, uow: &mut UnitOfWork, store: &dyn ObjectStore, scanner: &dyn ClamScanner, id: FileId, version: i32) -> Result<ScanOutcome, DomainError>;
fn render_preview(ctx: &Ctx, uow: &mut UnitOfWork, store: &dyn ObjectStore, id: FileId, version: i32) -> Result<PreviewState, DomainError>;
```

**Transaction boundaries.** `complete_upload` runs one `UnitOfWork` covering the `files` upsert, the
`file_versions` insert at `current_version`, the `files.current_version` bump and the ticket's
consumption, so a ticket can never be spent twice and a file can never exist without the version it
points at. `create_proof` writes the `proofs` row and all 1–20 `proof_reviewers` rows in one
boundary, which is what enforces the lower bound the `position` check cannot express: an empty
reviewer set never commits. `record_decision` writes the `proof_decisions` row and the proof's state
transition together, so the `approved` state and the last approving decision are always consistent
and `proof.decided.v1` is emitted exactly once per transition. `add_version` plus `supersede_proof`
share one boundary at completion time: the new `file_versions` row and the closing of any `open`
proof as `superseded` commit together (FR-F017-13), so no reviewer can decide against a version that
has already been replaced. `scan_file` commits the `file_scans` row and the `file_versions.scan_state`
change in one boundary, and the quarantine `copy_object` runs before that commit, so a version marked
`quarantined` always has its object already moved out of the servable prefix.

### PostgreSQL/SQLx

- Migration `*_files_*.sql` creates `files(id uuid pk, tenant_id uuid not null, target_kind text not null, target_id uuid not null, file_name text not null, mime_type text not null, current_version int not null default 1, version bigint not null default 1, created_by, created_at, updated_by, updated_at, deleted_at)`, `file_versions(tenant_id, file_id uuid references files(id) on delete restrict, version int, storage_key text not null, size_bytes bigint not null, sha256 bytea not null, scan_state text not null default 'pending', preview_state text not null default 'pending', preview_key text, created_by, created_at, primary key (file_id, version))`, `file_scans(id uuid pk, tenant_id, file_id, version, engine text, signature_db_version text, result text not null, signature text, duration_ms int, scanned_at timestamptz)`, `proofs(id uuid pk, tenant_id, file_id, file_version int, state text not null default 'open', due_at timestamptz, instructions text, version, audit fields)`, `proof_reviewers(id uuid pk, tenant_id uuid not null, proof_id uuid not null references proofs(id) on delete cascade, reviewer_id uuid not null references users(id) on delete restrict, position smallint not null, created_by, created_at)`, `proof_decisions(id uuid pk, tenant_id, proof_id uuid references proofs(id) on delete cascade, reviewer_id uuid not null, decision text not null, reason text, decided_at timestamptz not null)`, `file_upload_tickets(id uuid pk, tenant_id, file_id uuid, target_kind, target_id, storage_key, file_name, mime_type, size_bytes, sha256, expires_at, created_by, created_at)`. The reviewer set is a joined, constrained, audited set, so it is `proof_reviewers` rows rather than a `reviewer_ids uuid[]` column on `proofs`; `file_versions`, `file_scans`, and `file_upload_tickets` carry no array or `jsonb` column and are already normalized — the scan verdict is the typed `result`/`signature` pair, not a provider blob.
- Invariants: `check (scan_state in ('pending','clean','quarantined'))`, `check (preview_state in ('pending','ready','unsupported','failed'))`, `check (state in ('open','approved','rejected','changes_requested','superseded'))`, `check (decision in ('approved','rejected','changes_requested'))`, `check (target_kind in ('row','sheet','comment','document'))`; on `proof_reviewers` `check (position between 1 and 20)`, `unique (proof_id, reviewer_id)`, and `unique (proof_id, position)`, so the ≤ 20 reviewer limit is declarative through `position` while the ≥ 1 lower bound is enforced in the create-proof transaction, which inserts the proof and its reviewer rows together and rejects an empty set; partial unique index `proofs(file_id) where state = 'open'`; unique `proof_decisions(proof_id, reviewer_id)`; foreign key `proof_decisions(proof_id, reviewer_id) references proof_reviewers(proof_id, reviewer_id) on delete restrict`, which makes "a decision by a non-reviewer is rejected" declarative without changing the response — the API still checks reviewer membership first and returns `403 denied` (FR-F017-12), the constraint being the backstop; `storage_key` unique per tenant.
- Indexes: `files(tenant_id, target_kind, target_id, created_at desc) where deleted_at is null`, `file_versions(tenant_id, scan_state) where scan_state = 'pending'`, `proofs(tenant_id, state, due_at)`, `proof_reviewers(tenant_id, reviewer_id)` so "proofs awaiting my decision" is a join instead of an array containment scan, `file_upload_tickets(expires_at)`.
- Audit events: `file.upload.start`, `file.upload.complete`, `file.download`, `file.version.add`, `file.delete`, `proof.create`, `proof.decide`, `proof.supersede`; download audit records the version served.
- Retention/deletion: soft delete on `files`; expired upload tickets are removed hourly by the worker; S3 objects and quarantine copies purged by the F027 retention job; migration rollback drops the seven tables `files`, `file_versions`, `file_scans`, `proofs`, `proof_reviewers`, `proof_decisions`, and `file_upload_tickets` (no data before this feature).

### React/TypeScript

- Routes: `/files/:fileId/proof` in `apps/web/src/features/files/`; components `FileList`, `FileCard`, `UploadDropZone`, `UploadProgress`, `ScanBadge`, `PreviewThumbnail`, `VersionDrawer`, `RequestReviewDialog`, `ProofPanel`, `DecisionButtons`.
- State: TanStack Query keys `['files', targetKind, targetId, { cursor, scanState }]`, `['file', fileId]`, `['proof', proofId]`; scan state polls `['file', fileId]` every 3 s while `pending` up to 5 minutes, then shows `Still scanning` with manual refresh.
- API client: generated `FilesApi` with `startUpload`, `completeUpload`, `getFile`, `downloadFile`, `addVersion`, `deleteFile`, `listFiles`, `createProof`, `recordDecision`; browser PUT to `put_url` via `fetch` with progress from a `ReadableStream` wrapper; SHA-256 computed client-side with `crypto.subtle` before `startUpload`.
- Optimistic updates: none for uploads (server state is authoritative); decision buttons disable during the request and roll back on `conflict` or `denied`.
- Telemetry: `file_upload_started`, `file_upload_completed`, `file_scan_result`, `file_downloaded`, `file_version_added`, `proof_requested`, `proof_decided` with `mime_type` and `size_bucket`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F017-01 through FR-F017-15 in `testing/features/F017/requirements/cases.md`
- [ ] Failure/edge-case tests: disallowed MIME, oversize, missing object on complete, EICAR detection, checksum mismatch, download while pending, second open proof, repeat decision, version upload supersedes proof
- [ ] Permission-negative and tenant-isolation tests: viewer upload returns `denied`, non-reviewer decision returns `denied`, cross-tenant file returns `not_found`, presigned URL for tenant A object rejected for tenant B
- [ ] Rust unit tests: `crates/domain/src/files/` allowlist, checksum parsing, proof state machine over the reviewer set, storage key builder
- [ ] Persistence tests: `crates/persistence/src/files/` repository named queries including `list_reviewers` ordering by `position`, `page_proofs_for_reviewer`, `claim_expired_tickets`, and the two `UnitOfWork` writes
- [ ] API contract/integration tests: every route above with success and each error code
- [ ] Database migration/constraint tests: state checks, open-proof partial index, `proof_reviewers` position range and both unique constraints, the `proof_decisions → proof_reviewers` foreign key rejecting a non-reviewer decision, decision uniqueness, ticket expiry index, rollback of all seven tables
- [ ] React component tests: `FileList`, `UploadDropZone`, `VersionDrawer`, `ProofPanel` states
- [ ] Browser E2E tests: upload, scan clean, preview, version, proof approve, quarantine visible
- [ ] Accessibility tests: axe on file tab and proof panel, keyboard upload, live region
- [ ] Performance/load tests: 250 MB scan duration, list p95, upload initiation p95

### Fast fanout configuration

- Test harness path: `testing/features/F017/`
- Feature flag: `F017_FEATURE`
- Fixture/seed factory: `testing/fixtures/files.rs` builds tenant, sheet, row, editor, viewer, two reviewers, foreign tenant, a clean PDF, a PNG, an EICAR test file, and a seeded row with 12 files across scan states
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, UTC, fixed presign secret
- Mock/stub contracts: MinIO container from `testing/harness/minio.rs`; `ClamScanner` stub returning clean or the EICAR signature by content; outbox recorder in memory
- Parallel isolation: one schema and one MinIO bucket prefix per test worker, tenant ID per test
- Targeted command: `cargo xtask test-feature F017`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F017/`

## 6. Acceptance criteria

```gherkin
Feature: File upload, scanning, versions, and proofs

Scenario: Upload becomes downloadable after a clean scan
  Given editor Eli has editor access to row "Kickoff"
  When Eli starts an upload of "spec.pdf", puts the object, and completes it
  Then the file is version 1 with scan_state pending and file.uploaded.v1 is published
  And after scan_file runs the state is clean, file.scanned.v1 is published, and download returns 302

Scenario: Infected file is quarantined and never served
  Given Eli completes an upload whose content is the EICAR test string
  When scan_file runs
  Then scan_state is quarantined, file.quarantined.v1 is published, and download returns 403 denied

Scenario: Viewer cannot upload
  Given Vic has viewer access to row "Kickoff"
  When Vic starts an upload on the row
  Then the response is 403 denied and no upload ticket is created

Scenario: Proof approved by all reviewers
  Given a proof on "spec.pdf" with proof_reviewers rows for Rae at position 1 and Ron at position 2
  When Rae approves and Ron approves
  Then the proof state is approved and proof.decided.v1 with outcome approved is published once
  And the proof response lists reviewer_ids as Rae then Ron
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F006 (rows and sheets as targets), F004 (worker runtime, JetStream jobs, MinIO compose service, secrets for S3 credentials); decisions sections 2–5, 7; contracts row F017
- Blocks: F045 (document revisions reuse the object store and scan path), F057 (assets reuse versions and proofs)
- Conflicts with: none (disjoint owned paths)
- External dependencies: S3-compatible object storage (MinIO locally), ClamAV `clamd` container with daily signature refresh
- Risks and mitigations: ClamAV is slow on large archives, so scans stream with a 120 s timeout and dead-letter leaves the file `pending` rather than serving it; presigned URL leakage is bounded by the 15-minute expiry and single-object binding; client-side checksum lies are caught by the worker recomputation; preview rendering of malformed PDFs runs in a sandboxed worker process with a 30 s timeout and reports `failed` without blocking download.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F006 and F004 accepted and archived; MinIO and `clamd` present in `infra/compose.yml`
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F017/`
- [ ] Migration file name and owned paths claimed
- [ ] Fixture factory, MinIO harness, and schema-per-worker isolation available in `testing/harness/`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/worker/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for every mutation and worker transition
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] `cargo xtask check-persistence` passes: every F017 table is reached only through `crates/persistence/src/files/`
- [ ] Rollback verified: disable `F017_FEATURE`, run down migration dropping all seven tables on an empty tenant, objects left in the bucket are inert
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Users can attach files to rows and sheets, see them scanned before download, preview images and PDFs, keep version history, and request recorded approve or reject decisions.
- Migration adds `files`, `file_versions`, `file_scans`, `proofs`, `proof_reviewers`, `proof_decisions`, and `file_upload_tickets`; rollback drops them. Requires the MinIO and `clamd` services. Feature is off by default behind `F017_FEATURE`.
