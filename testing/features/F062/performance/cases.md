# F062 performance cases

File: `testing/features/F062/performance/{budget_tests,visual_tests}.ts`. Flag `F062_FEATURE`.

- `themed_bundle_under_budget` — NFR-F062-01: the built `apps/web/src/ui` entry stays under 210 KB gzipped with Data Grid and Charts split into their own chunks; the check names the largest contributors on failure.
- `tokens_css_under_12kb` — NFR-F062-01: the emitted token and theme CSS stays under 12 KB.
- `ten_thousand_row_grid_scroll_holds_sixty_fps` — NFR-F062-01: scrolling a virtualized 10,000-row `DataGridPanel` holds 60 fps with no frame over 16 ms at the 95th percentile.
- `theme_switch_repaints_under_sixteen_ms` — NFR-F062-01: toggling theme on a 1,000-row table repaints without a reflow exceeding 16 ms.
- `density_switch_causes_no_layout_thrash` — FR-F062-07: switching density triggers one style recalculation, not one per row.
- `story_screenshots_match_pinned_baselines` — NFR-F062-04, FR-F062-15: every story renders to a deterministic screenshot at device pixel ratio 1 with animations disabled and fails on a pixel diff above 0.1%.
- `story_matrix_runs_in_both_entitlement_states` — FR-F062-17: every story renders unentitled and entitled; with no CI licence secret the entitled lane reports `skipped: no licence key` and fails the job when it was expected, never passing silently.
- `baseline_diff_names_the_token_that_changed` — NFR-F062-04: a deliberate token edit fails the visual lane and the report names the changed token and the affected stories.

Evidence: bundle report, frame timings, and screenshot diffs under `testing/evidence/F062/performance/`.
