---
id: T067
type: task
status: planned
parent_epic: E004
parent_feature: F017
parent_story: S034
depends_on: [S034]
owned_paths: [crates/domain/src/files/**, services/api/src/files/**, testing/features/F017/api/**]
feature_flag: F017_FEATURE
branch: t067-file-versions
started_at: null
finished_at: null
---

# T067 — File versions

## Identity

- Parent story: `S034` Review/versioning
- Owner: platform
- Branch: `t067-file-versions`
- Decision references: `docs/architecture-decisions.md` sections 2–4; `docs/capability-contracts.md` row F017

## Objective

Implement version upload, soft delete, proof creation, reviewer decisions, and proof supersession with the proof state machine and their four routes.

## Specification

- Owned paths: `crates/domain/src/files/{proof.rs, proof_state.rs, service_versions.rs, service_proofs.rs}`, `services/api/src/files/{handlers_version.rs, handlers_proof.rs, dto.rs}`
- Contract/input: `POST /api/v1/files/{id}/versions` with `StartUploadRequest` body and `If-Match`; version completion through `PUT /api/v1/files/uploads/{id}/complete` where the ticket carries `file_id`; `DELETE /api/v1/files/{id}`; `CreateProofRequest { reviewer_ids (1–20), due_at?, instructions? (≤ 2,000) }`; `DecisionRequest { decision, reason? }`; `ProofState` transitions: `open → approved` when all reviewers approve, `open → rejected` on first rejection, `open → changes_requested` on first such decision, `open → superseded` on new version; terminal states reject further decisions with `409 conflict`.
- Output/behavior: version completion inserts `file_versions(current_version + 1)`, bumps `files.current_version`, publishes `file.version-added.v1`, enqueues `scan_file`, and supersedes any open proof publishing `proof.decided.v1 { outcome: superseded }`; earlier versions stay downloadable via `?version=<n>`; delete sets `deleted_at`, publishes `file.deleted.v1`, and removes the file from the target list; proof creation enforces the `proofs(file_id) where state = 'open'` index and reviewer target-read validation; decisions insert one `proof_decisions` row per reviewer, require `reason` for non-approval, apply the state machine, and publish `proof.decided.v1 { proof_id, outcome, reviewer_id }` on each state change; non-reviewers get `403 denied`; every mutation is idempotent and audited.
- Dependencies: T065 tables, store, and upload flow; T066 scan enqueue; F003 `check_many` for reviewer validation.
- Feature flag: `F017_FEATURE`.

## TDD

- Failing test first: `testing/features/F017/api/version_tests.rs::version_add_increments_and_keeps_old`, `::version_add_stale_if_match_conflicts`, `::version_upload_supersedes_open_proof`, `::file_delete_hides_from_list`; `testing/features/F017/api/proof_tests.rs::proof_create_binds_current_version`, `::proof_second_open_conflicts`, `::proof_reviewer_without_access_invalid`, `::proof_all_approve_transitions_approved`, `::proof_first_reject_transitions_rejected`, `::proof_reject_without_reason_invalid`, `::proof_repeat_decision_conflicts`, `::proof_non_reviewer_denied`
- Targeted command: `cargo xtask test-feature F017`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: seeded file with 3 versions; reviewers `rae`, `ron`, outsider `oz`; in-memory outbox recorder asserting `proof.decided.v1` payloads

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Routes mounted in `services/api/src/files/routes.rs`; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S034
- [ ] `finished_at` recorded
