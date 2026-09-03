# F024 frontend cases

File: `testing/features/F024/frontend/{BarChart.test.tsx,LineChart.test.tsx,PieChart.test.tsx,BurndownChart.test.tsx,TimelineChart.test.tsx,WorkloadHeatmap.test.tsx,KpiWidget.test.tsx,MetricComparisonWidget.test.tsx,ChartFrame.test.tsx,ChartDataTable.test.tsx,ChartSpecEditor.test.tsx}`. Vitest with MSW. Flag `F024_FEATURE`.

- `bar_renders_one_rect_per_owner_with_legend` — FR-F024-11: 6 owners → 6 bars, legend entries per measure, colors from `--chart-1`..`--chart-8`.
- `line_draws_actual_and_dashed_projection` — FR-F024-06, FR-F024-11: `actual` solid, `projected` dashed with a shaded `lower`/`upper` band.
- `pie_renders_single_measure_slices_with_percentages` — FR-F024-11: slices sum to 100% and each label shows `formatted`.
- `burndown_plots_ideal_and_remaining` — FR-F024-08: 15 daily points draw two lines; `added` shows as a marker on the days it is non-zero.
- `timeline_renders_bars_and_milestone_diamonds` — FR-F024-09: null `end` renders a diamond, grouped rows share a lane label.
- `workload_marks_cells_over_capacity` — FR-F024-09: a cell above `capacity_per_bucket` gets the over-capacity token and a text label, not colour alone.
- `workload_freezes_person_column_on_scroll` — FR-F024-11: horizontal scroll keeps the person column pinned.
- `kpi_widget_wraps_metric_card` — FR-F024-05: renders the F022 `KpiCard` with `current`, `formatted`, and target direction.
- `metric_comparison_shows_delta_and_direction` — FR-F024-05: `delta_abs`, `delta_pct`, and an up/down indicator with a text sign.
- `renders_empty_state_message_when_all_series_empty` — FR-F024-10: `empty_state.message` "No open risks" centered with the Lucide icon.
- `renders_error_state_with_correlation_id_and_retry` — FR-F024-10: 500 response → `error_state.message`, `correlation_id`, retry button that refetches.
- `renders_truncated_note_at_one_thousand_points` — FR-F024-03: `meta.truncated` → "Showing first 1,000 points".
- `renders_denied_tile_and_stale_badge` — FR-F024-05: widget status `denied` shows the F023 tile; `meta.stale` shows the stale badge.
- `legend_moves_below_plot_under_480px` — FR-F024-11: at 420 px the legend renders under the plot area.
- `table_toggle_matches_series_values` — FR-F024-11: pressing `T` renders `ChartDataTable` whose cells equal each point's `formatted`.
- `spec_editor_blocks_save_when_formatting_missing` — FR-F024-01: save disabled until `formatting`, `empty_state`, and `error_state` are set.
- `spec_editor_maps_field_errors_to_controls` — FR-F024-01: server `field_errors.spec.error_state` renders on the state messages control.
- `spec_editor_previews_through_chart_query` — FR-F024-11: preview issues the same `POST /api/v1/charts/query` payload the widget will send.
- `renderers_registered_for_eight_kinds` — FR-F024-11: `registerChartRenderers` registers `kpi`, `metric_comparison`, `bar`, `line`, `pie`, `burndown`, `timeline`, `workload`.
- `telemetry_emitted_on_render_and_toggle` — NFR-F024-04: `chart_rendered` with `kind`, `point_count`, `truncated`; `chart_table_toggled` on the toggle.

Evidence: Vitest JUnit and DOM snapshots under `testing/evidence/F024/frontend/`.
