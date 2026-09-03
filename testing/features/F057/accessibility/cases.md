# F057 accessibility cases

File: `testing/features/F057/accessibility/assets.a11y.spec.ts`. axe-core via Playwright. Flag `F057_FEATURE`.

- `library_drawer_tree_have_no_serious_axe_violations` — NFR-F057-03: zero `serious`/`critical` on grid with 40 tiles, drawer, and tree.
- `tiles_have_alt_text_and_badge_text` — NFR-F057-03: every thumbnail `alt` equals the title; badges expose text not color alone.
- `tile_grid_keyboard_navigation` — NFR-F057-03: arrow keys move between tiles, Enter opens drawer, Escape returns focus to the tile.
- `drawer_traps_focus_and_restores` — NFR-F057-03: drawer traps focus and returns it to the originating tile.
- `collection_tree_aria_tree_semantics` — NFR-F057-03: tree exposes `treeitem` roles with `aria-expanded` and level.
- `reduced_motion_disables_tile_fade` — NFR-F057-03: `prefers-reduced-motion` removes tile fade-in.

Evidence: axe JSON reports under `testing/evidence/F057/accessibility/`.
