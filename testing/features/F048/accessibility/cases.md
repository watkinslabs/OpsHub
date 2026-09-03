# F048 accessibility cases

File: `testing/features/F048/accessibility/entitlements.a11y.spec.ts`. axe-core via Playwright. Flag `F048_FEATURE`.

- `admin_pages_have_no_serious_axe_violations` — NFR-F048-03: zero `serious`/`critical` violations on `/admin/entitlements` and `/admin/feature-flags` with the seeded registry.
- `kill_dialog_traps_focus_and_requires_key` — NFR-F048-03: kill dialog traps focus, typed-key input is labelled, confirm is announced as disabled until the key matches, focus returns to the flag row on close.
- `rollout_state_badges_have_text` — NFR-F048-03: each badge (`draft`, `internal`, `percentage`, `tenant_list`, `general`, `retired`) exposes its state as text, not color alone.
- `drawer_keyboard_operable` — NFR-F048-03: `Enter` on a row opens the drawer, `Tab` cycles inside it, `Escape` closes without saving and restores focus.
- `locked_fields_announce_reason` — FR-F048-04: read-only platform fields expose `aria-describedby` text `Platform operators only`.
- `reduced_motion_disables_drawer_transition` — NFR-F048-03: `prefers-reduced-motion` removes the drawer slide animation.

Evidence: axe JSON reports under `testing/evidence/F048/accessibility/`.
