# F033 accessibility cases

File: `testing/features/F033/accessibility/resources.a11y.spec.ts`. axe-core via Playwright. Flag `F033_FEATURE`.

- `planner_has_no_serious_axe_violations` — NFR-F033-03: zero `serious`/`critical` violations on directory, profile, and planner with 50 resources.
- `capacity_meters_expose_values` — NFR-F033-03: each period `meter` has `aria-valuenow`, `aria-valuemax`, and a label naming the week.
- `over_allocation_not_color_only` — NFR-F033-03: over-allocated cells include text `Over by N h` and an icon with accessible name.
- `planner_grid_keyboard_pattern` — NFR-F033-03: `role="grid"` with arrow-key cell movement, `Enter` opens dialog, `Delete` prompts removal; focus ring visible.
- `dialogs_trap_focus_and_restore` — NFR-F033-03: resource, allocation, and deactivate dialogs trap focus and return it to the trigger.
- `availability_editor_labels_and_errors` — NFR-F033-03: date inputs have labels; overlap errors are associated by `aria-describedby`.
- `reduced_motion_disables_bar_transitions` — NFR-F033-03: `prefers-reduced-motion` removes allocation bar animation.

Evidence: axe JSON reports under `testing/evidence/F033/accessibility/`.
