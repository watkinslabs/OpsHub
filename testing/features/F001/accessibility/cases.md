# F001 accessibility cases

File: `testing/features/F001/accessibility/status.a11y.spec.ts`. axe-core via Playwright on `/status`. Flag `F001_FEATURE`.

- `status_page_has_no_serious_axe_violations` — NFR-F001-03: zero `serious`/`critical` violations in ok, degraded, and unreachable states.
- `status_page_single_h1_and_landmarks` — NFR-F001-03: exactly one `h1`, a `main` landmark, and the badge inside a labelled region.
- `state_change_announced_by_live_region` — NFR-F001-03: transition ok → unreachable announces "Status: unreachable" through `aria-live="polite"`.
- `retry_moves_focus_to_badge` — NFR-F001-03: activating retry with Enter refetches and moves focus to the status badge.
- `contrast_and_focus_tokens` — NFR-F001-03: badge text contrast ≥ 4.5:1 for every state; focus ring visible on the retry button.
- `reduced_motion_disables_spinner_animation` — NFR-F001-03: `prefers-reduced-motion: reduce` removes the spinner transition.

Evidence: axe JSON reports under `testing/evidence/F001/accessibility/`.
