---
id: S032
type: story
status: planned
parent_epic: E004
parent_feature: F016
depends_on: [S031]
owned_paths: [crates/domain/src/comments/**, services/api/src/comments/**, apps/web/src/features/comments/**, testing/features/F016/**]
feature_flag: F016_FEATURE
branch: s032-mentions-history
started_at: null
finished_at: null
---

# S032 — Mentions/history

## Identity

- Parent feature: `F016` Comments and activity
- Owner: platform
- Branch: `s032-mentions-history`
- Decision references: `docs/architecture-decisions.md` sections 2–4, 6; `docs/capability-contracts.md` row F016

## Vertical slice

As a sheet collaborator, I want to see every human and automated change to a row in one activity feed and to hold conversations with keyboard-accessible mention autocomplete in the row drawer, so that history and discussion are visible where the work is.

## Requirements

- **SR-S032-01:** A durable JetStream consumer `activity_projector` turns `row.created.v1`, `row.updated.v1`, `row.moved.v1`, `row.deleted.v1`, `row.restored.v1`, `cell.updated.v1`, `comment.*.v1`, `file.uploaded.v1`, and `workflow-run.completed.v1` into `activity_entries`, deduplicated by `(tenant_id, source_event_id)` (FR-F016-10).
- **SR-S032-02:** `GET /api/v1/{target_kind}/{target_id}/activity` pages newest first with `limit` ≤ 200 and filters `actor_kind`, `action`, `since`, `until`; entries carry `actor_kind` derived from the event's actor context (`automation` for F019 runs, `integration` for F030 syncs) (FR-F016-09).
- **SR-S032-03:** Soft-deleting a row hides its threads; restoring shows them again together with `row.deleted` and `row.restored` activity entries (FR-F016-14).
- **SR-S032-04:** `ConversationPanel` renders threads, a reply composer, resolve toggles, and edit/delete menus honoring the 24-hour window; `MentionCombobox` queries `['mention-suggestions']` with at most 20 tenant-scoped suggestions the actor may see (FR-F016-13, NFR-F016-02).
- **SR-S032-05:** `ActivityTab` renders entries with actor chips, changed-field summaries, and filter chips; loading, empty, error, denied, stale, and offline states are explicit (FR-F016-13, FR-F016-09).
- **SR-S032-06:** The combobox is an ARIA combobox with listbox popup; new replies are announced via a polite live region; the panel and tab have zero serious axe violations (NFR-F016-03).
- **SR-S032-07:** Thread list on a 1,000-comment row and projection lag meet NFR-F016-01; `activity_projection_lag_seconds` is exported (NFR-F016-04).

## Surfaces

- Infrastructure/container: JetStream consumer `activity_projector` registered in the API process startup
- Rust service/API: `crates/domain/src/comments/{activity.rs, projector.rs}`; `services/api/src/comments/{handlers_activity.rs, activity_consumer.rs}`
- Data/migration: none new; uses `activity_entries` from S031
- React/UI: `apps/web/src/features/comments/{ConversationPanel.tsx, ThreadCard.tsx, CommentItem.tsx, ReplyComposer.tsx, MentionCombobox.tsx, ResolveToggle.tsx, ActivityTab.tsx, ActivityEntryRow.tsx, ActivityFilters.tsx, api.ts, hooks.ts}`
- Mocks/fixtures: recorded event list for the projector; seeded row with 5 threads and 40 comments; 1,000-comment generator for the performance lane; MSW handlers for component tests

## TDD harness

- Test path: `testing/features/F016/{api,frontend,e2e,accessibility,performance}/`
- Feature flag: `F016_FEATURE`
- Targeted command: `cargo xtask test-feature F016`
- Full command: `cargo xtask test-all`
- First failing tests: `activity_replayed_event_not_duplicated`, `activity_filters_by_actor_kind`, `mention_combobox_keyboard_select`, `activity_tab_shows_delete_and_restore`, `thread_list_1000_comments_p95`

## Exit criteria

- [ ] Requirement tests SR-S032-01 through SR-S032-07 written first and failing
- [ ] Tasks T063 and T064 complete; UI wired to real API through generated client
- [ ] Unit, API, React, E2E, accessibility, permission, and performance tests pass
- [ ] Production call path named: `apps/web/src/features/comments/ConversationPanel.tsx` mounted in the row drawer at `/w/:workspaceId/sheets/:sheetId?row=:rowId&tab=conversation`
- [ ] Handoff evidence recorded in the F016 ticket
