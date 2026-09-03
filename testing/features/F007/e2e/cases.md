# F007 e2e cases

File: `testing/features/F007/e2e/columns.spec.ts`. Playwright against seeded tenant. Flag `F007_FEATURE`.

- `add_select_column_reorder_and_validate` — FR-F007-01, FR-F007-07, FR-F007-12, FR-F007-11: editor adds `Status` with three options, drags it before `Owner`, runs `Validate`, reload shows the new order and counts.
- `type_change_with_preview_flags_cells` — FR-F007-05, FR-F007-06, FR-F007-17: change `Estimate` to `number`, preview shows 1 invalid, confirm, cell `n/a` shows the validation icon with `type_mismatch`.
- `rename_column_keeps_formula_working` — FR-F007-04: rename `Estimate` to `Effort`; formula column `Total` still shows the same value.
- `duplicate_label_shows_inline_error` — FR-F007-03: second `Status` shows the label field error and no column is added.
- `primary_column_cannot_be_deleted` — FR-F007-13: primary header menu has no delete; direct route call from devtools returns 400.
- `viewer_cannot_edit_columns` — FR-F007-16, NFR-F007-02: viewer sees headers without menus or the add button.
- `concurrent_column_edit_shows_stale_banner` — FR-F007-16: second session renames a column; first session's save shows stale banner and reload.

Evidence: Playwright traces and videos under `testing/evidence/F007/e2e/`.
