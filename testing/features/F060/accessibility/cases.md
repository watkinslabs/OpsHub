# F060 accessibility cases

File: `testing/features/F060/accessibility/formatting.a11y.spec.ts` and `token_contrast.spec.ts`. axe-core via Playwright plus a token-contrast check over `apps/web/src/design/tokens.css`. Flag `F060_FEATURE`.

- `color_is_never_the_only_signal` — NFR-F060-03, FR-F060-04: every rendered state carrying a fill or text colour also renders an icon, a badge, or a text style; the server rejects the colour-only rule that this test attempts to create.
- `token_pairs_meet_contrast_thresholds` — NFR-F060-03: each of the seven colour tokens holds at least 4.5:1 for text on fill and at least 3:1 for its icon against the fill, in light and dark themes.
- `formatted_row_describes_applied_rules` — NFR-F060-03, FR-F060-15: a formatted row exposes `aria-describedby` resolving to `Formatted by Late tasks, Mine`, and icons are `aria-hidden`.
- `formatting_surfaces_have_no_serious_violations` — NFR-F060-03: zero `serious` or `critical` axe violations on the panel, the rule editor, the legend, the explanation popover, and the formatted grid.
- `rule_editor_labels_condition_and_format_controls` — NFR-F060-03: each condition row has labelled column, operator, and value controls; the format picker is a labelled radio group where each swatch names its colour and its paired icon in text.
- `reorder_is_keyboard_operable_and_announced` — NFR-F060-03, FR-F060-06: `Alt+ArrowUp` and `Alt+ArrowDown` reorder rules with visible focus and a polite live-region announcement of the new position.
- `legend_and_popover_are_keyboard_reachable` — NFR-F060-03, FR-F060-15: `Shift+F` opens the legend, focus is trapped and restored, and the popover opens from the keyboard cell menu.
- `icon_only_mode_keeps_meaning_without_color` — NFR-F060-03: in `Icon only` mode a monochrome screenshot still distinguishes every rule by icon or badge, and the mode switch is a labelled two-option radio group.
- `reduced_motion_removes_newly_matched_flash` — NFR-F060-03: with `prefers-reduced-motion: reduce` the flash animation on a newly matched row is not applied.
- `degraded_page_is_announced` — FR-F060-13: a budget-degraded page announces `Formatting paused for this page` through a live region and keeps the rows readable.

Evidence: axe JSON reports, monochrome screenshots, and contrast tables under `testing/evidence/F060/accessibility/`.
