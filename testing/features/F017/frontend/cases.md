# F017 frontend cases

File: `testing/features/F017/frontend/{FileList.test.tsx,UploadDropZone.test.tsx,VersionDrawer.test.tsx,ProofPanel.test.tsx}`. Vitest with MSW. Flag `F017_FEATURE`.

- `FileList.test.tsx::renders_cards_with_scan_badges` — FR-F017-14: seeded row renders 12 cards with `Scanning`, `Clean`, and `Quarantined` badges.
- `FileList.test.tsx::file_list_disables_download_until_clean` — FR-F017-05, FR-F017-14: pending card has disabled `Download`; after the polled response turns clean it enables and the live region announces it.
- `FileList.test.tsx::quarantined_card_shows_reason_and_no_download` — FR-F017-05: quarantined card shows the signature text and no download control.
- `FileList.test.tsx::shows_loading_skeleton_then_cards` — FR-F017-14: pending query shows skeleton cards.
- `FileList.test.tsx::shows_empty_state_with_drop_zone` — FR-F017-14: no files shows `No files attached. Drop files here or browse.`
- `FileList.test.tsx::shows_error_banner_with_correlation_id` — NFR-F017-04: 500 response shows banner with `correlation_id` and retry.
- `FileList.test.tsx::viewer_sees_no_upload_controls` — FR-F017-15: `canEdit=false` hides drop zone, delete, and version upload.
- `FileList.test.tsx::offline_disables_drop_zone` — FR-F017-14: `navigator.onLine=false` shows the offline badge and disables the picker.
- `UploadDropZone.test.tsx::rejects_disallowed_mime_client_side` — FR-F017-02: dropping `.exe` shows `not_allowed` without calling the API.
- `UploadDropZone.test.tsx::computes_sha256_and_puts_with_progress` — FR-F017-01, FR-F017-03: start, PUT with progress events, complete called with the computed hash; emits `file_upload_completed`.
- `UploadDropZone.test.tsx::keyboard_opens_picker` — NFR-F017-03: Enter on the focused zone opens the hidden file input.
- `VersionDrawer.test.tsx::lists_versions_with_download` — FR-F017-08: 3 versions each with download; upload new version calls the versions route with `If-Match`.
- `VersionDrawer.test.tsx::stale_version_shows_conflict_banner` — FR-F017-08: 409 shows `A newer version exists` with reload.
- `ProofPanel.test.tsx::reject_requires_reason` — FR-F017-12: `Reject` without reason blocks submit with field error.
- `ProofPanel.test.tsx::decision_rolls_back_on_conflict` — FR-F017-12: 409 restores buttons and shows the already-decided message.
- `ProofPanel.test.tsx::non_reviewer_sees_read_only_status` — FR-F017-12: `oz` sees reviewer statuses and no decision buttons.

Evidence: Vitest JUnit under `testing/evidence/F017/frontend/`.
