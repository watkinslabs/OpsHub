---
id: S092
type: story
status: planned
parent_epic: E004
parent_feature: F046
depends_on: [S091]
owned_paths: [crates/domain/src/realtime/**, services/api/src/realtime/**, services/realtime/src/realtime/**, apps/web/src/features/realtime/**, testing/features/F046/**]
feature_flag: F046_FEATURE
branch: s092-change-recovery
started_at: null
finished_at: null
---

# S092 — Change recovery

## Identity

- Parent feature: `F046` Live collaboration
- Owner: platform
- Branch: `s092-change-recovery`
- Decision references: `docs/architecture-decisions.md` sections 3, 5, 6; `docs/capability-contracts.md` row F046

## Vertical slice

As an editor whose connection drops, I want my queued changes to be sent when I reconnect, missed changes to be replayed in order, snapshots to keep replay short, conflicts to be shown for me to resolve, and presence and status to be visible in the editor, so that nothing is lost or silently overwritten.

## Requirements

- **SR-S092-01:** `GET /api/v1/documents/{id}/changes?since={rev}` returns changes with `rev > since` in order, `limit` ≤ 1,000 with cursor; `since` older than retention returns `409 conflict` with `snapshot_rev` (FR-F046-09).
- **SR-S092-02:** The socket `replay { since }` message delivers the same range before any live change; the client applies by `rev` and requests replay on any gap (FR-F046-09, FR-F046-13).
- **SR-S092-03:** The snapshotter posts a revision through `POST /api/v1/documents/{id}/revisions` every 500 changes or 5 minutes and stamps `snapshot_rev`; joining clients load the revision and replay only later changes (FR-F046-06).
- **SR-S092-04:** The client outbound queue retransmits unacknowledged changes and patches in order after reconnect with backoff `1, 2, 4, 8, max 30 s`; `Reconnecting` after 2 seconds, `Changes not saved` after 30 seconds, `beforeunload` prompt with pending changes (FR-F046-10).
- **SR-S092-05:** `ConflictBanner` shows the server and local values with `Keep mine` and `Take theirs`; `Keep mine` resubmits with the server version; the banner stays until resolved (FR-F046-08).
- **SR-S092-06:** `GET /api/v1/collaboration/sessions` and `DELETE /api/v1/collaboration/sessions/{id}` list and force-close sessions for tenant-admin or self; the ACL re-check every 60 seconds downgrades or closes revoked editors (FR-F046-12, NFR-F046-02).
- **SR-S092-07:** `PresenceAvatars`, `RemoteCursorLayer`, `ConnectionStatusBadge`, and `SessionPanel` integrate into the F045 editor and F006 grid with loading, empty, error, denied, stale, offline states and the announcements from NFR-F046-03; round trip and replay meet NFR-F046-01 (FR-F046-14).

## Surfaces

- Infrastructure/container: none beyond S091
- Rust service/API: `crates/domain/src/realtime/{replay.rs, snapshot.rs, service_admin.rs}`; `services/realtime/src/realtime/{replay.rs, snapshotter.rs, acl_recheck.rs}`; `services/api/src/realtime/{handlers_changes.rs, handlers_admin.rs}`
- Data/migration: none new; uses tables from S091
- React/UI: `apps/web/src/features/realtime/{PresenceAvatars.tsx, RemoteCursorLayer.tsx, ConnectionStatusBadge.tsx, ConflictBanner.tsx, SessionPanel.tsx, useCollaborationSession.ts, usePresence.ts, useDocumentSync.ts, useSheetPatches.ts, socket.ts, queue.ts, api.ts, routes.ts}`
- Mocks/fixtures: document with snapshot at rev 10 and changes to rev 20; controllable clock; mock WebSocket server for component tests; 50-editor and 1,000-session load generators

## TDD harness

- Test path: `testing/features/F046/{api,frontend,e2e,accessibility,performance}/`
- Feature flag: `F046_FEATURE`
- Targeted command: `cargo xtask test-feature F046`
- Full command: `cargo xtask test-all`
- First failing tests: `changes_since_returns_ordered_range`, `changes_since_before_retention_conflicts`, `snapshot_after_500_changes_posts_revision`, `reconnect_replays_then_flushes_queue`, `conflict_banner_keep_mine_resubmits`, `revoked_editor_downgraded_within_60s`, `change_round_trip_50_editors_p95`

## Exit criteria

- [ ] Requirement tests SR-S092-01 through SR-S092-07 written first and failing
- [ ] Tasks T183 and T184 complete; UI wired to real socket and API through generated client
- [ ] Unit, API, React, E2E, accessibility, permission, and performance tests pass
- [ ] Production call path named: `apps/web/src/features/realtime/useCollaborationSession.ts` consumed by `apps/web/src/features/documents/DocumentEditor.tsx` at `/w/:workspaceId/documents/:documentId`; `services/realtime/src/realtime/replay.rs` registered in `services/realtime/src/main.rs`
- [ ] Handoff evidence recorded in the F046 ticket
