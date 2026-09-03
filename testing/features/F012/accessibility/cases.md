# F012 accessibility cases

File: `testing/features/F012/accessibility/gantt.a11y.spec.ts`. axe-core via Playwright. Flag `F012_FEATURE`.

- `gantt_has_no_serious_axe_violations` — NFR-F012-03: zero `serious`/`critical` violations with 12 rows, critical toggle on and off.
- `bars_and_arrows_keyboard_reachable` — NFR-F012-03: every bar, diamond, summary bar, and arrow is in the tab order with a label such as "Build, Mon 7 Sep to Tue 8 Sep, 2 predecessors".
- `shift_announced_by_live_region` — NFR-F012-03: committed shift announces "Shifted 15 rows"; cycle rejection announces the cycle path.
- `dialogs_trap_focus_and_restore` — NFR-F012-03: dependency and shift dialogs trap focus and return it to the originating bar.
- `critical_bars_meet_contrast` — NFR-F012-03: critical bar fill and label contrast ≥ 4.5:1 against the timeline background; critical state is not colour-only (pattern plus label).
- `reduced_motion_disables_bar_animation` — NFR-F012-03: `prefers-reduced-motion` removes bar and arrow transitions during shift.

Evidence: axe JSON reports under `testing/evidence/F012/accessibility/`.
