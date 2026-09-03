# F018 accessibility cases

File: `testing/features/F018/accessibility/workflow.a11y.spec.ts`. axe-core via Playwright. Flag `F018_FEATURE`.

- `builder_has_no_serious_axe_violations` — NFR-F018-03: zero `serious`/`critical` violations on the builder with a depth-3 condition and 5 actions.
- `list_has_no_serious_axe_violations` — NFR-F018-03: zero violations on the list with 50 workflows.
- `condition_tree_levels_announced` — NFR-F018-03: screen-reader output includes `level 2 of 4` for nested groups.
- `validation_errors_linked_to_fields` — NFR-F018-03: each error region is referenced by the field's `aria-describedby`.
- `dialogs_trap_focus_and_restore` — NFR-F018-03: publish and disable dialogs trap focus and return it to the trigger button.
- `reorder_announced_by_live_region` — NFR-F018-03: `Alt+ArrowDown` announces "Assign moved to position 2".
- `reduced_motion_disables_step_transitions` — NFR-F018-03: `prefers-reduced-motion` removes stepper animation.

Evidence: axe JSON reports under `testing/evidence/F018/accessibility/`.
