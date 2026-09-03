# F040 accessibility cases

File: `testing/features/F040/accessibility/insights.a11y.spec.ts`. axe-core via Playwright. Flag `F040_FEATURE`.

- `insights_routes_have_no_serious_violations` — NFR-F040-03: zero `serious` or `critical` violations on `/insights`, an insight detail with 20 evidence rows, and `/insights/actions/:actionId` with a 25-target diff.
- `severity_not_color_only` — NFR-F040-03: `low`, `medium`, and `high` cards carry visible text and a labelled icon; a greyscale render still distinguishes them.
- `evidence_table_has_headers_and_caption` — NFR-F040-03: the evidence table has column headers, a row header per record, and a caption naming the insight.
- `diff_table_has_headers_and_target_count_caption` — NFR-F040-03: `ActionPreviewDiff` exposes `Target`, `Field`, `Before`, `After` headers and a caption stating `4 targets`.
- `confirm_dialog_traps_focus_and_restores` — NFR-F040-03: focus is trapped in the confirm dialog, `Escape` closes it, and focus returns to the `Confirm` trigger.
- `run_result_announced_in_live_region` — NFR-F040-03: reaching `applied` or `denied` announces the outcome through a polite live region.
- `scan_progress_announced_without_stealing_focus` — NFR-F040-01, NFR-F040-03: the queued-scan toast is announced politely and does not move focus off the list.
- `reduced_motion_disables_timeline_animation` — NFR-F040-03: `prefers-reduced-motion` removes the run timeline transition.

Evidence: axe JSON reports and greyscale screenshots under `testing/evidence/F040/accessibility/`.
