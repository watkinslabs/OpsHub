# F045 api cases

File: `testing/features/F045/api/{document_tests.rs,tree_tests.rs,search_tests.rs,revision_tests.rs,access_tests.rs}`. Flag `F045_FEATURE`.

- `document_create_returns_version_one_and_path` — FR-F045-01: POST folder then doc inside it → 201, `version: 1`, `path: [folder_id]`, `current_revision: 1`.
- `document_sibling_title_conflicts` — FR-F045-02: "runbooks" beside "Runbooks" under one parent → 409 `conflict`, `field_errors.title = "taken"`; same title under another parent → 201.
- `document_move_into_descendant_rejected` — FR-F045-03: move A under A/B → 400 `invalid`, `field_errors.parent_id = "cycle"`; move A under A → same.
- `document_move_depth_33_rejected` — FR-F045-03: chain of 32 folders, move a folder beneath the leaf → 400 `parent_id = "too_deep"`.
- `document_move_rewrites_descendant_paths` — FR-F045-03: move folder with 40 descendants → every descendant `path` and `depth` updated, `document.moved.v1` carries old and new parent.
- `document_patch_stale_version_conflicts` — FR-F045-04: `If-Match: 2` against version 3 → 409 with `current_version: 3`, title unchanged.
- `document_restore_subtree_keeps_ids` — FR-F045-05: delete folder with 3 docs, restore folder → 4 nodes with original ids and `deleted_at` null.
- `document_restore_orphan_goes_to_root` — FR-F045-05: restore a doc whose parent stays deleted → `parent_id` null, `restored_to_root: true`.
- `document_list_pages_children_by_title` — FR-F045-06: 250 children, `limit=100` → three pages in title order; `kind=folder` filter; `archived=true` filter.
- `document_search_returns_snippets` — FR-F045-06: `q=deploy` over seeded tree → hits carry `snippet` containing `deploy`, ranked by `ts_rank_cd`.
- `document_search_updates_on_revision` — FR-F045-06: new revision adds word `rollback` → next `q=rollback` returns the doc.
- `revision_add_increments_and_checksums` — FR-F045-07: POST 1 MB body with `If-Match: 1` → `revision: 2`, SHA-256 matches fixture, `document.revision-added.v1` published.
- `revision_stale_if_match_conflicts` — FR-F045-07: `If-Match: 2` against `current_revision` 3 → 409 with `current_revision: 3`, no object put recorded.
- `revision_over_20mb_invalid` — FR-F045-07: 20 MB + 1 byte body → 400 `invalid`, `field_errors.body`.
- `revision_failed_put_rolls_back_metadata` — NFR-F045-04: object store put fails → 503 `unavailable`, no `document_revisions` row, `current_revision` unchanged.
- `revision_download_verifies_checksum` — FR-F045-08: GET revision → `download_url` with `expires_at` 15 min ahead; corrupted object → 503 `unavailable`, `document_checksum_mismatch` alert recorded.
- `revision_list_pages_newest_first` — FR-F045-09: 250 revisions, `limit=100` → three pages descending, `label` present where set.
- `explicit_deny_hides_descendants` — FR-F045-10: viewer with workspace grant and deny on "Finance" → 404 on the folder, its docs, and their revision routes; `effective_role` on allowed nodes.
- `viewer_mutation_denied` — NFR-F045-02: viewer POST/PATCH/move/DELETE/revision → 403 `denied`.
- `link_principal_cannot_list_root` — FR-F045-11: link scoped to "Runbooks" → root list 403 `denied`; `parent_id=Runbooks` → 200.
- `link_principal_reads_granted_subtree_only` — FR-F045-11: link principal GET a doc outside the granted folder → 404; mutation inside → 403.
- `link_principal_rate_limited_after_60` — FR-F045-11: 61 GETs within 60 s on one token → 61st is 429 `rate_limited` with `Retry-After`.
- `expired_link_not_found` — NFR-F045-02: link past `expires_at` or revoked → 404 on every route.
- `hidden_nodes_excluded_from_search` — FR-F045-12: `search_visibility=hidden` and link-only nodes absent from `q`; present when workspace `link_search_discoverable` is true.
- `document_cross_tenant_not_found` — FR-F045-13: tenant B GET/PATCH/move/DELETE/revisions by tenant A id → 404 on every route.
- `document_mutation_writes_audit_and_outbox` — FR-F045-13: each mutation → one `audit_events` row with diff and one `outbox_events` row; idempotent replay returns the original body.
- `request_span_carries_ids` — NFR-F045-04: tracing span has `tenant_id`, `document_id`, `revision`, `correlation_id`; `document_checksum_verified_total` increments on read.

Evidence: JUnit output and request logs under `testing/evidence/F045/api/`.
