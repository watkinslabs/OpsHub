# F007 accessibility cases

File: `testing/features/F007/accessibility/columns.a11y.spec.ts`. axe-core via Playwright. Flag `F007_FEATURE`.

- `drawer_and_menu_have_no_serious_axe_violations` — NFR-F007-03: zero `serious`/`critical` violations with the drawer open on a `select` column and the header menu open.
- `drawer_traps_focus_and_restores` — NFR-F007-03: focus cycles inside the drawer; `Escape` returns focus to the header that opened it.
- `header_menu_keyboard_operable` — NFR-F007-03: `Enter` opens the menu, arrows move, `Escape` closes; `Alt+ArrowLeft/Right` reorders and a live region announces `Status moved before Owner`.
- `validation_icon_described_for_screen_readers` — FR-F007-17, NFR-F007-03: icon has an accessible name `Invalid: value does not match pattern` via `aria-describedby`.
- `type_picker_icons_have_labels` — NFR-F007-03: every type option exposes text plus icon with `aria-hidden` on the SVG.
- `contrast_and_focus_tokens` — NFR-F007-03: option color chips carry text labels; focus ring visible on every control; contrast ≥ 4.5:1.
- `reduced_motion_disables_drawer_transition` — NFR-F007-03: `prefers-reduced-motion` removes the drawer slide animation.

Evidence: axe JSON reports under `testing/evidence/F007/accessibility/`.
