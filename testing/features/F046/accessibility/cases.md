# F046 accessibility cases

File: `testing/features/F046/accessibility/collab.a11y.spec.ts`. axe-core via Playwright. Flag `F046_FEATURE`.

- `editor_with_presence_and_banner_has_no_serious_axe_violations` — NFR-F046-03: zero `serious`/`critical` violations with 6 collaborators and an open conflict banner.
- `presence_join_announced_rate_limited` — NFR-F046-03: polite live region announces "Ben joined" once for three joins within 5 s.
- `connection_status_text_and_icon` — NFR-F046-03: every badge state has visible text and `aria-label`; contrast ≥ 4.5:1.
- `conflict_banner_focusable_and_keyboard_resolvable` — NFR-F046-03: banner is in tab order, `Keep mine` and `Take theirs` reachable, choice announced.
- `remote_cursors_have_accessible_names` — NFR-F046-03: each cursor label exposes the collaborator name to assistive tech.
- `reduced_motion_disables_cursor_animation` — NFR-F046-03: `prefers-reduced-motion` removes cursor transitions.
- `presence_list_shortcut_opens_dialog` — NFR-F046-03: `Alt+Shift+P` opens the presence list with focus trapped and restored.

Evidence: axe JSON reports under `testing/evidence/F046/accessibility/`.
