# F036 api cases

File: `testing/features/F036/api/{share_tests.rs,evaluate_tests.rs,guest_tests.rs,link_tests.rs,isolation_tests.rs}`. Flag `F036_FEATURE`.

- `share_grant_returns_version_one` — FR-F036-01: owner POST `/api/v1/shares` for `dana` commenter on "Launch plan" → 201, `version: 1`, `share.granted.v1`.
- `share_duplicate_principal_conflicts` — FR-F036-02: second grant for the same pair → 409 `field_errors.principal: already_shared`.
- `share_update_stale_version_conflicts` — FR-F036-02: PATCH with `If-Match: 1` against version 2 → 409; PATCH with current → `share.updated.v1`.
- `share_last_owner_revoke_conflicts` — FR-F036-03: DELETE the only owner grant → 409 `field_errors.role: last_owner`; downgrade to editor → 409; with a second owner → 200.
- `share_list_includes_inherited_with_source` — FR-F036-05: sheet list shows `Contractors` editor with `inherited_from: workspace` and `dana` viewer direct; `effect=deny` filter returns only denies.
- `share_editor_denied` — FR-F036-15: `eli` on GET list, POST, PATCH, DELETE, share-links, invite → 403 `denied`.
- `share_cross_tenant_not_found` — FR-F036-15: tenant B on share, link, and invitation IDs → 404.
- `share_mutation_writes_audit_and_outbox` — FR-F036-15: each mutation → one `audit_events` row with before/after and one `outbox_events` row.
- `share_deny_beats_inherited_allow` — FR-F036-04: `dana` with workspace editor via `Contractors` and dashboard deny → dashboard read 404, sheet read 200.
- `share_closest_allow_narrows_role` — FR-F036-04: sheet viewer over workspace editor → row PATCH 403, row GET 200.
- `share_no_grant_denies` — FR-F036-04: user with no grant or membership → 404 on the sheet.
- `share_evaluation_error_fails_closed` — NFR-F036-04: injected ancestry lookup failure → `denied`, error logged with correlation ID.
- `share_expired_grant_ignored_and_swept` — FR-F036-13: grant with `expires_at` in the past → read 404; sweeper deletes it and publishes `share.revoked.v1 { reason: expired }` once across two runs.
- `guest_invite_owner_role_invalid` — FR-F036-06: `role: owner` → 400 `field_errors.role: guest_role_not_allowed`; `expires_in_days: 15` → 400.
- `guest_invite_publishes_event_with_accept_url` — FR-F036-06: invite → `guest_invitations` row with hashed token, `guest.invited.v1` payload has `accept_url`, response includes `accept_url`.
- `guest_accept_creates_identity_and_grant` — FR-F036-07: accept → `guest_users` row, F002 user with `is_guest`, viewer grant on the sheet, `accepted_at`, session cookie, `guest.accepted.v1`.
- `guest_accept_reuses_existing_email` — FR-F036-07: second invitation for the same email → same `guest_users.id`, new grant only.
- `guest_accept_expired_token_not_found` — FR-F036-07: token at +8 days, used token, and random token → 404.
- `guest_workspace_list_only_granted` — FR-F036-08: guest `GET /api/v1/workspaces` → only "Ops"; `GET /api/v1/search` scoped to granted targets.
- `link_create_returns_url_once` — FR-F036-09: POST → `url` with 43-char token; GET list never returns `url`; `share-link.created.v1`.
- `link_expiry_over_30_days_invalid` — FR-F036-09: `expires_at` now + 31 days → 400 `field_errors.expires_at: max_30_days`; role `editor` → 400.
- `link_resolve_mints_scoped_token` — FR-F036-11: GET `/public/share/{token}` → `scoped_token` with 15-minute expiry and scope `share-link:sheet:<id>:viewer`, `use_count` 1.
- `link_max_uses_exhausted_not_found` — FR-F036-11: third resolve on `max_uses` 2 → 404.
- `link_revoked_resolve_not_found` — FR-F036-10: DELETE → `share-link.revoked.v1`; resolve → 404; existing scoped token → 401 `denied`.
- `link_resolve_rate_limited` — FR-F036-11: 61 requests in one minute from one IP → 429 `rate_limited`, metric incremented.
- `link_token_stored_hashed` — NFR-F036-02: `share_links.token_hash` equals SHA-256 of the returned token; raw token absent from the database and logs.
- `link_scoped_token_cannot_search_or_write` — FR-F036-12: scoped token on `GET /api/v1/workspaces`, `GET /api/v1/search`, `PATCH /api/v1/rows/{id}` → 403.
- `link_scoped_token_cannot_read_other_resources` — FR-F036-12: another sheet in the same workspace → 404; target sheet and its rows → 200.
- `link_scoped_token_expires_after_15_minutes` — FR-F036-11: clock +16 min → 401 `denied`.
- `guest_cannot_reach_ungranted_sheet` — FR-F036-08: guest GET another sheet → 404.
- `guest_cannot_open_share_dialog_routes` — FR-F036-15: guest GET shares list on the granted sheet → 403.
- `deny_wins_for_group_member` — FR-F036-04: deny on group `Contractors` at folder level → `dana` read 404 despite direct sheet viewer.
- `public_routes_redact_tokens_in_traces` — NFR-F036-02: captured spans for public routes contain `token=<redacted>`.

Evidence: JUnit output and request logs under `testing/evidence/F036/api/`.
