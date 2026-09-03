# F052 accessibility cases

File: `testing/features/F052/accessibility/data_shuttle.a11y.spec.ts`. axe-core via Playwright. Flag `F052_FEATURE`.

- `pages_have_no_serious_axe_violations` — NFR-F052-03: zero `serious`/`critical` violations on the flow list, editor with a 20-row preview, run history, and open run drawer.
- `mapping_table_keyboard_operable` — NFR-F052-03: arrow keys move between mapping rows, `Enter` opens the column picker, each row is labelled by its source column name.
- `run_status_has_text_and_icon` — NFR-F052-03: `queued`, `running`, `succeeded`, `partial`, `failed` badges expose the state as text, not color alone.
- `run_drawer_traps_focus_and_restores` — NFR-F052-03: drawer traps focus, `Escape` closes it, focus returns to the run row.
- `replay_confirm_dialog_labelled` — FR-F052-09: replay dialog has an accessible name, describes the source run, and confirm is reachable by keyboard.
- `reduced_motion_disables_polling_animation` — NFR-F052-03: `prefers-reduced-motion` removes the running-state spinner animation.

Evidence: axe JSON reports under `testing/evidence/F052/accessibility/`.
