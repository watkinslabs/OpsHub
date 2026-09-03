---
id: S058
type: story
status: planned
parent_epic: E006
parent_feature: F029
depends_on: [S057]
owned_paths: [crates/domain/src/integrations/**, services/api/src/integrations/**, services/worker/src/integrations/**, apps/web/src/features/integrations/**, testing/features/F029/**]
feature_flag: F029_FEATURE
branch: s058-notifications-sync
started_at: null
finished_at: null
---

# S058 — Notifications/sync

## Identity

- Parent feature: `F029` Microsoft/Google/Slack
- Owner: platform
- Branch: `s058-notifications-sync`
- Decision references: `docs/architecture-decisions.md` sections 5, 7; `docs/capability-contracts.md` row F029

## Vertical slice

As an integration administrator, I want OpsHub notifications delivered to Teams, Google Chat, and Slack, sheet dates mirrored to Outlook and Google Calendar with a conflict policy I choose, and thread replies captured as comments, so that people work from their own tools while OpsHub stays the record of truth.

## Requirements

- **SR-S058-01:** A connection with `notify` registers a F037 channel; adapters render Adaptive Cards, Google Chat cards, and Block Kit messages for `mention`, `assignment`, `approval`, `due_soon`, and `workflow_failed` with deep links (covers FR-F029-08).
- **SR-S058-02:** `POST /api/v1/integrations/connections/{id}/notify-test` delivers within 10 s, returns `delivered` and `provider_message_id`, publishes `integration.notified.v1`, and is limited to 10 per connection per hour (FR-F029-09).
- **SR-S058-03:** Calendar bindings validate column types, and the `calendar_sync` job pushes row changes to Outlook and Google Calendar and pulls provider changes using Graph delta tokens and Google `syncToken` cursors stored per binding (FR-F029-10).
- **SR-S058-04:** `resolve_conflict` applies `opshub_wins`, `provider_wins`, `newest_wins`, and `manual`; conflicts write `integration_events` of `kind: conflict` and `manual` marks the row `needs_review` (FR-F029-11).
- **SR-S058-05:** The `chat_sync` job imports Slack and Teams thread replies as F016 comments with `source: provider`, mapping authors by email or attributing to the owner (FR-F029-12).
- **SR-S058-06:** Adapters honor provider `429` and `Retry-After`, retry 3 times with backoff, and log every call in `integration_events` (FR-F029-13, NFR-F029-04).
- **SR-S058-07:** `NotifyTestDialog`, `CalendarBindingDialog`, `ConflictList`, and `CallLogTable` implement the states in ticket section 3 (FR-F029-15, NFR-F029-03).
- **SR-S058-08:** The full F029 harness with mocked providers passes, including a 1,000-row calendar sync under 5 minutes and notification p95 under 3 s (NFR-F029-01, NFR-F029-02).

## Surfaces

- Infrastructure/container: worker jobs `calendar_sync`, `chat_sync`, `notify` registered with per-connection concurrency 1
- Rust service/API: `crates/domain/src/integrations/{notify.rs, templates.rs, calendar.rs, conflict.rs, chat.rs, adapters/{microsoft365_calendar.rs, google_calendar.rs, slack_chat.rs, teams_chat.rs}}`; `services/api/src/integrations/{handlers_notify.rs, binding_validation.rs}`; `services/worker/src/integrations/{calendar_sync.rs, chat_sync.rs, notify.rs}`
- Data/migration: none new; uses `calendar_bindings`, `calendar_event_links`, `integration_events` from S057
- React/UI: `apps/web/src/features/integrations/{NotifyTestDialog.tsx, CalendarBindingDialog.tsx, ConflictList.tsx, CallLogTable.tsx}`
- Mocks/fixtures: mock providers with Graph delta, Calendar sync token, `chat.postMessage`, `conversations.replies`, and programmable 429 responses; sheet with 50 rows and a 1,000-row generator

## TDD harness

- Test path: `testing/features/F029/{api,frontend,e2e,accessibility,performance}/`
- Feature flag: `F029_FEATURE`
- Targeted command: `cargo xtask test-feature F029`
- Full command: `cargo xtask test-all`
- First failing tests: `notify_test_delivers_and_publishes_notified`, `notify_test_rate_limited_after_ten`, `calendar_sync_pushes_row_dates_to_provider`, `calendar_sync_pulls_provider_changes_with_cursor`, `conflict_newest_wins_takes_provider_value`, `conflict_manual_marks_needs_review`, `chat_sync_imports_thread_reply_as_comment`, `adapter_honors_retry_after`

## Exit criteria

- [ ] Requirement tests SR-S058-01 through SR-S058-08 written first and failing
- [ ] Tasks T115 and T116 complete; jobs registered in `services/worker/src/registry.rs`; UI wired to the real API through the generated client
- [ ] Unit, API, React, E2E, permission, accessibility, and performance tests pass
- [ ] Production call path named: `services/worker/src/integrations/calendar_sync.rs` registered in `services/worker/src/registry.rs`; `apps/web/src/features/integrations/ConnectionDetail.tsx` mounted at `/admin/integrations/:connectionId`
- [ ] Handoff evidence recorded in the F029 ticket
