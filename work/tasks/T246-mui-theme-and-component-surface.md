---
id: T246
type: task
status: planned
parent_epic: E001
parent_feature: F062
parent_story: S123
depends_on: [T245]
owned_paths: [apps/web/src/design/theme.ts, apps/web/src/ui/ThemeProvider.tsx, apps/web/src/ui/internal/**, apps/web/src/ui/index.ts, apps/web/src/ui/icons.ts, testing/features/F062/frontend/**]
feature_flag: F062_FEATURE
branch: t246-mui-theme-and-component-surface
started_at: null
finished_at: null
---

# T246 — MUI theme and component surface

## Identity

- Parent story: `S123` Design tokens and theming
- Owner: platform
- Branch: `t246-mui-theme-and-component-surface`
- Decision references: `docs/architecture-decisions.md` sections 5, 6; `docs/capability-contracts.md` row F062

## Objective

Map the tokens onto the MUI v7 theme, stand up the provider and the single re-export surface features import from, build the icon registry, and add the lint rules that stop a feature bypassing any of it.

## Specification

- Owned paths: `apps/web/src/design/theme.ts`, `apps/web/src/ui/{ThemeProvider.tsx, index.ts, icons.ts, internal/{focus.ts, usePersistedState.ts, useMediaQuery.ts}}`, and the ESLint rule set the `web` package runs.
- Contract/input: the token names from T245; MUI v7 with Emotion; the component list in FR-F062-09 — `Button`, `IconButton`, `TextField`, `Select`, `Autocomplete`, `Checkbox`, `Radio`, `Switch`, `Slider`, `Dialog`, `Drawer`, `Popover`, `Tooltip`, `Menu`, `Tabs`, `Accordion`, `Snackbar`, `Alert`, `Chip`, `Badge`, `Avatar`, `CircularProgress`, `Skeleton`, `Table`, `Pagination`, `Breadcrumbs`, `ToggleButtonGroup`, `Divider`.
- Output/behavior: `theme.ts` builds the MUI theme from the CSS variables — `palette` (mode, primary from `--brand`, `background.default|paper`, `text.primary|secondary|disabled`, `divider`, `success|warning|error|info` from the intent families), `typography` (the seven steps, both families, the four weights), `shape.borderRadius` 6, `spacing(1) = 4px`, `zIndex` from the layer tokens, `transitions.duration` from the motion tokens, and `components` overrides taking default sizes from the density tokens; MUI's CSS-variables mode is enabled so a theme or density switch never re-renders the tree. `ThemeProvider` wraps MUI's provider, reads `localStorage` after the pre-paint bootstrap, and exposes theme, density and brand to the app. `index.ts` re-exports the themed component list as the only import surface. `icons.ts` is the only module importing an icon package and exposes the stroke set at 14, 16, 20 and 24px with `aria-hidden` on decorative icons and a required `title` on meaningful ones. The lint rules fail a raw color, spacing, radius or duration literal under `apps/web/src/**`, a direct `@mui/material` or icon-package import outside `apps/web/src/ui`, `dangerouslySetInnerHTML`, and a re-exported component name redefined under `apps/web/src/features/**`.
- Dependencies: T245 tokens; F001 web workspace and CI job; `@mui/material` v7 with `@emotion/react` and `@emotion/styled`.
- Feature flag: `F062_FEATURE` gates the `apps/web/src/ui` barrel export; nothing imports these files while it is off.

## TDD

- Failing test first: `testing/features/F062/frontend/theme_tests.tsx::mui_theme_reads_every_token`, `::palette_tracks_the_brand_variable`, `::spacing_unit_is_four_px`, `::component_defaults_follow_density_tokens`, `::theme_switch_does_not_rerender_tree`; `testing/features/F062/frontend/surface_tests.tsx::every_listed_component_is_re_exported`, `::themed_button_renders_all_variants_and_sizes`, `::focus_ring_only_on_focus_visible`; `testing/features/F062/frontend/lint_tests.ts::direct_mui_import_fails_lint`, `::duplicate_component_name_in_feature_fails_lint`, `::raw_color_literal_fails_lint`, `::icons_import_only_through_registry`
- Targeted command: `cargo xtask test-feature F062`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/design_system.ts` story matrix over states × 2 themes × 2 densities; a `fetch` spy asserting zero calls

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Every re-exported component has stories for its states in both themes and both densities
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S123
- [ ] `finished_at` recorded
