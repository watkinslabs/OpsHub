# F038 accessibility cases

File: `testing/features/F038/accessibility/auth.a11y.spec.ts`. axe-core via Playwright. Flag `F038_FEATURE`.

- `login_page_keyboard_and_axe` — NFR-F038-03: zero `serious`/`critical` on `/login`; slug field, submit, and help link reachable by `Tab`.
- `security_settings_no_serious_axe_violations` — NFR-F038-03: `/settings/security` with 3 sessions, 2 factors, 2 tokens passes axe.
- `totp_dialog_qr_has_text_alternative` — NFR-F038-03: QR has descriptive `alt`; secret is selectable text; six-digit cells have labels `Digit 1` to `Digit 6`.
- `callback_and_error_states_announced` — NFR-F038-03: `Signing you in` and error reasons are announced through `aria-live`.
- `dialogs_trap_focus_and_restore` — NFR-F038-03: revoke, remove-factor, and create-token dialogs trap focus and return it on `Escape`.
- `token_reveal_panel_copy_button_labelled` — NFR-F038-03: copy button has `aria-label` `Copy API token` and confirms via live region.
- `reduced_motion_disables_interstitial_transition` — NFR-F038-03: `prefers-reduced-motion` removes the interstitial slide.

Evidence: axe JSON reports under `testing/evidence/F038/accessibility/`.
