# F022 accessibility cases

File: `testing/features/F022/accessibility/kpi.a11y.spec.ts`. axe-core via Playwright. Flag `F022_FEATURE`.

- `kpi_cards_and_editor_have_no_serious_axe_violations` — NFR-F022-03: zero `serious`/`critical` violations on a grid of 8 cards and the editor.
- `direction_conveyed_by_text_not_color` — NFR-F022-03: arrows are `aria-hidden`; visible text "up"/"down" present.
- `sparkline_summary_read_by_screen_reader` — NFR-F022-03: card region announces the sparkline summary once.
- `card_is_focusable_and_opens_source` — NFR-F022-03: `Tab` reaches the card, `Enter` opens the source report.
- `kpi_color_tokens_meet_contrast` — NFR-F022-03: `--kpi-better`, `--kpi-worse`, `--kpi-flat` text ≥ 4.5:1 on card background.
- `reduced_motion_disables_sparkline_animation` — NFR-F022-03: `prefers-reduced-motion` removes the draw animation.

Evidence: axe JSON reports under `testing/evidence/F022/accessibility/`.
