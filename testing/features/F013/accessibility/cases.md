# F013 accessibility cases

File: `testing/features/F013/accessibility/views.a11y.spec.ts`. axe-core via Playwright. Flag `F013_FEATURE`.

- `card_view_no_serious_axe_violations` — NFR-F013-03: zero `serious`/`critical` violations on a card view with 3 lanes and 200 rows.
- `calendar_and_timeline_no_serious_axe_violations` — NFR-F013-03: zero `serious`/`critical` violations on month calendar and week timeline.
- `lane_move_announced_by_live_region` — NFR-F013-03: keyboard move announces "Kickoff moved to Doing".
- `calendar_day_move_announced` — NFR-F013-03: ArrowRight on a focused event announces "Kickoff moved to 17 September".
- `timeline_bar_keyboard_move_and_announce` — NFR-F013-03: Space, ArrowRight, Enter on a bar moves it one zoom unit and announces the new range.
- `filter_builder_rows_keyboard_operable` — NFR-F013-03: conditions can be added, edited, and removed by keyboard; each row has a labelled remove button.
- `share_dialog_traps_focus_and_restores` — NFR-F013-03: `ShareViewDialog` traps focus and returns it to the `Share` button on close.
- `reduced_motion_disables_drag_animation` — NFR-F013-03: `prefers-reduced-motion` removes card, event, and bar transitions.

Evidence: axe JSON reports under `testing/evidence/F013/accessibility/`.
