# F054 accessibility cases

File: `testing/features/F054/accessibility/bridge.a11y.spec.ts`. axe-core via Playwright. Flag `F054_FEATURE`.

- `builder_and_console_have_no_serious_axe_violations` — NFR-F054-03: zero `serious`/`critical` violations on the flow builder with 5 steps and the console with a 5-step run.
- `step_timeline_keyboard_navigable` — NFR-F054-03: arrow keys move focus across steps, `Enter` expands the payload viewer, `Escape` collapses and restores focus.
- `run_status_announced_by_live_region` — NFR-F054-03: polite live region announces `Run succeeded` and `Step 4 failed` without stealing focus.
- `step_status_uses_text_not_color` — NFR-F054-03: each step badge exposes `succeeded`, `failed`, `waiting`, `cancelled` as text.
- `step_forms_have_labels_and_errors_linked` — FR-F054-15: every form field has a label; validation errors linked with `aria-describedby`.
- `reordering_steps_with_keyboard` — FR-F054-15: `Alt+ArrowUp/Down` reorders a step and announces the new position.
- `reduced_motion_disables_timeline_animation` — NFR-F054-03: `prefers-reduced-motion` removes step transition animations.

Evidence: axe JSON reports under `testing/evidence/F054/accessibility/`.
