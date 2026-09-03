# F031 accessibility cases

File: `testing/features/F031/accessibility/portfolio.a11y.spec.ts`. axe-core via Playwright. Flag `F031_FEATURE`.

- `rollup_page_has_no_serious_axe_violations` — NFR-F031-03: zero `serious`/`critical` violations on list and rollup pages with 50 projects.
- `rollup_table_uses_headers_and_sort_buttons` — NFR-F031-03: `<table>` has `<th scope="col">` per measure and sortable headers are buttons with `aria-sort`.
- `refresh_completion_announced` — NFR-F031-03: live region announces "Rollup refreshed at {time}" after the poll completes.
- `stale_and_missing_states_not_color_only` — NFR-F031-03: stale badge and missing cells carry text and icon labels, not only color.
- `keyboard_navigates_table_and_triggers_refresh` — NFR-F031-03: arrow keys move cells, `Enter` opens drill link, `R` triggers refresh for admin; focus ring visible.
- `dialogs_trap_focus_and_restore` — NFR-F031-03: new-portfolio dialog and project picker trap focus and return it to the trigger.
- `reduced_motion_disables_refresh_spinner_animation` — NFR-F031-03: `prefers-reduced-motion` replaces the spinner with static text.

Evidence: axe JSON reports under `testing/evidence/F031/accessibility/`.
