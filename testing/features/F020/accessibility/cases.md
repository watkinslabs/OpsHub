# F020 accessibility cases

File: `testing/features/F020/accessibility/approvals.a11y.spec.ts`. axe-core via Playwright. Flag `F020_FEATURE`.

- `inbox_and_detail_have_no_serious_axe_violations` — NFR-F020-03: zero `serious`/`critical` violations on inbox with 20 approvals and detail with 3 decisions.
- `due_state_text_and_icon` — NFR-F020-03: `Overdue` and `Due in 2 days` badges have visible text and `aria-label`; contrast ≥ 4.5:1.
- `reject_reason_error_receives_focus` — NFR-F020-03: submitting reject without reason moves focus to the reason field with the error announced.
- `dialogs_trap_focus_and_restore` — NFR-F020-03: decide, reassign, cancel dialogs trap focus and return it to the trigger.
- `decision_announced_by_live_region` — NFR-F020-03: approving announces "Vendor contract approved".
- `escalation_trail_is_ordered_list` — NFR-F020-03: trail renders as `<ol>` with level and timestamp announced.
- `reduced_motion_disables_badge_pulse` — NFR-F020-03: `prefers-reduced-motion` removes the pending-count animation.

Evidence: axe JSON reports under `testing/evidence/F020/accessibility/`.
