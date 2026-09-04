---
id: T115
type: task
status: planned
parent_epic: E006
parent_feature: F029
parent_story: S058
depends_on: [S058]
owned_paths: [crates/domain/src/integrations/**, crates/persistence/src/integrations/**, services/api/src/integrations/**, services/worker/src/integrations/**, apps/web/src/features/integrations/**, testing/features/F029/api/**, testing/features/F029/frontend/**]
feature_flag: F029_FEATURE
branch: t115-conflict-policy
started_at: null
finished_at: null
---

# T115 — Conflict policy

## Identity

- Parent story: `S058` Notifications/sync
- Owner: platform
- Branch: `t115-conflict-policy`
- Decision references: `docs/architecture-decisions.md` sections 2, 2.1, 5, 7; `docs/capability-contracts.md` row F029

## Objective

Implement notification channels and the notify-test route, calendar bindings with cursor-based two-way sync, the conflict policy resolver, thread-reply comment import, and the binding, conflict, and call-log UI.

## Specification

- Owned paths: `crates/domain/src/integrations/{notify.rs, templates.rs, calendar.rs, conflict.rs, chat.rs, adapters/{microsoft365_calendar.rs, google_calendar.rs, slack_chat.rs, teams_chat.rs}}`, `crates/persistence/src/integrations/{binding_repository.rs, event_repository.rs}`, `services/api/src/integrations/{handlers_notify.rs, binding_validation.rs}`, `services/worker/src/integrations/{calendar_sync.rs, chat_sync.rs, notify.rs}`, `apps/web/src/features/integrations/{NotifyTestDialog.tsx, CalendarBindingDialog.tsx, ConflictList.tsx, CallLogTable.tsx}`
- Contract/input: `NotifyTestRequest { target }`; F037 channel delivery `{ notification_id, kind, recipient, record_ref, deep_link }`; `settings.calendar_binding { connection_id, start_column_id, end_column_id?, title_column_id, assignee_column_id?, conflict_policy }` on `PATCH /api/v1/sheets/{id}`; cursors: Graph delta link, Google `syncToken`.
- Output/behavior: route `POST /api/v1/integrations/connections/{id}/notify-test` (10 per hour per connection, 10 s budget, `integration.notified.v1`); `templates.rs` renders Adaptive Card, Google Chat card, and Block Kit payloads for the five notification kinds with deep links; `notify.rs` worker consumes F037 channel deliveries and records `integration_events` of `kind: notify`; `calendar.rs` maps rows to events (all-day when no time), writes `calendar_event_links` with both `updated_at` values, ignores echoes of OpsHub's own writes, and stores the cursor after each successful page; `conflict.rs` exposes `resolve(policy, ours: Change, theirs: Change) -> Outcome::{ApplyOurs, ApplyTheirs, Hold}` with `newest_wins` comparing timestamps and ties going to OpsHub; a conflict writes an `integration_events` row of `kind: conflict` and one `integration_conflicts` row per contested field (`field`, `opshub_value`, `provider_value`, both `updated_at` values, `winner`) through `IntegrationEventRepository::append_conflict`; `manual` sets `calendar_event_links.review_state = 'needs_review'` with winner `none` and the `ConflictList` reads those rows until either side changes; `chat.rs` imports thread replies as F016 comments with `source: provider` and email author mapping; binding validation rejects non-date and non-text columns with `field_errors`.
- Data access: `notify.rs`, `templates.rs`, `calendar.rs`, `conflict.rs`, `chat.rs`, `handlers_notify.rs`, `binding_validation.rs`, and the three worker jobs hold no SQL; bindings, link rows, cursors, and `review_state` go through `CalendarBindingRepository` (`find_active_binding_for_sheet`, `upsert_event_link`, `save_binding_cursor`, `mark_link_needs_review`, `list_links_needing_review`), call/notify/conflict rows through `IntegrationEventRepository`, and the notify-test rate window through `IntegrationEventRepository::list_events_for_connection`; one sync page commits its link rows, cursor, conflict rows, and F008 cell writes in a single `UnitOfWork` (decision section 2.1).
- Dependencies: T114 adapters and HTTP client; F037 channel registry; F006 sheet settings and rows; F016 comment creation; F008 cell updates.
- Feature flag: `F029_FEATURE`

## TDD

- Failing test first: `testing/features/F029/api/notify_tests.rs::notify_test_delivers_and_publishes_notified`, `::notify_test_rate_limited_after_ten`, `::templates_render_five_kinds_with_deep_links`; `testing/features/F029/api/calendar_tests.rs::calendar_sync_pushes_row_dates_to_provider`, `::calendar_sync_pulls_provider_changes_with_cursor`, `::calendar_sync_ignores_own_echo`, `::binding_rejects_non_date_column`; `testing/features/F029/api/conflict_tests.rs::conflict_newest_wins_takes_provider_value`, `::conflict_opshub_wins_and_provider_wins`, `::conflict_manual_marks_needs_review`, `::conflict_writes_one_row_per_contested_field`; `testing/features/F029/api/chat_tests.rs::chat_sync_imports_thread_reply_as_comment`, `::chat_sync_unknown_email_attributes_to_owner`; `testing/features/F029/frontend/CalendarBindingDialog.test.tsx::previews_first_five_rows`, `ConflictList.test.tsx::shows_both_values_and_winner`
- Targeted command: `cargo xtask test-feature F029`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: mock Graph delta and Google sync-token responses; Slack `conversations.replies` fixture; sheet with 50 rows and date columns; MSW handlers

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Jobs registered in `services/worker/src/registry.rs` behind the flag; OpenAPI regenerated without drift
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S058
- [ ] `finished_at` recorded
