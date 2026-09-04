# F069 accessibility cases

File: `testing/features/F069/accessibility/home.a11y.spec.ts`. axe-core via Playwright. Flag `F069_FEATURE`.

- `home_has_no_serious_violations_in_both_themes` — NFR-F069-03: zero serious or critical violations on `/` in light and dark and in both densities, with a full payload, a degraded section and the first-run panel.
- `sections_are_labelled_regions_with_headings` — NFR-F069-03: each section is a `section` landmark with an `h2` whose text matches the section title, so heading navigation reaches all five.
- `favourite_toggle_state_not_colour_only` — NFR-F069-03: the toggle exposes its pressed state to the accessibility tree and carries an accessible name naming the target and the resulting action, with no reliance on fill or hue.
- `empty_state_announced_once` — NFR-F069-03: the first-run panel is announced a single time on load, not once per section.
- `degraded_section_retry_is_reachable` — NFR-F069-03: the retry control is in the tab sequence with a visible `:focus-visible` ring and its error text is associated with the section.
- `reading_order_matches_tab_order_at_every_breakpoint` — NFR-F069-03: at 1,440, 1,024 and 640 px the DOM order and the tab order match the visual order.

Evidence: axe JSON reports under `testing/evidence/F069/accessibility/`.
