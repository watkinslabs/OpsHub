# F070 accessibility cases

File: `testing/features/F070/accessibility/trash.a11y.spec.ts`. axe-core via Playwright, both themes and both densities. Flag `F070_FEATURE`.

- `trash_page_has_no_serious_axe_violations` — NFR-F070-03: zero `serious` and `critical` violations on `/trash` with a mixed list of restorable, blocked, held and expired entries.
- `dialogs_have_no_serious_axe_violations` — NFR-F070-03: the restore and purge dialogs scan clean with their error and confirmation states rendered.
- `state_is_not_colour_only` — NFR-F070-03: each state renders a text label beside a titled icon, and the check passes with colour removed from the page.
- `countdown_is_readable_text` — NFR-F070-03: `30 days left` is text, not only a progress bar; a null retention policy announces `Kept until deleted` rather than an empty cell.
- `table_supports_roving_focus_and_row_shortcuts` — NFR-F070-03: arrow keys move a single tab stop through the grid, `r` restores the focused row, `Delete` opens the purge dialog.
- `dialogs_trap_focus_and_return_it` — NFR-F070-03: both dialogs trap focus, name the item in their heading, and return focus to the originating row on close.
- `purge_result_is_announced` — NFR-F070-03: success, denial and the legal-hold refusal are announced through a polite live region.
- `blocked_reason_is_reachable_by_keyboard` — FR-F070-07, NFR-F070-03: the reason and its `Restore parent first` link are focusable and labelled, not a hover-only popover.

Evidence: axe JSON reports per theme and density under `testing/evidence/F070/accessibility/`.
