# F023 accessibility cases

File: `testing/features/F023/accessibility/dashboard.a11y.spec.ts`. axe-core via Playwright. Flag `F023_FEATURE`.

- `builder_and_viewer_have_no_serious_axe_violations` — NFR-F023-03: zero `serious`/`critical` violations with five widgets in builder and viewer.
- `each_widget_is_a_labeled_region` — NFR-F023-03: every widget frame has `role="region"` and `aria-label` from its title.
- `keyboard_move_and_resize_announced` — NFR-F023-03: arrow move and Shift+arrow resize announce column, row, width, and height.
- `palette_and_config_panel_keyboard_reachable` — NFR-F023-03: all palette items and config fields in tab order; `Escape` closes the panel and restores focus.
- `freshness_badges_have_text` — NFR-F023-03: stale, computing, denied, unavailable badges expose text, not icon-only.
- `reduced_motion_disables_drag_animation` — NFR-F023-03: `prefers-reduced-motion` removes widget transitions.

Evidence: axe JSON reports under `testing/evidence/F023/accessibility/`.
