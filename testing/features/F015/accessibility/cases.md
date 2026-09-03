# F015 accessibility cases

File: `testing/features/F015/accessibility/templates.a11y.spec.ts`. axe-core via Playwright. Flag `F015_FEATURE`.

- `template_pages_have_no_serious_axe_violations` — NFR-F015-03: zero `serious`/`critical` violations on catalog, template detail, provision dialog, run status, baseline list, and variance panel.
- `provision_dialog_traps_focus_and_restores` — NFR-F015-03: focus stays inside the dialog and returns to `Provision` on close.
- `step_progress_announced_by_live_region` — NFR-F015-03: `aria-live="polite"` announces each step completion and the final `Project provisioned`.
- `variance_table_keyboard_navigation` — NFR-F015-03: arrow keys move between rows and columns; `Enter` opens the row; header cells expose sort state.
- `variance_status_chips_carry_text` — NFR-F015-03: `Slipped +3d`, `Early -1d`, `Added`, `Removed` are readable text with 4.5:1 contrast, not colour alone.
- `catalog_cards_have_accessible_names` — NFR-F015-03: each card is a link named by template name and category; category filter is a labelled group of toggle buttons.
- `reduced_motion_disables_progress_animation` — NFR-F015-03: `prefers-reduced-motion` removes the step progress transition.

Evidence: axe JSON reports under `testing/evidence/F015/accessibility/`.
