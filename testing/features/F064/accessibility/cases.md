# F064 accessibility cases

File: `testing/features/F064/accessibility/billing.a11y.spec.ts`. axe-core via Playwright. Flag `F064_FEATURE`.

- `billing_routes_have_no_serious_violations` — NFR-F064-03: zero `serious` and `critical` violations on `/admin/billing`, `/admin/billing/invoices`, and `/admin/billing/usage` with a dunning banner present.
- `plan_change_and_cancel_dialogs_pass_axe` — NFR-F064-03: both dialogs trap focus, are labelled, return focus to the invoking button, and report zero serious violations.
- `proration_preview_is_a_described_table` — NFR-F064-03: the preview is a table with row and column headers and a caption, readable without color, and its values are announced when the preview loads.
- `subscription_status_not_color_only` — NFR-F064-03: `trialing`, `active`, `past_due`, `restricted`, `suspended`, and `canceled` each carry text plus a labelled icon.
- `dunning_banner_is_a_polite_live_region` — NFR-F064-03: the banner announces the stage, the consequence, and the date of the next step once, without stealing focus.
- `usage_bars_have_text_equivalents` — NFR-F064-03: every usage bar exposes its value and allowance as text, and the corrected row's original, adjustment, and reason are reachable by keyboard.
- `reduced_motion_disables_usage_animation` — NFR-F064-03: `prefers-reduced-motion` removes the usage bar and status badge transitions.
- `confirmation_requires_explicit_activation` — NFR-F064-03: selecting a plan never commits on change; the confirm button is the only commit path and is reachable by keyboard alone.

Evidence: axe JSON reports under `testing/evidence/F064/accessibility/`.
