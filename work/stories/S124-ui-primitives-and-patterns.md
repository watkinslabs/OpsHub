---
id: S124
type: story
status: planned
parent_epic: E001
parent_feature: F062
depends_on: [S123]
owned_paths: [apps/web/src/ui/data/**, apps/web/src/ui/patterns/**, apps/web/src/ui/shell/**, apps/web/src/ui/icons.ts, apps/web/src/ui/index.ts, testing/features/F062/frontend/**, testing/features/F062/e2e/**, testing/features/F062/requirements/**]
feature_flag: F062_FEATURE
branch: s124-ui-primitives-and-patterns
started_at: null
finished_at: null
---

# S124 — UI primitives and patterns

## Identity

- Parent feature: `F062` Design system and UI primitives
- Owner: platform
- Branch: `s124-ui-primitives-and-patterns`
- Decision references: `docs/architecture-decisions.md` sections 5, 6; `docs/capability-contracts.md` row F062

## Vertical slice

As a product engineer building any OpsHub screen, I want the themed MUI set behind one import surface, the three MUI X data surfaces wrapped once, the composed states every feature ticket promises, and one application shell, so that I compose a feature from `apps/web/src/ui` instead of designing a button, a grid, an empty state and a page frame for the fifty-ninth time.

## Requirements

- **SR-S124-01:** `apps/web/src/ui/index.ts` re-exports the themed MUI vocabulary listed in the ticket as the single import surface, and lint fails on a direct `@mui/material` import or a duplicate component name under `apps/web/src/features/**` (covers FR-F062-09).
- **SR-S124-02:** `ui/data/DataGridPanel.tsx` wraps MUI X **Community** `DataGrid` with theme, density, virtualization above 100 rows, sticky header, column resize, selection, sorting, filtering and server-side pagination bound to the F028 cursor, plus its empty, error and denied states (FR-F062-10).
- **SR-S124-10:** One grid tier: grouping, tree rows, aggregation and xlsx export come from F013, F009, F022 and F010 and the grid never re-implements them; no paid grid package appears in the dependency tree or build graph and no upgrade prompt renders in the grid (FR-F062-16).
- **SR-S124-11:** `DataGridPanel` implements the F008 grid behaviours on the Community grid — reorder, freeze, hide, range and non-contiguous selection, clipboard TSV — writing through F008's `layout` field with a 1-second debounce, each with a keyboard path and an accessible announcement (FR-F062-17, FR-F008-10, FR-F008-14).
- **SR-S124-03:** `ui/data/ChartPanel.tsx` wraps MUI X `Charts` with the fixed five-series categorical palette, legend or direct labels so colour is never the only signal, and axis and grid colours from the border and text tokens; `ui/data/DateField.tsx` wraps the Date Pickers with the F049 locale and timezone and an `en-US`/`UTC` fallback (FR-F062-10, FR-F062-13).
- **SR-S124-04:** `ui/patterns/` exports `PageHeader`, `EmptyState`, `ErrorState`, `DeniedState`, `NotFoundState`, `OfflineBanner`, `StaleBanner`, `LoadingSkeleton`, `ConfirmDialog`, `FormLayout` and `FilterBar`, each taking copy as props with no hard-coded feature wording, and `ErrorState` always rendering `correlation_id` with a retry action (FR-F062-11, NFR-F062-04).
- **SR-S124-05:** `FormattedDate`, `FormattedNumber` and `RelativeTime` read locale and timezone from F049 context, always pass an explicit locale, and no component concatenates translated fragments (FR-F062-11).
- **SR-S124-06:** `AppShell` provides the 56px top bar, the persisted 240–400px rail, the optional inspector, the content region and one toast region, collapsing per the five breakpoints, and owns skip-to-content, `[`, `]` and `?`; F005 composes it rather than defining its own frame (FR-F062-12).
- **SR-S124-07:** `icons.ts` is the only module importing an icon package, exposes the stroke set at 14, 16, 20 and 24px, marks decorative icons `aria-hidden` and requires `title` on meaningful ones (FR-F062-14).
- **SR-S124-08:** Every export has stories covering its states in both themes and both densities, and the visual lane pins a deterministic screenshot per story that fails on a pixel diff above 0.1% (FR-F062-15, NFR-F062-04).
- **SR-S124-09:** No component renders raw HTML from props, links force `rel="noopener noreferrer"` with `target="_blank"`, the themed bundle stays under 210 KB gzipped with Data Grid and Charts in their own chunks, and a `fetch` spy proves no module under `apps/web/src/ui/**` performs a network call (NFR-F062-01, NFR-F062-02).

## Surfaces

- Infrastructure/container: none; stories build through the existing web pipeline from F001
- Rust service/API: none — F062 owns no Rust path
- Data/migration: none — the harness asserts no migration is added under this feature's owned paths
- React/UI: `apps/web/src/ui/{index.ts, icons.ts, data/{DataGridPanel.tsx, ChartPanel.tsx, DateField.tsx}, patterns/*.tsx, shell/{AppShell.tsx, TopBar.tsx, NavRail.tsx, InspectorPanel.tsx, ToastRegion.tsx}}` plus a `*.stories.tsx` beside each
- Mocks/fixtures: `testing/fixtures/design_system.ts` story matrix and the 10,000-row grid dataset; a `fetch` spy; screenshots at device pixel ratio 1 with animations disabled

## TDD harness

- Test path: `testing/features/F062/{frontend,e2e,requirements}/`
- Feature flag: `F062_FEATURE`
- Targeted command: `cargo xtask test-feature F062`
- Full command: `cargo xtask test-all`
- First failing tests: `direct_mui_import_fails_lint`, `no_paid_grid_package_in_build_graph`, `column_reorder_writes_layout_column_order`, `range_selection_extends_and_copies_tsv`, `data_grid_virtualizes_above_one_hundred_rows`, `chart_palette_is_fixed_and_labelled`, `error_state_renders_correlation_id_and_retry`, `app_shell_rail_width_persists_across_reload`, `icons_import_only_through_registry`, `formatted_date_uses_explicit_locale`, `ui_modules_perform_no_network_call`, `themed_bundle_under_budget`

## Exit criteria

- [ ] Requirement tests SR-S124-01 through SR-S124-09 written first and observed failing
- [ ] Tasks T247 and T248 complete
- [ ] Component, E2E, accessibility, visual and performance lanes pass in both themes and both densities
- [ ] Production call path named: `apps/web/src/ui/index.ts` is the single import surface; `AppShell` mounted by `apps/web/src/main.tsx`; the lint rules from ticket section 4 active in the `web` CI job
- [ ] Handoff evidence recorded in the F062 ticket
