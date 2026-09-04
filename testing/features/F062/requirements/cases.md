# F062 requirements cases

Feature: design system and UI primitives. Flag `F062_FEATURE`. Every case maps to a ticket requirement ID.

| Case | Requirement | Lane | Given / When / Then |
|---|---|---|---|
| `F062-REQ-001` | FR-F062-01 | accessibility, frontend | `tokens.css` declares the six scales with the specified values; and the lint set of ticket section 4 rejects each of: a spacing step off the 4px base, a raw hex, px or ms literal, a stylesheet outside `design/`, a direct vendor or icon-package import, a duplicate component name in a feature, an `sx` colour or typography key in a feature, `dangerouslySetInnerHTML`, and `any` or a silencing cast |
| `F062-REQ-002` | FR-F062-02 | accessibility, frontend | Plus Jakarta Sans and JetBrains Mono load from the repository with the documented fallbacks; the seven steps, four weights, `-0.02em` tracking above `--text-xl` and tabular numerals all match |
| `F062-REQ-003` | FR-F062-03 | accessibility | every semantic token carries the specified hex in light and in dark, including all three intent families; a literal reference in a component fails lint |
| `F062-REQ-004` | FR-F062-04 | e2e, accessibility | changing `--brand` from `#5b5bd6` to `#0e7c86` restyles every accent, selection and focus surface and nothing else; a hue breaking the contrast floor is refused with the failing pair named |
| `F062-REQ-005` | FR-F062-05 | e2e | light and dark define identical token names; `system` follows `prefers-color-scheme`; the stored choice applies before first paint with no flash on reload |
| `F062-REQ-006` | FR-F062-06 | accessibility | computed contrast over every pair in both themes for the default brand and all four presets: body ≥ 4.5:1, large text, icons, meaningful borders and focus ring ≥ 3:1 |
| `F062-REQ-007` | FR-F062-07 | e2e, frontend | `compact` changes controls to 24/28/34 and rows to 28px, persists across reload, and costs one style recalculation rather than one per row |
| `F062-REQ-008` | FR-F062-08 | frontend | the MUI theme reads palette, typography, radius, `spacing(1) = 4px`, z-index and durations from the tokens; a theme or density switch does not re-render the React tree |
| `F062-REQ-009` | FR-F062-09 | frontend | every listed MUI component is re-exported from `ui/index.ts` and renders themed; a direct `@mui/material` import or a duplicate component name in a feature fails lint |
| `F062-REQ-010` | FR-F062-10 | frontend, performance | `DataGridPanel` virtualizes above 100 rows with sticky header, resize, reorder, selection and cursor pagination; `ChartPanel` and `DateField` bind theme, palette, locale and timezone |
| `F062-REQ-011` | FR-F062-11 | frontend | every pattern takes copy as props; `ErrorState` renders `correlation_id` and retry; the five `LoadingSkeleton` shapes render; formatting components always pass an explicit locale |
| `F062-REQ-012` | FR-F062-12 | e2e | the shell renders top bar, rail, inspector, content and toast region; rail width persists; the rail becomes a drawer below `lg` and the inspector a sheet below `sm`; `[`, `]` and `?` work |
| `F062-REQ-013` | FR-F062-13 | frontend, accessibility | the five-series palette is fixed and in order, distinguishable under deuteranopia and protanopia simulation, and every series carries a legend entry, direct label or value |
| `F062-REQ-014` | FR-F062-14 | frontend | `icons.ts` is the only importer of an icon package; decorative icons are `aria-hidden`; meaningful icons require `title`; the four sizes align to the type scale |
| `F062-REQ-016` | FR-F062-16 | frontend, api | every pixel comes from MUI (core plus MIT MUI X Charts and Date Pickers) under one theme, TanStack supplies headless state only and renders no DOM of its own, and no other UI library is in the tree; no `@mui/x-data-grid`, `-pro` or `-premium` and no licence key anywhere in build or runtime |
| `F062-REQ-017` | FR-F062-17 | frontend, e2e, performance | a 100,000-row, 500-column sheet mounts at most 60 rows and 40 columns with `role="grid"` and `aria-rowindex`/`aria-colindex` on rendered cells; resize, reorder, hide, freeze persist through F008 `layout` within 1 s; Shift+Arrow, Shift+Click and Ctrl+Click selection and TSV clipboard copy work; grouping, tree rows, aggregation and export come from the F013, F009, F022 and F010 endpoints |
| `F062-REQ-015` | FR-F062-15 | performance | every export has stories for its states in both themes and both densities; the visual runner captures one deterministic screenshot per story |
| `F062-NFR-001` | NFR-F062-01 | performance | themed bundle < 210 KB gzipped with Data Grid and Charts in their own chunks; `tokens.css` < 12 KB; theme switch repaints a 1,000-row grid under 16 ms; 10,000-row scroll holds 60 fps |
| `F062-NFR-002` | NFR-F062-02 | api, frontend | no component uses `dangerouslySetInnerHTML`; `target="_blank"` forces `rel="noopener noreferrer"`; the theme bootstrap interpolates no stored value; no `ui/**` module performs a network call |
| `F062-NFR-003` | NFR-F062-03 | accessibility | axe reports zero serious or critical violations over every story in all four theme-density combinations; the keyboard walkthrough reaches every control; reduced motion collapses transitions to 1 ms |
| `F062-NFR-004` | NFR-F062-04 | api, database, performance | patterns hold no feature state and no network call; the feature adds no migration; a story screenshot diff above 0.1% fails the run |

Evidence: command, fixture seed, result, screenshot baseline, and artifact path recorded under `testing/evidence/F062/`.
