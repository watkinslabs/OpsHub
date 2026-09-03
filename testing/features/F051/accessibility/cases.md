# F051 accessibility cases

File: `testing/features/F051/accessibility/workapp.a11y.spec.ts`. axe-core via Playwright. Flag `F051_FEATURE`.

- `shell_and_builder_no_serious_axe_violations` — NFR-F051-03: zero `serious`/`critical` violations on `/apps/vendor-onboarding`, each page kind, and the builder tabs.
- `nav_is_labelled_with_current_page` — NFR-F051-03: `nav` has `aria-label` with the app name; the active item has `aria-current="page"`; arrow keys move focus between items.
- `keyboard_page_reorder_announced` — NFR-F051-03: `Alt+ArrowDown` in the page list announces `Intake form moved to position 2` through a live region.
- `role_preview_switch_announced` — NFR-F051-03: choosing `Preview as Vendor` announces the change and updates the visible page count.
- `publish_dialog_traps_focus_and_restores` — NFR-F051-03: publish dialog traps focus, note field is labelled, focus returns to the publish button on close.
- `denied_frame_has_heading_and_contrast` — FR-F051-06: denied page frame exposes an `h2`, contrast ≥ 4.5:1, and no focus loss.
- `nav_drawer_reduced_motion` — NFR-F051-03: under 960 px with `prefers-reduced-motion` the drawer opens without transition and traps focus.

Evidence: axe JSON reports under `testing/evidence/F051/accessibility/`.
