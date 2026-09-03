# F056 accessibility cases

File: `testing/features/F056/accessibility/pivot.a11y.spec.ts`. axe-core via Playwright. Flag `F056_FEATURE`.

- `builder_and_grid_have_no_serious_axe_violations` — NFR-F056-03: zero `serious`/`critical` on builder, grid with 200 cells, and output history.
- `dimension_chips_keyboard_operable` — NFR-F056-03: add, remove, and reorder chips without a mouse; focus returns to the list after removal.
- `status_chip_changes_announced` — NFR-F056-03: live region announces "Output succeeded" and "Output failed: timeout".
- `pivot_grid_has_table_semantics` — NFR-F056-03: grid exposes row and column headers; frozen column keeps header association.
- `materialize_dialog_traps_focus` — NFR-F056-03: dialog traps focus and returns it to the `Materialize` button.
- `reduced_motion_disables_chip_animation` — NFR-F056-03: `prefers-reduced-motion` removes the status chip transition.

Evidence: axe JSON reports under `testing/evidence/F056/accessibility/`.
