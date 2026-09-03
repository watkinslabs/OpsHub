# F046 api cases

File: `testing/features/F046/api/{session_tests.rs,ordering_tests.rs,patch_tests.rs,replay_tests.rs,admin_tests.rs}`. Flag `F046_FEATURE`. Realtime service runs in-process against embedded JetStream.

- `handshake_returns_hello_with_durable_rev` — FR-F046-01: editor upgrade on `/ws/v1/documents/{id}` → `hello { session_id, durable_rev: 20, read_only: false }`.
- `handshake_viewer_is_read_only` — FR-F046-01: viewer → `read_only: true`.
- `handshake_denied_closes_4403` — FR-F046-01: user with explicit deny → close 4403.
- `handshake_foreign_tenant_closes_4404` — FR-F046-01: tenant B document id → close 4404.
- `handshake_without_session_closes_4401` — FR-F046-01: no gateway context → close 4401.
- `out_of_order_seq_errors_without_close` — FR-F046-02: `seq` 1, 2, 4 → `error invalid`; socket open.
- `presence_join_writes_lease_and_broadcasts` — FR-F046-03: join → lease row with 30 s expiry; other session receives `presence`; `presence.joined.v1`.
- `presence_lease_expires_after_thirty_seconds` — FR-F046-03: no renewal, clock +31 s, sweeper → `presence.left.v1`, lease removed.
- `concurrent_changes_get_consecutive_revs` — FR-F046-04: two clients send at once → revs 21 and 22, no gap.
- `ack_sent_only_after_commit` — FR-F046-04: change with forced commit delay → ack arrives after row visible.
- `retransmitted_change_returns_original_rev` — FR-F046-05: same change twice → same rev, one row.
- `unknown_deps_rejected_with_conflict` — FR-F046-05: change depending on unknown hash → `error conflict` with `missing_deps`.
- `snapshot_after_500_changes_posts_revision` — FR-F046-06: 500 changes → F045 revision created, `snapshot_rev` stamped.
- `snapshot_after_five_minutes` — FR-F046-06: 3 changes then clock +5 min → revision created.
- `patch_applies_and_broadcasts` — FR-F046-07: patch with version 3 → ack `row_version: 4`, other session receives patch, `sheet.patch-applied.v1`.
- `stale_patch_returns_conflict` — FR-F046-07: patch with version 3 after server at 4 → `conflict { server_value, server_version: 4 }`, row unchanged.
- `changes_since_returns_ordered_range` — FR-F046-09: `GET /changes?since=12` → revs 13..20.
- `changes_since_before_retention_conflicts` — FR-F046-09: `since=2` after pruning → 409 with `snapshot_rev: 10`.
- `socket_replay_precedes_live_changes` — FR-F046-09: `replay { since: 12 }` → revs 13..20 delivered before any new change.
- `rate_limit_third_violation_closes_4429` — FR-F046-11: 101 messages in 1 s three times → 4429.
- `message_over_256kb_rejected` — FR-F046-11: 257 KB change → `error invalid`.
- `document_session_limit_101_closes_4429` — FR-F046-11: 101st session on one document → 4429.
- `session_list_self_only_for_non_admin` — FR-F046-12: editor sees own sessions; admin sees tenant sessions.
- `force_close_sends_4400` — FR-F046-12: DELETE by admin → client receives 4400; by another user → 403.
- `change_fans_out_across_two_nodes_within_one_second` — FR-F046-13: node A change → node B client receives it in < 1 s.
- `viewer_change_rejected` — FR-F046-14: viewer sends `change` → `error denied`, no row.
- `revoked_editor_downgraded_within_60s` — NFR-F046-02: ACL removed, clock +60 s → `read_only: true` message or 4403.
- `cursor_not_leaked_to_other_target` — NFR-F046-02: presence on document A never reaches a document B session.
- `duplicate_fanout_applied_once` — NFR-F046-04: JetStream redelivery of `(document_id, rev, hash)` → client receives one change.
- `session_span_carries_ids` — NFR-F046-04: span has `tenant_id`, `session_id`, `target_id`, `correlation_id`.

Evidence: JUnit output and socket transcripts under `testing/evidence/F046/api/`.
