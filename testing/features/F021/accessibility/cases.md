# F021 accessibility cases

File: `testing/features/F021/accessibility/report.a11y.spec.ts`. axe-core via Playwright. Flag `F021_FEATURE`.

- `editor_and_viewer_have_no_serious_axe_violations` — NFR-F021-03: zero `serious`/`critical` violations on editor with 3 sources and viewer with 120 rows.
- `join_and_filter_builders_keyboard_operable` — NFR-F021-03: every add, edit, remove, and reorder control reachable and operable by keyboard.
- `stale_and_computing_announced` — NFR-F021-03: transitions to computing, succeeded, and stale are announced through the live region.
- `group_headers_expose_expanded_state` — NFR-F021-03: header rows carry `aria-expanded` and toggle with `Space`.
- `restricted_bar_is_a_status_region` — NFR-F021-03: restricted-sources bar uses `role="status"` and is read once.
- `reduced_motion_disables_skeleton_shimmer` — NFR-F021-03: `prefers-reduced-motion` removes shimmer animation.

Evidence: axe JSON reports under `testing/evidence/F021/accessibility/`.
