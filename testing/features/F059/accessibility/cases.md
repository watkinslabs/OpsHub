# F059 accessibility cases

File: `testing/features/F059/accessibility/publishing.a11y.spec.ts`. axe-core via Playwright. Flag `F059_FEATURE`.

- `public_embed_dialog_have_no_serious_axe_violations` — NFR-F059-03: zero `serious`/`critical` on public dashboard, embed view, and publish dialog.
- `public_page_has_title_and_landmarks` — NFR-F059-03: document title equals publication title; `main` landmark present.
- `freshness_exposed_as_text` — NFR-F059-03: stale state readable by screen reader, not color alone.
- `publish_dialog_traps_focus_and_announces_copy` — NFR-F059-03: focus trapped; copy button announces "Copied".
- `error_states_have_headings` — NFR-F059-03: error, expired, and denied-origin states expose an `h1` with the reason.
- `reduced_motion_disables_refresh_spinner` — NFR-F059-03: `prefers-reduced-motion` removes spinner animation.

Evidence: axe JSON reports under `testing/evidence/F059/accessibility/`.
