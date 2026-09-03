---
id: T183
type: task
status: planned
parent_epic: E004
parent_feature: F046
parent_story: S092
depends_on: [S092]
owned_paths: [crates/domain/src/realtime/**, services/api/src/realtime/**, services/realtime/src/realtime/**, apps/web/src/features/realtime/**, testing/features/F046/api/**, testing/features/F046/frontend/**]
feature_flag: F046_FEATURE
branch: t183-presence-ui
started_at: null
finished_at: null
---

# T183 — Presence UI

## Identity

- Parent story: `S092` Change recovery
- Owner: platform
- Branch: `t183-presence-ui`
- Decision references: `docs/architecture-decisions.md` sections 5, 6; `docs/capability-contracts.md` row F046

## Objective

Implement the replay API, snapshotter, ACL re-check, and force-close route, and build the browser socket client, reconnect queue, Automerge sync hook, and presence, status, and conflict components integrated into the document editor and grid.

## Specification

- Owned paths: `crates/domain/src/realtime/{replay.rs, snapshot.rs, service_admin.rs}`, `services/realtime/src/realtime/{replay.rs, snapshotter.rs, acl_recheck.rs}`, `services/api/src/realtime/{handlers_changes.rs, handlers_admin.rs}`, `apps/web/src/features/realtime/{PresenceAvatars.tsx, RemoteCursorLayer.tsx, ConnectionStatusBadge.tsx, ConflictBanner.tsx, SessionPanel.tsx, useCollaborationSession.ts, usePresence.ts, useDocumentSync.ts, useSheetPatches.ts, socket.ts, queue.ts, api.ts, routes.ts}`
- Contract/input: `GET /api/v1/documents/{id}/changes?since={rev}` with `limit` ≤ 1,000 and cursor; socket `replay { since }`; `DELETE /api/v1/collaboration/sessions/{id}`; snapshot trigger every 500 changes or 5 minutes; ACL re-check every 60 seconds; generated `RealtimeApi`; `@automerge/automerge` in the browser.
- Output/behavior: replay returns ordered `ChangeResponse` rows, `409 conflict` with `snapshot_rev` when `since` predates retention; snapshotter materializes the document and posts `POST /api/v1/documents/{id}/revisions` with `If-Match`, stamps `snapshot_rev`; ACL re-check downgrades revoked editors to read-only or closes `4403`; force-close sends `4400`; `socket.ts` reconnects with backoff `1, 2, 4, 8, max 30 s`, `queue.ts` retransmits unacked messages in order after `replay`; `useDocumentSync` merges remote changes into the local Automerge doc and applies local edits optimistically; `useSheetPatches` applies patches and surfaces `conflict` to `ConflictBanner` with `Keep mine` / `Take theirs`; `ConnectionStatusBadge` states `Connecting`, `Live`, `Reconnecting`, `Read-only`, `Offline`, `Changes not saved`; `PresenceAvatars` collapses to `+N` over 5; polite live region announcements rate-limited to one per 5 seconds; telemetry `collab_session_opened`, `collab_reconnected`, `change_applied`, `patch_conflict_shown`, `patch_conflict_resolved`, `presence_lease_expired`.
- Dependencies: T182 ordering and fan-out; F045 `DocumentEditor.tsx` integration props; F006/F008 grid cell editor hook.
- Feature flag: `F046_FEATURE` read through the flag hook; editors fall back to F045 revision saves when off.

## TDD

- Failing test first: `testing/features/F046/api/replay_tests.rs::changes_since_returns_ordered_range`, `::changes_since_before_retention_conflicts`, `::snapshot_after_500_changes_posts_revision`, `::revoked_editor_downgraded_within_60s`, `::force_close_sends_4400`; `testing/features/F046/frontend/useDocumentSync.test.tsx::reconnect_replays_then_flushes_queue`, `ConflictBanner.test.tsx::conflict_banner_keep_mine_resubmits`, `ConnectionStatusBadge.test.tsx::shows_reconnecting_after_two_seconds`, `PresenceAvatars.test.tsx::collapses_over_five_collaborators`
- Targeted command: `cargo xtask test-feature F046`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: mock WebSocket server for Vitest; MSW handlers for changes and sessions; document fixture with snapshot at rev 10 and changes to rev 20

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Changes and admin routes mounted; components integrated into `DocumentEditor.tsx` and the grid behind the flag
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S092
- [ ] `finished_at` recorded
