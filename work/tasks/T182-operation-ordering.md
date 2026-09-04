---
id: T182
type: task
status: planned
parent_epic: E004
parent_feature: F046
parent_story: S091
depends_on: [T181]
owned_paths: [crates/domain/src/realtime/**, crates/persistence/src/realtime/**, services/api/src/realtime/**, services/realtime/src/realtime/**, testing/features/F046/api/**, testing/features/F046/requirements/**]
feature_flag: F046_FEATURE
branch: t182-operation-ordering
started_at: null
finished_at: null
---

# T182 — Operation ordering

## Identity

- Parent story: `S091` Presence/co-editing
- Owner: platform
- Branch: `t182-operation-ordering`
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 5, 7; `docs/capability-contracts.md` row F046

## Objective

Implement sequential document change application with acknowledgements and deduplication, sheet patches with visible conflicts, and cross-node fan-out through JetStream so every client sees changes in the same order.

## Specification

- Owned paths: `crates/domain/src/realtime/{change.rs, patch.rs, ordering.rs}`, `crates/persistence/src/realtime/{document_change_repository.rs, collaboration_session_repository.rs}`, `services/realtime/src/realtime/{changes.rs, patches.rs, fanout.rs}`, `services/api/src/realtime/{mod.rs, routes.rs, handlers_sessions.rs, dto.rs}`
- Contract/input: `change { change_base64 (≤ 256 KB Automerge change), deps, rev }`, whose `deps` hashes are stored as `document_change_deps` rows rather than an array column; `patch { row_id, column_id, value, if_match_version }`; JetStream subjects `realtime.doc.{document_id}` and `realtime.sheet.{sheet_id}`; HTTP `GET /api/v1/collaboration/sessions` list query `{ cursor?, limit?, filter[target_type]?, filter[actor_id]? }`.
- Output/behavior: `DocumentChangeRepository::next_rev`/`append_change` in `crates/persistence` take `pg_advisory_xact_lock(hashtext(document_id))` and run the `select coalesce(max(rev), 0) + 1 ... for update` that assigns `rev = max + 1` — only the SQL moved out of the service, and the same per-document lock in the same transaction still serializes concurrent appenders; one `UnitOfWork` covers the rev assignment, the `document_changes` row, its `document_change_deps` rows, and the F045 `current_revision` bump through `DocumentRevisionRepository`, and only after that commit does the service reply `ack { seq, rev }` and publish to the subject with `document.change-applied.v1` in the outbox; duplicate `(document_id, hash)` is resolved by `find_by_hash(document_id, hash)` and returns the original `rev`; `find_missing_deps(document_id, hashes)` joins `document_change_deps` against `document_changes(document_id, hash)` and any unresolved hash → `error { code: conflict, missing_deps }`; `apply_sheet_patch` calls the F008 row update and its cell repository with `If-Match`, acks `{ seq, rev, row_version }`, emits `sheet.patch-applied.v1`, and on `StaleVersion` replies `conflict { row_id, column_id, server_value, server_version }`; viewers sending `change` or `patch` get `error denied`; `fanout.rs` keeps one durable consumer per connected target per node, applies by `rev`, drops the consumer when the last local session leaves; the session list route reads `CollaborationSessionRepository::list_active_sessions` for tenant-admin or self. No file under `services/realtime/src/realtime/`, `services/api/src/realtime/`, or `crates/domain/src/realtime/` holds a SQL string, `sqlx::query*` call, or connection.
- Dependencies: T181 sessions and envelope; F008 `update_row` service; F004 JetStream client and outbox; `automerge` crate for dependency validation.
- Feature flag: `F046_FEATURE`

## TDD

- Failing test first: `testing/features/F046/api/ordering_tests.rs::concurrent_changes_get_consecutive_revs`, `::ack_sent_only_after_commit`, `::retransmitted_change_returns_original_rev`, `::dep_rows_written_in_same_transaction`, `::unknown_deps_rejected_with_conflict`, `::change_fans_out_across_two_nodes_within_one_second`, `::viewer_change_rejected`; `testing/features/F046/api/patch_tests.rs::patch_applies_and_broadcasts`, `::stale_patch_returns_conflict`, `::cursor_not_leaked_to_other_target`; `testing/features/F046/api/admin_tests.rs::session_list_self_only_for_non_admin`
- Targeted command: `cargo xtask test-feature F046`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: two in-process realtime nodes with embedded JetStream; WebSocket test clients; real F008 row service on the 50-row fixture sheet

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Session routes mounted in `services/api/src/router.rs` behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S091
- [ ] `finished_at` recorded
