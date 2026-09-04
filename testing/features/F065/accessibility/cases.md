# F065 accessibility cases

File: `testing/features/F065/accessibility/signup.a11y.spec.ts`. axe-core via Playwright at 320 px and 1,440 px. Flag `F065_FEATURE`.

- `public_pages_have_no_serious_violations` — NFR-F065-03: zero `serious` or `critical` violations on `/signup`, `/signup/verify-sent`, `/signup/complete/:token`, and `/signup/expired` at both widths.
- `availability_result_announced_politely` — NFR-F065-03: the slug verdict is read from a polite live region, so availability is never conveyed by the green or red border alone.
- `honeypot_outside_tab_order` — NFR-F065-03, FR-F065-04: keyboard traversal of the form never reaches `company_website`, and screen-reader output omits it.
- `errors_are_tied_to_their_inputs` — NFR-F065-03: each field error is referenced by `aria-describedby` from its input and announced on submit failure.
- `turnstile_has_accessible_fallback` — NFR-F065-03: the challenge exposes a labelled fallback control and does not trap focus.
- `focus_moves_to_success_heading` — NFR-F065-03: after submission focus lands on the `Check your email` heading rather than returning to the top of the document.
- `trial_and_suspended_notices_are_landmarks` — NFR-F065-03: the grace banner and the suspended notice are labelled regions with text, not colour, carrying the state.

Evidence: axe JSON reports per route and viewport under `testing/evidence/F065/accessibility/`.
