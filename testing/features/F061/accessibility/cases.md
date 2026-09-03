# F061 accessibility cases

File: `testing/features/F061/accessibility/update_requests.a11y.spec.ts`. axe-core via Playwright. Flag `F061_FEATURE`.

- `public_form_has_no_serious_violations_at_320px` — NFR-F061-03: zero `serious`/`critical` violations on `/public/update-requests/{token}` with 12 row cards at 320 px width.
- `requester_surfaces_have_no_serious_violations` — NFR-F061-03: zero `serious`/`critical` violations on the request dialog, `/w/{workspace_id}/update-requests`, and the detail drawer.
- `public_form_completable_by_keyboard` — NFR-F061-03: tab order walks each row `fieldset` in document order, `Ctrl+Enter` submits, and no control is reachable only by pointer.
- `row_cards_use_fieldset_and_legend` — NFR-F061-03: each row card is a `fieldset` whose `legend` carries the row label, and every field has a visible `<label>`.
- `field_errors_wired_to_inputs` — FR-F061-05: a rejected value sets `aria-invalid` and links the message through `aria-describedby`.
- `draft_and_submit_announced` — FR-F061-07: `Draft saved` and `36 cells updated` are announced through a polite live region without moving focus.
- `conflict_panel_moves_focus_and_labels_choice` — FR-F061-08: the conflict panel receives focus, names each stale row, and labels the `Use current` control with the row label.
- `terminal_screens_not_colour_only` — FR-F061-09, FR-F061-12: expired, cancelled, and completed screens carry text plus a labelled icon and a 4.5:1 contrast ratio.
- `recipient_status_not_colour_only` — FR-F061-13: `pending`, `opened`, `partial`, `completed`, and `revoked` rows carry text alongside their icon.
- `reduced_motion_disables_progress_animation` — NFR-F061-03: `prefers-reduced-motion` removes the sticky progress bar animation.

Evidence: axe JSON reports under `testing/evidence/F061/accessibility/`.
