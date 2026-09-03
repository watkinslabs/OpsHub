# F011 accessibility cases

File: `testing/features/F011/accessibility/schedule.a11y.spec.ts`. axe-core via Playwright. Flag `F011_FEATURE`.

- `settings_and_calendar_pages_have_no_serious_axe_violations` — NFR-F011-03: zero `serious`/`critical` violations on the schedule settings panel and the working-calendar admin page.
- `date_picker_keyboard_only` — NFR-F011-03: arrow keys move days, `PageDown` moves a month, `T` selects today, `Enter` commits, `Escape` cancels without a mouse.
- `snap_hint_announced_by_live_region` — NFR-F011-03: selecting a holiday announces `Moved from 2026-12-25 (Christmas)` through `aria-live="polite"`.
- `week_editor_intervals_labelled` — NFR-F011-03: every interval input has an accessible name including the weekday and start/end.
- `timezone_select_is_combobox` — NFR-F011-03: `TimezoneSelect` exposes `role="combobox"`, filters by typing, and announces the count of matches.
- `reduced_motion_disables_picker_transition` — NFR-F011-03: `prefers-reduced-motion` removes month-change animation.

Evidence: axe JSON reports under `testing/evidence/F011/accessibility/`.
