---
id: S091
type: story
status: planned
parent_epic: E004
parent_feature: F046
depends_on: [F045, F004]
owned_paths: [crates/domain/src/realtime/**, services/api/src/realtime/**, services/realtime/src/realtime/**, services/api/migrations/*_realtime_*.sql, testing/features/F046/**]
feature_flag: F046_FEATURE
branch: s091-presence-co-editing
started_at: null
finished_at: null
---

# S091 — Presence/co-editing

## Identity

- Parent feature: `F046` Live collaboration
- Owner: platform
- Branch: `s091-presence-co-editing`
- Decision references: `docs/architecture-decisions.md` sections 2–5, 7; `docs/capability-contracts.md` row F046

## Vertical slice

As a document or sheet editor, I want to open a live session, see who else is present, and have my document changes and sheet patches applied in a deterministic order with acknowledgements, so that several people can edit the same target at once without overwriting each other.

## Requirements

- **SR-S091-01:** `GET /ws/v1/documents/{id}` and `GET /ws/v1/sheets/{id}` authenticate the gateway context, check the target ACL, insert `collaboration_sessions`, and reply `hello { session_id, durable_rev, read_only }`; denied closes `4403`, foreign or unknown closes `4404`, unauthenticated closes `4401` (covers FR-F046-01).
- **SR-S091-02:** Envelopes `{ type, seq, rev, payload, correlation_id }` are validated; out-of-order `seq` returns `error { code: invalid }` without closing (FR-F046-02).
- **SR-S091-03:** Join writes a `presence_leases` row expiring in 30 seconds and broadcasts `presence.joined.v1`; `presence` messages every 10 seconds renew it; the sweeper expires stale leases and emits `presence.left.v1` (FR-F046-03).
- **SR-S091-04:** `change` appends to `document_changes` with the next `rev` under a per-document advisory lock, deduplicates on `(document_id, hash)`, rejects unknown deps with `error { code: conflict }`, acks after commit, and broadcasts with `document.change-applied.v1` (FR-F046-04, FR-F046-05).
- **SR-S091-05:** `patch` applies a cell write through the F008 row update path with `if_match_version`, acks with `row_version`, broadcasts `sheet.patch-applied.v1`, and on a stale version replies `conflict` with the server value (FR-F046-07).
- **SR-S091-06:** Per-session limits of 100 messages per second and 256 KB, per-tenant 1,000 sessions, per-document 100 sessions are enforced with `rate_limited` then `4429` (FR-F046-11).
- **SR-S091-07:** Fan-out across two realtime nodes through `realtime.doc.{id}` and `realtime.sheet.{id}` delivers presence and changes within 1 second; viewers cannot send `change` or `patch`; cursors never leak across targets (FR-F046-13, NFR-F046-02).

## Surfaces

- Infrastructure/container: `services/realtime` service added to the F004 compose baseline with JetStream subjects `realtime.doc.*` and `realtime.sheet.*`
- Rust service/API: `crates/domain/src/realtime/{session.rs, envelope.rs, presence.rs, change.rs, patch.rs, errors.rs, service.rs}`; `services/realtime/src/realtime/{mod.rs, ws_document.rs, ws_sheet.rs, session.rs, fanout.rs, lease_sweeper.rs, limits.rs}`; `services/api/src/realtime/{routes.rs, handlers_sessions.rs, dto.rs}`
- Data/migration: `services/api/migrations/<ts>_realtime_create_tables.sql` creating `collaboration_sessions`, `presence_leases`, `document_changes` with indexes from ticket section 4
- React/UI: none in this story (S092 and T183 cover UI)
- Mocks/fixtures: `testing/fixtures/realtime.rs` document with 20-change history, sheet with 50 rows, two editors, viewer, foreign tenant; WebSocket test client `testing/harness/ws.rs`; two in-process nodes with embedded JetStream

## TDD harness

- Test path: `testing/features/F046/api/`, `testing/features/F046/database/`, `testing/features/F046/requirements/`
- Feature flag: `F046_FEATURE`
- Targeted command: `cargo xtask test-feature F046`
- Full command: `cargo xtask test-all`
- First failing tests: `handshake_denied_closes_4403`, `handshake_foreign_tenant_closes_4404`, `presence_lease_expires_after_thirty_seconds`, `concurrent_changes_get_consecutive_revs`, `retransmitted_change_returns_original_rev`, `stale_patch_returns_conflict`, `viewer_change_rejected`

## Exit criteria

- [ ] Requirement tests SR-S091-01 through SR-S091-07 written first and failing
- [ ] Tasks T181 and T182 complete and wired through `services/realtime` main and `services/api` router
- [ ] Unit, API, database, permission tests pass in targeted and full modes
- [ ] Production call path named: `services/realtime/src/realtime/ws_document.rs` and `ws_sheet.rs` mounted in `services/realtime/src/main.rs`; `services/api/src/realtime/routes.rs` mounted in `services/api/src/router.rs`
- [ ] Handoff evidence recorded in the F046 ticket
