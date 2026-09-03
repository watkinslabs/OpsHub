# F002 accessibility cases

File: `testing/features/F002/accessibility/admin.a11y.spec.ts`. axe-core via Playwright. Flag `F002_FEATURE`.

- `admin_pages_have_no_serious_axe_violations` — NFR-F002-03: zero `serious`/`critical` on `/admin/tenant`, `/admin/users`, `/admin/groups/{id}` with 50 users.
- `dialogs_trap_focus_and_restore` — NFR-F002-03: invite, deactivate, and suspend dialogs trap focus and return it to the trigger on `Escape`.
- `member_toggle_keyboard_and_announced` — NFR-F002-03: `Space` toggles a member checkbox; live region announces `Pat added to Finance`.
- `status_badges_not_colour_only` — NFR-F002-03: each `UserStatusBadge` exposes its text label to screen readers.
- `table_rows_keyboard_reachable` — NFR-F002-03: tab order covers filters, invite button, every row action, and pagination.
- `reduced_motion_disables_row_transitions` — NFR-F002-03: `prefers-reduced-motion` removes row enter/leave animation.

Evidence: axe JSON reports under `testing/evidence/F002/accessibility/`.
