---
id: T181
type: task
status: planned
parent_epic: E004
parent_feature: F046
parent_story: S091
depends_on: [S091]
owned_paths: [services/api/migrations/*_realtime_*.sql, crates/domain/src/realtime/**, crates/persistence/src/realtime/**, services/realtime/src/realtime/**, testing/features/F046/database/**, testing/features/F046/api/**]
feature_flag: F046_FEATURE
branch: t181-realtime-session-service
started_at: null
finished_at: null
---

# T181 — Realtime session service

## Identity

- Parent story: `S091` Presence/co-editing
- Owner: platform
- Branch: `t181-realtime-session-service`
- Decision references: `docs/architecture-decisions.md` sections 2, 4, 5; `docs/capability-contracts.md` row F046

## Objective

Create the session, lease, and change tables and the WebSocket handshake, envelope handling, presence leases, sweeper, and limits in `services/realtime` so a client can join a document or sheet and see who else is present.

## Specification

- Owned paths: `services/api/migrations/<ts>_realtime_create_tables.sql`, `services/api/migrations/<ts>_realtime_create_tables.down.sql`, `crates/domain/src/realtime/{mod.rs, schema.rs, session.rs, envelope.rs, presence.rs, errors.rs, service.rs}`, `crates/persistence/src/realtime/{mod.rs, collaboration_session_repository.rs, presence_lease_repository.rs, document_change_repository.rs}`, `services/realtime/src/realtime/{mod.rs, ws_document.rs, ws_sheet.rs, session.rs, lease_sweeper.rs, limits.rs}`
- Contract/input: DDL per F046 ticket section 4: `collaboration_sessions`, `presence_leases`, `document_changes`, `document_change_deps` with check constraints, `(document_id, rev)` primary key, unique `(document_id, hash)`, `document_change_deps(document_id, rev, dep_hash)` primary key with `on delete cascade` to `document_changes(document_id, rev)`, `presence_leases.session_id` foreign key, partial indexes, and `document_change_deps(document_id, dep_hash)`. WebSocket upgrade on `GET /ws/v1/documents/{id}` and `GET /ws/v1/sheets/{id}` with the gateway context; envelope `{ type, seq, rev, payload, correlation_id }`; `presence { cursor, selection }` every 10 seconds.
- Data access: `CollaborationSessionRepository` owns `collaboration_sessions` with `open_session(session)`, `close_session(session_id, close_code)`, `list_active_sessions(target_type, target_id)`, and `force_close(session_id)`; `PresenceLeaseRepository` owns `presence_leases` with `renew_lease(session_id, expires_at)`, `expire_leases(now)`, and `list_presence(target_type, target_id)`; `DocumentChangeRepository` owns `document_changes` and `document_change_deps`. All SQL for this task lives in `crates/persistence/src/realtime/`; the WebSocket handlers, the session task, and the sweeper call these traits and hold no SQL string, `sqlx::query*` call, or connection.
- Output/behavior: handshake checks target ACL (`document-editor`/`sheet-editor` write, viewer read-only), inserts the session through `open_session`, replies `hello { session_id, durable_rev, read_only }`; close codes `4401`, `4403`, `4404`, `4429`, `4400`; out-of-order `seq` → `error invalid`; join writes a 30-second lease and emits `presence.joined.v1`; `presence` renews; sweeper every 5 seconds calls `expire_leases(now)` and emits `presence.left.v1`; token buckets enforce 100 messages per second, 256 KB, 1,000 sessions per tenant, 100 per document; audit `collaboration-session.open` and `close`; metrics `realtime_sessions{tenant}`, `realtime_lease_expired_total`.
- Dependencies: F045 `documents` table; F006 `sheets`; F003 authz; F004 metrics and gateway context extractor.
- Feature flag: `F046_FEATURE` gates route registration in `services/realtime/src/main.rs`.
- Large-table note: `document_changes` is append-only and pruned after snapshots; no existing data.

## TDD

- Failing test first: `testing/features/F046/database/migration_tests.rs::realtime_tables_exist_with_constraints`, `::duplicate_change_hash_rejected`, `::duplicate_rev_rejected`, `::lease_requires_session`, `::dep_row_cascades_with_change`, `::duplicate_dep_hash_rejected`, `::rollback_drops_four_tables`; `testing/features/F046/api/session_tests.rs::handshake_returns_hello_with_durable_rev`, `::handshake_denied_closes_4403`, `::handshake_foreign_tenant_closes_4404`, `::out_of_order_seq_errors_without_close`, `::presence_lease_expires_after_thirty_seconds`, `::rate_limit_third_violation_closes_4429`, `::document_session_limit_101_closes_4429`
- Targeted command: `cargo xtask test-feature F046`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: schema-per-worker database; WebSocket test client `testing/harness/ws.rs`; controllable clock; `testing/fixtures/realtime.rs`

## Exit criteria

- [ ] Tests written before the migration and service and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; WebSocket routes registered behind the flag
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S091
- [ ] `finished_at` recorded
