# F009 frontend cases

File: `testing/features/F009/frontend/{HierarchyControls.test.tsx,LinkedCellRenderer.test.tsx,LinkPicker.test.tsx,RollupRuleEditor.test.tsx}`. Vitest with MSW. Flag `F009_FEATURE`.

- `renders_treegrid_levels_and_guides` — FR-F009-15: 3-level `Plan` fixture renders `aria-level` 1–3 and indent guides per depth.
- `tab_indents_and_shift_tab_outdents` — FR-F009-01, FR-F009-02: `Tab` on a focused row calls `indentRow`; `Shift+Tab` calls `outdentRow`; not fired while a cell editor is open.
- `rolls_back_on_depth_exceeded` — FR-F009-03: `indentRow` 400 `depth_exceeded` restores the row and shows the reason toast.
- `expand_collapse_fetches_children` — FR-F009-04: `ArrowRight` sets `aria-expanded` and requests `['row-children', rowId]`; `ArrowLeft` collapses.
- `hides_controls_for_viewer` — FR-F009-14: viewer role renders no indent/outdent buttons and no link picker trigger.
- `shows_loading_skeleton_for_children` — FR-F009-15: pending subtree query shows shimmer rows.
- `shows_error_banner_with_correlation_id` — NFR-F009-04: 500 on children shows banner with `correlation_id` and retry.
- `rollup_cell_shows_pending_and_lock` — FR-F009-08: `validation.state = pending` shows shimmer; valid rolled-up cell shows the lock tooltip and rejects edit mode.
- `linked_cell_shows_chip_with_sheet_name` — FR-F009-09: active link renders `Acme · Vendors`.
- `linked_cell_shows_broken_state` — FR-F009-12: `status = broken` renders the amber `BrokenLinkBadge` with tooltip "Target row deleted".
- `redacted_target_shows_restricted_chip` — FR-F009-10: `target_redacted: true` renders `Restricted` with no value.
- `lists_only_readable_sheets` — FR-F009-14: picker sheet list omits sheets returning 404.
- `picker_search_debounces_and_creates_link` — FR-F009-09: typing "Acm" debounces 300 ms, selecting a row calls `createLink` and shows the chip optimistically; error reverts.
- `offers_only_compatible_functions` — FR-F009-06: number column offers sum/min/max/avg/count; select column offers count/any/all/first/last; `weighted_percent` requires a weight column.
- `stale_version_shows_conflict_banner` — FR-F009-01: 409 on indent shows the reload banner.
- `telemetry_events_emitted` — FR-F009-15: indent, link create, and rule save emit `row_indented`, `link_created`, `rollup_configured`.

Evidence: Vitest JUnit under `testing/evidence/F009/frontend/`.
