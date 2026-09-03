# F060 frontend cases

File: `testing/features/F060/frontend/{FormattingPanel.test.tsx,RuleList.test.tsx,RuleEditor.test.tsx,ConditionBuilder.test.tsx,TargetPicker.test.tsx,FormatPicker.test.tsx,RulePreviewTable.test.tsx,FormattingLegend.test.tsx,WhyFormattedPopover.test.tsx,SignalModeSwitch.test.tsx}`. Vitest with MSW. Flag `F060_FEATURE`.

- `blocks_save_until_non_color_signal_chosen` — FR-F060-04: selecting `format.red` alone disables `Save` with the message `Add an icon, badge, or text style so colour is not the only signal`; choosing `alert-triangle` enables it.
- `offers_only_operators_valid_for_column_type` — FR-F060-02: the `Due date` column offers `before`, `after`, `between`, `is_empty`; the `Status` select offers `eq`, `neq`, `in`, `is_empty`.
- `formula_tab_blocks_save_on_non_boolean_result` — FR-F060-02: the formula tab shows `This formula must return true or false` for `Budget * 2` and clears for `Variance > 0`.
- `reports_leaf_index_from_field_errors` — FR-F060-02: a 400 with `field_errors.condition` at index 2 highlights the third condition row.
- `target_picker_caps_column_selection_at_fifty` — FR-F060-03: the 51st column cannot be added and the helper text names the cap.
- `keyboard_reorder_announces_new_position` — FR-F060-06, FR-F060-15: `Alt+ArrowDown` moves a rule and the live region announces `Moved Late tasks to position 2 of 5`.
- `optimistic_reorder_rolls_back_on_conflict` — FR-F060-06: a 409 restores the server order and shows the stale banner with `Reload`.
- `scope_chip_distinguishes_sheet_and_view_rules` — FR-F060-08: list items render `Sheet` or `View: At risk` chips and view rules sort after sheet rules.
- `debounced_preview_renders_ten_rows` — FR-F060-12: editing the condition calls `evaluate` once after 300 ms and renders 10 rows with swatch, icon, and badge.
- `preview_error_shows_retry_with_correlation_id` — FR-F060-13: a 503 from evaluate renders `Formatting paused for this page` with `Retry` and the `correlation_id`.
- `legend_lists_enabled_rules_with_swatch_and_icon` — FR-F060-15: the legend shows only enabled rules, each with name, swatch, and icon, and hides disabled ones.
- `why_popover_lists_applied_rules_in_order` — FR-F060-12, FR-F060-15: the popover lists `Mine` then `Late` with the property each won.
- `why_popover_renders_hidden_inputs_message` — FR-F060-13: a rule in `hidden_inputs` renders `Uses a column you cannot read` with no value shown.
- `icon_only_mode_sets_transparent_fill` — NFR-F060-03: switching the signal mode sets `--fmt-fill: transparent` at the grid root and keeps icons and badges.
- `viewer_sees_read_only_panel` — FR-F060-14: a sheet-viewer sees the list and legend with no `New rule`, no reorder handles, and no enable toggles.
- `empty_state_offers_first_rule` — FR-F060-15: a sheet with no rules renders `No rules yet` with `New rule` and one worked example.

Evidence: Vitest JUnit under `testing/evidence/F060/frontend/`.
