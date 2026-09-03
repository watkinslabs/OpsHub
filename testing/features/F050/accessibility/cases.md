# F050 accessibility cases

File: `testing/features/F050/accessibility/dynamic_view.a11y.spec.ts`. axe-core via Playwright. Flag `F050_FEATURE`.

- `grid_editor_dialog_no_serious_axe_violations` — NFR-F050-03: zero `serious`/`critical` violations on the restricted grid, policy editor, audience panel, public link dialog, and public view page.
- `editable_and_locked_cells_announced` — NFR-F050-03: screen reader text for `Vendor status` cells says `editable`; `Due` cells say `read only`; lock icon has an accessible label.
- `policy_editor_keyboard_operable` — NFR-F050-03: predicate builder, field picker checkboxes, and edit mode radios are reachable and operable with keyboard only; `Escape` cancels an open predicate row.
- `public_link_dialog_traps_focus_and_restores` — NFR-F050-03: dialog traps focus, the copied-link status is announced by a live region, focus returns to `Audience` tab trigger on close.
- `inactive_link_page_has_heading_and_no_focus_loss` — FR-F050-13: `/dv/{revoked}` page has an `h1`, focus lands on the main content, and contrast ≥ 4.5:1.
- `reduced_motion_disables_cell_save_animation` — NFR-F050-03: `prefers-reduced-motion` removes the cell save flash transition.

Evidence: axe JSON reports under `testing/evidence/F050/accessibility/`.
