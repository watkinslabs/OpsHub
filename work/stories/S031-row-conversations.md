---
id: S031
type: story
status: planned
parent_epic: E004
parent_feature: F016
depends_on: [F006, F003]
owned_paths: [crates/domain/src/comments/**, crates/persistence/src/comments/**, services/api/src/comments/**, services/api/migrations/*_comments_*.sql, testing/features/F016/**]
feature_flag: F016_FEATURE
branch: s031-row-conversations
started_at: null
finished_at: null
---

# S031 — Row conversations

## Identity

- Parent feature: `F016` Comments and activity
- Owner: platform
- Branch: `s031-row-conversations`
- Decision references: `docs/architecture-decisions.md` sections 2–4; `docs/capability-contracts.md` row F016

## Vertical slice

As a sheet collaborator, I want to post, edit, delete, and resolve threaded comments on a row and have my `@` mentions recorded as events, so that the reasoning behind a work item lives on the record and the people I name can be told.

## Requirements

- **SR-S031-01:** `POST /api/v1/comments` with `{ target_kind: "row", target_id, body }` creates a `comment_threads` row and a `comments` row through `CommentThreadRepository::find_or_create_thread` and `CommentRepository::insert` in one `UnitOfWork` transaction and returns `CommentResponse` with `thread_id` and version 1 (covers FR-F016-01, FR-F016-02).
- **SR-S031-02:** A body over 10,000 characters or a `thread_id` bound to another target returns `400 invalid` with the named `field_errors` key (FR-F016-03, FR-F016-02).
- **SR-S031-03:** `parse_mentions` extracts `@[user:<uuid>]` and `@[group:<uuid>]` tokens; `resolve_mentions` keeps those with target read access, writes `mentions` rows through `CommentRepository` in the same `UnitOfWork`, and publishes one `mention.created.v1` per resolved mention; unresolved tokens are returned in `unresolved_mentions` (FR-F016-04).
- **SR-S031-04:** `GET /api/v1/row/{id}/comments` returns threads with nested comments in `created_at` order via `page_threads(target_kind, target_id, resolved, cursor)` and `page_comments(thread_id, cursor)`, cursor paged with `limit` ≤ 100 and `resolved` filter (FR-F016-05).
- **SR-S031-05:** `PATCH /api/v1/comments/{id}` enforces the 24-hour author window or `resource-admin`, requires `If-Match`, sets `edited_at`, and publishes `mention.created.v1` only for newly added mentions (FR-F016-06).
- **SR-S031-06:** `DELETE` calls `CommentRepository::soft_delete` and keeps a placeholder when replies exist; `POST /resolve` toggles thread resolution through `CommentThreadRepository` in one `UnitOfWork` and returns `409 conflict` when the state already holds (FR-F016-07, FR-F016-08).
- **SR-S031-07:** Every mutation checks `Idempotency-Key`, writes an audit row, and enqueues the matching `comment.*.v1` outbox event; viewers receive `403 denied` and foreign tenants `404 not_found` (FR-F016-11, FR-F016-12).

## Surfaces

- Infrastructure/container: none beyond F004 baseline
- Rust service/API: `crates/domain/src/comments/{thread.rs, comment.rs, mention.rs, mention_parser.rs, errors.rs, service.rs}` (repository traits only, no SQL); `crates/persistence/src/comments/{mod.rs, comment_thread_repository.rs, comment_repository.rs, activity_entry_repository.rs}` holding every SQL statement; `services/api/src/comments/{routes.rs, handlers_comment.rs, handlers_thread.rs, dto.rs}`
- Data/migration: `services/api/migrations/<ts>_comments_create_tables.sql` creating `comment_threads`, `comments`, `mentions`, `activity_entries`, and the child table `activity_entry_changed_fields` with indexes and the `comments_parent_same_thread` trigger from ticket section 4
- React/UI: none in this story (S032 covers the panel and activity tab)
- Mocks/fixtures: `testing/fixtures/comments.rs` tenant, sheet, row, commenter, viewer, admin, foreign-tenant builders; in-memory outbox recorder

## TDD harness

- Test path: `testing/features/F016/api/` and `testing/features/F016/database/`
- Feature flag: `F016_FEATURE`
- Targeted command: `cargo xtask test-feature F016`
- Full command: `cargo xtask test-all`
- First failing tests: `comment_create_opens_thread`, `comment_body_too_long_invalid`, `mention_resolved_publishes_event`, `mention_without_access_stays_plain_text`, `thread_resolve_twice_conflicts`, `comment_viewer_denied`

## Exit criteria

- [ ] Requirement tests SR-S031-01 through SR-S031-07 written first and failing
- [ ] Tasks T061 and T062 complete and wired through `services/api` router
- [ ] Unit, API, database, permission tests pass in targeted and full modes
- [ ] Production call path named: `services/api/src/comments/routes.rs` mounted in `services/api/src/router.rs`
- [ ] Handoff evidence recorded in the F016 ticket
