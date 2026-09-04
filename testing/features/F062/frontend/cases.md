# F062 frontend cases

File: `testing/features/F062/frontend/{theme_tests,surface_tests,lint_tests,pattern_tests,safety_tests}.tsx`. Flag `F062_FEATURE`.

- `mui_theme_reads_every_token` — FR-F062-08: palette, typography, radius, spacing, z-index and durations all resolve from the token variables, and the palette tracks `--brand`.
- `every_listed_component_is_re_exported` — FR-F062-09: every component in the ticket list is exported from `ui/index.ts` and renders themed in all variants and sizes.
- `direct_mui_import_fails_lint` — FR-F062-09: a feature module importing `@mui/material` directly, or redefining a re-exported name, fails lint.
- `sizes_derive_from_density_tokens` — FR-F062-07: switching to `compact` changes every control height and row height without a component hard-coding a pixel value.
- `focus_ring_only_on_focus_visible` — FR-F062-03: a mouse press shows no ring; a keyboard tab does; the ring uses `--focus-ring`.
- `disabled_and_loading_states_block_interaction` — FR-F062-09: a disabled or loading `Button` fires no click and exposes the matching ARIA state.
- `focus_returns_to_invoker_on_close` — FR-F062-09: opening and closing each overlay returns focus to the element that opened it.
- `nested_menu_escape_leaves_dialog_open` — FR-F062-09: with a menu open inside a dialog, `Escape` closes the menu only and focus returns to the menu trigger.
- `scroll_lock_causes_no_layout_shift` — FR-F062-09: opening a dialog locks background scroll with zero cumulative layout shift.
- `trigger_marks_aria_expanded_and_controls` — FR-F062-09: every overlay trigger reflects open state through `aria-expanded` and points at its surface with `aria-controls`.
- `roving_tabindex_moves_with_arrows_and_typeahead` — FR-F062-09: `Menu`, `Tabs`, `Combobox`, `Table`, and `SegmentedControl` expose one tab stop and move with arrows and type-ahead.
- `tabs_home_end_reach_bounds` — FR-F062-09: `Home` and `End` reach the first and last item in every composite widget.
- `error_state_renders_correlation_id_and_retry` — FR-F062-11: `ErrorState` always shows the `correlation_id` it is given and calls `onRetry`.
- `empty_state_takes_copy_from_props` — FR-F062-11: no pattern renders hard-coded feature wording; the five `LoadingSkeleton` shapes render distinctly.
- `data_grid_virtualizes_above_one_hundred_rows` — FR-F062-10: a 5,000-row `DataGridPanel` mounts a bounded number of row nodes and keeps its header sticky.
- `data_grid_scrolls_within_its_container` — FR-F062-10: a wide grid scrolls horizontally inside its own element and the page does not.
- `no_entitlement_is_consulted_by_the_grid` — FR-F062-16: the grid renders every capability without reading an entitlement and shows no upgrade prompt.
- `licence_key_is_build_time_only` — FR-F062-16: the key comes from the build-time secret, no runtime request is made for it, and a production build without it fails naming `mui/x-license-key`.
- `server_capabilities_available_at_every_tier` — FR-F062-16: grouping, tree rows, aggregation and xlsx export all work unentitled, and the grid calls the F013, F009, F022 and F010 endpoints rather than a client implementation.
- `column_reorder_writes_layout_column_order` — FR-F062-17: dragging a header, and its keyboard equivalent, persist the new order to F008 `layout.column_order` within 1 s and leave another user's order untouched.
- `pinning_persists_through_layout` — FR-F062-17: column and row pinning persist through the `layout` field and restore on reload.
- `freeze_and_hide_persist_through_layout` — FR-F062-17: freeze-up-to-here and hide-column persist through `layout.frozen_column_count` and `layout.hidden_columns`.
- `range_selection_extends_and_copies_tsv` — FR-F062-17: Shift+Arrow, Shift+Click and Ctrl+Click build contiguous and non-contiguous ranges and the clipboard carries TSV with the grid's visible formatting.
- `grid_behaviours_have_keyboard_equivalents` — FR-F062-17: reorder, freeze, hide and selection are each operable by keyboard with an accessible announcement.
- `chart_palette_is_fixed_and_labelled` — FR-F062-13: `ChartPanel` uses the five-series palette in order and every series carries a legend entry, direct label or value.
- `formatted_date_uses_explicit_locale` — FR-F062-11: the formatting components never call `toLocaleString` without a locale and fall back to `en-US`/`UTC`.
- `icons_import_only_through_registry` — FR-F062-14: a static scan finds no `lucide-react` import outside `apps/web/src/ui/icons.ts`.

Evidence: component test report under `testing/evidence/F062/frontend/`.
