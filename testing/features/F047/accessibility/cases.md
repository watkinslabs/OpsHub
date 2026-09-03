# F047 accessibility cases

File: `testing/features/F047/accessibility/mcp.a11y.spec.ts`. axe-core via Playwright. Flag `F047_FEATURE`.

- `approvals_page_has_no_serious_axe_violations` — NFR-F047-03: zero `serious`/`critical` violations on `/admin/mcp` with pending approvals and a populated activity table.
- `call_drawer_has_no_serious_axe_violations` — NFR-F047-03: zero `serious`/`critical` violations on `/admin/mcp/audit/:eventId`.
- `diff_exposed_as_labelled_description_list` — NFR-F047-03: `ChangeSummaryDiff` renders `dl`/`dt`/`dd` with `before` and `after` labelled in text, not by colour alone.
- `countdown_announced_at_five_and_one_minute` — NFR-F047-03: the polite live region announces the remaining time once at 5 minutes and once at 1 minute and never on every tick.
- `approve_dialog_traps_and_returns_focus` — NFR-F047-03: the confirm dialog traps focus, `Escape` closes it, and focus returns to the row's `Approve` button.
- `activity_rows_are_keyboard_reachable` — NFR-F047-03: table rows are focusable, `Enter` opens the drawer, and decision and outcome carry text alongside their icons.
- `reduced_motion_disables_drawer_and_countdown_animation` — NFR-F047-03: `prefers-reduced-motion` removes the drawer slide and the countdown pulse.

Evidence: axe JSON reports under `testing/evidence/F047/accessibility/`.
