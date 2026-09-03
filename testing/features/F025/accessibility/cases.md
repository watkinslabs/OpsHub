# F025 accessibility cases

File: `testing/features/F025/accessibility/report_exports.a11y.spec.ts`. axe-core via Playwright plus a PDF structure check. Flag `F025_FEATURE`.

- `drill_panel_has_no_serious_violations` — NFR-F025-03: zero `serious` and `critical` violations on the panel with allowed, denied, and empty results.
- `panel_traps_focus_and_returns_to_origin` — NFR-F025-03: focus moves to the panel heading, cycles inside, and `Escape` returns it to the chart point that opened it.
- `export_dialog_and_center_pass_axe` — NFR-F025-03: zero serious violations on the export dialog and `/exports` including failed and expired rows.
- `export_progress_announced_politely` — NFR-F025-03: `progress_pct` changes are announced through a polite live region without stealing focus.
- `denied_row_not_color_only` — NFR-F025-03: denied sources and denied widgets carry text and a labelled icon, verified with forced colors.
- `generated_pdf_is_tagged` — NFR-F025-03: the exported PDF has a document title, tagged table headers, and a reading order matching the visible grid.

Evidence: axe JSON reports and PDF structure dumps under `testing/evidence/F025/accessibility/`.
