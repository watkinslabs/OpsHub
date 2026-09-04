# F063 accessibility cases

File: `testing/features/F063/accessibility/entra.a11y.spec.ts`. axe-core via Playwright. Flag `F063_FEATURE`.

- `admin_entra_has_no_serious_violations` — NFR-F063-03: zero `serious`/`critical` violations on `/admin/entra` in `disconnected`, `needs_consent`, `active` and `error` states with the mapping table populated.
- `login_page_with_microsoft_button_has_no_serious_violations` — NFR-F063-03: zero `serious`/`critical` violations on `/login` while `Sign in with Microsoft` is rendered beside password and SAML.
- `microsoft_button_has_text_label_and_keyboard_path` — NFR-F063-03: the button carries a visible text label, not an icon alone, and is reachable and activatable by keyboard in the login method order.
- `connection_status_not_color_only` — NFR-F063-03: `disconnected`, `active`, `needs_consent` and `error` each render text plus a labelled icon.
- `test_result_announced_once` — NFR-F063-03: the `Test connection` result reaches a polite live region a single time, not once per field.
- `capability_switches_reachable_in_order` — NFR-F063-03: `Sign in`, `Group sync` and `Mail` switches take focus in visual order with their consent hints tied by `aria-describedby`.
- `disconnect_dialog_traps_and_returns_focus` — NFR-F063-03: the confirmation traps focus and returns it to `Disconnect` on close.
- `group_map_table_scroll_container_is_focusable` — NFR-F063-03: the mapping table's own scroll container is keyboard scrollable and labelled.

Evidence: axe JSON reports under `testing/evidence/F063/accessibility/`.
