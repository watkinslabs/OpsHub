---
id: T064
type: task
status: planned
parent_epic: E004
parent_feature: F016
parent_story: S032
depends_on: [T063]
owned_paths: [apps/web/src/features/comments/**, testing/features/F016/frontend/**, testing/features/F016/e2e/**, testing/features/F016/accessibility/**]
feature_flag: F016_FEATURE
branch: t064-collaboration-e2e
started_at: null
finished_at: null
---

# T064 — Collaboration E2E

## Identity

- Parent story: `S032` Mentions/history
- Owner: platform
- Branch: `t064-collaboration-e2e`
- Decision references: `docs/architecture-decisions.md` section 6; `docs/capability-contracts.md` row F016

## Objective

Build the conversation panel, mention combobox, and activity tab in the row drawer, wired to the real comments and activity routes, and prove the end-to-end comment, mention, resolve, and history flow in the browser.

## Specification

- Owned paths: `apps/web/src/features/comments/{ConversationPanel.tsx, ThreadCard.tsx, CommentItem.tsx, ReplyComposer.tsx, MentionCombobox.tsx, ResolveToggle.tsx, ActivityTab.tsx, ActivityEntryRow.tsx, ActivityFilters.tsx, markdown.ts, api.ts, hooks.ts}`
- Contract/input: generated `CommentsApi` client; props `{ targetKind, targetId, canComment, canAdmin }` from the hosting drawer; query keys `['comments', targetKind, targetId, { resolved, cursor }]`, `['activity', targetKind, targetId, filters, cursor]`, `['mention-suggestions', targetKind, targetId, query]`.
- Output/behavior: threads grouped into open and resolved; composer with `Ctrl+Enter` submit and `@` combobox (ARIA combobox, ≤ 20 suggestions, arrow and Enter selection) inserting `@[user:<uuid>]` tokens rendered as chips; Markdown rendered through the sanitizer in `markdown.ts` (no scripts, iframes, or remote images); edit and delete menus shown only inside the 24-hour author window or for admins; optimistic reply with rollback on `denied` or `invalid`; resolve toggle with rollback on `conflict`; activity tab with actor kind, action, and date filter chips; states loading, empty, error with `correlation_id`, denied composer message, not-found, stale, offline; polite live region announces new replies; telemetry `conversation_opened`, `comment_created`, `mention_added`, `comment_resolved`, `activity_filtered`.
- Dependencies: T063 routes; F006 row drawer host in `apps/web/src/features/sheets/` exposes a tab slot consumed here.
- Feature flag: `F016_FEATURE` read through the flag hook; tabs are not registered when off.

## TDD

- Failing test first: `testing/features/F016/frontend/ConversationPanel.test.tsx::renders_open_and_resolved_threads`, `::viewer_sees_read_only_message`, `::reply_rolls_back_on_denied`, `MentionCombobox.test.tsx::mention_combobox_keyboard_select`, `ActivityTab.test.tsx::activity_tab_shows_delete_and_restore`; `testing/features/F016/e2e/comments.spec.ts::comment_mention_resolve_and_history`, `::viewer_cannot_comment`; `testing/features/F016/accessibility/comments.a11y.spec.ts::panel_and_activity_have_no_serious_axe_violations`
- Targeted command: `cargo xtask test-feature F016`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: MSW handlers from the seeded 5-thread row fixture; Playwright uses the real API against a seeded tenant with users `ana`, `dana`, viewer `vic`

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Component, E2E, and accessibility lanes pass
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S032
- [ ] `finished_at` recorded
