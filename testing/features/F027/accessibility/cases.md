# F027 accessibility cases

File: `testing/features/F027/accessibility/compliance.a11y.spec.ts`. axe-core via Playwright. Flag `F027_FEATURE`.

- `compliance_routes_have_no_serious_violations` — NFR-F027-03: zero `serious`/`critical` violations on retention, holds, exports, purges, and access-review routes with seeded data.
- `purge_dialog_traps_focus_and_labels_code` — NFR-F027-03: `PurgeConfirmDialog` traps focus, the code input has a visible label and `aria-describedby` for the mismatch error, `Escape` returns focus to `Confirm purge`.
- `progress_bars_expose_values` — NFR-F027-03: `ExportProgress` bars have `role="progressbar"` with `aria-valuenow`, `aria-valuemin`, `aria-valuemax`, and a kind label.
- `flag_reasons_readable_without_color` — NFR-F027-03: flagged rows carry a text reason and an icon with an accessible label, not color alone.
- `tables_keyboard_navigable` — NFR-F027-03: all five tables and row actions reachable by tab and arrow keys; focus ring visible.
- `reduced_motion_disables_progress_animation` — NFR-F027-03: `prefers-reduced-motion` removes the progress transition.

Evidence: axe JSON reports under `testing/evidence/F027/accessibility/`.
