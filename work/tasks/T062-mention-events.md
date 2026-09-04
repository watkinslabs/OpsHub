---
id: T062
type: task
status: planned
parent_epic: E004
parent_feature: F016
parent_story: S031
depends_on: [T061]
owned_paths: [crates/domain/src/comments/**, crates/persistence/src/comments/**, services/api/src/comments/**, testing/features/F016/api/**, testing/features/F016/requirements/**]
feature_flag: F016_FEATURE
branch: t062-mention-events
started_at: null
finished_at: null
---

# T062 — Mention events

## Identity

- Parent story: `S031` Row conversations
- Owner: platform
- Branch: `t062-mention-events`
- Decision references: `docs/architecture-decisions.md` sections 3, 4; `docs/capability-contracts.md` row F016

## Objective

Parse mention tokens from comment bodies, resolve them against tenant users and groups with target access, persist `mentions` rows, and publish `mention.created.v1` so F037 can notify the mentioned principals.

## Specification

- Owned paths: `crates/domain/src/comments/{mention.rs, mention_parser.rs, mention_resolver.rs}` (no SQL), `crates/persistence/src/comments/comment_repository.rs` for the `mentions` writes and `list_mentions_for_comment(comment_id)`, `services/api/src/comments/{handlers_suggestions.rs, dto.rs}`
- Contract/input: Markdown body with tokens `@[user:<uuid>]` and `@[group:<uuid>]`, at most 50 tokens; actor context `{ tenant_id, actor_id }`; target `TargetRef`; `authz::check_many(actor_candidates, Permission::Read, target)` from F003; suggestion query `{ target_kind, target_id, q, limit ≤ 20 }` served on the list route's `?suggest=` parameter of `GET /api/v1/{target_kind}/{target_id}/comments`.
- Output/behavior: `parse_mentions(body) -> Vec<MentionToken>` rejects a 51st token with `CommentError::TooManyMentions → 400 invalid field_errors.body = "too_many_mentions"`; `resolve_mentions` returns `{ resolved: Vec<Mention>, unresolved: Vec<MentionToken> }`, inserting `mentions` rows for resolved principals through `CommentRepository` inside the comment's `UnitOfWork` and publishing `mention.created.v1 { comment_id, thread_id, target_kind, target_id, mentioned_kind, mentioned_id, author_id }` per resolved mention through the repository outbox enqueue in the comment transaction; on edit only mentions absent from the previous body are published; deactivated users, foreign-tenant IDs, and principals without target read are unresolved and never leak in the response beyond their token text; suggestions return `{ kind, id, display_name, avatar_url }` for principals the actor can see and that have target read.
- Dependencies: T061 service and tables; F002 `users` and `groups` for display names and active state; F003 `check_many`.
- Feature flag: `F016_FEATURE`.

## TDD

- Failing test first: `testing/features/F016/api/mention_tests.rs::mention_resolved_publishes_event`, `::mention_without_access_stays_plain_text`, `::mention_foreign_tenant_user_unresolved`, `::mention_limit_51_invalid`, `::mention_edit_publishes_only_new_mentions`, `::mention_group_resolves_once`, `::mention_suggestions_exclude_foreign_and_inactive`
- Targeted command: `cargo xtask test-feature F016`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: fixture users `ana`, `dana`, deactivated `old`, group `ops`, foreign-tenant user; in-memory outbox recorder asserting event payloads

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] `mention.created.v1` payload documented in `crates/contracts` and consumed by the F037 harness stub without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S031
- [ ] `finished_at` recorded
