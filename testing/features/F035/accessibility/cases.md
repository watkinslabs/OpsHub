# F035 accessibility cases

File: `testing/features/F035/accessibility/formula.a11y.spec.ts`. axe-core via Playwright. Flag `F035_FEATURE`.

- `editor_and_badges_have_no_serious_axe_violations` — NFR-F035-03: zero `serious`/`critical` violations with the editor open and 50 cells showing mixed error badges.
- `autocomplete_follows_combobox_pattern` — NFR-F035-03: textbox has `role=combobox`, `aria-expanded`, `aria-activedescendant`; listbox options are reachable by arrows.
- `parse_error_announced_via_describedby` — NFR-F035-03: live region announces "Expected ) at position 6" when the error appears.
- `error_badge_has_accessible_name` — NFR-F035-03: each badge exposes "Formula error: type mismatch" and opens the popover with `Enter`.
- `graph_panel_keyboard_and_contrast` — NFR-F035-03: nodes and edges are keyboard reachable; error color contrast ≥ 4.5:1 against cell background.
- `reduced_motion_disables_shimmer` — NFR-F035-03: `prefers-reduced-motion` replaces the pending shimmer with a static badge.

Evidence: axe JSON reports under `testing/evidence/F035/accessibility/`.
