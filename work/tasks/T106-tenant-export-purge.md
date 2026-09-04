---
id: T106
type: task
status: planned
parent_epic: E006
parent_feature: F027
parent_story: S053
depends_on: [T105]
owned_paths: [crates/domain/src/compliance/**, crates/persistence/src/compliance/**, services/api/src/compliance/**, services/worker/src/compliance/**, apps/web/src/features/compliance/**, testing/features/F027/api/**, testing/features/F027/frontend/**, testing/features/F027/performance/**]
feature_flag: F027_FEATURE
branch: t106-tenant-export-purge
started_at: null
finished_at: null
---

# T106 — Tenant export/purge

## Identity

- Parent story: `S053` Retention/export
- Owner: platform
- Branch: `t106-tenant-export-purge`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 5, 7; `docs/capability-contracts.md` row F027

## Objective

Implement the tenant export job with manifest and redaction, the purge proposal, preview, two-step confirmation, and batched purge execution that honors legal holds, plus the export and purge pages.

## Specification

- Owned paths: `crates/domain/src/compliance/{export.rs, redaction.rs, purge.rs, purge_state.rs}`, `crates/persistence/src/compliance/{export_repository.rs, purge_repository.rs}`, `services/api/src/compliance/{handlers_export.rs, handlers_purge.rs}`, `services/worker/src/compliance/{tenant_export.rs, purge_execute.rs}`, `apps/web/src/features/compliance/{ExportPanel.tsx, ExportProgress.tsx, PurgeWizard.tsx, PurgePreview.tsx, PurgeConfirmDialog.tsx}`
- Contract/input: `CreateTenantExportRequest { include: [kinds], format: "jsonl" | "csv", since? }`, `ProposePurgeRequest { scope, kinds, older_than }`, `ConfirmPurgeRequest { confirmation_code }`; job subjects `jobs.compliance.tenant_export` and `jobs.compliance.purge_execute` with `{ request_id }`.
- Output/behavior: routes `POST /api/v1/compliance/tenant-exports` (202, one running per tenant else 409), `GET /api/v1/compliance/tenant-exports/{id}` (status, per-kind progress, 7-day signed URL, download audited), `POST /api/v1/compliance/purges` (preview candidates and held counts, 8-char code hashed), `POST /api/v1/compliance/purges/{id}/confirm` (code, 24-hour window, two-person rule from `security_policies.two_person_purge`); export worker claims the next `tenant_export_kinds` row with `status = 'pending'`, streams that kind to `<kind>.jsonl` or `.csv`, applies `redaction.rs` allowlists (drops `oauth_tokens`, `scim_tokens`, `api_tokens.hash`), records `rows_written`, `bytes_written`, `checksum_sha256`, and `completed_at` on the row, writes `manifest.json` with counts and SHA-256, zips into MinIO key `tenant-exports/<tenant>/<id>.zip`, and resumes by re-claiming pending rows after a restart; purge worker deletes in 1,000-row batches with `purge_batches` checkpoints, skips held records, removes file blobs, writes `purge.executed` per kind, accumulates `purged_count` and `skipped_held_count` on the kind's `purge_request_kinds` row and sums them onto the request; the request and response DTOs keep `include`, `kinds`, `progress`, and `preview` as JSON arrays and objects, and the repositories fan them out to rows and reassemble them, so the API shape is unchanged; failures set the typed `error_code`/`error_message` columns instead of a jsonb blob; events `tenant-export.completed.v1`, `purge.confirmed.v1`; error mapping per ticket section 4.
- Data access: `export.rs`, `purge.rs`, `purge_state.rs`, the two handlers, and the two workers hold no SQL. `TenantExportRepository` (owns `tenant_exports`, `tenant_export_kinds`) exposes `find_running_export_for_tenant`, `insert_export_with_kinds`, `list_export_kinds`, `claim_next_pending_kind`, `complete_export_kind`, `set_download_target`, and `fail_export`; `PurgeRequestRepository` (owns `purge_requests`, `purge_request_kinds`, `purge_batches`) exposes `insert_proposal_with_preview`, `load_purge_with_kinds`, `confirm_with_code_hash`, `record_purge_batch`, `last_completed_batch`, `accumulate_kind_counts`, and `finish_purge_with_counts`. Candidate and held counts come from `LegalHoldRepository::count_held_by_kind` plus the owning feature's repository count; the batch delete calls `purge` on that repository. Proposal plus preview rows, confirmation plus outbox enqueue, and each batch delete plus its checkpoint and counter update commit in one `UnitOfWork` (decision section 2.1).
- Dependencies: T105 schema, holds, and router; F010 file writers; F017 blob deletion; F038 `security_policies`.
- Feature flag: `F027_FEATURE`

## TDD

- Failing test first: `testing/features/F027/api/export_tests.rs::tenant_export_second_running_conflicts`, `::tenant_export_redacts_secrets`, `::tenant_export_manifest_checksums_match`, `::tenant_export_resumes_after_restart`; `testing/features/F027/api/purge_tests.rs::purge_preview_counts_held_records`, `::purge_confirm_wrong_code_invalid`, `::purge_confirm_expired_conflicts`, `::purge_confirm_same_actor_denied`, `::purge_execute_skips_held_and_records_batches`, `::purge_never_deletes_audit_events`, `::purge_kind_counts_sum_to_request_totals`, `::export_progress_reassembles_from_kind_rows`; `testing/features/F027/frontend/PurgeConfirmDialog.test.tsx::button_disabled_until_code_matches`; `testing/features/F027/performance/purge_bench.rs::purge_100k_rows_under_10_minutes`
- Targeted command: `cargo xtask test-feature F027`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: 12,400 soft-deleted rows with 310 held; fixture secrets; MinIO bucket prefix per test; worker restart simulated by cancelling and re-enqueuing the job

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Export and purge jobs registered in `services/worker/src/registry.rs` behind the flag with dead-letter verified
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S053
- [ ] `finished_at` recorded
