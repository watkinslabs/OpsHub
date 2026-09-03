# F046 frontend cases

File: `testing/features/F046/frontend/{useDocumentSync.test.tsx,useSheetPatches.test.tsx,ConflictBanner.test.tsx,ConnectionStatusBadge.test.tsx,PresenceAvatars.test.tsx,RemoteCursorLayer.test.tsx,SessionPanel.test.tsx}`. Vitest with a mock WebSocket server and MSW. Flag `F046_FEATURE`.

- `reconnect_replays_then_flushes_queue` — FR-F046-10: socket drops with 2 queued changes; on reconnect `replay` is sent first, then the 2 changes in order, acks clear the queue.
- `remote_change_merges_into_local_doc` — FR-F046-04: incoming change at rev 21 merges; local text shows both edits.
- `gap_in_revs_triggers_replay` — FR-F046-09: receiving rev 23 after 21 sends `replay { since: 21 }`.
- `conflict_banner_keep_mine_resubmits` — FR-F046-08: `Keep mine` sends patch with `if_match_version: server_version`.
- `conflict_banner_take_theirs_applies_server_value` — FR-F046-08: `Take theirs` writes server value locally and clears the banner.
- `conflict_banner_persists_until_resolved` — FR-F046-08: incoming unrelated changes do not dismiss the banner.
- `shows_reconnecting_after_two_seconds` — FR-F046-10: offline 2 s → badge `Reconnecting`; 30 s → `Changes not saved`.
- `read_only_badge_disables_sending` — FR-F046-14: `hello.read_only: true` → badge `Read-only`, `send` for `change` disabled.
- `collapses_over_five_collaborators` — FR-F046-14: 8 presences render 5 avatars and `+3`.
- `remote_cursor_positions_from_presence` — FR-F046-14: presence payload places a labeled cursor at the given offset.
- `beforeunload_prompt_with_pending_changes` — FR-F046-10: pending queue sets `event.returnValue`.
- `session_panel_lists_and_closes_own_session` — FR-F046-12: panel lists sessions; close calls `closeSession`.
- `presence_announcement_rate_limited` — NFR-F046-03: three joins within 5 s produce one live-region announcement.

Evidence: Vitest JUnit under `testing/evidence/F046/frontend/`.
