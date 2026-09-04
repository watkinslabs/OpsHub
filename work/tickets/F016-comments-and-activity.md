---
id: F016
type: feature
status: planned
priority: P1
owner: platform
estimate: 5
target_milestone: M3
parent_epic: E004
depends_on: [F006, F003]
blocks: []
conflicts_with: []
parallel_safe: true
owned_paths: [crates/domain/src/comments/**, crates/persistence/src/comments/**, services/api/src/comments/**, apps/web/src/features/comments/**, services/api/migrations/*_comments_*.sql, testing/features/F016/**]
feature_flag: F016_FEATURE
flag_default: off
branch: f016-comments-and-activity
started_at: null
finished_at: null
---

# F016 — Comments and activity

## 1. Identity and dates

- Branch: `f016-comments-and-activity`
- Capability area: collaboration (spec 5.4b COLLAB-01, COLLAB-02; 5.5 notification categories; section 4 Comment/Mention entity)
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 4; `docs/capability-contracts.md` row F016
- Aggregate: `comment`
- Module slug: `comments`

## 2. Requirement specification

### Problem and user outcome

Teams discuss work in chat tools and email, so the reasoning behind a row's status is lost and nobody can tell who changed what. They need conversations attached to the record itself, the ability to pull a colleague in by name, a way to mark a discussion as settled, and one chronological history of human and automated changes.

As a sheet collaborator, I want to comment on a row, mention a teammate, resolve the thread when it is settled, and read the row's activity, so that decisions and changes stay attached to the work item they concern.

### Functional requirements

- **FR-F016-01:** An actor with `resource-commenter` or higher on the target can `POST /api/v1/comments` with `{ target_kind, target_id, body, thread_id?, parent_comment_id? }` where `target_kind` is one of `sheet`, `row`, `cell`, `file`, `report`, `dashboard`; the response returns the comment with UUIDv7 `id`, `thread_id`, `version` 1, and `created_at`.
- **FR-F016-02:** Omitting `thread_id` creates a new `comment_threads` row for the target in the same transaction; supplying a `thread_id` whose target differs from the request target returns `400 invalid` with `field_errors.thread_id = "target_mismatch"`.
- **FR-F016-03:** `body` is Markdown limited to 10,000 UTF-8 characters and at most 50 mention tokens of the form `@[user:<uuid>]` or `@[group:<uuid>]`; a body over the limit returns `400 invalid` with `field_errors.body = "too_long"`.
- **FR-F016-04:** Each mention token that resolves to an active user or group of the tenant with read access to the target creates a `mentions` row and publishes `mention.created.v1` with `{ comment_id, mentioned_kind, mentioned_id }`; tokens for users without target access are stored as plain text, are not published, and the response lists them under `unresolved_mentions`.
- **FR-F016-05:** `GET /api/v1/{target_kind}/{target_id}/comments` returns threads with nested comments in `created_at` order, cursor paged with `limit` 1–100 threads, filterable by `resolved=true|false`, and includes `resolved_at`, `resolved_by`, and per-comment `edited_at`.
- **FR-F016-06:** `PATCH /api/v1/comments/{id}` updates `body` only by the author within 24 hours of `created_at` or by a `resource-admin` at any time; it requires `If-Match`, sets `edited_at`, re-parses mentions (publishing `mention.created.v1` only for newly added mentions), and publishes `comment.updated.v1`.
- **FR-F016-07:** `DELETE /api/v1/comments/{id}` soft-deletes by the author or a `resource-admin`; a deleted comment keeps its position in the thread as a `[deleted]` placeholder when it has replies and is hidden when it has none; the call publishes `comment.deleted.v1`.
- **FR-F016-08:** `POST /api/v1/comments/{id}/resolve` with `{ resolved: true|false }` sets or clears `resolved_at` and `resolved_by` on the comment's thread, requires `resource-commenter`, publishes `comment.resolved.v1`, and returns `409 conflict` with code `conflict` when the requested state already holds.
- **FR-F016-09:** `GET /api/v1/{target_kind}/{target_id}/activity` returns `activity_entries` newest first, cursor paged with `limit` 1–200, filterable by `actor_kind=user|automation|integration`, `action` prefix, `since`/`until` timestamps, and `changed_field=<name>` (matched against `activity_entry_changed_fields`), each entry carrying `actor_id`, `actor_kind`, `action`, `changed_fields`, `summary`, `correlation_id`, and `occurred_at`; the `changed_fields` array in the response is assembled from the entry's `activity_entry_changed_fields` rows, so the API shape is unchanged.
- **FR-F016-10:** A worker subscription in the API process projects `row.*.v1`, `cell.updated.v1`, `comment.*.v1`, `file.uploaded.v1`, and `workflow-run.completed.v1` events into `activity_entries` and their `activity_entry_changed_fields` rows idempotently by `(tenant_id, source_event_id)` through `ActivityEntryRepository::insert_activity_if_absent`, so a replayed event never creates a second entry or a duplicate changed-field row.
- **FR-F016-11:** Every comment mutation writes an `audit_events` row with actor, action, diff, and correlation ID and publishes the matching `comment.*.v1` event through the outbox in the same transaction.
- **FR-F016-12:** Reads and mutations on a target the actor cannot read return `404 not_found`; a `viewer` attempting any mutation returns `403 denied`; cross-tenant IDs return `404 not_found` on every route.
- **FR-F016-13:** The web app renders a `ConversationPanel` on the row detail drawer and sheet header with thread list, reply composer with `@` mention autocomplete (users and groups the actor can see, max 20 suggestions), resolve toggle, edit and delete menus, and an `ActivityTab` whose filter chips cover actor kind, action, date range, and a changed-field chip backed by the `changed_field` query parameter.
- **FR-F016-14:** Deleting a target (row, sheet, file) cascades a soft delete to its threads; restoring the target restores them; the activity feed of a restored target shows the delete and restore entries.

### Non-functional requirements

- **NFR-F016-01 Performance:** listing 100 threads with 1,000 comments on a row responds under 500 ms p95; comment create responds under 800 ms p95; activity projection lag from outbox publish to entry visible is under 2 s p95 (spec section 6).
- **NFR-F016-02 Security/privacy:** mention resolution never reveals users outside the actor's tenant or without target access; comment bodies are stored as submitted Markdown and rendered with a sanitizer that strips scripts, iframes, and remote images; every query carries a `tenant_id` predicate.
- **NFR-F016-03 Accessibility:** the conversation panel and activity tab pass axe with zero serious violations; the mention autocomplete is a WAI-ARIA combobox operable by keyboard; new replies are announced through a polite live region.
- **NFR-F016-04 Reliability/observability:** activity projection is an idempotent JetStream consumer with bounded retry and dead-letter after 5 attempts; metrics `comments_created_total`, `activity_projection_lag_seconds`, and `mentions_unresolved_total` are exported; spans carry `tenant_id`, `target_kind`, `target_id`, and `correlation_id`.

### Scope

Included: threads and comments on the six target kinds, mentions to users and groups, edit and delete policy, resolution, activity projection and query, conversation panel, activity tab, audit and outbox events, `mention.created.v1` as the input contract for F037.

Excluded: notification delivery for mentions (F037 consumes `mention.created.v1`), file attachments inside comments beyond referencing an F017 file ID, approvals and review requests (F020), document body comments (F045), realtime comment push (F046), full-text search of comments (F010 indexes `comment.created.v1`).

## 3. UX specification

- Entry points: row detail drawer tab `Conversation` at `/w/{workspace_id}/sheets/{sheet_id}?row={row_id}&tab=conversation`; sheet header icon `MessageSquare` opening sheet-level threads; `Activity` tab on the same drawer; report and dashboard pages reuse `ConversationPanel` with their target kind.
- Primary flow: open a row, type a comment, type `@` and pick `Dana Ruiz` from the combobox, submit; the thread appears with the mention rendered as a chip; Dana replies; the original author clicks `Resolve`; the thread collapses into the `Resolved` group and the activity tab shows `comment.created`, `comment.created`, `comment.resolved` entries.
- Loading: skeleton of three thread cards; Empty: `No comments yet. Start the conversation.`; Error: inline banner with `correlation_id` and `Retry`; Success: reply appears in place and composer clears; Stale/conflict: edit with stale version shows `This comment changed` with `Reload`; Offline: composer disabled with offline badge and drafts kept in local state.
- Permission-denied: viewers see threads read-only with the composer replaced by `You can view but not comment`; users without target access see the not-found page; edit and delete menu items are hidden when the 24-hour author window has passed and the actor is not an admin.
- Responsive: the drawer becomes a full-screen sheet under 768 px; the actor-kind, action, date, and changed-field chips scroll horizontally.
- Keyboard: `Ctrl+Enter` submits, `Escape` closes the combobox then the drawer, arrow keys move through suggestions, `R` on a focused thread toggles resolve; focus returns to the composer after submit; motion respects `prefers-reduced-motion`.
- Font/icon/design tokens: Plus Jakarta Sans with JetBrains Mono for numerics (F062); Lucide `MessageSquare`, `AtSign`, `CheckCircle2`, `History`, `Pencil`, `Trash2`; spacing and colors from `apps/web/src/design/tokens.css`.

- Design: `design/artboards/Comments.dc.html` on the canvas indexed by `design/canvas.json`. The ticket is the contract and the artboard is the picture; when they disagree the ticket wins.

## 4. Technical specification

### Rust backend

- Domain entities in `crates/domain/src/comments/`: `CommentThread { id, tenant_id, target: TargetRef { kind: TargetKind, id }, resolved_at, resolved_by, version, audit fields, deleted_at }`, `Comment { id, tenant_id, thread_id, parent_comment_id, author_id, body: Markdown, edited_at, version, audit fields, deleted_at }`, `Mention { id, tenant_id, comment_id, mentioned: PrincipalRef { kind: User|Group, id } }`, `ActivityEntry { id, tenant_id, target: TargetRef, actor_id, actor_kind: ActorKind, action, changed_fields: Vec<ChangedField>, summary, source_event_id, correlation_id, occurred_at }` where `ChangedField { entry_id, field_name }` maps one `activity_entry_changed_fields` row.
- Use cases: `create_comment`, `update_comment`, `delete_comment`, `set_thread_resolution`, `list_threads`, `parse_mentions`, `resolve_mentions`, `project_activity`, `list_activity`.
- Persistence (`crates/persistence/src/comments/`): `CommentThreadRepository` owns `comment_threads`; `CommentRepository` owns `comments` and `mentions`; `ActivityEntryRepository` owns `activity_entries` and `activity_entry_changed_fields`. Each implements the shared `Repository` contract (`get`, `list` with cursor pagination, `insert`, `update` under an expected version, `soft_delete`, `restore`, `purge`) and adds named queries `find_or_create_thread(target_kind, target_id)`, `page_threads(target_kind, target_id, resolved, cursor)`, `page_comments(thread_id, cursor)`, `list_mentions_for_comment(comment_id)`, `page_activity(target_kind, target_id, cursor)`, `page_activity_by_actor(actor_id, cursor)`, `insert_activity_if_absent(source_event_id, entry)`; the tenant predicate, soft-delete filter, version check, audit row, and outbox enqueue come from the base contract. Multi-table writes — creating a comment with its `mentions` rows, and resolving a thread — run in one `UnitOfWork` that owns the transaction. The activity projector consuming `row.updated.v1`, `sheet.deleted.v1`, `file.deleted.v1` and the mention notification path call these repositories; the consumer holds no SQL and gets its idempotency from `insert_activity_if_absent` on `(tenant_id, source_event_id)`, which writes the entry and its `activity_entry_changed_fields` rows in one insert transaction. The service-layer cascade on target soft delete goes through `CommentThreadRepository::soft_delete`, not inline SQL. Per decision 2.1 the use cases above depend on these repository traits and contain no SQL: no SQL string, `sqlx::query*` call, or connection exists in `crates/domain/src/comments` or `services/api/src/comments`.
- API endpoints (`services/api/src/comments/`): `GET /api/v1/{target_kind}/{target_id}/comments`, `POST /api/v1/comments`, `PATCH /api/v1/comments/{id}`, `DELETE /api/v1/comments/{id}`, `POST /api/v1/comments/{id}/resolve`, `GET /api/v1/{target_kind}/{target_id}/activity`. DTOs `CreateCommentRequest`, `UpdateCommentRequest`, `ResolveRequest`, `CommentResponse { id, thread_id, parent_comment_id, author, body, mentions, unresolved_mentions, edited_at, deleted, version, created_at }`, `ThreadResponse { id, target, resolved_at, resolved_by, comments: Vec<CommentResponse>, version }`, `Page<ThreadResponse>`, `ActivityEntryResponse`, `Page<ActivityEntryResponse>`.
- Events: `comment.created.v1`, `comment.updated.v1`, `comment.deleted.v1`, `comment.resolved.v1`, `mention.created.v1`; payloads carry `target_kind`, `target_id`, `thread_id`, `changed_fields`, and for mentions `mentioned_kind`, `mentioned_id`, `comment_id`.
- Authorization: `resource-commenter` on the target for create, resolve, and own-edit; `resource-admin` for edit or delete of others' comments; reads require target read; `TargetAccess::check(actor, target)` maps to the F003 ACL of the row's sheet, the file's target, or the report/dashboard itself; unreadable targets map to `not_found`.
- Validation: `body` 1–10,000 chars, ≤ 50 mention tokens, `limit` bounds per route, `target_kind` enum; idempotency via `idempotency_keys` for 24 hours; `If-Match` compared inside the update transaction.
- Error mapping: `CommentError::BodyTooLong → 400 invalid`, `CommentError::ThreadTargetMismatch → 400 invalid`, `CommentError::EditWindowClosed → 403 denied`, `CommentError::AlreadyInState → 409 conflict`, `CommentError::StaleVersion → 409 conflict`, `CommentError::NotFound → 404 not_found`, `AuthzError::Denied → 403 denied`.

### Interface

Exact shapes. Every field gives its JSON name, type, whether it is required, and the constraint that
makes it invalid. `T?` is nullable; an absent optional field and an explicit `null` mean the same
thing. Ids are UUIDv7 strings, timestamps are RFC 3339 UTC, and `version` increments by one per
write. Unlisted fields are rejected with `400 invalid`. `Page<T>` and the opaque cursor are F028's
`{ items, next_cursor, has_more, total? }`; the error codes are the shared six. Every mutation
requires `Idempotency-Key`, and `PATCH`, `DELETE` and `resolve` require `If-Match`.

**`TargetRef`** `{ kind: "sheet" | "row" | "cell" | "file" | "report" | "dashboard", id: uuid }` —
the pair addressed by the two path segments of the list routes and carried in every response. Access
is the target's own ACL: a target the actor cannot read is `404 not_found` on every route, so a
comment count never confirms that a record exists.

**`CreateCommentRequest`** — `POST /api/v1/comments`

| Field | Type | Required | Constraint |
|---|---|---|---|
| `target_kind` | TargetKind | yes | one of the six; any other member → `400 invalid` |
| `target_id` | uuid | yes | a live record of that kind the actor may read, with `resource-commenter` or higher, else `403 denied` when readable and `404 not_found` when not |
| `body` | string | yes | Markdown, 1–10,000 UTF-8 characters; longer → `400 invalid` with `field_errors.body = "too_long"`; at most 50 mention tokens, more → `field_errors.body = "too_many_mentions"` |
| `thread_id` | uuid? | no | omitted creates a `comment_threads` row in the same transaction; a thread whose target differs from the request → `400 invalid` with `field_errors.thread_id = "target_mismatch"` |
| `parent_comment_id` | uuid? | no | a live comment of `thread_id`; a comment of another thread → `400 invalid` with `field_errors.parent_comment_id = "thread_mismatch"` |

**`UpdateCommentRequest`** — `PATCH /api/v1/comments/{id}`: `{ body }` only, under the same body
constraints. The author may edit within 24 hours of `created_at`, a `resource-admin` at any time;
outside that window a non-admin gets `403 denied` with code `denied`. The edit sets `edited_at` and
re-parses mentions, publishing `mention.created.v1` only for tokens the previous body did not carry.

**`ResolveRequest`** — `POST /api/v1/comments/{id}/resolve`: `{ resolved: bool }`, required. It sets
or clears `resolved_at` and `resolved_by` on the comment's **thread**, not on the comment, so two
comments of one thread can never disagree. Requesting the state the thread already holds is
`409 conflict`.

#### Mentions

A mention lives in the body as the literal token `@[user:<uuid>]` or `@[group:<uuid>]`; the body is
stored exactly as submitted and the tokens are never rewritten, so an edit round-trips. Each token is
resolved once at write time against the tenant and the target ACL.

| Field | Type | Notes |
|---|---|---|
| `kind` | `"user" \| "group"` | from the token |
| `id` | uuid | the mentioned principal |
| `display_name` | string | resolved at read time for rendering the chip |

`CommentResponse.mentions` holds the tokens that resolved: an active user or group of this tenant
with read access to the target. Each is one `mentions` row and one `mention.created.v1`.
`CommentResponse.unresolved_mentions` holds the rest as `{ kind, id }` with **no** `display_name`,
because naming a principal the actor cannot see would leak it; those tokens stay plain text in the
body, write no row and publish no event (FR-F016-04).

**`CommentResponse`**

| Field | Type | Notes |
|---|---|---|
| `id` / `thread_id` | uuid | |
| `parent_comment_id` | uuid? | `null` at the top of a thread |
| `author` | PrincipalSummary? | `{ id, display_name }`; `null` on a deleted comment |
| `body` | string? | the submitted Markdown, sanitized at render time, never at rest; `null` on a deleted comment |
| `mentions` | Mention[] | `[]` on a deleted comment |
| `unresolved_mentions` | `{ kind, id }[]` | present on create and update responses and on reads by the author |
| `deleted` | bool | `true` for a soft-deleted comment that is still returned |
| `edited_at` | timestamp? | present only after an edit |
| `created_at` | timestamp | |
| `version` | integer | pass as `If-Match` on the next write |

**A deleted comment.** Soft delete keeps the row. When the comment has at least one live reply it is
still returned in thread order with `deleted: true`, `body: null`, `author: null` and
`mentions: []`, keeping `id`, `thread_id`, `parent_comment_id` and `created_at` so its replies keep
their parent and their position; the client renders the removed-comment placeholder from the
`deleted` flag rather than from server-sent text. When it has no live replies it is omitted from the
thread entirely and `GET` by its id is `404 not_found` (FR-F016-07). Deleting a comment never
deletes its replies.

**`ThreadResponse`**

| Field | Type | Notes |
|---|---|---|
| `id` | uuid | |
| `target` | TargetRef | |
| `resolved_at` | timestamp? | `null` while open |
| `resolved_by` | PrincipalSummary? | present exactly when `resolved_at` is |
| `comments` | CommentResponse[] | ascending by `created_at`, replies following their parent |
| `version` | integer | |

`GET /api/v1/{target_kind}/{target_id}/comments` returns `Page<ThreadResponse>` sorted by the
thread's `created_at` ascending. Query parameters: `cursor` (opaque), `limit` (1–100 threads, default
25), `resolved` (bool; omitted returns both).

**`ActivityEntryResponse`**

| Field | Type | Notes |
|---|---|---|
| `id` | uuid | |
| `target` | TargetRef | |
| `actor_id` | uuid? | `null` for a system actor with no principal |
| `actor_kind` | `"user" \| "automation" \| "integration"` | |
| `action` | string | the source event name, `row.updated` or `comment.created` |
| `changed_fields` | string[] | assembled from the entry's `activity_entry_changed_fields` rows, each field named at most once; `[]` when the action changed no field |
| `summary` | string | a rendered one-line description |
| `source_event_id` | uuid | the event this entry was projected from; unique per tenant, which is what makes a redelivery a no-op |
| `correlation_id` | uuid | |
| `occurred_at` | timestamp | |

`GET /api/v1/{target_kind}/{target_id}/activity` returns `Page<ActivityEntryResponse>` sorted by
`occurred_at` descending. Query parameters: `cursor`, `limit` (1–200, default 50), `actor_kind`
(enum), `action` (string, matched as a prefix, ≤ 64 chars), `since` and `until` (timestamps, `until`
not before `since`), `changed_field` (string matched against `activity_entry_changed_fields`).
Activity is append-only: there is no route that writes it, and the entries of a soft-deleted target
stay readable so the delete and the restore are both visible (FR-F016-14).

**Status codes**

| Code | Produced by |
|---|---|
| `200` | comment list, activity list, `PATCH`, resolve |
| `201` | comment created |
| `204` | comment deleted |
| `400 invalid` | `too_long`, `too_many_mentions`, `target_mismatch`, `thread_mismatch`, an unknown `target_kind`, a `limit` outside its route bounds, `until` before `since`, an unlisted field |
| `403 denied` | a viewer creating, editing or resolving; an author editing after the 24-hour window; a non-admin editing or deleting another principal's comment |
| `404 not_found` | a target, thread or comment the actor cannot read, one that is soft-deleted with no live replies, and every foreign-tenant id — never `denied`, so ids do not leak |
| `409 conflict` | resolving to the state the thread already holds, stale `If-Match` (body carries the current `version`), `Idempotency-Key` replayed with a different body |
| `429 rate_limited` | tenant write quota on comment creation |
| `502 unavailable` | outbox publish failed; the mutation is rolled back |

### Use case signatures

In `crates/domain/src/comments/`. Each takes `ctx` carrying tenant, actor and correlation id, takes a
`UnitOfWork` to write or a repository to read, never a pool or a connection, and returns the shared
`DomainError`.

```rust
fn create_comment(ctx: &Ctx, uow: &mut UnitOfWork, req: CreateComment) -> Result<Comment, DomainError>;
fn update_comment(ctx: &Ctx, uow: &mut UnitOfWork, id: CommentId, expected: Version, body: Markdown) -> Result<Comment, DomainError>;
fn delete_comment(ctx: &Ctx, uow: &mut UnitOfWork, id: CommentId, expected: Version) -> Result<(), DomainError>;
fn set_thread_resolution(ctx: &Ctx, uow: &mut UnitOfWork, id: CommentId, expected: Version, resolved: bool) -> Result<CommentThread, DomainError>;
fn list_threads(ctx: &Ctx, repo: &dyn CommentThreadRepository, target: TargetRef, filter: ThreadFilter, page: Cursor) -> Result<Page<CommentThread>, DomainError>;
fn parse_mentions(body: &Markdown) -> Vec<MentionToken>;
fn resolve_mentions(ctx: &Ctx, repo: &dyn PrincipalReader, target: TargetRef, tokens: &[MentionToken]) -> Result<ResolvedMentions, DomainError>;
fn project_activity(ctx: &Ctx, uow: &mut UnitOfWork, event: &DomainEvent) -> Result<Projected, DomainError>;
fn list_activity(ctx: &Ctx, repo: &dyn ActivityEntryRepository, target: TargetRef, filter: ActivityFilter, page: Cursor) -> Result<Page<ActivityEntry>, DomainError>;
```

`parse_mentions` is pure, so the same tokenizer runs in the create path, the edit diff and the tests.
`resolve_mentions` batches every token into one `authz::check_many` call capped at 50.

**Transaction boundaries.** One `UnitOfWork` per mutation. `create_comment` writes the
`comment_threads` row when the thread is new, the `comments` row, every resolved `mentions` row, the
`audit_events` row and both outbox enqueues in one boundary — a comment can never exist without its
thread, and a `mention.created.v1` can never reach F037 for a comment that was rolled back.
`update_comment` writes the new body, the added `mentions` rows and the removed ones inside the
version check, so the stored mention set always matches the stored body. `set_thread_resolution`
compares `If-Match` against the thread inside its own transaction, which is what makes the
already-in-state case a `409` rather than a silent second write. `project_activity` writes one
`activity_entries` row and all of its `activity_entry_changed_fields` rows in the single insert
transaction of `insert_activity_if_absent`, keyed on `(tenant_id, source_event_id)`; the unique index
is the idempotency, so a redelivered event adds neither a duplicate entry nor an orphan changed-field
row. The cascade from a target's soft delete runs in the consumer's own `UnitOfWork` through
`CommentThreadRepository::soft_delete`, never inside the target feature's transaction.

### PostgreSQL/SQLx

- Migration `*_comments_*.sql` creates `comment_threads(id uuid pk, tenant_id uuid not null, target_kind text not null, target_id uuid not null, resolved_at timestamptz, resolved_by uuid, version bigint not null default 1, created_by, created_at, updated_by, updated_at, deleted_at)`, `comments(id uuid pk, tenant_id, thread_id uuid not null references comment_threads(id) on delete restrict, parent_comment_id uuid null references comments(id), author_id uuid not null, body text not null, edited_at timestamptz, version, audit fields, deleted_at)`, `mentions(id uuid pk, tenant_id, comment_id uuid not null references comments(id) on delete cascade, mentioned_kind text not null check (mentioned_kind in ('user','group')), mentioned_id uuid not null, created_at)`, `activity_entries(id uuid pk, tenant_id, target_kind, target_id, actor_id uuid, actor_kind text not null check (actor_kind in ('user','automation','integration')), action text not null, summary text not null, source_event_id uuid not null, correlation_id uuid not null, occurred_at timestamptz not null)`, and `activity_entry_changed_fields(entry_id uuid not null references activity_entries(id) on delete cascade, tenant_id uuid not null, field_name text not null, created_at timestamptz not null default now(), primary key (entry_id, field_name))` holding one row per changed field instead of an array column. No `jsonb` column exists in this feature: diffs live in the F003 `audit_events` payload, and every value this feature filters, sorts, or constrains on is a typed column or a child-table row.
- Invariants: `check (target_kind in ('sheet','row','cell','file','report','dashboard'))` on threads and entries; `check (char_length(body) <= 10000)`; unique `mentions(comment_id, mentioned_kind, mentioned_id)`; unique `activity_entries(tenant_id, source_event_id)` for projection idempotency; `activity_entry_changed_fields` primary key `(entry_id, field_name)` replaces the array's implicit distinctness, so a field is named at most once per entry; a comment's `parent_comment_id` must belong to the same thread, enforced by trigger `comments_parent_same_thread`.
- Indexes: `comment_threads(tenant_id, target_kind, target_id, resolved_at, created_at) where deleted_at is null`, `comments(thread_id, created_at) where deleted_at is null`, `mentions(tenant_id, mentioned_id)`, `activity_entries(tenant_id, target_kind, target_id, occurred_at desc)`, `activity_entries(tenant_id, actor_id, occurred_at desc)`, `activity_entry_changed_fields(tenant_id, field_name)` so the activity feed can filter to changes touching one field.
- Audit events: `comment.create`, `comment.update`, `comment.delete`, `thread.resolve`, `thread.unresolve` with field diffs.
- Retention/deletion: soft delete on threads and comments; cascade from target soft delete runs in the service layer listening to `row.deleted.v1`, `sheet.deleted.v1`, `file.deleted.v1` and calling `CommentThreadRepository::soft_delete`; activity entries are append-only and that guarantee now covers `activity_entry_changed_fields`, whose rows are written in the same insert transaction as their entry and are never updated; both are purged only by the F027 retention job, which relies on the `on delete cascade`; migration rollback drops the five tables `activity_entry_changed_fields`, `activity_entries`, `mentions`, `comments`, `comment_threads` in that order.

### React/TypeScript

- Routes: none new; components in `apps/web/src/features/comments/`: `ConversationPanel`, `ThreadCard`, `CommentItem`, `ReplyComposer`, `MentionCombobox`, `ResolveToggle`, `ActivityTab`, `ActivityEntryRow`, `ActivityFilters`.
- State: TanStack Query keys `['comments', targetKind, targetId, { resolved, cursor }]`, `['activity', targetKind, targetId, filters, cursor]`, `['mention-suggestions', targetKind, targetId, query]`; mutations invalidate the thread list and append optimistically.
- API client: generated `CommentsApi` with `listComments`, `createComment`, `updateComment`, `deleteComment`, `resolveComment`, `listActivity`.
- Optimistic updates: reply appears immediately with a pending marker and rolls back on `invalid` or `denied`; resolve toggles locally and rolls back on `conflict`.
- Telemetry: `comment_created`, `comment_resolved`, `mention_added`, `activity_filtered`, `conversation_opened` with `target_kind`.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F016-01 through FR-F016-14 in `testing/features/F016/requirements/cases.md`
- [ ] Failure/edge-case tests: body over 10,000 chars, thread target mismatch, edit after 24 hours, resolve twice, replayed activity event leaving one entry and one set of `activity_entry_changed_fields` rows, mention of a user without access
- [ ] Permission-negative and tenant-isolation tests: viewer create returns `denied`, cross-tenant thread returns `not_found`, mention suggestions exclude foreign tenant users
- [ ] Rust unit tests: `crates/domain/src/comments/` mention parser, edit window, sanitizer contract
- [ ] Repository tests: `crates/persistence/src/comments/` named queries, `insert_activity_if_absent` idempotency, changed-field row assembly into the `changed_fields` response array, `UnitOfWork` rollback of comment plus mentions
- [ ] API contract/integration tests: every route above with success and each error code
- [ ] Database migration/constraint tests: parent-thread trigger, unique mention, unique source event, `activity_entry_changed_fields` primary key and cascade delete, indexes, rollback dropping five tables
- [ ] React component tests: `ConversationPanel`, `MentionCombobox`, `ActivityTab` states
- [ ] Browser E2E tests: comment, mention, resolve, activity visible, viewer read-only
- [ ] Accessibility tests: axe on panel and tab, combobox keyboard, live region
- [ ] Performance/load tests: 1,000-comment thread list p95, projection lag

### Fast fanout configuration

- Test harness path: `testing/features/F016/`
- Feature flag: `F016_FEATURE`
- Fixture/seed factory: `testing/fixtures/comments.rs` builds tenant, sheet with 20 rows, commenter, viewer, admin, foreign tenant, and a seeded row with 5 threads and 40 comments
- Deterministic test data: fixed UUIDv7 seeds, fixed clock `2026-09-03T00:00:00Z`, UTC
- Mock/stub contracts: outbox recorder in memory; activity projector fed from a recorded event list; authz uses the real F003 engine with fixture bindings
- Parallel isolation: one schema per test worker, tenant ID per test
- Targeted command: `cargo xtask test-feature F016`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F016/`

## 6. Acceptance criteria

```gherkin
Feature: Comments, mentions, resolution, and activity

Scenario: Comment with a mention creates a thread and a mention event
  Given commenter Ana has commenter access to row "Kickoff"
  When Ana posts "Can you check this @[user:dana]?"
  Then a thread exists for the row with one comment at version 1
  And comment.created.v1 and mention.created.v1 for dana are in the outbox

Scenario: Resolving an already resolved thread conflicts
  Given the thread on row "Kickoff" is resolved
  When Ana posts resolve with resolved true again
  Then the response is 409 conflict and resolved_at is unchanged

Scenario: Viewer cannot comment
  Given Vic has viewer access to row "Kickoff"
  When Vic posts a comment on the row
  Then the response is 403 denied and no thread is created

Scenario: Replayed event does not duplicate activity
  Given row.updated.v1 with source_event_id E1 was projected
  When the same event is delivered again
  Then the activity feed still shows one entry for E1
  And that entry has one activity_entry_changed_fields row per changed field

Scenario: Activity feed filters to one changed field
  Given row "Kickoff" has entries changing status and owner
  When Ana requests activity with changed_field status
  Then only the status entry is returned with changed_fields containing status
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F006 (rows and sheets as targets, `row.*.v1` events), F003 (ACL checks, audit writer); decisions sections 2–4; contracts row F016
- Blocks: none directly; F037 consumes `mention.created.v1` and F020 consumes comment targets by contract
- Conflicts with: none (disjoint owned paths)
- External dependencies: none
- Risks and mitigations: mention resolution requires a per-token ACL check, so `resolve_mentions` batches the check into one `authz::check_many` call capped at 50 tokens; activity projection can lag under load, so the consumer uses a durable JetStream pull subscription with a 200-message batch and the lag metric alerts above 5 s; Markdown rendering is a script injection surface, so the sanitizer allowlist is tested with the OWASP XSS corpus.
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F006 and F003 accepted and archived
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F016/`
- [ ] Migration file name and owned paths claimed
- [ ] Fixture factory and schema-per-worker isolation available in `testing/harness/`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] Rust unit/API/database, React, E2E, permission-negative, accessibility, and performance gates pass
- [ ] Audit events and outbox events verified for every mutation; `mention.created.v1` payload matches the F037 consumer contract
- [ ] All changed files ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disable `F016_FEATURE`, run down migration on an empty tenant
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Users can hold threaded conversations on rows, sheets, cells, files, reports, and dashboards, mention people and groups, resolve threads, and read a filterable activity history.
- Migration adds `comment_threads`, `comments`, `mentions`, `activity_entries`, and `activity_entry_changed_fields`; rollback drops all five. Feature is off by default behind `F016_FEATURE`.
