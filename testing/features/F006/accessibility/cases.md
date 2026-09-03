# F006 accessibility cases

File: `testing/features/F006/accessibility/sheet.a11y.spec.ts`. axe-core via Playwright. Flag `F006_FEATURE`.

- `grid_and_board_have_no_serious_axe_violations` — NFR-F006-03: zero `serious`/`critical` violations on grid and board with 50 rows.
- `dialogs_trap_focus_and_restore` — NFR-F006-03: new-sheet and restore dialogs trap focus and return it to the trigger.
- `lane_move_announced_by_live_region` — NFR-F006-03: moving a card announces "Kickoff moved to Doing".
- `all_actions_keyboard_reachable` — NFR-F006-03: tab order covers header, mode switch, add row, each row, each card.
- `contrast_and_focus_tokens` — NFR-F006-03: focus ring visible on every interactive element; text contrast ≥ 4.5:1.
- `reduced_motion_disables_drag_animation` — NFR-F006-03: `prefers-reduced-motion` removes card transition.

Evidence: axe JSON reports under `testing/evidence/F006/accessibility/`.
