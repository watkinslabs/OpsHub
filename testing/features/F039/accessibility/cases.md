# F039 accessibility cases

File: `testing/features/F039/accessibility/ai_assist.a11y.spec.ts`. axe-core via Playwright. Flag `F039_FEATURE`.

- `panels_and_diff_have_no_serious_violations` — NFR-F039-03: zero `serious` or `critical` violations on the formula panel, the query panel with a compiled plan, the plan diff, the preview table, and `/admin/ai-settings`.
- `diff_uses_ins_del_and_text_labels` — NFR-F039-03, FR-F039-13: additions and removals are `ins` and `del` elements with visible `Added`/`Removed` text; a forced-monochrome render still distinguishes them.
- `generation_state_announced_in_live_region` — NFR-F039-03: a polite live region announces "Generating", "Suggestion ready", and the failure message in turn.
- `apply_dialog_traps_focus_and_names_target` — NFR-F039-03, FR-F039-11: the confirmation dialog traps focus, is dismissible with `Escape`, and its accessible name includes the target column or report name.
- `panel_is_keyboard_operable_end_to_end` — NFR-F039-03: prompt, `Ctrl+Enter` submit, cancel, diff navigation, `Apply`, and `Reject` are reachable by keyboard with visible focus in a single tab order.
- `confidence_and_status_not_color_only` — NFR-F039-03: confidence buckets and proposal status render text plus a labelled icon.
- `reduced_motion_disables_generating_shimmer` — NFR-F039-03: `prefers-reduced-motion` replaces the shimmer with a static state.
- `settings_form_fields_have_labels_and_errors` — NFR-F039-03, FR-F039-14: every `ai-settings` field has a programmatic label and its validation error is linked by `aria-describedby`.

Evidence: axe JSON reports and forced-monochrome screenshots under `testing/evidence/F039/accessibility/`.
