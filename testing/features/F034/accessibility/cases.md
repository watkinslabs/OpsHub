# F034 accessibility cases

File: `testing/features/F034/accessibility/{axe_spec.ts,keyboard_spec.ts,semantics_spec.ts}` over `/w/{id}/workload`, `/w/{id}/workload/conflicts`, `/w/{id}/time`, and `/w/{id}/workload/reconcile`. Flag `F034_FEATURE`.

- `workload_pages_have_no_serious_axe_violations` — NFR-F034-03: axe reports zero serious or critical violations on all four routes in light and dark themes.
- `heatmap_exposes_grid_semantics` — NFR-F034-03: the heatmap is a `grid` with row and column headers naming the resource and period, and each cell has an accessible name of the form `Ana, week of 12 October, 137.5 percent, over`.
- `heatmap_cell_uses_meter_semantics` — NFR-F034-03, FR-F034-13: each utilization cell renders a `meter` with `aria-valuenow`, `aria-valuemin` 0, `aria-valuemax` 200, and a text equivalent.
- `status_is_conveyed_by_text_and_icon` — NFR-F034-03: `under`, `ok`, `over`, and `no_capacity` are distinguishable with colour disabled, each pairing a word with a Lucide icon.
- `heatmap_keyboard_navigation_and_activation` — NFR-F034-03: arrow keys move focus one cell at a time, `Home` and `End` jump within the row, and `Enter` opens the resource's conflicts with focus placed on the first conflict.
- `time_sheet_is_keyboard_editable` — NFR-F034-03, FR-F034-04: `Tab` reaches every day cell, typing edits, `Enter` saves, `Escape` reverts, and the saved state is announced in a polite live region.
- `dialogs_trap_and_restore_focus` — NFR-F034-03: the time entry, import, and reconcile dialogs trap `Tab`, close on `Escape`, and return focus to the invoking control.
- `reconcile_reason_error_is_programmatically_associated` — FR-F034-08: a reason under 10 characters sets `aria-invalid` and links the message with `aria-describedby`.
- `locked_and_denied_states_are_announced` — FR-F034-05, FR-F034-12: the lock hint and the hidden import action leave no unlabelled control, and the lock reason is reachable by screen reader.
- `reduced_motion_disables_cell_transitions` — NFR-F034-03: with `prefers-reduced-motion: reduce` no heatmap cell animates on refresh.
- `stale_updating_badge_is_announced_once` — FR-F034-10: the `Updating` badge announces once per transition, not on every 5-second refetch.

Evidence: axe JSON reports and keyboard traces under `testing/evidence/F034/accessibility/`.
