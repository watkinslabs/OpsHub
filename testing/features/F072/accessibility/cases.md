# F072 accessibility cases

File: `testing/features/F072/accessibility/inbound_email.a11y.spec.ts`. axe-core via Playwright. Flag `F072_FEATURE`.

- `routes_have_no_serious_violations` — NFR-F072-03: zero `serious` or `critical` violations on `/sheets/:sheetId/settings/inbound-email` and `/admin/inbound-email` with a log holding an accepted, a rejected and a quarantined message.
- `disposition_not_colour_only` — NFR-F072-03: `Accepted`, `Rejected` and `Quarantined` rows each carry text and a labelled icon, and the contrast of every state chip meets WCAG 2.2 AA in both themes.
- `auth_results_announced_as_text` — NFR-F072-03: SPF, DKIM and DMARC results are read by a screen reader as `SPF pass, DKIM pass, DMARC fail`, not as unlabelled marks.
- `copy_control_announces_and_is_a_button` — FR-F072-17: the address copy control is a real button, reachable by keyboard, and its success is announced through a polite live region.
- `log_table_is_keyboard_operable` — NFR-F072-03: arrow keys move the row focus, `Enter` opens the message drawer, and the header sort controls are reachable and labelled.
- `drawer_traps_and_restores_focus` — NFR-F072-03: the message drawer traps focus while open and returns it to the originating row on close.
- `dialogs_label_policy_and_mapping_groups` — FR-F072-06, FR-F072-11: the sender policy radio group and the mapping editor have group labels with per-option descriptions through `aria-describedby`.
- `reduced_motion_disables_drawer_transition` — NFR-F072-03: `prefers-reduced-motion` removes the drawer slide and the log row highlight animation.

Evidence: axe JSON reports under `testing/evidence/F072/accessibility/`.
