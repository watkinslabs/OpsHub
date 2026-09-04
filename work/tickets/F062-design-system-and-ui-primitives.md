---
id: F062
type: feature
status: planned
priority: P0
owner: platform
estimate: 13
target_milestone: M1
parent_epic: E001
depends_on: [F001]
blocks: [F005]
conflicts_with: []
parallel_safe: true
owned_paths: [apps/web/src/design/**, apps/web/src/ui/**, testing/features/F062/**]
feature_flag: F062_FEATURE
flag_default: off
branch: f062-design-system-and-ui-primitives
started_at: null
finished_at: null
---

# F062 — Design system and UI primitives

## 1. Identity and dates

- Branch: `f062-design-system-and-ui-primitives`
- Aggregate: `design-system`
- Capability area: web client foundation (spec section 6 internationalization and accessibility; section 7 UX consistency; every feature's section 3 UX specification depends on this one)
- Decision references: `docs/architecture-decisions.md` sections 5, 6; `docs/capability-contracts.md` row F062
- Module slug: `design-system`
- Visual source of truth: the OpsHub Design System canvas — token sheet, component library, chart gallery, and six reference screens in light and dark. Values in this ticket and the canvas must agree; the canvas is the picture, this ticket is the contract. The canvas link is in `docs/design-canvas.md`, the one file exempt from the forbidden-token scanner because the URL carries a vendor name.

## 2. Requirement specification

### Problem and user outcome

Fifty-nine feature tickets specify their own screens and each says "tokens from `apps/web/src/design/tokens.css`", but nothing defined what is in that file, and no one owned a shared component layer. Built as written, every feature would invent its own button, dialog, table, menu, toast, and empty state; the product would look like fifty-nine applications, accessibility would be re-litigated per feature, dark mode would be impossible to retrofit, and rebranding would mean a repaint.

OpsHub does not hand-roll a component library to fix that. It adopts MUI v7 as the component foundation and spends its effort on the part that is actually ours: a token set with real values, a theme that maps those tokens onto MUI, and the composites MUI does not have.

As a product engineer building any OpsHub feature, I want a themed MUI installation and a small set of OpsHub composites, so that I compose a screen instead of designing one; and as a customer, I want the whole product to carry my brand by changing one hue.

### Functional requirements

- **FR-F062-01:** `apps/web/src/design/tokens.css` defines every token as a CSS custom property on `:root` across six scales. Spacing is 4px-based: `--space-1:4px` through `--space-12:96px` (4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96). Radius is `--radius-sm:4px`, `-md:6px`, `-lg:10px`, `-full:9999px`. Elevation is `--shadow-1: 0 1px 2px rgba(16,20,28,.06), 0 1px 1px rgba(16,20,28,.04)`, `--shadow-2: 0 4px 12px rgba(16,20,28,.08), 0 1px 3px rgba(16,20,28,.05)`, `--shadow-3: 0 16px 40px rgba(16,20,28,.14), 0 4px 10px rgba(16,20,28,.07)`, with dark-theme equivalents. Motion is `--duration-fast:100ms`, `-base:150ms`, `-slow:250ms` with `--ease-standard`, `--ease-in`, `--ease-out`. Layer order is `--z-dropdown:1000`, `-sticky:1100`, `-drawer:1200`, `-dialog:1300`, `-popover:1400`, `-toast:1500`, `-tooltip:1600`. No component may use a raw hex, px, or ms literal where a token exists; `pnpm --filter web lint` fails on one.
- **FR-F062-02:** Typography is Plus Jakarta Sans for UI (weights 400, 500, 600, 700) and JetBrains Mono for numerics, identifiers, and code (400, 500), both self-hosted from `apps/web/src/design/fonts/` with `--font-sans` falling back to `ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif` and `--font-mono` to `ui-monospace, "SF Mono", "Cascadia Mono", monospace`. Steps are `--text-xs:12px/16px`, `-sm:13px/18px`, `-base:14px/20px`, `-lg:16px/24px`, `-xl:20px/28px`, `-2xl:24px/32px`, `-3xl:30px/38px`. Body default is `--text-base` at 400; grid and table cells use `--text-sm`; headings from `--text-xl` up carry `letter-spacing: -0.02em`. Every numeric column, identifier, timestamp, and measure renders in `--font-mono` with `font-variant-numeric: tabular-nums`. No size outside the scale.
- **FR-F062-03:** Color tokens are semantic and defined once per theme, with these values. Light: `--bg-canvas:#f6f7f9`, `--bg-surface:#ffffff`, `--bg-raised:#ffffff`, `--bg-sunken:#eff1f4`, `--bg-hover:#f1f3f6`, `--bg-active:#e6e9ee`, `--text-primary:#14171c`, `--text-secondary:#5b636f`, `--text-tertiary:#8c94a1`, `--text-inverse:#ffffff`, `--border-subtle:#edeff2`, `--border-default:#dee2e8`, `--border-strong:#c2c9d2`. Dark: `--bg-canvas:#0c0e12`, `--bg-surface:#14171d`, `--bg-raised:#1a1e25`, `--bg-sunken:#0f1216`, `--bg-hover:#1e232b`, `--bg-active:#262c35`, `--text-primary:#eef1f5`, `--text-secondary:#a2abb8`, `--text-tertiary:#6f7885`, `--text-inverse:#0c0e12`, `--border-subtle:#1e232b`, `--border-default:#2a313a`, `--border-strong:#3d4650`. Intent families carry `-bg`, `-fg`, `-border`, `-emphasis`: light success `#e9f7ef / #0f6d39 / #b6e2c8 / #17a35a`, warning `#fdf3e2 / #8a5806 / #f2dba6 / #d98207`, danger `#fdeded / #a41c1c / #f4c5c5 / #dc2b2b`; dark success `#0f2a1c / #6ee7a8 / #1d4c33 / #22c46e`, warning `#2c2010 / #f0c073 / #4d3a18 / #e0930f`, danger `#2d1516 / #f5a3a3 / #552527 / #e5484d`. A component referencing a literal rather than a semantic token fails lint.
- **FR-F062-04:** One variable brands the product. `--brand` defaults to `#5b5bd6`, and `--accent-bg`, `--accent-fg`, `--accent-border`, `--accent-emphasis`, `--bg-selected`, and `--focus-ring` are all derived from it with `color-mix(in oklch, …)` per theme rather than being authored separately. Setting `--brand` on the app root rebrands every accent, selection, and focus surface with no other change; a tenant brand hue that fails the FR-F062-06 contrast floor is rejected at save time with the failing pair named, and the deployment presets `#5b5bd6`, `#0e7c86`, `#b4530a`, `#1f6feb` all pass.
- **FR-F062-05:** Two themes ship: `light` on `:root` and `dark` under `[data-theme="dark"]`, both defining the identical token name set. `[data-theme="system"]` (the default) resolves through `prefers-color-scheme`. The choice persists per viewer in `localStorage` key `opshub.theme` and is applied before first paint by a static inline script in `apps/web/index.html`, so no frame renders in the wrong theme. A token defined in one theme but not the other fails the parity test.
- **FR-F062-06:** Every text, icon, border, and focus pair meets WCAG 2.2 AA in both themes: 4.5:1 for body text, 3:1 for text at `--text-lg` and above and for icons and borders that carry meaning. `--focus-ring` reaches 3:1 against both the adjacent surface and the component it outlines. Contrast is asserted by computation over the token file for the default brand and each preset, not by inspection.
- **FR-F062-07:** Density is a token set, not a prop: `[data-density="comfortable"]` (default) defines `--control-sm:28px`, `--control-md:32px`, `--control-lg:40px`, `--row-h:36px`; `[data-density="compact"]` redefines them to 24, 28, 34, and 28px. Density is set on the app root, persists in `localStorage` key `opshub.density`, and every control derives its height from these tokens rather than a fixed value, so switching costs one style recalculation and not one per row.
- **FR-F062-08:** The MUI v7 theme in `apps/web/src/design/theme.ts` is the single binding between tokens and components: `palette` (mode, primary from `--brand`, `background.default|paper`, `text.primary|secondary|disabled`, `divider`, and `success|warning|error|info` from the intent families), `typography` (the seven steps and both families), `shape.borderRadius` 6, `spacing(1) = 4px`, `zIndex` from the layer tokens, `transitions.duration` from the motion tokens, and `components` overrides setting default sizes from the density tokens. Tokens reach the theme through CSS variables, so a theme or density switch is a CSS change and never a React re-render of the tree.
- **FR-F062-09:** Features consume MUI components directly for the standard vocabulary — `Button`, `IconButton`, `TextField`, `Select`, `Autocomplete`, `Checkbox`, `Radio`, `Switch`, `Slider`, `Dialog`, `Drawer`, `Popover`, `Tooltip`, `Menu`, `Tabs`, `Accordion`, `Snackbar`, `Alert`, `Chip`, `Badge`, `Avatar`, `CircularProgress`, `Skeleton`, `Table`, `Pagination`, `Breadcrumbs`, `ToggleButtonGroup`, `Divider` — and no feature may define its own version of one. A duplicate component name under `apps/web/src/features/**` fails lint. `apps/web/src/ui/index.ts` re-exports the themed set so a feature has one import surface and the theme cannot be bypassed.
- **FR-F062-10:** Three wrapped data surfaces serve every feature rather than hand-built equivalents per screen: the TanStack-based `DataGridPanel` of FR-F062-16 backs the sheet grid, admin tables, and every list (virtualization above 100 rows, sticky header, column resize, single and multiple selection, sorting, filtering, and server-side pagination bound to the F028 cursor), MUI X `Charts` backs every widget in F022–F024, and MUI X `DatePickers` backs every date and range field with the F049 locale and timezone. Each is wrapped once in `apps/web/src/ui/data/` to bind theme, density, locale, and empty and error states; features use the wrapper, never the raw import.
- **FR-F062-11:** `apps/web/src/ui/patterns/` supplies the composites MUI does not have, which every feature ticket's §3 already promises: `PageHeader`, `EmptyState`, `ErrorState` (renders `correlation_id` and a retry action), `DeniedState`, `NotFoundState`, `OfflineBanner`, `StaleBanner`, `LoadingSkeleton` (list, table, tree, card, detail shapes), `ConfirmDialog`, `FormLayout`, `FilterBar`, and the locale-aware `FormattedDate`, `FormattedNumber`, and `RelativeTime`. Each takes its copy as props; none hard-codes feature wording, and none calls `toLocaleString` without an explicit locale.
- **FR-F062-12:** `AppShell` in `apps/web/src/ui/shell/` defines the frame every route renders inside: a 56px top bar, a left navigation rail (collapsed 56px, expanded 240–400px, width persisted per viewer), an optional right inspector panel, the content region, and one global toast region. Breakpoints are `--bp-sm:640px`, `-md:768px`, `-lg:1024px`, `-xl:1280px`, `-2xl:1536px`; below `--bp-lg` the rail collapses to a drawer and below `--bp-sm` the inspector becomes a sheet. The shell owns skip-to-content, `[` and `]` to toggle rail and inspector, and `?` for the shortcut sheet. F005 composes this shell rather than defining its own.
- **FR-F062-13:** Charts use one fixed categorical series palette in order — `var(--brand)`, `#0e9aa7`, `#e0930f`, `#d6558f`, `#5aa06b` — distinguishable under deuteranopia and protanopia, and no chart uses color as its only signal: every series carries a legend entry, a direct label, or a value. Sequential scales derive from a single hue by lightness; the axis, grid, and label colors come from the border and text tokens.
- **FR-F062-14:** Icons come from one registry, `apps/web/src/ui/icons.ts`, exporting a stroke set on a 24px grid at sizes 14, 16, 20, and 24 aligned to the type scale. A decorative icon is `aria-hidden`; a meaningful one takes a required `title`. Importing an icon package directly from a feature module fails lint.
- **FR-F062-16:** One visual system, one headless engine, no mixed concerns. **Every pixel comes from MUI**: MUI core for the component vocabulary and the MIT parts of MUI X — Charts and Date Pickers — for charts and dates, all under the single OpsHub theme from FR-F062-08. **TanStack contributes no markup and no styles**: `@tanstack/react-table` and `@tanstack/react-virtual` are headless state and virtualization only, and their output renders through the same themed MUI components as everything else, so the grid is not a second design system wearing a costume. No third UI library may enter `apps/web` — a component, chart or date library beyond those two MUI packages fails the dependency test — so there is one theme, one density model, one accessibility model and one set of APIs to learn. The grid carries no licence and no per-seat cost. `DataGridPanel` is built on TanStack Table v8 with TanStack Virtual (both MIT), rendered with the themed MUI Community components and the tokens above, so the grid matches the rest of the product visually while remaining free for commercial use. No `@mui/x-data-grid`, `-pro` or `-premium` package appears in the dependency tree, no licence key exists anywhere in the build or runtime, and no watermark can ship; a dependency test fails the build if a licensed grid package is added. MUI X Charts and Date Pickers are MIT and stay, keeping charts and dates inside the same MUI family as the rest of the UI rather than introducing another vendor's look.
- **FR-F062-17:** The wrapper supplies every grid behaviour F008 requires from TanStack state plus its own rendering: virtualized rows and columns holding a 100,000-row, 500-column sheet at F008's render budget; column resize, reorder, hide and freeze bound to F008's `layout` field with a 1-second debounce (`columnSizing`, `columnOrder`, `columnVisibility` and `columnPinning` state); range selection extended by Shift+Arrow and Shift+Click with non-contiguous Ctrl+Click; clipboard copy emitting TSV that pastes into a spreadsheet with visible formatting; and inline cell editors from F007's typed columns. Because the rows are real DOM rather than a canvas, the grid carries `role="grid"` with `aria-rowindex` and `aria-colindex` on virtualized cells as F008 NFR-F008-03 requires. Server-owned capabilities stay server-owned and are rendered, never re-implemented: row grouping from F013 `settings.group_by`, tree rows from F009 `row_hierarchy`, aggregation from F022 metrics, and file export from F010 `POST /api/v1/exports`. `ui/data/` is the only place the table library is imported, so the engine can be replaced without touching a feature.
- **FR-F062-15:** Every themed component, wrapper, and pattern has a story in `apps/web/src/ui/**/*.stories.tsx` covering its states (default, hover, focus, disabled, loading, error, empty where applicable) in both themes and both densities; `pnpm --filter web storybook` builds them and the visual harness renders each story deterministically.

### Non-functional requirements

- **NFR-F062-01 Performance:** the themed UI bundle is under 210 KB gzipped excluding MUI X Data Grid and Charts, which load in their own chunks on first use; `tokens.css` is under 12 KB; theme and density switches repaint a 1,000-row grid without a reflow over 16 ms and never re-render the React tree; `DataGrid` holds 60 fps scrolling 10,000 rows.
- **NFR-F062-02 Security/privacy:** no component renders raw HTML from props (no `dangerouslySetInnerHTML`), every link forces `rel="noopener noreferrer"` with `target="_blank"`, the theme bootstrap is a static inline literal that interpolates no stored value, and no module under `apps/web/src/ui/**` performs a network call.
- **NFR-F062-03 Accessibility:** every story passes axe with zero serious or critical violations in both themes and both densities; a keyboard-only walkthrough reaches and operates every interactive element of every pattern and the shell; the focus ring shows on `:focus-visible` only; contrast is verified by computation; under `prefers-reduced-motion: reduce` no transition exceeds 1 ms and no state relies on movement alone.
- **NFR-F062-04 Reliability/observability:** patterns carry no feature state and no network call; `ErrorState` always surfaces `correlation_id`; the visual harness pins each story to a deterministic screenshot and fails on a pixel diff above 0.1%, so a token or theme change cannot silently restyle fifty-nine features.

### Scope

Included: the token file with the values above, light and dark themes with pre-paint resolution, the brand-hue derivation and its contrast gate, comfortable and compact density, the MUI v7 theme mapping, the re-export surface, the three MUI X wrappers, the OpsHub pattern composites, the application shell and breakpoints, the categorical chart palette, the icon registry, locale-aware formatting, stories for every state, and the visual, accessibility, and contrast harnesses.

Excluded: row grouping (F013), tree data (F009), aggregation (F022) and file export (F010), which are server capabilities this feature renders but never re-implements; the cell editing, bulk edit, undo and layout persistence semantics themselves (F008 — this feature supplies the grid surface they drive); feature screens themselves (each feature ticket), workspace navigation content and routing (F005), locale and timezone resolution (F049 — consumed here with a documented fallback), sheet-specific grid behavior such as formulas and cell editors (F008 composes the `DataGrid` wrapper), chart data queries and widget definitions (F022–F024 use the palette and wrapper), sharing and publishing surfaces (F036, F059, F061), and any marketing or brand site styling.

## 3. UX specification

- Entry points: not user-facing on its own. Developers browse `pnpm --filter web storybook`; users meet it through every screen. The theme, density, and brand controls are rendered by F005's user menu and tenant settings and read and write the tokens this feature defines.
- Primary flow: an engineer building a screen imports `Button`, `TextField`, `DataGridPanel`, `EmptyState`, and `PageHeader` from `apps/web/src/ui`, passes copy and data, and receives correct theme, density, focus, keyboard, locale, and accessibility behavior without writing CSS.
- Loading: `Skeleton` and `LoadingSkeleton` shapes per surface. Empty: `EmptyState` with icon, headline, body, and one primary action. Error: `ErrorState` with `correlation_id` and retry. Denied: `DeniedState` naming the missing permission without leaking the resource. Success: `Snackbar` in the shell's toast region. Stale: `StaleBanner`. Offline: `OfflineBanner` with mutations disabled.
- Responsive: the five breakpoints in FR-F062-12; every surface is usable at 320px; the `DataGrid` scrolls horizontally inside its own container and never the page.
- Keyboard: MUI's pattern behavior plus the shell shortcuts; the focus ring is visible on `:focus-visible` only.
- Font/icon/design tokens: this feature defines them — Plus Jakarta Sans and JetBrains Mono self-hosted from `apps/web/src/design/fonts/`, icons through `apps/web/src/ui/icons.ts`.

## 4. Technical specification

### Rust backend

- None. F062 is a web-only feature and owns no Rust path, no route, no event, no table, and therefore no repository class under `crates/persistence` (decision 2.1); the catalog row lists its surface as `apps/web/src/design/**`, `apps/web/src/ui/**`, `pnpm --filter web storybook`, and `pnpm --filter web test:ui`. Nothing here reaches the API, and the harness asserts that absence.

### PostgreSQL/SQLx

- None. No migration, no table, no query. Theme, density, and rail width are per-viewer browser state in `localStorage` (`opshub.theme`, `opshub.density`, `opshub.rail`); the tenant brand hue is stored by F002 tenant settings and applied here as `--brand`. Rollback is removal of the `F062_FEATURE` flag and the `apps/web/src/ui` barrel export; there is nothing to revert in the database.

### React/TypeScript

- Files: `apps/web/src/design/{tokens.css, themes/{light.css, dark.css}, density.css, typography.css, theme.ts, brand.ts, fonts/}`; `apps/web/src/ui/{index.ts, icons.ts, ThemeProvider.tsx, data/{DataGridPanel.tsx, ChartPanel.tsx, DateField.tsx}, patterns/*.tsx, shell/{AppShell.tsx, TopBar.tsx, NavRail.tsx, InspectorPanel.tsx, ToastRegion.tsx}, internal/{focus.ts, usePersistedState.ts, useMediaQuery.ts}}`.
- Dependencies: `@mui/material` v7 with `@emotion/react` and `@emotion/styled`, `@tanstack/react-table` and `@tanstack/react-virtual` as headless grid state, `@mui/x-charts` and `@mui/x-date-pickers` for charts and dates. Every one is MIT: the product carries no commercial UI licence, no per-seat cost and no key. This is the complete list of UI-bearing dependencies; adding another component, chart or date library is a change to this ticket, not a library choice. The trade is that the grid's rendering is ours to write, which section 7 records as the cost of this choice. MUI's CSS-variables theme mode is enabled so theme and density switch without re-rendering the tree.
- `ui/data/gridLayout.ts` binds the grid's column order, widths, hidden set and frozen count to F008's `layout` field with a 1-second debounce, and `ui/data/gridSelection.ts` implements range and non-contiguous selection with the clipboard TSV writer. These are the two places any later vendor-grid change would touch.
- `brand.ts` exposes `deriveBrand(hue)` returning the accent, selection, and focus tokens by `color-mix`, plus `validateBrand(hue)` running the FR-F062-06 contrast check that tenant settings calls before saving.
- State: no global store. `ThemeProvider` wraps MUI's provider and reads `localStorage` with the pre-paint bootstrap; the toast region owns a queue capped at 5 with a 6-second dismissal that pauses on hover and focus.
- Lint: an ESLint rule set banning raw color, spacing, radius, and duration literals under `apps/web/src/**`, direct MUI or icon-package imports outside `apps/web/src/ui`, `dangerouslySetInnerHTML`, and redefinition of a re-exported component name inside `apps/web/src/features/**`.
- Telemetry: `theme_changed`, `density_changed`, `brand_changed`, `shortcut_sheet_opened` with the resolved value; components emit nothing else.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F062-01 through FR-F062-15 in `testing/features/F062/requirements/cases.md`
- [ ] Failure/edge-case tests: token present in light but not dark, raw hex in a component, brand hue failing contrast, feature importing MUI directly, toast queue overflow past 5, reduced-motion with an animation-only state
- [ ] Permission-negative and tenant-isolation tests: not applicable — F062 owns no route, no data, and no tenant-scoped state; the harness asserts instead that no module under `apps/web/src/ui/**` performs a network call
- [ ] Rust unit tests: none; this feature owns no Rust path
- [ ] API contract/integration tests: none; the harness asserts the absence of network calls instead
- [ ] Database migration/constraint tests: none; the harness asserts no migration file is added under this feature's owned paths
- [ ] React component tests: the theme mapping, every wrapper and pattern, controlled and uncontrolled state, and keyboard interaction
- [ ] Browser E2E tests: theme switch with no flash on reload, density switch, brand switch, shell rail and inspector persistence, shortcut sheet
- [ ] Accessibility tests: axe over every story in both themes and densities, keyboard-only walkthrough, computed contrast over the token file for every brand preset, focus-visible-only ring
- [ ] Performance/load tests: bundle budgets, token file size, 10,000-row `DataGrid` scroll, theme switch repaint

### Fast fanout configuration

- Test harness path: `testing/features/F062/`
- Feature flag: `F062_FEATURE`
- Fixture/seed factory: `testing/fixtures/design_system.ts` builds the story matrix (every export × states × 2 themes × 2 densities), a 10,000-row grid dataset, a 1,000-row repaint dataset, the four brand presets, and a fixed locale `en-US` with timezone `UTC`
- Deterministic test data: fixed clock `2026-09-03T00:00:00Z`, fonts loaded from the repository rather than the network, animations disabled during capture, device pixel ratio 1
- Mock/stub contracts: no API mocks are needed; a `fetch` spy asserts zero calls from `apps/web/src/ui/**`
- Parallel isolation: stories render in isolated browser contexts per worker; screenshot baselines are keyed by story id, theme, and density
- Targeted command: `cargo xtask test-feature F062`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F062/`

## 6. Acceptance criteria

```gherkin
Feature: One themed foundation every feature composes

Scenario: Rebranding is one variable
  Given the tenant brand hue is changed from #5b5bd6 to #0e7c86
  When any screen renders
  Then every accent, selection and focus surface uses the new hue
  And no other token, stylesheet or component changed

Scenario: A brand hue that fails contrast is refused
  Given an administrator enters a brand hue whose focus ring falls below 3:1 on the dark surface
  When they save
  Then the save is refused and the failing pair is named

Scenario: Dark theme has no missing tokens and no flash
  Given a viewer whose stored theme is dark
  When the app loads
  Then every token name defined in light is defined in dark
  And the first painted frame is already dark

Scenario: A feature cannot bypass the theme
  Given a feature module that imports Button from @mui/material directly
  When pnpm --filter web lint runs
  Then the run fails naming the direct import

Scenario: Every grid capability ships to every tenant at no licence cost
  Given any tenant on any plan
  When a sheet grid renders
  Then pinning, reorder, range selection, clipboard copy, grouping, tree rows and xlsx export all work
  And the dependency tree contains no licensed grid package and no licence key

Scenario: The grid stays accessible at 100,000 rows
  Given a sheet of 100,000 rows and 500 columns
  When the grid mounts
  Then at most 60 rows and 40 columns are rendered
  And each rendered cell carries aria-rowindex and aria-colindex inside role="grid"

Scenario: Column reorder persists through the F008 layout field
  Given an editor drags a column to a new position
  When the layout is saved within one second
  Then F008 layout.column_order records the new order for that user
  And another user's column order is unchanged

Scenario: Reduced motion removes animation without removing meaning
  Given prefers-reduced-motion is reduce
  When a toast appears and a dialog opens
  Then no transition exceeds 1ms and both still convey their state through text and position
```

- [ ] Every functional requirement has an executable acceptance test.
- [ ] Every non-functional requirement has a measurable verification method.

## 7. Dependencies and risks

- Depends on: F001 (pnpm workspace, Vite, React and TypeScript baseline, `web` CI job); decisions sections 5 and 6; contracts row F062
- Blocks: F005, and in practice every feature with a React surface — none should build screens before this lands
- Conflicts with: none; `apps/web/src/design/**` and `apps/web/src/ui/**` are owned by this feature alone and F001 no longer claims `tokens.css`
- External dependencies: MUI v7 with Emotion, MUI X Data Grid, Charts and Date Pickers, Plus Jakarta Sans and JetBrains Mono (vendored), axe for the accessibility lane, a deterministic screenshot runner for the visual lane
- Risks and mitigations: MUI major-version churn, mitigated by consuming it only through the re-export surface and the three wrappers so an upgrade touches one directory; the grid being a headless engine means its rendering, virtualization, selection and clipboard behaviour are ours to build and maintain — a real cost accepted deliberately over a per-seat licence, mitigated by confining it to `ui/data/` behind the wrapper seam, by F008 already specifying the behaviour in detail, and by the story matrix and the 100,000-row performance lane guarding it; the engine proving insufficient later, mitigated by the same seam so a swap touches one directory; a token change silently restyling fifty-nine features, mitigated by pinned visual baselines failing on a 0.1% diff; features drifting by importing MUI directly or writing local CSS, mitigated by the lint rules in section 4 and the owned-path gate; over-theming MUI until upgrades are painful, mitigated by keeping overrides to the token mapping and default sizes rather than restyling internals
- Open questions: none. The grid engine is settled: TanStack Table with TanStack Virtual, MIT, no licence and no seat cost, rendered with themed MUI Community components. MUI X Charts and Date Pickers stay because they are MIT too.

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F001 accepted and archived so the pnpm workspace and `web` CI job exist
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F062/`
- [ ] Owned paths claimed and `tokens.css` released by F001
- [ ] MUI v7, TanStack Table and Virtual, MUI X Charts and Date Pickers, Plus Jakarta Sans and JetBrains Mono vendored; no licensed UI package in the tree

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] React component, E2E, accessibility, visual, and performance gates pass in both themes and both densities
- [ ] Token parity and computed contrast pass for every brand preset; no raw color, spacing, radius, or duration literal exists under `apps/web/src/**`; no feature imports MUI or the table engine directly; the dependency test confirms no licensed grid package and no licence key exist
- [ ] Every changed file ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disabling `F062_FEATURE` falls back to the unstyled `/status` baseline without a build error
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Establishes the OpsHub design language and its component foundation: a token set with fixed values, light and dark themes with system resolution, a brand hue that rebrands the product through one variable, comfortable and compact density, and a themed MUI v7 installation with MUI X Data Grid, Charts and Date Pickers that every feature composes instead of reinventing.
- No migration and no API change. The feature is off by default behind `F062_FEATURE`; enabling it switches the app shell and every screen onto the token set.
