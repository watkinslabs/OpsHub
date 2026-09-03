# F019 accessibility cases

File: `testing/features/F019/accessibility/runs.a11y.spec.ts`. axe-core via Playwright. Flag `F019_FEATURE`.

- `runs_have_no_serious_axe_violations` — NFR-F019-03: zero `serious`/`critical` violations on list with 50 runs and on a detail with 5 steps.
- `status_conveyed_by_text_and_icon` — NFR-F019-03: each badge has visible text and an `aria-label`; contrast ≥ 4.5:1.
- `dialogs_trap_focus_and_restore` — NFR-F019-03: retry and cancel dialogs trap focus and return it to the triggering button.
- `step_timeline_is_ordered_list` — NFR-F019-03: timeline renders as `<ol>` with step index and status announced.
- `status_change_announced_by_live_region` — NFR-F019-03: polling update from `running` to `completed` announces "Run completed".
- `reduced_motion_disables_status_pulse` — NFR-F019-03: `prefers-reduced-motion` removes the running-status animation.

Evidence: axe JSON reports under `testing/evidence/F019/accessibility/`.
