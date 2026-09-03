# F003 accessibility cases

File: `testing/features/F003/accessibility/authz.a11y.spec.ts`. axe-core via Playwright. Flag `F003_FEATURE`.

- `matrix_keyboard_navigation_and_axe` — NFR-F003-03: zero `serious`/`critical` on `/admin/roles`; arrow keys traverse cells; headers announced.
- `matrix_checkboxes_have_role_permission_labels` — NFR-F003-03: every checkbox `aria-label` follows `{role} can {permission}`.
- `acl_editor_drawer_traps_focus_and_restores` — NFR-F003-03: drawer traps focus; `Escape` returns focus to the `Permissions` button.
- `audit_page_no_serious_axe_violations` — NFR-F003-03: `/admin/audit` with 200 rows and an expanded diff passes axe.
- `diff_viewer_changes_readable_by_screen_reader` — NFR-F003-03: additions and removals exposed as `Added` / `Removed` text.
- `reduced_motion_disables_drawer_transition` — NFR-F003-03: `prefers-reduced-motion` removes the drawer slide.

Evidence: axe JSON reports under `testing/evidence/F003/accessibility/`.
