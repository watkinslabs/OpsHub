# F017 accessibility cases

File: `testing/features/F017/accessibility/files.a11y.spec.ts`. axe-core via Playwright. Flag `F017_FEATURE`.

- `file_tab_and_proof_panel_have_no_serious_axe_violations` — NFR-F017-03: zero `serious`/`critical` violations on the file tab with 12 cards and on the proof panel with a PDF preview.
- `drop_zone_is_keyboard_operable` — NFR-F017-03: zone has `role=button`, accessible name "Upload files", Enter and Space open the picker; hidden input is labelled.
- `upload_progress_uses_progressbar_role` — NFR-F017-03: `role=progressbar` with `aria-valuenow` updates and completion is announced.
- `scan_badge_has_text_not_only_color` — NFR-F017-03: `Scanning`, `Clean`, `Quarantined` badges carry text and icon labels; contrast ≥ 4.5:1.
- `version_drawer_traps_focus_and_restores` — NFR-F017-03: drawer traps focus, Escape closes, focus returns to the card menu.
- `decision_buttons_grouped_and_labelled` — NFR-F017-03: `role=group` labelled "Your decision"; reason textarea is associated with its error via `aria-describedby`.
- `reduced_motion_disables_progress_animation` — NFR-F017-03: `prefers-reduced-motion` removes the progress transition and thumbnail fade.

Evidence: axe JSON reports under `testing/evidence/F017/accessibility/`.
