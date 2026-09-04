# F071 accessibility cases

File: `testing/features/F071/accessibility/migration.a11y.spec.ts`. axe-core via Playwright, both themes and both densities. Flag `F071_FEATURE`.

- `migration_routes_have_no_serious_violations` — NFR-F071-03: zero `serious` and `critical` violations on the list route, the review route with 12 tabs and 40 issues, and the commit progress state.
- `review_table_has_real_headers_and_labelled_selects` — NFR-F071-03: the column review table exposes column headers and every type select is labelled by its source header rather than by position.
- `confidence_is_text_and_icon_not_colour_alone` — NFR-F071-03: `High`, `Medium`, and `Low` carry text and a titled icon; a monochrome render keeps the meaning.
- `issue_groups_are_headings_with_counts` — NFR-F071-03: `Blocking`, `Warning`, and `Information` are headings with counts and each group is reachable by heading navigation.
- `commit_progress_announced_through_live_region` — NFR-F071-03: each tab reaching `committed` is announced once through a polite region, and completion is announced with the sheet count.
- `override_and_waive_are_keyboard_reachable` — NFR-F071-03: `Tab` reaches every type select and waive action, `Enter` waives the focused issue, `Escape` closes the issues sheet, and focus returns to the trigger.
- `confirm_dialog_traps_focus_and_is_described` — NFR-F071-03: the commit dialog traps focus and its body is referenced by `aria-describedby`.
- `reduced_motion_disables_progress_animation` — NFR-F071-03: `prefers-reduced-motion` removes the per-tab progress transition without removing the announcement.

Evidence: axe JSON reports per theme under `testing/evidence/F071/accessibility/`.
