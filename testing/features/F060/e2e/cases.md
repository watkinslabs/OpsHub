# F060 e2e cases

File: `testing/features/F060/e2e/formatting.spec.ts`. Playwright against the seeded `Delivery plan` tenant. Flag `F060_FEATURE`.

- `author_two_rules_and_see_the_grid_repaint` — FR-F060-01, FR-F060-04, FR-F060-09, FR-F060-15: an editor creates `Late` (red fill plus `alert-triangle`) and `Mine` (blue fill plus badge `Mine`), and the grid marks exactly the 6 seeded exception rows without a page reload.
- `grid_repaints_after_rule_reorder` — FR-F060-06, FR-F060-07: dragging `Late` above `Mine` swaps which rule wins the fill while the badge stays; the order survives a reload.
- `stop_if_true_hides_the_third_rule` — FR-F060-07: enabling `Stop evaluating later rules` on `Late` removes the amber `Blocked` styling from rows matching all three rules.
- `view_scoped_rule_stays_in_its_view` — FR-F060-08: a rule created from the `At risk` view header paints there and is absent when the user switches to `All work`.
- `editing_a_cell_updates_the_formula_rule_state` — FR-F060-10, FR-F060-11: raising `Budget` on a row flips the `Variance > 0` rule on within one recalculation cycle and the row shows the new icon.
- `why_formatted_popover_lists_rules_in_order` — FR-F060-12, FR-F060-15: the cell context menu opens the popover listing the applied rules and the property each won.
- `icon_only_mode_drops_fills` — NFR-F060-03: switching to `Icon only` removes every fill, keeps icons and badges, and puts `signals=icon-only` in the URL after a reload.
- `viewer_sees_formatting_but_cannot_edit_rules` — FR-F060-14: a sheet-viewer sees formatted rows and the legend, and the panel shows no `New rule`.
- `hidden_column_rule_paints_nothing_for_restricted_actor` — FR-F060-13: the actor denied `Budget` sees unformatted rows for the budget rule and the popover explains the hidden input.

Evidence: Playwright traces, screenshots, and network logs under `testing/evidence/F060/e2e/`.
