---
id: F046
type: feature
status: planned
priority: P2
owner: platform
estimate: 8
target_milestone: M3
parent_epic: E004
depends_on: [F045, F004]
blocks: []
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/realtime/**, crates/persistence/src/realtime/**, services/api/src/realtime/**, services/realtime/src/realtime/**, apps/web/src/features/realtime/**, services/api/migrations/*_realtime_*.sql, testing/features/F046/**]
feature_flag: F046_FEATURE
flag_default: off
branch: f046-live-collaboration
started_at: null
finished_at: null
---

# F046 — Live collaboration

## 1. Identity and dates

- Branch: `f046-live-collaboration`
- Capability area: concurrent editing (spec 5.4a DOC-03 and the live-session low-level rules; section 6 scale target of 1,000 concurrent edits per tenant; section 10 mobile decision excluding offline co-editing)
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4, 5, 7; `docs/capability-contracts.md` row F046
- Aggregate: `collaboration-session`
- Module slug: `realtime`

## 2. Requirement specification

### Problem and user outcome

Two people editing the same document or sheet today overwrite each other or wait for a page refresh to see changes. They need a live session that shows who is present, merges document edits deterministically, delivers sheet cell patches in order, recovers what was missed after a disconnect, and makes any conflict visible instead of silently discarding a newer revision.

As a document or sheet editor, I want to see collaborators' presence and cursors, have my edits merged live, reconnect without losing changes, and be told when a change conflicts, so that co-editing is safe and nothing is silently lost.

### Functional requirements

- **FR-F046-01:** A client opens `GET /ws/v1/documents/{id}` or `GET /ws/v1/sheets/{id}` with the gateway session; the handshake verifies `{ tenant_id, actor_id, roles, scopes, correlation_id }` and the target ACL (`document-editor` or `sheet-editor` for write, viewer roles for read-only), creates a `collaboration_sessions` row, and replies `hello { session_id, durable_rev, read_only }`; a denied actor is closed with code `4403`, an unknown or foreign-tenant target with `4404`, and a missing session with `4401`.
- **FR-F046-02:** Every message is a JSON envelope `{ type, seq, rev, payload, correlation_id }` with `type` in `hello, presence, change, ack, replay, patch, conflict, error, ping, pong`; the client increments `seq` per message and the server rejects an out-of-order `seq` with `error { code: invalid }` without closing the socket.
- **FR-F046-03:** On join the server writes a `presence_leases` row with `expires_at = now + 30 s`, broadcasts `presence.joined.v1` to the target's other sessions, and the client renews the lease every 10 seconds with `presence { cursor, selection }`; a lease not renewed within 30 seconds is expired by the sweeper, which emits `presence.left.v1` and removes the collaborator from every client's presence list.
- **FR-F046-04:** A `change` message for a document carries an Automerge binary change (≤ 256 KB) and the client's last known `rev`; the server appends it to `document_changes` with the next sequential `rev` for that document, replies `ack { seq, rev }` only after the row commits, and broadcasts the change with its `rev` to other sessions, emitting `document.change-applied.v1`.
- **FR-F046-05:** Document changes are deduplicated on `(document_id, hash)` so a client retransmitting after a lost `ack` receives the original `rev` and no duplicate row is written; the change's Automerge dependency hashes are written as `document_change_deps` rows in the same transaction, and a change with a dependency hash that has no matching `document_changes(document_id, hash)` row is rejected with `error { code: conflict, missing_deps }` and the client must replay first.
- **FR-F046-06:** Every 500 changes or 5 minutes since the last snapshot, whichever comes first, the realtime service materializes the Automerge document and posts a revision through the F045 route `POST /api/v1/documents/{id}/revisions` with `If-Match` on the last snapshot revision, recording `snapshot_rev` on the change row; clients joining after a snapshot load the revision body and replay only changes with `rev > snapshot_rev`.
- **FR-F046-07:** A `patch` message for a sheet carries `{ row_id, column_id, value, if_match_version }`; the server applies it through the F008 row update path as the actor, replies `ack { seq, rev, row_version }`, broadcasts `sheet.patch-applied.v1` to other sessions, and on a stale `if_match_version` replies `conflict { row_id, column_id, server_value, server_version }` without applying anything.
- **FR-F046-08:** A conflict is never resolved silently: the client renders the server value beside the local value with `Keep mine` and `Take theirs`, and `Keep mine` resubmits the patch with the server version; the conflict stays visible until the user chooses.
- **FR-F046-09:** `GET /api/v1/documents/{id}/changes?since={rev}` returns changes with `rev > since` in order, paged with `limit` up to 1,000 and an opaque cursor, and a reconnecting client sends `replay { since }` over the socket to receive the same range before resuming live changes; a `since` older than the oldest retained change returns `conflict` with `snapshot_rev` so the client reloads from the revision.
- **FR-F046-10:** The client keeps unacknowledged changes and patches in an in-memory outbound queue, retransmits them after reconnect in order, and shows `Reconnecting` after 2 seconds offline and `Changes not saved` after 30 seconds; when the tab is closed with pending changes the browser `beforeunload` prompt is shown.
- **FR-F046-11:** Each session is limited to 100 messages per second and 256 KB per message; exceeding the rate returns `error { code: rate_limited }` and a third violation within one minute closes the socket with `4429`; each tenant is limited to 1,000 concurrent sessions and each document to 100, and joins beyond the limit are closed with `4429`.
- **FR-F046-12:** `GET /api/v1/collaboration/sessions` lists sessions for the tenant (tenant-admin) or the actor's own sessions with `target_type`, `target_id`, `actor_id`, `connected_at`, `last_seen_at`; `DELETE /api/v1/collaboration/sessions/{id}` force-closes a session with code `4400` and is allowed for tenant-admin or the session's own actor.
- **FR-F046-13:** Presence, changes, and patches are fanned out across realtime nodes through JetStream subjects `realtime.doc.{document_id}` and `realtime.sheet.{sheet_id}` so two clients on different nodes see each other within 1 second; each node keeps a durable consumer per connected target and drops it when the last local session leaves.
- **FR-F046-14:** The web app shows presence avatars and remote cursors in the F045 document editor and the F006 grid, a connection status badge (`Live`, `Reconnecting`, `Read-only`, `Offline`), and the conflict banner; read-only viewers see presence and live changes but cannot send `change` or `patch`.

### Non-functional requirements

- **NFR-F046-01 Performance:** change round trip (send to ack) p95 under 250 ms in-region with 50 concurrent editors on one document; presence propagation under 1 second across nodes; 1,000 concurrent sessions per tenant on one realtime node with under 512 MB resident memory; replay of 1,000 changes under 500 ms.
- **NFR-F046-02 Security/privacy:** ACL checked at handshake and re-checked every 60 seconds so a revoked editor is downgraded to read-only or closed with `4403`; cursors and selections are broadcast only to sessions on the same target; cross-tenant targets close with `4404`; change payloads are never logged.
- **NFR-F046-03 Accessibility:** presence joins and leaves are announced through a polite live region with a rate limit of one announcement per 5 seconds; connection status uses text and icon; remote cursor animation respects `prefers-reduced-motion`; the conflict banner is focusable and keyboard resolvable.
- **NFR-F046-04 Reliability/observability:** at-least-once fan-out with idempotent `(document_id, rev, hash)` application; `ack` only after commit; metrics `realtime_sessions{tenant}`, `realtime_change_latency_ms`, `realtime_conflict_total`, `realtime_lease_expired_total`, `realtime_replay_total`; spans carry `tenant_id`, `session_id`, `target_id`, `correlation_id`.

### Scope

Included: WebSocket session service, handshake and ACL, message envelope, presence leases and sweeper, Automerge change log and snapshots, sheet patches with visible conflicts, replay API and socket replay, reconnect queue, per-session and per-tenant limits, session admin routes, cross-node fan-out, presence and conflict UI.

Excluded: document metadata, revisions, folders, and search (F045); grid editing semantics and bulk edits (F008); offline document co-editing (excluded by section 10); comments and mentions (F016); mobile offline queue for rows and forms (F058).

## 3. UX specification

- Entry points: opening a document at `/w/{workspace_id}/documents/{document_id}` or a sheet at `/w/{workspace_id}/sheets/{sheet_id}` with `F046_FEATURE` on connects automatically; the status badge in the header opens a session panel.
- Primary flow: two editors open the same document; each sees the other's avatar and a colored cursor with a name label; typing merges live; one editor loses network, keeps typing, sees `Reconnecting`, regains network, changes replay, and both documents converge; on a sheet, two editors change the same cell, the later one sees the conflict banner and picks `Take theirs`.
- Loading: badge shows `Connecting` with skeleton avatars; Empty: no other collaborators shows only the actor's avatar; Error: badge `Offline` with retry; Success: badge `Live`; Stale/conflict: conflict banner with both values; Offline: editor stays editable for documents with `Changes not saved` after 30 seconds and sheet cells locked.
- Permission-denied: viewers see `Read-only` badge, presence, and live changes; revoked editors are downgraded live with a toast; foreign targets render not-found.
- Responsive: avatars collapse to `+N` over 5 collaborators under 768 px; conflict banner stacks values vertically under 640 px.
- Keyboard: `Alt+Shift+P` opens the presence list, `Alt+Shift+C` focuses the conflict banner, `Enter` on `Keep mine` / `Take theirs`, `Escape` closes; focus ring from shared token; cursor animation off under `prefers-reduced-motion`.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062); Lucide icons `Users`, `Wifi`, `WifiOff`, `RefreshCw`, `Eye`, `AlertTriangle`; tokens from `apps/web/src/design/tokens.css`.

- Design: `design/artboards/Document.dc.html` on the canvas indexed by `design/canvas.json`. The ticket is the contract and the artboard is the picture; when they disagree the ticket wins.

## 4. Technical specification

### Rust backend

- Domain entities in `crates/domain/src/realtime/`: `CollaborationSession { id, tenant_id, actor_id, target: Target::{Document(id), Sheet(id)}, read_only, node_id, connected_at, last_seen_at, closed_at, close_code }`, `PresenceLease { session_id, tenant_id, target, actor_id, cursor: serde_json::Value, expires_at }`, `DocumentChange { tenant_id, document_id, rev: i64, actor_id, session_id, change: Vec<u8>, hash: [u8; 32], deps: Vec<[u8; 32]>, snapshot_rev: Option<i64>, applied_at }` whose `deps` are persisted as `document_change_deps` rows, not an array column, `Envelope { type: MessageType, seq: u64, rev: Option<i64>, payload, correlation_id }`, `SheetPatch { row_id, column_id, value, if_match_version }`.
- Use cases: `open_session`, `close_session`, `renew_lease`, `expire_leases`, `append_change`, `replay_changes`, `snapshot_document`, `apply_sheet_patch`, `list_sessions`, `force_close_session`, `recheck_acl`.
- Persistence (`crates/persistence/src/realtime/`): `CollaborationSessionRepository` owns `collaboration_sessions`; `PresenceLeaseRepository` owns `presence_leases`; `DocumentChangeRepository` owns `document_changes` and `document_change_deps`. Each implements the shared `Repository` contract (`get`, `list` with cursor pagination, `insert`, `update` under an expected version, `soft_delete`, `restore`, `purge`) and adds named queries `open_session(session)`, `close_session(session_id, close_code)`, `list_active_sessions(target_type, target_id)`, `force_close(session_id)`, `renew_lease(session_id, expires_at)`, `expire_leases(now)`, `list_presence(target_type, target_id)`, `next_rev(document_id)`, `append_change(document_id, change)`, `list_changes_since(document_id, rev)`, `find_missing_deps(document_id, hashes)`, `find_by_hash(document_id, hash)`, `delete_changes_before_snapshot(document_id, snapshot_rev, cutoff)`; the tenant predicate, soft-delete filter, version check, audit row, and outbox enqueue come from the base contract. The `pg_advisory_xact_lock(hashtext(document_id))` and the `select coalesce(max(rev), 0) + 1 ... for update` that assign `rev` live inside `next_rev`/`append_change` in `crates/persistence`: only the SQL moved, and the same per-document lock taken in the same transaction still serializes concurrent appenders. Appending a change — rev assignment, the `document_changes` row, its `document_change_deps` rows, and the F045 `current_revision` bump through `DocumentRevisionRepository` — runs in one `UnitOfWork` that owns the transaction. Sheet cell patches are applied through F008's cell repository, never through this feature's SQL. Per decision 2.1 the use cases above depend on these repository traits and contain no SQL: no SQL string, `sqlx::query*` call, or connection exists in `crates/domain/src/realtime`, `services/api/src/realtime`, or `services/realtime/src/realtime`.
- Realtime service (`services/realtime/src/realtime/`): Axum WebSocket handlers `ws_document.rs`, `ws_sheet.rs`; `session.rs` per-connection task with outbound queue; `fanout.rs` JetStream publish/subscribe on `realtime.doc.{id}` and `realtime.sheet.{id}`; `lease_sweeper.rs` every 5 seconds calling `PresenceLeaseRepository::expire_leases(now)`; `snapshotter.rs`; `limits.rs` token buckets; `acl_recheck.rs` every 60 seconds. The reconnect path calls `DocumentChangeRepository::{list_changes_since, find_missing_deps}`; no file in this service holds a SQL string, a `sqlx::query*` call, or a connection.
- API endpoints (`services/api/src/realtime/`): `GET /ws/v1/documents/{id}` (WebSocket), `GET /ws/v1/sheets/{id}` (WebSocket), `GET /api/v1/collaboration/sessions`, `DELETE /api/v1/collaboration/sessions/{id}`, `GET /api/v1/documents/{id}/changes?since={rev}`. The two `/ws/v1` routes are served by `services/realtime` behind the gateway; the three HTTP routes by `services/api`. DTOs: `SessionResponse`, `Page<SessionResponse>`, `ChangeResponse { rev, actor_id, change_base64, hash, applied_at }`, `Page<ChangeResponse>`.
- Events: `presence.joined.v1`, `presence.left.v1`, `document.change-applied.v1` (with `rev`, `hash`), `sheet.patch-applied.v1` (with `row_id`, `column_id`, `row_version`).
- Authorization: handshake requires target read; `change` and `patch` require `document-editor` or `sheet-editor`; session list for tenant-admin or self; force-close for tenant-admin or self; explicit deny wins; foreign tenant closes `4404`.
- Validation: message ≤ 256 KB, `seq` strictly increasing, Automerge change decodes and every dependency hash resolves through `DocumentChangeRepository::find_missing_deps(document_id, hashes)`, `since ≥ 0`, `limit` 1–1,000. Idempotency: changes by `(document_id, hash)`, patches by `(session_id, seq)` retained for 10 minutes.
- Error mapping: `RealtimeError::Denied → close 4403`, `RealtimeError::NotFound → close 4404`, `RealtimeError::Unauthenticated → close 4401`, `RealtimeError::RateLimited → error rate_limited then close 4429`, `RealtimeError::MissingDeps → error conflict`, `SheetError::StaleVersion → conflict message`, HTTP routes map `denied`, `not_found`, `conflict`, `invalid` per contracts.

### Interface

This feature is a WebSocket protocol plus three HTTP routes. The protocol is defined message by
message and direction by direction, because an ambiguous frame produces two incompatible clients.
`T?` is nullable; an absent optional field and an explicit `null` mean the same thing. Ids are
UUIDv7 strings, timestamps are RFC 3339 UTC, binary payloads are base64 (standard alphabet, padded).
Unlisted fields in any frame are rejected with an `error` frame of code `invalid` and the socket
stays open. `Page<T>`, the signed cursor and the error body are F028's; `ActorContext` is F038's;
`CellValue` is F007's.

**Envelope** — every frame in both directions is one JSON object with exactly these five keys
(FR-F046-02)

| Field | Type | Required | Constraint |
|---|---|---|---|
| `type` | enum | yes | one of `hello`, `presence`, `change`, `ack`, `replay`, `patch`, `conflict`, `error`, `ping`, `pong`; any other value → `error { code: invalid }` |
| `seq` | integer | yes on client frames | strictly increasing per connection from 1; a repeat or a gap → `error { code: invalid, reason: "seq_out_of_order" }` without closing the socket; server frames carry the `seq` they answer, or `0` for unsolicited broadcasts |
| `rev` | integer? | conditional | the client's last known document `rev` on `change` and `replay`; the assigned `rev` on `ack` and on a broadcast `change`; `null` on every sheet, presence, error and liveness frame |
| `payload` | object | yes | the per-type table below; `{}` where the type carries no fields |
| `correlation_id` | uuid | yes | generated by the sender, echoed by the peer on the frame that answers it |

A frame above 256 KB serialized, or a `seq` that is not strictly increasing, is rejected with
`error` and never applied. Frames are ordered per connection; a client applies document changes by
`rev` and requests `replay` on a gap.

**Client → server frames**

| `type` | `payload` fields | Constraint |
|---|---|---|
| `presence` | `cursor: object?`, `selection: object?` | renews the lease for 30 s; sent every 10 s; the editor-defined cursor object is broadcast verbatim and never interpreted |
| `change` | `change_base64: string`, `deps: string array` | document sockets only; decoded Automerge change ≤ 256 KB; `deps` are lowercase hex hashes; a dependency with no `document_changes(document_id, hash)` row → `error { code: conflict, missing_deps }` (FR-F046-05); a retransmit of a hash already stored returns the original `ack` and writes nothing |
| `patch` | `row_id: uuid`, `column_id: uuid`, `value: CellValue`, `if_match_version: integer` | sheet sockets only; `value` is F007's typed union for that column; a stale `if_match_version` returns `conflict` and applies nothing |
| `replay` | `since: integer` | `since ≥ 0`; older than the oldest retained change → `error { code: conflict, snapshot_rev }` so the client reloads from the F045 revision (FR-F046-09) |
| `ping` | `{}` | answered with `pong` carrying the same `correlation_id` |
| `pong` | `{}` | answer to a server `ping`; a connection silent for two server pings is closed `4400` |

**Server → client frames**

| `type` | `payload` fields | When |
|---|---|---|
| `hello` | `session_id: uuid`, `durable_rev: integer`, `read_only: bool`, `snapshot_rev: integer?`, `presence: PresenceEntry array` | first frame after a successful handshake (FR-F046-01); `durable_rev` is the newest committed `rev`, `snapshot_rev` the newest snapshot or null |
| `presence` | `PresenceEntry` plus `state: "joined" \| "updated" \| "left"` | on another session's join, cursor renewal, or lease expiry; scoped to the same target only (NFR-F046-02) |
| `ack` | `seq: integer`, `rev: integer?`, `row_version: integer?` | after the writing transaction commits, never before; `rev` on a document `change`, `row_version` on a sheet `patch` |
| `change` | `rev: integer`, `actor_id: uuid`, `change_base64: string`, `hash: string` | broadcast of another session's committed change, in `rev` order, and the replay range answering a `replay` frame before any live change resumes |
| `patch` | `row_id: uuid`, `column_id: uuid`, `value: CellValue`, `row_version: integer`, `actor_id: uuid` | broadcast of another session's applied cell patch |
| `conflict` | `row_id: uuid`, `column_id: uuid`, `server_value: CellValue`, `server_version: integer` | a `patch` whose `if_match_version` was stale; nothing was applied and the client shows both values until the user chooses (FR-F046-07, FR-F046-08) |
| `error` | `code: enum`, `reason: string?`, `missing_deps: string array?`, `snapshot_rev: integer?`, `retry_after_seconds: integer?` | `code` is one of the shared six; the socket stays open unless a close frame follows |
| `pong` | `{}` | answer to a client `ping` |
| `ping` | `{}` | liveness probe; the client answers `pong` |

**`PresenceEntry`** — the shape carried by `hello.presence` and every `presence` frame

| Field | Type | Notes |
|---|---|---|
| `session_id` | uuid | |
| `actor_id` | uuid | |
| `cursor` | object? | the sender's editor-defined cursor and selection, broadcast verbatim |
| `expires_at` | timestamp | lease expiry, always within 30 s of the last renewal |

**Close codes** — the only codes this service sends

| Code | Meaning |
|---|---|
| `1000` | orderly close by either peer; no product condition attached |
| `4400` | force-closed by `DELETE /api/v1/collaboration/sessions/{id}`, or an unanswered liveness probe |
| `4401` | no gateway session on the handshake (`RealtimeError::Unauthenticated`) |
| `4403` | the actor may not read the target at handshake, or lost the right at a 60-second ACL recheck and cannot be downgraded to read-only |
| `4404` | unknown target, or a target in another tenant — never `4403`, so ids do not leak |
| `4429` | a third rate-limit violation within one minute, a join beyond 1,000 tenant or 100 per-target sessions, or an outbound queue past 1,000 messages (FR-F046-11) |

**HTTP routes.** `GET /api/v1/collaboration/sessions` returns `Page<SessionResponse>` sorted by
`connected_at` descending with `id` as tiebreak, `limit` 1–200 (default 50), filters `target_type`
(`document` or `sheet`), `target_id`, `actor_id`, and `active` (default `true`); a `tenant-admin`
sees the tenant, any other actor sees only its own sessions, and an `actor_id` filter naming another
user from a non-admin returns an empty page rather than `403 denied`.

**`SessionResponse`**

| Field | Type | Notes |
|---|---|---|
| `id` | uuid | |
| `actor_id` | uuid | |
| `target_type` | `"document" \| "sheet"` | |
| `target_id` | uuid | |
| `read_only` | bool | |
| `node_id` | string | the realtime node holding the socket |
| `connected_at` / `last_seen_at` | timestamp | |
| `closed_at` | timestamp? | present only on a closed session |
| `close_code` | integer? | one of the close codes above; present only when `closed_at` is |

`DELETE /api/v1/collaboration/sessions/{id}` takes `Idempotency-Key`, closes the socket with `4400`
and returns `204`; it is allowed for `tenant-admin` or the session's own actor and returns
`404 not_found` for any other session. `GET /api/v1/documents/{id}/changes?since={rev}` returns
`Page<ChangeResponse>` in ascending `rev` order with `limit` 1–1,000 (default 200) and
`since ≥ 0`; `ChangeResponse` is `{ rev, actor_id, change_base64, hash, deps: string array,
snapshot_rev: integer?, applied_at }` where `deps` is reassembled from `document_change_deps`.

**Status codes** (HTTP routes only; socket failures are `error` frames and close codes)

| Status | `code` | Produced by |
|---|---|---|
| `400` | `invalid` | `since < 0`, `limit` out of range, an unknown `target_type` filter |
| `403` | `denied` | force-closing a session that is neither the caller's nor within a `tenant-admin`'s tenant scope |
| `404` | `not_found` | unknown or foreign-tenant session or document id |
| `409` | `conflict` | `since` older than the oldest retained change; the body carries `snapshot_rev` |
| `429` | `rate_limited` | the F038 limiter for the route; carries `Retry-After` |
| `503` | `unavailable` | JetStream or the change store is unreachable |

### Use case signatures

In `crates/domain/src/realtime/`. Every use case takes `ctx` carrying tenant, actor, session and
correlation id, and a `UnitOfWork` for writes or a repository trait for reads — never a pool or a
connection — and returns the shared `DomainError`, which the socket layer maps to the close codes
and `error` frames above and the HTTP layer to the status table.

```rust
fn open_session(ctx: &Ctx, uow: &mut UnitOfWork, target: Target, node_id: NodeId) -> Result<Hello, DomainError>;
fn close_session(ctx: &Ctx, uow: &mut UnitOfWork, id: SessionId, code: CloseCode) -> Result<(), DomainError>;
fn renew_lease(ctx: &Ctx, uow: &mut UnitOfWork, id: SessionId, cursor: Option<Json>, now: DateTime<Utc>) -> Result<PresenceLease, DomainError>;
fn expire_leases(ctx: &Ctx, uow: &mut UnitOfWork, now: DateTime<Utc>) -> Result<Vec<PresenceLease>, DomainError>;
fn append_change(ctx: &Ctx, uow: &mut UnitOfWork, doc: DocumentId, req: AppendChange) -> Result<DocumentChange, DomainError>;
fn replay_changes(ctx: &Ctx, repo: &dyn DocumentChangeRepository, doc: DocumentId, since: Rev, page: Cursor) -> Result<Page<DocumentChange>, DomainError>;
fn snapshot_document(ctx: &Ctx, uow: &mut UnitOfWork, doc: DocumentId, expected: RevisionNo) -> Result<Rev, DomainError>;
fn apply_sheet_patch(ctx: &Ctx, uow: &mut UnitOfWork, sheet: SheetId, req: SheetPatch) -> Result<PatchOutcome, DomainError>;
fn list_sessions(ctx: &Ctx, repo: &dyn CollaborationSessionRepository, filter: SessionFilter, page: Cursor) -> Result<Page<CollaborationSession>, DomainError>;
fn force_close_session(ctx: &Ctx, uow: &mut UnitOfWork, id: SessionId) -> Result<(), DomainError>;
fn recheck_acl(ctx: &Ctx, repo: &dyn CollaborationSessionRepository, id: SessionId) -> Result<AclOutcome, DomainError>;
```

`PatchOutcome` is `Applied { row_version }` or `Conflict { server_value, server_version }`, so a
stale patch is a value the caller must handle rather than an error that could be logged and dropped.

Transaction boundaries. `append_change` holds one `UnitOfWork` over `next_rev`, the
`document_changes` insert, its `document_change_deps` rows and the F045 `current_revision` bump, all
under the per-document advisory lock — that boundary is what makes `rev` gap-free and dependency
rows never orphaned, and it is why `ack` is sent only after the commit (NFR-F046-04). `open_session`
writes the `collaboration_sessions` row, its `presence_leases` row and the `presence.joined.v1`
outbox entry in one `UnitOfWork`, so a session never exists without a lease. `apply_sheet_patch`
runs inside the F008 cell-update `UnitOfWork` so the version check, the cell write and the
`sheet.patch-applied.v1` enqueue commit together and a conflict rolls back all three.
`snapshot_document` posts the F045 revision first and stamps `snapshot_rev` on the change row in one
`UnitOfWork` afterwards, so a snapshot marker never points at a revision that was not stored.
`expire_leases` runs one `UnitOfWork` per sweeper batch.

### PostgreSQL/SQLx

- Migration `*_realtime_*.sql` creates `collaboration_sessions(id uuid pk, tenant_id uuid not null, actor_id uuid not null, target_type text not null check (target_type in ('document','sheet')), target_id uuid not null, read_only bool not null, node_id text not null, connected_at timestamptz not null, last_seen_at timestamptz not null, closed_at timestamptz null, close_code int null, correlation_id uuid not null)`, `presence_leases(session_id uuid pk references collaboration_sessions(id), tenant_id uuid not null, target_type text not null, target_id uuid not null, actor_id uuid not null, cursor jsonb not null default '{}', expires_at timestamptz not null)`, `document_changes(tenant_id uuid not null, document_id uuid not null, rev bigint not null, actor_id uuid not null, session_id uuid not null, change bytea not null, hash bytea not null, snapshot_rev bigint null, applied_at timestamptz not null, primary key (document_id, rev))`, and `document_change_deps(tenant_id uuid not null, document_id uuid not null, rev bigint not null, dep_hash bytea not null, created_at timestamptz not null default now(), primary key (document_id, rev, dep_hash), foreign key (document_id, rev) references document_changes(document_id, rev) on delete cascade)`.
- `document_changes.deps` is not an array column: the dependency hashes are an enumerable set that the reconnect path resolves against `document_changes.hash`, so they are rows in `document_change_deps`. The Automerge change payload itself is unchanged, and missing-dependency detection on reconnect joins those rows against `document_changes(document_id, hash)` instead of scanning an array. `document_changes.change` and `document_changes.hash` stay `bytea`: they are opaque Automerge binary, not a queried structure, and are never `jsonb`.
- `presence_leases.cursor` stays `jsonb`: the cursor and selection position is a per-client, editor-defined payload broadcast verbatim to other viewers and never filtered, joined or aggregated by the product.
- Invariants: unique `document_changes(document_id, hash)`; `rev` assigned by `select coalesce(max(rev), 0) + 1 ... for update` on a per-document advisory lock `pg_advisory_xact_lock(hashtext(document_id))`; every `document_change_deps` row cascades with its `document_changes` parent and its `(document_id, rev, dep_hash)` primary key makes a dependency listed at most once per change; `presence_leases.expires_at` always within 30 seconds of `last_seen_at`; `document_changes.document_id` references F045 `documents(id)` with `on delete restrict`.
- Indexes: `collaboration_sessions(tenant_id, target_type, target_id) where closed_at is null`, `collaboration_sessions(tenant_id, actor_id) where closed_at is null`, `presence_leases(expires_at)`, `document_changes(document_id, rev desc)`, `document_changes(document_id, snapshot_rev) where snapshot_rev is not null`, `document_change_deps(document_id, dep_hash)` so "which change depends on this hash" is an index lookup rather than an array scan.
- Audit events: `collaboration-session.open`, `collaboration-session.close`, `collaboration-session.force-close`, `document.snapshot` with session and target IDs; individual changes and patches are not audited (the F045 revision and F008 row update carry the audit).
- Retention/deletion: closed sessions and expired leases older than 7 days are deleted by the sweeper; `document_changes` older than the latest snapshot plus 30 days are deleted by the F027 job through `DocumentChangeRepository::delete_changes_before_snapshot(document_id, snapshot_rev, cutoff)` once the snapshot revision exists, taking their `document_change_deps` rows with them by cascade; rollback drops the four tables `document_change_deps`, `document_changes`, `presence_leases`, and `collaboration_sessions`.

### React/TypeScript

- Module `apps/web/src/features/realtime/`: components `PresenceAvatars`, `RemoteCursorLayer`, `ConnectionStatusBadge`, `ConflictBanner`, `SessionPanel`; hooks `useCollaborationSession(target)`, `usePresence(target)`, `useDocumentSync(documentId)` (Automerge in the browser via the `@automerge/automerge` package), `useSheetPatches(sheetId)`; integration props exported for `apps/web/src/features/documents/DocumentEditor.tsx` and the F006/F008 grid.
- State: socket state in a per-target store; TanStack Query keys `['collab-sessions', workspaceId]`, `['document-changes', documentId, since]`; outbound queue persisted in memory only.
- API client: generated `RealtimeApi` with `listSessions`, `closeSession`, `listDocumentChanges`; socket client `RealtimeSocket` with `connect`, `send`, `onMessage`, reconnect with exponential backoff `1 s, 2 s, 4 s, 8 s, max 30 s`.
- Optimistic updates: local Automerge changes apply immediately; sheet patches apply locally and roll back on `conflict` with the banner.
- Telemetry: `collab_session_opened`, `collab_reconnected`, `change_applied`, `patch_conflict_shown`, `patch_conflict_resolved`, `presence_lease_expired` with `target_type`, `session_id`, `latency_ms`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F046-01 through FR-F046-14 in `testing/features/F046/requirements/cases.md`
- [ ] Failure/edge-case tests: out-of-order seq, retransmitted change, missing deps, lease expiry, replay older than retention, stale patch, rate-limit close, 101st document session, revoked editor mid-session
- [ ] Permission-negative and tenant-isolation tests: viewer `change` rejected, foreign tenant closes `4404`, cursor not leaked across targets
- [ ] Rust unit tests: `crates/domain/src/realtime/` envelope parsing, rev assignment, lease expiry math, backoff schedule
- [ ] API contract/integration tests: every route above with success and each close code or error
- [ ] Database migration/constraint tests: change hash uniqueness, rev primary key, `document_change_deps` composite key and cascade from `document_changes`, lease reference, rollback of all four tables
- [ ] React component tests: `PresenceAvatars`, `ConnectionStatusBadge`, `ConflictBanner`, `useDocumentSync`
- [ ] Browser E2E tests: two-browser co-editing convergence, reconnect replay, sheet conflict resolution, read-only viewer
- [ ] Accessibility tests: axe with presence and banner, live region announcements, keyboard conflict resolution
- [ ] Performance/load tests: 50-editor round trip, 1,000 sessions per node, replay 1,000 changes

### Fast fanout configuration

- Test harness path: `testing/features/F046/`
- Feature flag: `F046_FEATURE`
- Fixture/seed factory: `testing/fixtures/realtime.rs` builds tenant, workspace, one document with a 20-change history, its `document_change_deps` rows, and a snapshot at rev 10, one sheet with 50 rows, two editors, one viewer, tenant-admin, foreign tenant
- Deterministic test data: fixed UUIDv7 seeds, controllable clock `2026-09-03T00:00:00Z` with `advance()`, fixed Automerge actor IDs
- Mock/stub contracts: embedded NATS JetStream per worker; two in-process realtime nodes for fan-out tests; F045 revision route real; F008 row update real; WebSocket test client in `testing/harness/ws.rs`
- Parallel isolation: one schema and JetStream subject prefix per test worker, tenant ID per test
- Targeted command: `cargo xtask test-feature F046`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F046/`

## 6. Acceptance criteria

```gherkin
Feature: Live collaboration

Scenario: Two editors converge on a document
  Given editors Ana and Ben connected to document "Launch brief"
  When Ana inserts "Goals" at the top and Ben appends "Risks" at the bottom within the same second
  Then both receive acks with consecutive revs and both documents render the same text
  And document.change-applied.v1 is published twice

Scenario: Reconnect replays missed changes
  Given Ben disconnected at rev 12 while Ana made changes to rev 20
  When Ben reconnects and sends replay since 12
  Then Ben receives revs 13 to 20 in order before any live change
  And his queued offline changes are acked with revs 21 and 22

Scenario: Stale sheet patch shows a conflict
  Given Ana and Ben both see cell Status at row version 3
  When Ana patches it to "Done" and Ben patches it to "Blocked" with if_match_version 3
  Then Ben receives conflict with server_value "Done" and server_version 4 and nothing is overwritten

Scenario: Viewer cannot send changes
  Given a viewer connected read-only to "Launch brief"
  When the viewer sends a change message
  Then the server replies error denied and the change is not stored

Scenario: Presence lease expires
  Given Ana connected with a lease renewed every 10 seconds
  When her client stops renewing and 30 seconds pass
  Then presence.left.v1 is published and Ben's presence list no longer shows Ana
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F045 (documents, revisions route, editor integration point), F004 (JetStream, worker baseline, metrics); decisions sections 2–5, 7; contracts row F046
- Blocks: none
- Conflicts with: none (disjoint owned paths)
- External dependencies: `@automerge/automerge` in the browser and the `automerge` Rust crate for server-side materialization; NATS JetStream
- Risks and mitigations: rev assignment under concurrent writers could collide, so `DocumentChangeRepository::append_change` takes the per-document advisory lock inside the `UnitOfWork` transaction; change log growth is bounded by snapshots every 500 changes and F027 pruning; a slow client could exhaust node memory, so outbound queues are capped at 1,000 messages and the socket is closed with `4429` beyond that; multi-node fan-out could reorder, so clients apply by `rev` and request replay on gaps.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F045 and F004 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F046/`
- [ ] Migration file name and owned paths claimed
- [ ] WebSocket test client and two-node harness available in `testing/harness/`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for sessions, changes, patches, and presence
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F046_FEATURE` (editors fall back to F045 revision saves), run down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Documents and sheets now support live co-editing with presence, cursors, ordered changes, reconnect replay, and visible conflicts that are never overwritten silently.
- Migration adds `collaboration_sessions`, `presence_leases`, `document_changes`, and `document_change_deps`; rollback drops them. Feature is off by default behind `F046_FEATURE`.
