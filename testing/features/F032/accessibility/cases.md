# F032 accessibility cases

File: `testing/features/F032/accessibility/governance.a11y.spec.ts`. axe-core via Playwright. Flag `F032_FEATURE`.

- `governance_pages_have_no_serious_axe_violations` — NFR-F032-03: zero `serious`/`critical` violations on governance, intake form, intake status, and model editor pages.
- `health_colours_have_text_and_icon` — NFR-F032-03: green, amber, red, unknown render label text and a Lucide icon with accessible name.
- `gate_timeline_is_ordered_list_with_status` — NFR-F032-03: `<ol>` items expose `Gate 1 Charter, approved by Dana on 3 Sep 2026`.
- `dialogs_trap_focus_and_restore` — NFR-F032-03: override, submit, and decide dialogs trap focus and return it to the trigger; `Escape` cancels.
- `indicator_bars_have_accessible_values` — NFR-F032-03: each bar is a `meter` with `aria-valuenow` and label naming the indicator.
- `keyboard_completes_submit_flow` — NFR-F032-03: keyboard-only user opens gate, completes checklist, attaches file, submits; live region announces `Gate submitted`.
- `reduced_motion_disables_score_animation` — NFR-F032-03: `prefers-reduced-motion` renders the score without transition.

Evidence: axe JSON reports under `testing/evidence/F032/accessibility/`.
