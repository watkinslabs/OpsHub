# F017 api cases

File: `testing/features/F017/api/{upload_tests.rs,download_tests.rs,scan_tests.rs,version_tests.rs,proof_tests.rs,list_tests.rs}`. Flag `F017_FEATURE`.

- `upload_start_returns_presigned_put` — FR-F017-01: POST `/api/v1/files/uploads` for `spec.pdf` on row "Kickoff" → 201, `put_url` host is MinIO, `expires_at` = now + 15 min, ticket row exists.
- `upload_mime_not_allowed_invalid` — FR-F017-02: `application/x-msdownload` → 400 `field_errors.mime_type: not_allowed`.
- `upload_size_over_limit_invalid` — FR-F017-02: `size_bytes` 251 MB on default tenant → 400 `field_errors.size_bytes: too_large`.
- `upload_complete_missing_object_conflicts` — FR-F017-03: complete without PUT → 409 `field_errors.upload: object_missing`.
- `upload_complete_creates_pending_version` — FR-F017-03: PUT then complete → `files` and `file_versions(1, pending)`, `file.uploaded.v1`, `files.scan` job enqueued.
- `upload_expired_ticket_not_found` — FR-F017-03: complete at +16 min → 404 `not_found`.
- `upload_viewer_denied` — FR-F017-15: `vic` POST uploads → 403 `denied`, no ticket row.
- `file_cross_tenant_not_found` — FR-F017-15: tenant B on GET, download, versions, delete, proofs → 404.
- `download_clean_redirects_with_expiry` — FR-F017-05: clean version → 302, `Location` signed for 15 min, `file.download` audit row with version.
- `download_pending_conflicts` — FR-F017-05: pending → 409 `field_errors.scan_state: pending`.
- `download_quarantined_denied` — FR-F017-05, NFR-F017-02: quarantined → 403 `field_errors.scan_state: quarantined`; no presign call made.
- `download_specific_old_version` — FR-F017-05: `?version=1` on a 3-version file → 302 to the version-1 key.
- `scan_clean_sets_state_and_publishes` — FR-F017-04: `scan_file` on `spec.pdf` → `clean`, `file_scans` row with `duration_ms`, `file.scanned.v1`, preview job enqueued.
- `scan_eicar_quarantines_file` — FR-F017-04: EICAR → `quarantined`, object copied to `quarantine/`, original deleted, `signature` recorded, `file.quarantined.v1`.
- `scan_checksum_mismatch_quarantines` — FR-F017-04, NFR-F017-02: declared sha256 differs from content → `quarantined` with `result: checksum_mismatch`.
- `scan_replay_is_noop_when_not_pending` — NFR-F017-04: second `scan_file` on a clean version → no writes, no event.
- `scan_error_dead_letters_after_five_attempts` — NFR-F017-04: failing scanner → 5 attempts, `dead_letters` row, state still `pending`.
- `preview_image_and_pdf_ready` — FR-F017-07: PNG → 320 px WebP; PDF → 1,024 px first page; `preview_state ready`.
- `preview_unsupported_type_marked` — FR-F017-07: ZIP → `preview_state unsupported`, no object written.
- `sweeper_removes_expired_tickets` — FR-F017-03: ticket at +2 h without complete → ticket and orphan object removed.
- `version_add_increments_and_keeps_old` — FR-F017-08: versions route + complete → `current_version 2`, version 1 downloadable, `file.version-added.v1`.
- `version_add_stale_if_match_conflicts` — FR-F017-08: `If-Match: 1` against version 2 → 409.
- `version_upload_supersedes_open_proof` — FR-F017-13: open proof → `superseded`, `proof.decided.v1 { outcome: superseded }`.
- `file_delete_hides_from_list` — FR-F017-09: DELETE → `deleted_at`, absent from target list, `file.deleted.v1`, objects untouched.
- `file_list_pages_filters_sorts` — FR-F017-10: 150 files, `limit=100`, two pages; `scan_state=clean`; `sort=file_name`.
- `proof_create_binds_current_version` — FR-F017-11: proof → `open`, `file_version` = current, reviewers stored.
- `proof_second_open_conflicts` — FR-F017-11: second proof while open → 409.
- `proof_reviewer_without_access_invalid` — FR-F017-11: reviewer `oz` without row read → 400 `field_errors.reviewer_ids`.
- `proof_all_approve_transitions_approved` — FR-F017-12: `rae` and `ron` approve → `approved`, one `proof.decided.v1 { outcome: approved }`.
- `proof_first_reject_transitions_rejected` — FR-F017-12: `rae` rejects with reason → `rejected` immediately.
- `proof_reject_without_reason_invalid` — FR-F017-12: `rejected` without `reason` → 400 `field_errors.reason`.
- `proof_repeat_decision_conflicts` — FR-F017-12: `rae` decides twice → 409.
- `proof_non_reviewer_denied` — FR-F017-12: `oz` decides → 403 `denied`.
- `file_mutation_writes_audit_and_outbox` — FR-F017-15: each mutation → one `audit_events` row and one `outbox_events` row in the same transaction.
- `request_span_carries_file_ids` — NFR-F017-04: span has `tenant_id`, `file_id`, `version`, `correlation_id`.

Evidence: JUnit output and request logs under `testing/evidence/F017/api/`.
