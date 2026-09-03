# F010 accessibility cases

File: `testing/features/F010/accessibility/dataio.a11y.spec.ts`. axe-core via Playwright. Flag `F010_FEATURE`.

- `palette_wizard_dialog_have_no_serious_axe_violations` — NFR-F010-03: zero `serious`/`critical` violations on the search palette, results page, each wizard step, status panel, and export dialog.
- `palette_follows_combobox_pattern` — NFR-F010-03: input has `role=combobox`, `aria-expanded`, `aria-activedescendant`; result count announced as "12 results".
- `wizard_steps_expose_progress` — NFR-F010-03: step list uses `aria-current="step"`; preview table has column headers with `scope`; mapping selects are labelled.
- `import_progress_announced_politely` — NFR-F010-03: progress bar has `aria-valuenow`; live region announces "2,000 of 5,000 rows imported" and "Import completed".
- `dialogs_trap_focus_and_restore` — NFR-F010-03: palette and export dialog trap focus and return it to the trigger on close.
- `all_actions_keyboard_reachable` — NFR-F010-03: `Ctrl+K`, arrows, `Enter`, `Escape`, wizard `Tab`/`Enter`/`Shift+Enter` cover every action without a mouse.
- `contrast_and_reduced_motion` — NFR-F010-03: invalid-row badges and progress bar meet 4.5:1; `prefers-reduced-motion` removes progress animation.

Evidence: axe JSON reports under `testing/evidence/F010/accessibility/`.
