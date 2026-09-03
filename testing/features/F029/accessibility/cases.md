# F029 accessibility cases

File: `testing/features/F029/accessibility/integrations.a11y.spec.ts`. axe-core via Playwright. Flag `F029_FEATURE`.

- `integrations_routes_have_no_serious_violations` — NFR-F029-03: zero `serious`/`critical` violations on `/admin/integrations` and a connection detail with conflicts and call log.
- `popup_handoff_returns_focus_and_announces` — NFR-F029-03: after the consent popup closes, focus returns to `Connect` and a polite live region announces the result.
- `connection_status_not_color_only` — NFR-F029-03: `active`, `limited`, `needs_reauth`, `revoked` rows carry text and a labelled icon.
- `binding_dialog_traps_focus_and_labels_policy` — NFR-F029-03: dialog traps focus; the conflict policy radio group has a group label and per-option descriptions via `aria-describedby`.
- `notify_test_result_announced` — NFR-F029-03: `Delivered` or error result announced through a live region.
- `reduced_motion_disables_status_transition` — NFR-F029-03: `prefers-reduced-motion` removes the status badge animation.

Evidence: axe JSON reports under `testing/evidence/F029/accessibility/`.
