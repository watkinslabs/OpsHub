---
id: T061
type: task
status: planned
parent_epic: E004
parent_feature: F016
parent_story: S031
depends_on: [S031]
owned_paths: [services/api/migrations/*_comments_*.sql, crates/domain/src/comments/**, crates/persistence/src/comments/**, services/api/src/comments/**, testing/features/F016/database/**, testing/features/F016/api/**]
feature_flag: F016_FEATURE
branch: t061-thread-api
started_at: null
finished_at: null
---

# T061 — Thread API

## Identity

- Parent story: `S031` Row conversations
- Owner: platform
- Branch: `t061-thread-api`
- Decision references: `docs/architecture-decisions.md` sections 2–4; `docs/capability-contracts.md` row F016

## Objective

Create the comments schema and implement the thread and comment domain service with the five comment routes, authorization, idempotency, optimistic concurrency, audit, and outbox publication.

## Specification

- Owned paths: `services/api/migrations/<ts>_comments_create_tables.sql`, `services/api/migrations/<ts>_comments_create_tables.down.sql`, `crates/domain/src/comments/{mod.rs, thread.rs, comment.rs, errors.rs, service.rs, schema.rs}`, `crates/persistence/src/comments/{mod.rs, comment_thread_repository.rs, comment_repository.rs, activity_entry_repository.rs}`, `services/api/src/comments/{mod.rs, routes.rs, handlers_comment.rs, handlers_thread.rs, dto.rs}`
- Contract/input: DDL for `comment_threads`, `comments`, `mentions`, `activity_entries`, and the child table `activity_entry_changed_fields(entry_id, tenant_id, field_name, primary key (entry_id, field_name))` per F016 ticket section 4, including the `comments_parent_same_thread` trigger, unique `(tenant_id, source_event_id)`, and the `(tenant_id, field_name)` index; repository traits `CommentThreadRepository`, `CommentRepository`, `ActivityEntryRepository` with the named queries listed in ticket section 4; `CreateCommentRequest { target_kind, target_id, body, thread_id?, parent_comment_id? }`, `UpdateCommentRequest { body }`, `ResolveRequest { resolved }`; headers `Idempotency-Key`, `If-Match`; list query `{ cursor?, limit?, resolved? }`.
- Output/behavior: routes `GET /api/v1/{target_kind}/{target_id}/comments`, `POST /api/v1/comments`, `PATCH /api/v1/comments/{id}`, `DELETE /api/v1/comments/{id}`, `POST /api/v1/comments/{id}/resolve` return `CommentResponse`, `ThreadResponse`, `Page<ThreadResponse>`; `body` limited to 10,000 chars; author edit window 24 hours or `resource-admin`; delete keeps a placeholder when replies exist; resolve on an already-held state returns `409 conflict`; events `comment.created.v1`, `comment.updated.v1`, `comment.deleted.v1`, `comment.resolved.v1` written to `outbox_events` in the same `UnitOfWork` transaction by the repository base contract; audit rows via the F003 writer; handlers and the domain service call repository methods and contain no SQL; `sqlx migrate revert` drops the five tables.
- Dependencies: F006 `rows` and `sheets` tables for target validation; F003 `authz::require(actor, Permission::Comment, target)` and `TargetAccess`; F004 outbox writer.
- Feature flag: `F016_FEATURE` gates router mounting; migration runs regardless.

## TDD

- Failing test first: `testing/features/F016/database/migration_tests.rs::comments_tables_exist_with_constraints`, `::parent_comment_must_share_thread`, `::changed_fields_child_cascades_with_entry`, `::rollback_drops_five_tables`; `testing/features/F016/api/comment_tests.rs::comment_create_opens_thread`, `::comment_body_too_long_invalid`, `::comment_thread_target_mismatch_invalid`, `::comment_edit_after_window_denied`, `::comment_delete_keeps_placeholder_with_replies`, `::thread_resolve_twice_conflicts`, `::comment_viewer_denied`, `::comment_cross_tenant_not_found`
- Targeted command: `cargo xtask test-feature F016`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/comments.rs` tenants A and B, commenter, viewer, admin; schema-per-worker database; in-memory outbox recorder

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Migration applies and reverts on CI PostgreSQL 18; router mounted in `services/api/src/router.rs` behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S031
- [ ] `finished_at` recorded
