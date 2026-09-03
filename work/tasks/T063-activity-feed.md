---
id: T063
type: task
status: planned
parent_epic: E004
parent_feature: F016
parent_story: S032
depends_on: [S032]
owned_paths: [crates/domain/src/comments/**, services/api/src/comments/**, testing/features/F016/api/**, testing/features/F016/performance/**]
feature_flag: F016_FEATURE
branch: t063-activity-feed
started_at: null
finished_at: null
---

# T063 — Activity feed

## Identity

- Parent story: `S032` Mentions/history
- Owner: platform
- Branch: `t063-activity-feed`
- Decision references: `docs/architecture-decisions.md` sections 2, 3, 7; `docs/capability-contracts.md` row F016

## Objective

Project row, cell, comment, file, and workflow-run events into `activity_entries` through an idempotent JetStream consumer and expose the filtered activity route.

## Specification

- Owned paths: `crates/domain/src/comments/{activity.rs, projector.rs}`, `services/api/src/comments/{handlers_activity.rs, activity_consumer.rs}`
- Contract/input: JetStream durable pull consumer `activity_projector` on subjects `row.*.v1`, `cell.updated.v1`, `comment.*.v1`, `mention.created.v1`, `file.uploaded.v1`, `file.deleted.v1`, `workflow-run.completed.v1`; event envelope `{ tenant_id, actor_id, aggregate_id, version, changed_fields, correlation_id, occurred_at }` plus `event_id`; query `{ cursor?, limit? ≤ 200, actor_kind?, action?, since?, until? }`.
- Output/behavior: `project_activity(event) -> Option<ActivityEntry>` maps each event to `{ target, actor_kind, action, changed_fields, summary }` where `actor_kind` is `automation` when the actor context carries `workflow_run_id`, `integration` when it carries `sync_id`, else `user`; insert uses `on conflict (tenant_id, source_event_id) do nothing`; a row delete or restore also flips `deleted_at` on that row's `comment_threads`; failures retry with exponential backoff up to 5 attempts then dead-letter; `GET /api/v1/{target_kind}/{target_id}/activity` returns `Page<ActivityEntryResponse>` newest first and `404 not_found` when the actor cannot read the target; metrics `activity_projection_lag_seconds` and `activity_entries_total` exported.
- Dependencies: T061 tables; F004 JetStream transport and dead-letter table; F003 `TargetAccess`.
- Feature flag: `F016_FEATURE` gates both the consumer registration and the route.

## TDD

- Failing test first: `testing/features/F016/api/activity_tests.rs::activity_projects_row_updated`, `::activity_replayed_event_not_duplicated`, `::activity_filters_by_actor_kind`, `::activity_marks_workflow_actor_automation`, `::activity_row_delete_hides_threads_restore_shows`, `::activity_unreadable_target_not_found`; `testing/features/F016/performance/activity_bench.rs::activity_projection_lag_p95`
- Targeted command: `cargo xtask test-feature F016`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: recorded event list with duplicate `event_id`; embedded JetStream from `testing/harness/nats.rs`; fixed clock

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Consumer registered in `services/api/src/main.rs` startup behind the flag; route mounted in `services/api/src/comments/routes.rs`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S032
- [ ] `finished_at` recorded
