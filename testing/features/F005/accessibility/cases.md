# F005 accessibility cases

File: `testing/features/F005/accessibility/workspace.a11y.spec.ts`. axe-core via Playwright. Flag `F005_FEATURE`.

- `list_and_shell_have_no_serious_axe_violations` — NFR-F005-03: zero `serious`/`critical` violations on `/w` and `/w/{id}` with the 12-folder tree expanded.
- `tree_has_aria_tree_roles` — NFR-F005-03: sidebar exposes `role="tree"`, each node `treeitem` with `aria-level`, `aria-expanded` on parents, `group` for children, and an accessible name equal to the folder name.
- `tree_keyboard_navigation` — NFR-F005-03: ArrowDown/ArrowUp move focus, ArrowRight expands, ArrowLeft collapses, Enter opens the folder route, F2 opens rename.
- `folder_move_announced_by_live_region` — NFR-F005-03: keyboard move announces "Q4 moved to Ops root".
- `dialogs_trap_focus_and_restore` — NFR-F005-03: new-workspace, members, and move dialogs trap focus and return it to the trigger on close.
- `contrast_and_focus_tokens` — NFR-F005-03: focus ring visible on every tree node, button, and role select; text contrast ≥ 4.5:1 in light and dark themes.
- `reduced_motion_disables_drawer_and_drag_animation` — NFR-F005-03: `prefers-reduced-motion` removes the sidebar drawer transition and drag preview animation.

Evidence: axe JSON reports under `testing/evidence/F005/accessibility/`.
