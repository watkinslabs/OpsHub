# F062 frontend cases

File: `testing/features/F062/frontend/{primitive_tests,overlay_tests,keyboard_tests,pattern_tests,safety_tests}.tsx`. Flag `F062_FEATURE`.

- `every_exported_primitive_renders_all_variants` — FR-F062-07: each primitive on the closed list renders every variant and size, forwards its ref, and spreads `...rest` onto its root.
- `sizes_derive_from_density_tokens` — FR-F062-06: switching to `compact` changes every control height and row height without a component hard-coding a pixel value.
- `focus_ring_only_on_focus_visible` — FR-F062-11: a mouse press shows no ring; a keyboard tab does; the ring uses `--focus-ring`.
- `disabled_and_loading_states_block_interaction` — FR-F062-07: a disabled or loading `Button` fires no click and exposes the matching ARIA state.
- `focus_returns_to_invoker_on_close` — FR-F062-08: opening and closing each overlay returns focus to the element that opened it.
- `nested_menu_escape_leaves_dialog_open` — FR-F062-08: with a menu open inside a dialog, `Escape` closes the menu only and focus returns to the menu trigger.
- `scroll_lock_causes_no_layout_shift` — FR-F062-08: opening a dialog locks background scroll with zero cumulative layout shift.
- `trigger_marks_aria_expanded_and_controls` — FR-F062-08: every overlay trigger reflects open state through `aria-expanded` and points at its surface with `aria-controls`.
- `roving_tabindex_moves_with_arrows_and_typeahead` — FR-F062-11: `Menu`, `Tabs`, `Combobox`, `Table`, and `SegmentedControl` expose one tab stop and move with arrows and type-ahead.
- `tabs_home_end_reach_bounds` — FR-F062-11: `Home` and `End` reach the first and last item in every composite widget.
- `error_state_renders_correlation_id_and_retry` — FR-F062-09: `ErrorState` always shows the `correlation_id` it is given and calls `onRetry`.
- `empty_state_takes_copy_from_props` — FR-F062-09: no pattern renders hard-coded feature wording; the five `LoadingSkeleton` shapes render distinctly.
- `data_table_virtualizes_above_one_hundred_rows` — FR-F062-09: a 5,000-row table mounts a bounded number of row nodes and keeps its header sticky.
- `data_table_scrolls_within_its_container` — FR-F062-09: a wide table scrolls horizontally inside its own element and the page does not.
- `formatted_date_uses_explicit_locale` — FR-F062-14: the formatting components never call `toLocaleString` without a locale and fall back to `en-US`/`UTC`.
- `icons_import_only_through_registry` — FR-F062-13: a static scan finds no `lucide-react` import outside `apps/web/src/ui/icons.ts`.

Evidence: component test report under `testing/evidence/F062/frontend/`.
