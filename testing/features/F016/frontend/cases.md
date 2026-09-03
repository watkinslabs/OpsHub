# F016 frontend cases

File: `testing/features/F016/frontend/{ConversationPanel.test.tsx,MentionCombobox.test.tsx,ActivityTab.test.tsx}`. Vitest with MSW. Flag `F016_FEATURE`.

- `ConversationPanel.test.tsx::renders_open_and_resolved_threads` — FR-F016-13: seeded row renders 3 open threads and 2 under the `Resolved` group with nested replies in order.
- `ConversationPanel.test.tsx::shows_loading_skeleton_then_threads` — FR-F016-13: pending query shows three skeleton cards; resolves to threads.
- `ConversationPanel.test.tsx::shows_empty_state` — FR-F016-13: row with no threads shows `No comments yet. Start the conversation.`
- `ConversationPanel.test.tsx::shows_error_banner_with_correlation_id` — NFR-F016-04: 500 response shows banner with `correlation_id` and retry.
- `ConversationPanel.test.tsx::viewer_sees_read_only_message` — FR-F016-12: `canComment=false` replaces the composer with the read-only message and hides menus.
- `ConversationPanel.test.tsx::reply_rolls_back_on_denied` — FR-F016-12: optimistic reply removed and error shown on 403.
- `ConversationPanel.test.tsx::edit_menu_hidden_after_24h` — FR-F016-06: comment created 25 h ago shows no edit item for the author; shown for admin.
- `ConversationPanel.test.tsx::resolve_toggle_rolls_back_on_conflict` — FR-F016-08: 409 restores the previous state and shows stale banner.
- `ConversationPanel.test.tsx::markdown_sanitizer_strips_script` — NFR-F016-02: body with `<script>` and remote `<img>` renders without them.
- `MentionCombobox.test.tsx::mention_combobox_keyboard_select` — FR-F016-13, NFR-F016-03: typing `@da`, ArrowDown, Enter inserts `@[user:<dana>]` chip and emits `mention_added`.
- `MentionCombobox.test.tsx::limits_suggestions_to_20` — NFR-F016-02: 30 matches render 20 options.
- `ActivityTab.test.tsx::activity_tab_shows_delete_and_restore` — FR-F016-14: entries `row.deleted` and `row.restored` render with actor chips.
- `ActivityTab.test.tsx::filter_chips_change_query_key` — FR-F016-09: selecting `Automation` refetches with `actor_kind=automation` and emits `activity_filtered`.
- `ActivityTab.test.tsx::offline_disables_composer_and_keeps_draft` — FR-F016-13: `navigator.onLine=false` disables submit; draft text persists after reconnect.

Evidence: Vitest JUnit under `testing/evidence/F016/frontend/`.
