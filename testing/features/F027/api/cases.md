# F027 api cases

File: `testing/features/F027/api/{policy_tests.rs,hold_tests.rs,sweep_tests.rs,export_tests.rs,purge_tests.rs,review_tests.rs,negative_tests.rs}`. Flag `F027_FEATURE`.

- `retention_policy_defaults_seeded` — FR-F027-01: first GET returns eight kinds with `soft_delete_days: 30`, `purge_after_days: null`.
- `retention_policy_rejects_audit_below_365` — FR-F027-01: PUT `audit_events` with `purge_after_days: 200` → 400 `invalid`, `field_errors.purge_after_days`.
- `retention_policy_stale_version_conflicts` — FR-F027-02: `If-Match: 1` against version 2 → 409 `conflict`; valid PUT publishes `retention-policy.updated.v1`.
- `retention_sweep_marks_purge_eligible` — FR-F027-03: rows soft-deleted 400 days ago with purge 365 → `purge_eligible`; none hard-deleted.
- `retention_sweep_skips_held_records` — FR-F027-04: 310 held rows untouched by the sweep.
- `legal_hold_scope_sheet_matches_rows` — FR-F027-04: `sheet:{id}` hold marks that sheet's rows held and no others; `legal-hold.applied.v1` published.
- `legal_hold_two_person_release_denied` — FR-F027-05: creator DELETE under policy → 403 `denied`; second admin → 204.
- `tenant_export_second_running_conflicts` — FR-F027-06: second POST while first is running → 409 `conflict`.
- `tenant_export_redacts_secrets` — FR-F027-07, NFR-F027-02: archive contains no fixture OAuth, SCIM, or API token secrets.
- `tenant_export_manifest_checksums_match` — FR-F027-07: SHA-256 in `manifest.json` equals each file; counts match fixture.
- `tenant_export_resumes_after_restart` — NFR-F027-04: job cancelled after `rows`; re-run skips `rows` and completes.
- `tenant_export_download_audited` — NFR-F027-02: each GET of the download URL writes `tenant-export.download`.
- `purge_preview_counts_held_records` — FR-F027-08: preview 12,400 candidates and 310 held; status `proposed`; no deletion.
- `purge_confirm_wrong_code_invalid` — FR-F027-09: bad code → 400 `invalid`.
- `purge_confirm_expired_conflicts` — FR-F027-09: confirm at +25 h → 409 `conflict`, status `expired`.
- `purge_confirm_same_actor_denied` — FR-F027-09: proposer confirms under two-person policy → 403; allowed on tenant B without the policy.
- `purge_execute_skips_held_and_records_batches` — FR-F027-10: 13 `purge_batches` rows, `purged_count 12,090`, `skipped_held_count 310`, blobs removed.
- `purge_never_deletes_audit_events` — FR-F027-10: purge with kind `audit_events` → 400 `invalid`; audit rows unchanged.
- `purge_dead_letters_after_three_retries` — NFR-F027-04: injected storage failure → 3 retries, dead letter, status `failed`.
- `access_review_lists_roles_shares_links_tokens` — FR-F027-11: 40 principals with correct role, share, link, and token counts; JSON and CSV stored.
- `access_review_flags_inactive_and_stale_guests` — FR-F027-12: 2 inactive users and 3 stale guests flagged, `flagged_count 5`.
- `access_review_revoke_removes_acl_and_tokens` — FR-F027-12: `revoke` guest → share link revoked, ACL removed, token revoked, audit rows written.
- `access_review_list_filters_by_scope` — FR-F027-11: `scope=workspace:{id}` returns only that workspace's reports; cursor paging.
- `tenant_admin_denied_on_all_routes` — FR-F027-13: tenant-admin without compliance role → 403 on all ten routes.
- `foreign_tenant_ids_not_found` — FR-F027-13: tenant B hold, export, purge, and report IDs → 404 from tenant A.
- `compliance_mutation_requires_idempotency_key` — FR-F027-13: POST without header → 400 `invalid`.
- `compliance_job_metrics_emitted` — NFR-F027-04: `compliance_job_duration_seconds{kind}` and `purge_rows_total` observed.

Evidence: JUnit output and request logs under `testing/evidence/F027/api/`.
