# F014 accessibility cases

File: `testing/features/F014/accessibility/forms.a11y.spec.ts`. axe-core via Playwright. Flag `F014_FEATURE`.

- `builder_has_no_serious_axe_violations` — NFR-F014-03: zero `serious`/`critical` violations on the builder with 8 fields and the condition editor open.
- `public_form_has_no_serious_axe_violations` — NFR-F014-03: zero `serious`/`critical` violations on the public form at 1,280 px and 320 px.
- `every_field_has_label_and_described_error` — NFR-F014-03, FR-F014-12: each input has a visible `<label>`; an error is linked by `aria-describedby` and announced.
- `conditional_show_hide_announced` — FR-F014-03, NFR-F014-03: revealing "Budget" announces "Budget field added" through the live region.
- `palette_and_reorder_keyboard_only` — NFR-F014-03: fields inserted with `Enter` and reordered with `Alt+Arrow`; focus stays on the moved field.
- `dialogs_trap_focus_and_restore` — NFR-F014-03: publish and share dialogs trap focus and return it to the trigger.
- `accent_color_contrast_enforced` — NFR-F014-03: accent `#ffff00` rejected by the builder with a contrast message; `#1d4ed8` accepted.
- `reduced_motion_disables_reveal_animation` — NFR-F014-03: `prefers-reduced-motion` removes the field reveal transition.

Evidence: axe JSON reports under `testing/evidence/F014/accessibility/`.
