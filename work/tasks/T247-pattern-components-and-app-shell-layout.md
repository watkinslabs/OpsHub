---
id: T247
type: task
status: planned
parent_epic: E001
parent_feature: F062
parent_story: S124
depends_on: [S124]
owned_paths: [apps/web/src/ui/patterns/**, apps/web/src/ui/shell/**, apps/web/src/ui/index.ts, testing/features/F062/e2e/**]
feature_flag: F062_FEATURE
branch: t247-pattern-components-and-app-shell-layout
started_at: null
finished_at: null
---

# T247 — Pattern components and app shell layout

## Identity

- Parent story: `S124` UI primitives and patterns
- Owner: platform
- Branch: `t247-pattern-components-and-app-shell-layout`
- Decision references: `docs/architecture-decisions.md` sections 5, 6; `docs/capability-contracts.md` row F062

## Objective

Wrap the three MUI X data surfaces once, compose the state patterns every feature ticket promises and the locale-aware formatting components, and build the application shell that all routes render inside.

## Specification

- Owned paths: `apps/web/src/ui/data/{DataGridPanel,ChartPanel,DateField,gridLayout,gridSelection}.ts(x)`, `apps/web/src/ui/patterns/{PageHeader,EmptyState,ErrorState,DeniedState,NotFoundState,OfflineBanner,StaleBanner,LoadingSkeleton,ConfirmDialog,FormLayout,FilterBar,DataTable,FormattedDate,FormattedNumber,RelativeTime}.tsx` with stories, `apps/web/src/ui/shell/{AppShell,TopBar,NavRail,InspectorPanel,ToastRegion}.tsx`, `apps/web/src/ui/index.ts`.
- Contract/input: every pattern takes its copy as props — `EmptyState { icon, headline, body, action }`, `ErrorState { correlationId, onRetry, message }`, `DeniedState { permission }`, `StaleBanner { onReload }`, `LoadingSkeleton { shape: list|table|tree|card|detail }`, `ConfirmDialog { title, body, confirmLabel, destructive }`, `DataGridPanel { columns, rows, selection, pagination, emptyState, errorState }` over MUI X `DataGrid`, `ChartPanel { kind, series, legend }` over MUI X `Charts`; the shell takes `{ nav, inspector, children }`.
- Output/behavior: `ErrorState` always renders `correlation_id` with a retry action; no pattern hard-codes feature wording; `DataGridPanel` binds theme, density and the F028 cursor to MUI X `DataGrid`, virtualizing above 100 rows with a sticky header, column resize and reorder, selection, and horizontal scroll inside its own container so the page never scrolls; the grid is `@mui/x-data-grid-pro` with the licence key injected at build time from `mui/x-license-key` and no entitlement consulted; grouping, tree rows, aggregation and xlsx export are rendered from the F013, F009, F022 and F010 endpoints and never re-implemented client-side; `gridLayout.ts` binds column order, widths, hidden set, frozen count and pinning to F008's `layout` field with a 1-second debounce and `gridSelection.ts` drives Pro range selection with the clipboard TSV writer, each with a keyboard path and an accessible announcement; `ChartPanel` fixes the five-series categorical palette and requires a legend or direct labels so colour is never the only signal; `DateField` binds the Date Pickers to the F049 locale and timezone; `AppShell` renders a 56px top bar, a rail collapsed at 56px and expanded 240–400px persisted per user, an optional inspector, the content region, and the toast region, collapsing the rail to a drawer below `--bp-lg` and the inspector to a sheet below `--bp-sm`; the shell provides skip-to-content, `[` and `]` toggles, and `?` for the shortcut sheet; `FormattedDate`, `FormattedNumber`, and `RelativeTime` read locale and timezone from F049 context, fall back to `en-US` and `UTC`, and always pass an explicit locale; `index.ts` is the single import surface for features.
- Dependencies: T246 theme and re-export surface; T245 tokens and breakpoints; `@mui/x-data-grid`, `@mui/x-charts` and `@mui/x-date-pickers`; F049 locale context when it lands, with the documented fallback until then.
- Feature flag: `F062_FEATURE` gates the barrel export and the shell mount in `main.tsx`.

## TDD

- Failing test first: `testing/features/F062/e2e/shell.spec.ts::app_shell_rail_width_persists_across_reload`, `::rail_collapses_to_drawer_below_lg`, `::inspector_becomes_sheet_below_sm`, `::skip_to_content_reaches_main`, `::shortcut_sheet_opens_with_question_mark`; `testing/features/F062/e2e/theme.spec.ts::theme_switch_has_no_flash_on_reload`, `::density_switch_changes_row_height`; `testing/features/F062/frontend/pattern_tests.tsx::error_state_renders_correlation_id_and_retry`, `::empty_state_takes_copy_from_props`, `::data_grid_virtualizes_above_one_hundred_rows`, `::data_grid_scrolls_within_its_container`, `::chart_palette_is_fixed_and_labelled`, `::no_entitlement_is_consulted_by_the_grid`, `::licence_key_is_build_time_only`, `::column_reorder_writes_layout_column_order`, `::freeze_and_hide_persist_through_layout`, `::range_selection_extends_and_copies_tsv`, `::formatted_date_uses_explicit_locale`
- Targeted command: `cargo xtask test-feature F062`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/design_system.ts` 10,000-row dataset and fixed clock `2026-09-03T00:00:00Z`; locale pinned to `en-US`/`UTC`

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Every pattern and the shell have stories in both themes and both densities
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S124
- [ ] `finished_at` recorded
