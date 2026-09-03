# F030 accessibility cases

File: `testing/features/F030/accessibility/syncs.a11y.spec.ts`. axe-core via Playwright. Flag `F030_FEATURE`.

- `sync_list_has_no_serious_violations` — NFR-F030-03: zero `serious`/`critical` violations on `/admin/syncs` with paused, active, and error rows present.
- `wizard_steps_have_no_serious_violations` — NFR-F030-03: each of the three wizard steps is axe-clean, traps focus, and restores focus to the invoking control on close.
- `mapping_rows_reorder_without_pointer` — NFR-F030-03: `Alt+ArrowUp` and `Alt+ArrowDown` reorder mapping rows and a polite live region announces the new position; no drag-only path exists.
- `transform_arguments_are_labelled` — FR-F030-06: every transform argument input has a programmatic label and `aria-describedby` explaining its format.
- `conflict_queue_has_no_serious_violations` — NFR-F030-03: `/admin/syncs/:syncId/conflicts` is axe-clean with 50 open conflicts rendered.
- `conflict_diff_reads_in_sequence` — NFR-F030-03: the diff exposes field name, OpsHub value, then external value in reading order with labelled columns rather than color-coded cells.
- `run_and_conflict_states_not_color_only` — NFR-F030-03: `completed`, `partial`, `failed`, `open`, `resolved` carry text and a labelled icon.
- `replay_confirmation_announced` — FR-F030-12: the dry-run result and the replay outcome are announced through a live region.
- `reduced_motion_disables_run_pulse` — NFR-F030-03: `prefers-reduced-motion` removes the running-state pulse animation.

Evidence: axe JSON reports under `testing/evidence/F030/accessibility/`.
