# F058 accessibility cases

File: `testing/features/F058/accessibility/mobile.a11y.spec.ts`. axe-core via Playwright at 360 px. Flag `F058_FEATURE`.

- `mobile_pages_have_no_serious_axe_violations` — NFR-F058-03: zero `serious`/`critical` on home, grid, row detail, form, queue, and conflict card.
- `grid_and_detail_touch_targets_44px` — NFR-F058-03: every interactive element measures at least 44×44 px.
- `offline_state_announced` — NFR-F058-03: going offline announces "Offline, changes will sync" through the live region.
- `conflict_card_receives_focus` — NFR-F058-03: a new conflict card moves focus to its heading and both actions are labelled.
- `bottom_nav_keyboard_reachable` — NFR-F058-03: external keyboard tabs through Home, Sheets, Forms, Inbox with visible focus.
- `reduced_motion_disables_badge_animation` — NFR-F058-03: `prefers-reduced-motion` removes queue badge pulse.

Evidence: axe JSON reports under `testing/evidence/F058/accessibility/`.
