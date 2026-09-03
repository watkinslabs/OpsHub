# F053 accessibility cases

File: `testing/features/F053/accessibility/datamesh.a11y.spec.ts`. axe-core via Playwright. Flag `F053_FEATURE`.

- `pages_have_no_serious_axe_violations` — NFR-F053-03: zero `serious`/`critical` violations on the mapping list, editor with 2 field maps, preview with 50 sample rows, and conflicts tab with 2 conflicts.
- `change_markers_and_conflict_kinds_have_text` — NFR-F053-03: `create`, `update`, `clear`, `conflict` markers and `ambiguous_match`, `both_changed`, `unmatched_source`, `source_deleted` badges expose their meaning as text.
- `field_map_table_keyboard_operable` — NFR-F053-03: arrow keys move between rows, `Enter` opens the column picker, `Escape` closes it, rows are labelled by source column.
- `resolve_dialog_traps_focus_and_restores` — NFR-F053-03: dialog traps focus, `Escape` cancels, focus returns to the conflict row after resolve.
- `tabs_announced_and_selectable_by_keyboard` — FR-F053-14: `Setup`, `Preview`, `Runs`, `Conflicts` use the tab pattern with arrow navigation and `aria-selected`.
- `reduced_motion_disables_run_spinner` — NFR-F053-03: `prefers-reduced-motion` removes the running-state animation.

Evidence: axe JSON reports under `testing/evidence/F053/accessibility/`.
