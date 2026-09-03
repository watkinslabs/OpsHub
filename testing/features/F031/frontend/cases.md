# F031 frontend cases

File: `testing/features/F031/frontend/{RollupTable.test.tsx,PortfolioPage.test.tsx,ProjectPicker.test.tsx,NewPortfolioDialog.test.tsx}`. Vitest with MSW. Flag `F031_FEATURE`.

- `renders_rows_with_measure_states` — FR-F031-13: three-project fixture renders status, variance, budget, risk, value, health cells; missing budget shows `Missing` with reason tooltip.
- `shows_stale_badge_after_threshold` — FR-F031-09: `computed_at` older than `stale_after_seconds` renders the amber `Stale since` badge.
- `hides_drill_link_for_denied_row` — FR-F031-09, FR-F031-13: `denied` row renders `Restricted project` and no link element.
- `shows_totals_with_excluded_count` — FR-F031-09: totals header shows budget sums and `1 restricted project excluded`.
- `refresh_polls_until_fresh` — FR-F031-06, FR-F031-13: clicking `Refresh` calls `requestRefresh`, polls every 2 s while `refreshing`, then shows toast and `Last refreshed`.
- `shows_failed_state_with_error` — NFR-F031-04: `rollup_state: failed` renders red banner containing `last_refresh_error` and `Retry`.
- `shows_loading_skeleton_then_content` — FR-F031-13: pending query shows six-column skeleton.
- `shows_empty_state_with_add_projects` — FR-F031-13: zero members shows `No projects yet` with `Add projects`.
- `shows_error_banner_with_correlation_id` — NFR-F031-04: 500 response shows banner with `correlation_id` and retry.
- `shows_denied_affordances_for_viewer` — FR-F031-12: viewer role hides `Refresh`, `Add projects`, and mapping editor.
- `shows_per_project_errors_on_invalid` — FR-F031-04: `field_errors.projects[1]` renders inline on the second picked project and rolls back the optimistic list.
- `mapping_editor_limits_to_six_measures` — FR-F031-05: editor offers exactly the six measure keys and rejects an empty column.
- `stacks_rows_as_cards_under_768px` — FR-F031-13: narrow viewport renders one card per project with measure labels.
- `refresh_emits_telemetry` — FR-F031-13: clicking `Refresh` emits `portfolio_refresh_requested` with `portfolio_id` and `project_count`.

Evidence: Vitest JUnit under `testing/evidence/F031/frontend/`.
