# F024 accessibility cases

File: `testing/features/F024/accessibility/charts.a11y.spec.ts`. axe-core via Playwright on dashboard "Weekly review" and the `ChartSpecEditor` drawer. Flag `F024_FEATURE`.

- `dashboard_charts_have_no_serious_violations` — NFR-F024-03: zero `serious`/`critical` violations with all eight renderers on the page.
- `spec_editor_drawer_has_no_serious_violations` — NFR-F024-03: zero `serious`/`critical` violations with `DimensionPicker`, `MeasurePicker`, `FormattingForm`, and `StateMessagesForm` open and in an error state.
- `chart_summary_label_names_min_max_latest` — NFR-F024-03: each chart's `aria-label` names kind, series count, min, max, and latest value.
- `table_alternative_reachable_by_keyboard` — NFR-F024-03: `T` from the focused chart opens `ChartDataTable` with a caption, header scope, and the same values as the plot.
- `series_distinguishable_without_colour` — NFR-F024-03: every series carries a pattern fill plus a legend text label; token colors meet 3:1 against the surface.
- `point_navigation_announced_in_live_region` — NFR-F024-03: arrow keys move focus between points and a polite live region announces the label and formatted value.
- `tooltip_reachable_by_keyboard` — NFR-F024-03: the focused point exposes a `role="tooltip"` element referenced by `aria-describedby`; `Escape` dismisses it.
- `workload_over_capacity_not_colour_only` — NFR-F024-03: over-capacity cells carry text and a labelled icon, not just the warning token.
- `empty_and_error_states_announced` — FR-F024-10, NFR-F024-03: `empty_state.message` and `error_state.message` with `correlation_id` are announced and the retry button is labelled.
- `reduced_motion_disables_chart_transitions` — NFR-F024-03: `prefers-reduced-motion` removes bar growth and line draw animations.

Evidence: axe JSON reports and contrast measurements under `testing/evidence/F024/accessibility/`.
