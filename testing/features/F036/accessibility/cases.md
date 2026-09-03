# F036 accessibility cases

File: `testing/features/F036/accessibility/sharing.a11y.spec.ts`. axe-core via Playwright. Flag `F036_FEATURE`.

- `share_dialog_and_landing_have_no_serious_axe_violations` — NFR-F036-03: zero `serious`/`critical` violations on the share dialog with 12 grants and 3 links and on the public landing page.
- `share_dialog_traps_focus_and_restores` — NFR-F036-03: `role=dialog` with `aria-labelledby`; Tab cycles inside; Escape closes and focus returns to the `Share` button.
- `role_select_is_keyboard_operable` — NFR-F036-03: native `select` labelled with the person's name; arrow keys change the value and the change is announced.
- `copy_link_announced_by_live_region` — NFR-F036-03: `Copy link` is a `button`; success announces `Link copied` via `aria-live=polite`; revoke announces `Link revoked`.
- `deny_and_inherited_states_not_color_only` — NFR-F036-03: deny rows show the `Ban` icon with text `Denied`; inherited rows show text `Inherited from Ops`; contrast ≥ 4.5:1.
- `landing_page_expiry_banner_is_status` — NFR-F036-03: `role=status` banner reads `This link expires in 14 days`; not-found page has an `h1` and a labelled `Request access` link.
- `reduced_motion_disables_dialog_transition` — NFR-F036-03: `prefers-reduced-motion` removes the dialog slide animation.

Evidence: axe JSON reports under `testing/evidence/F036/accessibility/`.
