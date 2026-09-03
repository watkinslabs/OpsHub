# F045 accessibility cases

File: `testing/features/F045/accessibility/documents.a11y.spec.ts`. axe-core via Playwright. Flag `F045_FEATURE`.

- `library_and_editor_have_no_serious_axe_violations` — NFR-F045-03: zero `serious`/`critical` violations on the library with the seeded tree and on the editor with a 1 MB body.
- `folder_tree_follows_aria_tree_pattern` — NFR-F045-03: `role="tree"`, `treeitem` with `aria-expanded` and `aria-level`, roving tabindex, arrow keys and `Home`/`End` move focus.
- `dialogs_trap_focus_and_restore` — NFR-F045-03: new-node and move dialogs trap focus and return it to the trigger on `Escape`.
- `revision_restore_announced_by_live_region` — NFR-F045-03: restoring revision 2 announces "Revision 4 saved from revision 2".
- `editor_toolbar_keyboard_reachable` — NFR-F045-03: every toolbar control and `Save revision` reachable by Tab with visible focus ring and accessible names.
- `contrast_and_reduced_motion` — NFR-F045-03: text contrast ≥ 4.5:1 in tree, list, and history; `prefers-reduced-motion` removes tree expand animation.

Evidence: axe JSON reports under `testing/evidence/F045/accessibility/`.
