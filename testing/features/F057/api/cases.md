# F057 api cases

File: `testing/features/F057/api/{asset_tests.rs,collection_tests.rs,metadata_tests.rs,rights_tests.rs,rendition_tests.rs,approval_tests.rs,lifecycle_tests.rs}`. Flag `F057_FEATURE`.

- `asset_register_returns_version_one` — FR-F057-01: POST `/api/v1/assets` from a clean PNG → 201, `version: 1`, `approval_state: draft`, `rendition_state: pending`.
- `asset_register_unscanned_file_invalid` — FR-F057-02: quarantined file → 400 `field_errors.file_id = not_scanned`.
- `asset_register_unreadable_file_not_found` — FR-F057-02: file outside actor ACL → 404.
- `asset_missing_entitlement_denied` — FR-F057-11: unentitled tenant → 403 `denied`, `field_errors.entitlement = dam` on all ten routes.
- `asset_cross_tenant_not_found` — FR-F057-11: tenant B on tenant A asset and collection → 404.
- `asset_viewer_mutation_denied` — NFR-F057-02: viewer POST/PATCH/DELETE/rights → 403.
- `asset_list_filters_and_search` — FR-F057-07: `q=logo`, `usable=true`, `mime_prefix=image`, `sort=title` → expected page.
- `asset_stale_version_conflicts` — FR-F057-10: `If-Match: 1` against version 2 → 409 with `current_version`.
- `asset_idempotent_replay_returns_original` — FR-F057-10: same key twice → one asset.
- `asset_archive_hides_from_collections` — FR-F057-09: archive → absent from list and collection listing; `asset_collection_items` row remains; `asset.archived.v1`.
- `collection_depth_six_rejected` — FR-F057-08: sixth nesting level → 400.
- `collection_replace_requires_read_access` — FR-F057-08: list containing an unreadable asset → 404; 5,001 IDs → 400.
- `asset_metadata_type_mismatch_invalid` — FR-F057-12: text in number field → 400 `field_errors.metadata.budget`.
- `schema_field_removal_blocked_with_values` — FR-F057-12: removing a populated field → 400.
- `rights_set_publishes_event` — FR-F057-05: PUT rights → `asset.rights-updated.v1`, audit diff.
- `rights_expired_makes_asset_unusable` — FR-F057-05, FR-F057-06: approved asset with past `valid_until` → `usable: false`.
- `rights_expiry_uses_tenant_end_of_day` — FR-F057-05: `valid_until` today in `America/Los_Angeles` still active at 23:00 local.
- `rendition_job_writes_three_image_kinds` — FR-F057-03: PNG → thumbnail 256, preview 1280, web 1920 with checksums.
- `rendition_job_video_poster_and_preview` — FR-F057-03: MP4 → poster and 720p preview.
- `rendition_failed_after_three_attempts` — FR-F057-14, NFR-F057-04: backend error ×3 → `failed`, `error_code`, dead letter.
- `rendition_url_redirects_when_ready` — FR-F057-04: 302 with 15-minute expiry; pending → 409.
- `approval_decision_sets_state` — FR-F057-06: `approval.decided.v1` approved → `approved`; rejected → `rejected`.
- `asset_lifecycle_event_sequence` — FR-F057-10: exact outbox order across the full lifecycle.

Evidence: JUnit output and request logs under `testing/evidence/F057/api/`.
