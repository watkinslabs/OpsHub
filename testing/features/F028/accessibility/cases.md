# F028 accessibility cases

File: `testing/features/F028/accessibility/developer.a11y.spec.ts`. axe-core via Playwright. Flag `F028_FEATURE`.

- `developer_routes_have_no_serious_violations` — NFR-F028-03: zero `serious`/`critical` violations on applications, webhooks, delivery log, and reference routes with seeded data.
- `secret_and_token_dialogs_trap_focus` — NFR-F028-03: reveal dialogs trap focus, `Escape` closes, focus returns to the trigger, copy announces "Copied".
- `delivery_status_not_color_only` — NFR-F028-03: `succeeded`, `failed`, `exhausted`, `disabled` rows carry text and a labelled icon.
- `delivery_drawer_keyboard_operable` — NFR-F028-03: open drawer with Enter, navigate attempts table, activate `Replay`, close with `Escape`.
- `reference_page_headings_and_landmarks` — NFR-F028-03: operation groups use heading levels in order and a navigation landmark.
- `reduced_motion_disables_drawer_slide` — NFR-F028-03: `prefers-reduced-motion` removes the drawer transition.

Evidence: axe JSON reports under `testing/evidence/F028/accessibility/`.
