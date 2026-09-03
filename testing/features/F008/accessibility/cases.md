# F008 accessibility cases

File: `testing/features/F008/accessibility/grid.a11y.spec.ts`. axe-core via Playwright. Flag `F008_FEATURE`.

- `grid_has_no_serious_axe_violations` — NFR-F008-03: zero `serious`/`critical` violations on the editable grid with 500 rows and 12 columns, editor open and closed.
- `grid_roles_and_indices_correct` — NFR-F008-03: `role="grid"`, `aria-rowcount=100000`, virtualized rows carry `aria-rowindex` and cells `aria-colindex`.
- `keyboard_only_edit_paste_undo` — NFR-F008-03: no mouse; arrows, F2, type, Enter, Shift+Arrow, Ctrl+V, Ctrl+Z complete an edit cycle.
- `live_region_announces_results` — NFR-F008-03: paste announces "119 cells updated, 1 invalid"; undo announces "Undid 120 cells".
- `conflict_outline_has_text_and_focus` — NFR-F008-03: conflict cell exposes "Changed by Ada Lovelace" to screen readers and `Reload` is focusable.
- `dialogs_and_popovers_trap_and_restore_focus` — NFR-F008-03: bulk edit dialog and history popover trap focus and return it to the origin cell.
- `contrast_focus_and_reduced_motion` — NFR-F008-03: focus ring visible on cells and handles; contrast ≥ 4.5:1 including invalid and conflict states; `prefers-reduced-motion` removes fill and scroll animation.

Evidence: axe JSON reports under `testing/evidence/F008/accessibility/`.
