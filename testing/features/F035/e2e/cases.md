# F035 e2e cases

File: `testing/features/F035/e2e/formula.spec.ts`. Playwright against seeded tenant. Flag `F035_FEATURE`.

- `set_formula_edit_child_parent_updates` — FR-F035-06, FR-F035-09, FR-F035-15: editor sets `=SUM(CHILDREN([Estimate]))` on `Total`, edits a child Estimate from 3 to 5, parent shows the new sum within 2 s.
- `cycle_rejected_in_editor` — FR-F035-10: setting `=[A]+1` on B when A references B shows the cycle message naming both columns; nothing saved.
- `cross_sheet_lookup_and_broken_reference` — FR-F035-12: `LOOKUP` into `Rates` shows values; deleting `Rates` turns the cells to `#REF`.
- `recalculate_all_and_graph` — FR-F035-13, FR-F035-14: `Recalculate all` shows the job toast; `Formula graph` lists three columns and one sheet node.
- `viewer_cannot_set_formula` — FR-F035-16: viewer login sees values and a read-only formula view; `Set formula` absent.
- `unsupported_function_message` — FR-F035-03: `=FOO(1)` shows "FOO is not a supported function" and the catalog link.
- `keyboard_only_formula_authoring` — FR-F035-15, NFR-F035-03: no mouse; open editor, autocomplete with arrows, save with `Ctrl+Enter`, focus returns to the column header.

Evidence: Playwright traces and videos under `testing/evidence/F035/e2e/`.
