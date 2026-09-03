---
id: T068
type: task
status: planned
parent_epic: E004
parent_feature: F017
parent_story: S034
depends_on: [T067]
owned_paths: [apps/web/src/features/files/**, testing/features/F017/frontend/**, testing/features/F017/e2e/**, testing/features/F017/accessibility/**]
feature_flag: F017_FEATURE
branch: t068-proofing-tests
started_at: null
finished_at: null
---

# T068 — Proofing tests

## Identity

- Parent story: `S034` Review/versioning
- Owner: platform
- Branch: `t068-proofing-tests`
- Decision references: `docs/architecture-decisions.md` section 6; `docs/capability-contracts.md` row F017

## Objective

Build the file tab, upload drop zone, version drawer, and proof panel wired to the real file routes and presigned S3 PUT, and prove upload, scan, version, quarantine, and proof decisions end to end in the browser.

## Specification

- Owned paths: `apps/web/src/features/files/{FileList.tsx, FileCard.tsx, UploadDropZone.tsx, UploadProgress.tsx, ScanBadge.tsx, PreviewThumbnail.tsx, VersionDrawer.tsx, RequestReviewDialog.tsx, ProofPanel.tsx, DecisionButtons.tsx, upload.ts, api.ts, hooks.ts, routes.ts}`
- Contract/input: generated `FilesApi` client; `upload.ts` computes SHA-256 with `crypto.subtle`, calls `startUpload`, PUTs to `put_url` with progress, then `completeUpload`; props `{ targetKind, targetId, canEdit }`; route `/files/:fileId/proof`; query keys `['files', targetKind, targetId, { cursor, scanState }]`, `['file', fileId]`, `['proof', proofId]` with 3 s polling while `scan_state = pending` for at most 5 minutes.
- Output/behavior: drop zone accepts drag and keyboard-opened picker, rejects disallowed MIME and oversize client-side with the same `field_errors` text as the API; cards show `ScanBadge` (`Scanning`, `Clean`, `Quarantined` with reason), thumbnail when `preview.state = ready`, and `Download` enabled only when clean; `VersionDrawer` lists versions with per-version download and `Upload new version`; `RequestReviewDialog` picks 1–20 reviewers and a due date; `ProofPanel` shows the preview, instructions, reviewer statuses, and `DecisionButtons` with a required reason field for reject and changes requested; states loading, empty, error with `correlation_id`, denied controls for viewers, not-found, stale on version conflict, offline; live region announces scan completion and decisions; telemetry `file_upload_started`, `file_upload_completed`, `file_scan_result`, `file_downloaded`, `file_version_added`, `proof_requested`, `proof_decided`.
- Dependencies: T067 routes; F006 row drawer tab slot; F037 delivers the reviewer link (outside this task).
- Feature flag: `F017_FEATURE` read through the flag hook; tab and route are not registered when off.

## TDD

- Failing test first: `testing/features/F017/frontend/FileList.test.tsx::file_list_disables_download_until_clean`, `::quarantined_card_shows_reason_and_no_download`, `::viewer_sees_no_upload_controls`, `UploadDropZone.test.tsx::rejects_disallowed_mime_client_side`, `ProofPanel.test.tsx::reject_requires_reason`, `::decision_rolls_back_on_conflict`; `testing/features/F017/e2e/files.spec.ts::upload_scan_preview_download`, `::eicar_upload_is_quarantined`, `::version_and_proof_approval`; `testing/features/F017/accessibility/files.a11y.spec.ts::file_tab_and_proof_panel_have_no_serious_axe_violations`
- Targeted command: `cargo xtask test-feature F017`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: MSW handlers from the seeded 12-file row fixture with a fake presigned PUT endpoint; Playwright uses the real API, MinIO, and the ClamAV stub against a seeded tenant with editor `eli`, viewer `vic`, reviewers `rae` and `ron`

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Component, E2E, and accessibility lanes pass
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S034
- [ ] `finished_at` recorded
