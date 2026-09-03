# F016 api cases

File: `testing/features/F016/api/{comment_tests.rs,mention_tests.rs,activity_tests.rs}`. Flag `F016_FEATURE`.

- `comment_create_opens_thread` — FR-F016-01, FR-F016-02: POST `/api/v1/comments` on row "Kickoff" without `thread_id` → 201, new `thread_id`, `version: 1`.
- `comment_reply_uses_existing_thread` — FR-F016-01: POST with `thread_id` and `parent_comment_id` → nested under parent, no new thread.
- `comment_thread_target_mismatch_invalid` — FR-F016-02: `thread_id` from another row → 400 `field_errors.thread_id: target_mismatch`.
- `comment_body_too_long_invalid` — FR-F016-03: 10,001 characters → 400 `field_errors.body: too_long`.
- `comment_list_pages_and_filters_resolved` — FR-F016-05: 120 threads, `limit=100`, two pages; `resolved=false` returns only open threads.
- `comment_edit_inside_window_sets_edited_at` — FR-F016-06: author PATCH at +1 h → 200, `edited_at` set, `comment.updated.v1`.
- `comment_edit_after_window_denied` — FR-F016-06: author PATCH at +25 h → 403 `denied`; admin PATCH → 200.
- `comment_edit_stale_version_conflicts` — FR-F016-06: `If-Match: 1` against version 2 → 409.
- `comment_delete_keeps_placeholder_with_replies` — FR-F016-07: delete parent with reply → list shows `deleted: true` placeholder; delete leaf → absent.
- `thread_resolve_sets_fields_and_event` — FR-F016-08: resolve → `resolved_at`, `resolved_by`, `comment.resolved.v1`.
- `thread_resolve_twice_conflicts` — FR-F016-08: second resolve → 409 `conflict`, `resolved_at` unchanged.
- `comment_idempotent_replay_returns_original` — FR-F016-11: same `Idempotency-Key` twice → one comment; different body → 409.
- `comment_mutation_writes_audit_and_outbox` — FR-F016-11: each mutation → one `audit_events` row with diff and one `outbox_events` row.
- `comment_viewer_denied` — FR-F016-12: viewer `vic` POST/PATCH/DELETE/resolve → 403 `denied`.
- `comment_cross_tenant_not_found` — FR-F016-12: tenant B on all six routes → 404.
- `mention_resolved_publishes_event` — FR-F016-04: `@[user:dana]` → `mentions` row and `mention.created.v1 { mentioned_kind: user }`.
- `mention_without_access_stays_plain_text` — FR-F016-04: user without row access → no event, token in `unresolved_mentions`.
- `mention_foreign_tenant_user_unresolved` — NFR-F016-02: tenant B user id → unresolved, response reveals nothing but the token.
- `mention_limit_51_invalid` — FR-F016-03: 51 tokens → 400 `too_many_mentions`.
- `mention_edit_publishes_only_new_mentions` — FR-F016-06: edit adding `@[group:ops]` → exactly one new `mention.created.v1`.
- `mention_group_resolves_once` — FR-F016-04: same group token twice in body → one `mentions` row.
- `mention_suggestions_exclude_foreign_and_inactive` — NFR-F016-02: `?suggest=d` returns `dana`, not deactivated `old` or tenant B users, max 20.
- `activity_projects_row_updated` — FR-F016-10: `row.updated.v1` → entry with `changed_fields` and `actor_kind: user`.
- `activity_replayed_event_not_duplicated` — FR-F016-10: same `event_id` twice → one entry.
- `activity_filters_by_actor_kind` — FR-F016-09: `actor_kind=automation` returns only workflow-run entries; `since`/`until` bound the page.
- `activity_marks_workflow_actor_automation` — FR-F016-09: event with `workflow_run_id` → `actor_kind: automation`.
- `activity_row_delete_hides_threads_restore_shows` — FR-F016-14: delete row → threads hidden; restore → visible with two new entries.
- `activity_unreadable_target_not_found` — FR-F016-12: non-member GET activity → 404.
- `activity_dead_letters_after_five_failures` — NFR-F016-04: projector failing 5 times → `dead_letters` row and metric increment.
- `request_span_carries_target_ids` — NFR-F016-04: span has `tenant_id`, `target_kind`, `target_id`, `correlation_id`.

Evidence: JUnit output and request logs under `testing/evidence/F016/api/`.
