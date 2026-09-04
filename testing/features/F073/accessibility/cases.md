# F073 accessibility cases

File: `testing/features/F073/accessibility/announcements.a11y.spec.ts`. axe-core via Playwright. Flag `F073_FEATURE`.

- `panel_and_drawer_have_no_serious_violations` — NFR-F073-03: zero `serious` and `critical` violations on the what's-new panel with mixed severities, the interrupting modal, and the help drawer showing an article plus its contextual list.
- `severity_is_not_colour_only` — NFR-F073-03: `info`, `change` and `action_required` each carry a text label and a titled icon, so the distinction survives greyscale and a colour-vision simulation.
- `panel_returns_focus_to_bell` — NFR-F073-03: closing the panel with `Escape` or a click outside returns focus to the bell trigger, and the panel is arrow-navigable between items.
- `drawer_announces_arrival_politely` — NFR-F073-03: opening the drawer announces the article title through a polite live region without stealing focus from the underlying grid until the user tabs into it.
- `modal_is_escapable_with_reduced_motion` — NFR-F073-03: under `prefers-reduced-motion` the modal opens without animation, is closable with `Escape` and with `Later`, and imposes no time limit, meeting WCAG 2.2 AA 2.2.1.
- `modal_does_not_trap_navigation` — NFR-F073-03, FR-F073-09: with the modal open the browser back control and the application shell links remain reachable, so nothing blocks work.
- `help_content_headings_are_ordered` — NFR-F073-03: rendered article bodies produce a single `h1` and no skipped heading level, and code blocks carry an accessible name.
- `fallback_note_is_programmatically_associated` — NFR-F073-03, FR-F073-11: the `Shown in English` note is associated with the article body through `aria-describedby` rather than being visual only.

Evidence: axe JSON reports under `testing/evidence/F073/accessibility/`.
