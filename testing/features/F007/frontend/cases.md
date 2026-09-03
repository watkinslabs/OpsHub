# F007 frontend cases

File: `testing/features/F007/frontend/{ColumnEditorDrawer.test.tsx,ColumnHeaderMenu.test.tsx,OptionListEditor.test.tsx,ValidationIcon.test.tsx}`. Vitest with MSW. Flag `F007_FEATURE`.

- `creates_select_column_with_options` — FR-F007-01, FR-F007-07, FR-F007-17: pick `select`, label `Status`, add three options, save → `createColumn` called with ordered options; toast `Column added`.
- `shows_field_error_for_duplicate_label` — FR-F007-03: 409 with `field_errors.label` renders inline under the label field.
- `drawer_type_change_shows_preview_count` — FR-F007-06: choosing `number` on a text column shows `3 cells will become invalid` from the dry run before the confirm button is enabled.
- `unsupported_conversion_disables_type` — FR-F007-05: `file` column type picker lists other types disabled with reason.
- `primary_column_hides_delete_and_hide` — FR-F007-13: header menu for the primary column omits `Hide`, `Delete`, and the type field is read-only.
- `keyboard_reorder_calls_api_and_rolls_back_on_conflict` — FR-F007-12: `Alt+ArrowRight` calls `reorderColumn`; 409 restores order and shows the stale banner.
- `option_list_reorders_and_archives` — FR-F007-07: `Alt+ArrowUp` moves an option; archive toggle marks it and keeps it listed.
- `validation_rule_editor_validates_regex_length` — FR-F007-10: 513-char pattern shows inline error and blocks save.
- `validate_button_polls_until_complete` — FR-F007-11: click `Validate` → progress chip; MSW returns `running` then `completed`; counts shown.
- `exposes_message_in_accessible_name` — FR-F007-17, NFR-F007-03: `ValidationIcon` with code `regex` has `aria-describedby` resolving to the message.
- `shows_denied_state_for_viewer` — FR-F007-17: viewer role hides `+` button and header menu.
- `shows_error_banner_with_correlation_id` — NFR-F007-04: 500 on list shows banner with `correlation_id` and retry.
- `offline_disables_drawer_save` — FR-F007-17: `navigator.onLine=false` shows offline badge and disables save.

Evidence: Vitest JUnit under `testing/evidence/F007/frontend/`.
