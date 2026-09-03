---
id: S034
type: story
status: planned
parent_epic: E004
parent_feature: F017
depends_on: [S033]
owned_paths: [crates/domain/src/files/**, services/api/src/files/**, apps/web/src/features/files/**, testing/features/F017/**]
feature_flag: F017_FEATURE
branch: s034-review-versioning
started_at: null
finished_at: null
---

# S034 — Review/versioning

## Identity

- Parent feature: `F017` Files and proofing
- Owner: platform
- Branch: `s034-review-versioning`
- Decision references: `docs/architecture-decisions.md` sections 2–6; `docs/capability-contracts.md` row F017

## Vertical slice

As a sheet editor, I want to upload a new version of an attachment without losing the old one, ask named reviewers for a decision, and see their approve or reject outcome on the file card, so that artifacts keep a visible history and a recorded review.

## Requirements

- **SR-S034-01:** `POST /api/v1/files/{id}/versions` reuses the upload ticket flow, requires `If-Match`, creates `file_versions` row `current_version + 1` on completion, keeps earlier versions downloadable with `?version=<n>`, and publishes `file.version-added.v1` (covers FR-F017-08, FR-F017-05).
- **SR-S034-02:** `DELETE /api/v1/files/{id}` soft-deletes the file and versions, hides it from the target list, and publishes `file.deleted.v1` (FR-F017-09).
- **SR-S034-03:** `POST /api/v1/files/{id}/proofs` creates an `open` proof bound to the current version with 1–20 reviewers who have target read; a second open proof returns `409 conflict` (FR-F017-11).
- **SR-S034-04:** `POST /api/v1/proofs/{id}/decisions` records one decision per reviewer, requires a reason for `rejected` and `changes_requested`, transitions the proof per the state machine, publishes `proof.decided.v1` on each state change, and returns `403 denied` to non-reviewers and `409 conflict` on repeat decisions (FR-F017-12).
- **SR-S034-05:** Completing a new version on a file with an open proof marks that proof `superseded` and publishes `proof.decided.v1` with `outcome = superseded` (FR-F017-13).
- **SR-S034-06:** `FileList`, `UploadDropZone`, `ScanBadge`, `PreviewThumbnail`, `VersionDrawer`, `RequestReviewDialog`, and `ProofPanel` render the states in ticket section 3, poll scan state every 3 s while pending, and disable download until clean (FR-F017-14).
- **SR-S034-07:** File tab and proof panel pass axe with zero serious violations; upload is keyboard-triggerable; scan completion and decisions are announced (NFR-F017-03).

## Surfaces

- Infrastructure/container: none new
- Rust service/API: `crates/domain/src/files/{proof.rs, proof_state.rs, service_versions.rs, service_proofs.rs}`; `services/api/src/files/{handlers_version.rs, handlers_proof.rs}`
- Data/migration: none new; uses `file_versions`, `proofs`, `proof_decisions` from S033
- React/UI: `apps/web/src/features/files/{FileList.tsx, FileCard.tsx, UploadDropZone.tsx, UploadProgress.tsx, ScanBadge.tsx, PreviewThumbnail.tsx, VersionDrawer.tsx, RequestReviewDialog.tsx, ProofPanel.tsx, DecisionButtons.tsx, upload.ts, api.ts, hooks.ts, routes.ts}`
- Mocks/fixtures: seeded row with 12 files across scan states and one file with 3 versions and an open proof; reviewers `rae`, `ron`; MSW handlers for component tests

## TDD harness

- Test path: `testing/features/F017/{api,frontend,e2e,accessibility}/`
- Feature flag: `F017_FEATURE`
- Targeted command: `cargo xtask test-feature F017`
- Full command: `cargo xtask test-all`
- First failing tests: `version_add_increments_and_keeps_old`, `proof_second_open_conflicts`, `proof_all_approve_transitions_approved`, `proof_non_reviewer_denied`, `version_upload_supersedes_open_proof`, `file_list_disables_download_until_clean`

## Exit criteria

- [ ] Requirement tests SR-S034-01 through SR-S034-07 written first and failing
- [ ] Tasks T067 and T068 complete; UI wired to real API through generated client and direct presigned PUT
- [ ] Unit, API, React, E2E, accessibility, and permission tests pass
- [ ] Production call path named: `apps/web/src/features/files/FileList.tsx` mounted in the row drawer at `/w/:workspaceId/sheets/:sheetId?row=:rowId&tab=files` and `ProofPanel.tsx` at `/files/:fileId/proof`
- [ ] Handoff evidence recorded in the F017 ticket
