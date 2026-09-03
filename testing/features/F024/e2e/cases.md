# F024 e2e cases

File: `testing/features/F024/e2e/charts.spec.ts`. Playwright against the seeded tenant with dashboard "Weekly review", report "Portfolio status", sheet "Sprint 12", and metric "Open high risks". Flag `F024_FEATURE`.

- `add_bar_widget_from_builder_palette` — FR-F024-01, FR-F024-04, FR-F024-11: editor drags `Bar`, picks source "Portfolio status", dimension `Projects.owner`, measure `count(Risks.id)`, timezone `America/New_York`, 0 decimals, empty message "No open risks", saves; the widget renders one bar per owner and `chart_definitions` holds the spec.
- `add_line_with_thirty_day_projection` — FR-F024-06, FR-F024-07: editor adds `Line` over "Open high risks" with `linear` and horizon 30; the projection appears after the `charts.project` job runs and the stale badge clears.
- `add_burndown_for_sprint_twelve` — FR-F024-08: editor adds `Burndown` for "Sprint 12" with done values `Done, Cancelled` from 2026-08-20 to 2026-09-03; 15 daily points render with ideal and remaining lines.
- `add_workload_heatmap_and_scroll` — FR-F024-09: editor adds `Workload` bucketed by week with `sum(Points)`; over-capacity cells are labelled and the person column stays pinned while scrolling.
- `chart_this_report_drawer_previews_ad_hoc_spec` — FR-F024-11: report viewer toolbar `Chart this report` opens `ChartSpecEditor` and previews without saving a widget.
- `line_chart_arrow_keys_announce_point` — NFR-F024-03: `Tab` focuses the chart, arrows move between points and the live region announces "Dana, 7 risks", `T` reveals the table, `Escape` leaves.
- `viewer_sees_denied_tile_for_restricted_sheet` — FR-F024-12: Lee opens "Weekly review" and the burndown widget shows the denied tile while the bar widget still renders.
- `hidden_field_series_shows_no_values` — FR-F024-03: Lee's view of the bar widget shows the `sum(Budget.margin)` series with no plotted points and a note in the table alternative.
- `truncated_chart_shows_note` — FR-F024-03: a two-dimension bar over 35 owners renders 20 series and the "Showing first 1,000 points" note where applicable.
- `flag_off_shows_unavailable_widget` — FR-F024-04: with `F024_FEATURE` off the chart widgets fall back to the F023 unavailable state and the dashboard still loads.

Evidence: Playwright traces, screenshots, and outbox dumps under `testing/evidence/F024/e2e/`.
