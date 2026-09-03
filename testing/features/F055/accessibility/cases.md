# F055 accessibility cases

File: `testing/features/F055/accessibility/` (axe plus keyboard-only walkthroughs). Flag `F055_FEATURE`.

- `axe_month_week_agenda_zero_serious` — NFR-F055-03: all three layouts and the calendar list page report zero serious violations in light and dark themes.
- `event_grid_roving_tabindex` — NFR-F055-03: one tab stop enters the grid; arrows move between days and events; `Home`/`End` reach the week bounds.
- `keyboard_reschedule_path` — NFR-F055-03, FR-F055-06: `Space` picks an event, arrows move it, `Enter` commits, `Escape` cancels and restores focus to the chip.
- `source_colour_is_not_the_only_signal` — NFR-F055-03: each chip carries the source name in its accessible label and legend entries pair colour with text.
- `dialogs_trap_focus_and_announce` — FR-F055-13: source editor and publish dialogs trap focus, restore it on close, and announce results in a live region.
- `hidden_sources_notice_announced` — FR-F055-04: the notice is announced once per window change, not per event.

Evidence: axe JSON and keyboard walkthrough recordings under `testing/evidence/F055/accessibility/`.
