# F009 accessibility cases

File: `testing/features/F009/accessibility/links.a11y.spec.ts`. axe-core via Playwright. Flag `F009_FEATURE`.

- `treegrid_has_no_serious_axe_violations` — NFR-F009-03: zero `serious`/`critical` violations on the 3-level `Plan` tree with linked and rolled-up cells.
- `rows_expose_level_expanded_setsize` — NFR-F009-03: every row has `aria-level`, parents have `aria-expanded`, siblings share `aria-setsize` and `aria-posinset`.
- `level_change_is_announced` — NFR-F009-03: indent announces "Design moved to level 2 under Phase 1"; outdent announces the new level.
- `broken_link_is_announced` — FR-F009-12, NFR-F009-03: broken chip has an accessible name "Acme, broken link, target row deleted".
- `link_picker_is_a_combobox_with_focus_trap` — NFR-F009-03: picker uses the combobox pattern, traps focus, and returns focus to the cell on close.
- `rollup_editor_labels_and_errors` — NFR-F009-03: every control labelled; validation errors linked by `aria-describedby`.
- `rolled_up_cell_exposes_readonly_reason` — FR-F009-08: rolled-up cell has `aria-readonly` and description "Computed from children".
- `contrast_and_focus_tokens` — NFR-F009-03: focus ring visible on rows, chips, and controls; broken badge contrast ≥ 4.5:1.
- `reduced_motion_disables_expand_animation` — NFR-F009-03: `prefers-reduced-motion` removes subtree expand transition.

Evidence: axe JSON reports under `testing/evidence/F009/accessibility/`.
