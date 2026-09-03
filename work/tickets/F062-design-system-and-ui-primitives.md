---
id: F062
type: feature
status: planned
priority: P0
owner: platform
estimate: 8
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

## 2. Requirement specification

### Problem and user outcome

Fifty-nine feature tickets specify their own screens and each says "tokens from `apps/web/src/design/tokens.css`", but nothing defines what is in that file, and no one owns a shared component layer. Built as written today, every feature would invent its own button, dialog, table, menu, toast, and empty state, and the product would look and behave like fifty-nine separate applications. Accessibility would be re-litigated per feature, dark mode would be impossible to add later, and the density and keyboard rules each ticket promises would drift immediately.

As a product engineer building any OpsHub feature, I want one token set and one primitive library with settled behavior, focus, density, and theming, so that I compose a screen instead of designing one, and so a user moving between sheets, dashboards, and admin sees a single product.

### Functional requirements

- **FR-F062-01:** `apps/web/src/design/tokens.css` defines every token as a CSS custom property on `:root` in six scales: color, spacing, radius, type, elevation, and motion. Spacing is `--space-0:0` then `--space-1:4px` through `--space-12:96px` on a 4px base (4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96). Radius is `--radius-sm:4px`, `-md:6px`, `-lg:10px`, `-full:9999px`. Elevation is `--elevation-0` through `--elevation-3` as composed `box-shadow` values. No component may use a raw hex, px, or ms value for any property a token covers; `pnpm --filter web lint` fails on one.
- **FR-F062-02:** The type scale is Inter variable, self-hosted from `apps/web/src/design/fonts/`, with `--font-sans` falling back to `system-ui, -apple-system, "Segoe UI", Roboto, sans-serif` and `--font-mono` to `ui-monospace, "SF Mono", "Cascadia Mono", monospace`. Steps are `--text-xs:12px/16px`, `-sm:13px/18px`, `-base:14px/20px`, `-lg:16px/24px`, `-xl:20px/28px`, `-2xl:24px/32px`, `-3xl:30px/38px`, with weights `--weight-regular:400`, `-medium:500`, `-semibold:600`. Body default is `--text-base` at `--weight-regular`; the grid uses `--text-sm`; no component introduces a size outside the scale.
- **FR-F062-03:** Color tokens are semantic, never literal: `--bg-canvas`, `--bg-surface`, `--bg-raised`, `--bg-sunken`, `--bg-hover`, `--bg-active`, `--bg-selected`, `--text-primary`, `--text-secondary`, `--text-tertiary`, `--text-inverse`, `--border-subtle`, `--border-default`, `--border-strong`, `--focus-ring`, plus intent families `--accent-*`, `--success-*`, `--warning-*`, `--danger-*`, `--info-*` each with `-bg`, `-fg`, `-border`, and `-emphasis`. Each is defined once per theme; a component referencing a literal palette variable rather than a semantic one fails lint.
- **FR-F062-04:** Two themes ship: `light` on `:root` and `dark` under `[data-theme="dark"]`, both defining the identical token names. `[data-theme="system"]` (the default) resolves through `prefers-color-scheme`. The choice persists per user in `localStorage` key `opshub.theme` and is applied before first paint by an inline script so no flash of the wrong theme occurs. A token defined in one theme but not the other fails the token parity test.
- **FR-F062-05:** Every text and icon token pair meets WCAG 2.2 AA in both themes: 4.5:1 for body text, 3:1 for text at `--text-lg` and above and for icons and borders that carry meaning. `--focus-ring` reaches 3:1 against both the adjacent surface and the component it outlines. Contrast is asserted by a computed test over the token file, not by inspection.
- **FR-F062-06:** Density is a first-class token set: `[data-density="comfortable"]` (default) and `[data-density="compact"]` redefine `--control-height-sm|md|lg` (28/32/40px comfortable, 24/28/34px compact), `--control-padding-x`, and `--row-height` (36px / 28px). Density is set on the app root, persists in `localStorage` key `opshub.density`, and every primitive derives its size from these tokens rather than fixed values.
- **FR-F062-07:** `apps/web/src/ui/` exports the primitive layer, each a typed React 19 component with a documented prop contract: `Button` (variants `primary|secondary|ghost|danger`, sizes `sm|md|lg`, `loading`, `iconOnly`), `IconButton`, `Input`, `Textarea`, `Select`, `Combobox`, `Checkbox`, `Radio`, `Switch`, `Slider`, `DatePicker`, `Label`, `FieldError`, `Field`, `Dialog`, `Drawer`, `Popover`, `Tooltip`, `Menu`, `Tabs`, `Accordion`, `Toast`, `Banner`, `Badge`, `Avatar`, `Spinner`, `Skeleton`, `Table`, `Pagination`, `Breadcrumb`, `SegmentedControl`, `ContextMenu`, `Separator`, `VisuallyHidden`. No feature may define its own version of a listed primitive; the owned-path gate and a lint rule banning duplicate component names enforce it.
- **FR-F062-08:** Overlay primitives (`Dialog`, `Drawer`, `Popover`, `Tooltip`, `Menu`, `ContextMenu`, `Combobox`, `Select`) are built on a single focus-management module: focus moves into the overlay on open, is trapped while open, returns to the invoking element on close, `Escape` closes the topmost layer only, and a layer stack prevents a nested overlay from closing its parent. Scroll is locked without layout shift, and the trigger is marked `aria-expanded` and `aria-controls`.
- **FR-F062-09:** `apps/web/src/ui/patterns/` exports the composed states every feature ticket promises, so none reimplements them: `PageHeader`, `EmptyState`, `ErrorState` (renders `correlation_id` and a retry action), `DeniedState`, `NotFoundState`, `OfflineBanner`, `StaleBanner` (renders "This record changed" with reload), `LoadingSkeleton` (list, table, tree, card, and detail shapes), `ConfirmDialog`, `FormLayout`, `FilterBar`, and `DataTable` (selection, sticky header, column resize, virtualized rows). Each accepts the copy as props; none hard-codes feature wording.
- **FR-F062-10:** `AppShell` in `apps/web/src/ui/shell/` defines the application frame every route renders inside: a 56px top bar, a resizable left navigation rail (collapsed 56px, expanded 240–400px, persisted per user), an optional right inspector panel, the content region, and a global toast region. Breakpoints are `--bp-sm:640px`, `-md:768px`, `-lg:1024px`, `-xl:1280px`, `-2xl:1536px`; below `--bp-lg` the rail collapses to a drawer, below `--bp-sm` the inspector becomes a sheet. F005 composes this shell rather than defining its own.
- **FR-F062-11:** Every interactive primitive is reachable and operable by keyboard alone, exposes a visible `--focus-ring` on `:focus-visible` only, and carries the ARIA role, name, and state its pattern requires. Composite widgets (`Menu`, `Tabs`, `Combobox`, `Table`, `SegmentedControl`) implement roving tabindex with arrow, `Home`, `End`, and type-ahead per the WAI-ARIA authoring practice they name in their source doc comment.
- **FR-F062-12:** All motion is token-driven: `--duration-fast:100ms`, `-base:150ms`, `-slow:250ms`, and `--ease-standard`, `--ease-in`, `--ease-out`. Under `prefers-reduced-motion: reduce`, every transition and animation is reduced to `1ms` and no component uses movement as its only state signal.
- **FR-F062-13:** Icons come from one registry, `apps/web/src/ui/icons.ts`, re-exporting the Lucide set the tickets name, at sizes 14, 16, 20, and 24 aligned to the type scale; a decorative icon is `aria-hidden`, a meaningful one takes a required `title`. Importing directly from `lucide-react` in a feature module fails lint.
- **FR-F062-14:** Copy and formatting primitives are locale-aware from the start: `FormattedDate`, `FormattedNumber`, and `RelativeTime` take the tenant timezone and locale from F049 context, fall back to `en-US` and UTC before F049 ships, and never call `toLocaleString` without an explicit locale. No component concatenates translated fragments.
- **FR-F062-15:** Every primitive and pattern has a story in `apps/web/src/ui/**/*.stories.tsx` covering its states (default, hover, focus, disabled, loading, error, empty where applicable) in both themes and both densities; `pnpm --filter web storybook` builds them and the visual harness renders each story deterministically.

### Non-functional requirements

- **NFR-F062-01 Performance:** the primitive bundle is under 90 KB gzipped excluding icons and fonts; `tokens.css` is under 12 KB; theme and density switches repaint without a reflow over 16 ms on a 1,000-row `DataTable`; `DataTable` virtualizes above 100 rows and holds 60 fps while scrolling 10,000 rows.
- **NFR-F062-02 Security/privacy:** no primitive renders raw HTML from props (no `dangerouslySetInnerHTML`), every link primitive forces `rel="noopener noreferrer"` on `target="_blank"`, and the theme bootstrap script is a static inline literal with no interpolation of stored values.
- **NFR-F062-03 Accessibility:** every story passes axe with zero serious or critical violations in both themes and densities; a keyboard-only walkthrough reaches every interactive element of every pattern; contrast is verified by computation over the token file; the suite fails on a regression rather than warning.
- **NFR-F062-04 Reliability/observability:** primitives are pure of feature state and carry no network calls; `ErrorState` always surfaces `correlation_id`; the visual harness pins each story to a deterministic screenshot and fails on a pixel diff above 0.1% so a token change cannot silently restyle 59 features.

### Scope

Included: the six token scales with real values, light and dark themes, system resolution and persistence, comfortable and compact density, the primitive component library, the focus and layering module, the composed pattern components every ticket's §3 promises, the application shell and breakpoints, the icon registry, locale-aware formatting primitives, stories for every state, and the visual, accessibility, and contrast harnesses.

Excluded: feature screens themselves (each feature ticket), workspace navigation content and routing (F005), locale and timezone resolution (F049 — this feature consumes its context and falls back before it ships), grid virtualization specific to sheets (F008 composes `DataTable`), charting (F024 supplies its own marks but takes color from these tokens), publishing and embed theming (F059), and any brand or marketing site styling.

## 3. UX specification

- Entry points: not user-facing on its own. Developers browse `pnpm --filter web storybook`; users meet it through every screen. Theme and density controls are rendered by F005's user menu and read and write the tokens this feature defines.
- Primary flow: an engineer building a screen imports `Button`, `Field`, `DataTable`, and `EmptyState` from `apps/web/src/ui`, passes copy and data, and receives correct focus, keyboard, density, theme, and accessibility behavior without writing CSS.
- Loading: `Skeleton` and `LoadingSkeleton` shapes per surface. Empty: `EmptyState` with icon, headline, body, and one primary action. Error: `ErrorState` with `correlation_id` and retry. Denied: `DeniedState` explaining the missing permission without leaking the resource name. Success: `Toast` in the shell's toast region. Stale: `StaleBanner`. Offline: `OfflineBanner` with mutations disabled.
- Responsive: the five breakpoints in FR-F062-10; every primitive is usable at 320px; the `DataTable` scrolls horizontally within its own container and never the page.
- Keyboard: as FR-F062-11; the shell provides skip-to-content, `[` toggles the rail, `]` toggles the inspector, and `?` opens the shortcut sheet.
- Font/icon/design tokens: this feature defines them; Inter variable self-hosted from `apps/web/src/design/fonts/`; Lucide through `apps/web/src/ui/icons.ts`.

## 4. Technical specification

### Rust backend

- None. F062 is a web-only feature and owns no Rust path, no route, no event, and no table; the catalog row lists its surface as `apps/web/src/design/**`, `apps/web/src/ui/**`, `pnpm --filter web storybook`, and `pnpm --filter web test:ui`. The `/healthz` contract it renders against belongs to F004; nothing here reaches the API.

### PostgreSQL/SQLx

- None. No migration, no table, no query. Theme and density are per-user browser state in `localStorage` (`opshub.theme`, `opshub.density`); when F002 user preferences exist, F005 may mirror them server-side, which is out of scope here. Rollback is removal of the `F062_FEATURE` flag and the `apps/web/src/ui` barrel export; there is nothing to revert in the database.

### React/TypeScript

- Files: `apps/web/src/design/{tokens.css, themes/{light.css, dark.css}, density.css, typography.css, fonts/}`; `apps/web/src/ui/{index.ts, icons.ts, primitives/*.tsx, patterns/*.tsx, shell/{AppShell.tsx, TopBar.tsx, NavRail.tsx, InspectorPanel.tsx, ToastRegion.tsx}, internal/{focus.ts, layers.ts, useControllableState.ts, useMediaQuery.ts, usePersistedState.ts}}`.
- Every primitive is a forwardRef function component with an explicit props interface, spreads `...rest` onto its root element, accepts `className` for layout only, and takes variant and size as literal unions, never strings.
- State: no global store. `ThemeProvider` and `DensityProvider` expose context read from `localStorage` with the pre-paint bootstrap; `ToastProvider` owns a queue capped at 5 with a 6-second default dismissal that pauses on hover and focus.
- Layering: `layers.ts` keeps an ordered stack of open overlays with z-index tokens `--z-dropdown:1000`, `--z-sticky:1100`, `--z-drawer:1200`, `--z-dialog:1300`, `--z-popover:1400`, `--z-toast:1500`, `--z-tooltip:1600`; `Escape` and outside-click dismiss only the top entry.
- Lint: an ESLint rule set in the web package bans raw color, spacing, radius, duration literals in `apps/web/src/**`, direct `lucide-react` imports outside `icons.ts`, `dangerouslySetInnerHTML`, and redefinition of any exported primitive name inside `apps/web/src/features/**`.
- Telemetry: `theme_changed`, `density_changed`, `shortcut_sheet_opened` with the resolved value; primitives emit nothing else.

## 5. TDD and isolated test harness

- [ ] Requirement tests: FR-F062-01 through FR-F062-15 in `testing/features/F062/requirements/cases.md`
- [ ] Failure/edge-case tests: token present in light but not dark, raw hex in a component, nested dialog closing its parent, toast queue overflow past 5, reduced-motion with an animation-only state, icon imported outside the registry
- [ ] Permission-negative and tenant-isolation tests: not applicable — F062 owns no route, no data, and no tenant-scoped state; the harness asserts that no file under `apps/web/src/ui/**` performs a network call, which is the isolation guarantee that matters here
- [ ] Rust unit tests: none; this feature owns no Rust path
- [ ] API contract/integration tests: none; the harness asserts the absence of network calls instead
- [ ] Database migration/constraint tests: none; the harness asserts no migration file is added under this feature's owned paths
- [ ] React component tests: every primitive and pattern for render, variants, disabled, loading, controlled and uncontrolled state, and keyboard interaction
- [ ] Browser E2E tests: theme switch with no flash on reload, density switch, overlay layering, shell rail and inspector persistence, shortcut sheet
- [ ] Accessibility tests: axe over every story in both themes and densities, keyboard-only walkthrough, computed contrast over the token file, focus-visible-only ring
- [ ] Performance/load tests: bundle size budget, token file size, 10,000-row `DataTable` scroll, theme switch repaint

### Fast fanout configuration

- Test harness path: `testing/features/F062/`
- Feature flag: `F062_FEATURE`
- Fixture/seed factory: `testing/fixtures/design_system.ts` builds the story matrix (every exported component × states × 2 themes × 2 densities), a 10,000-row table dataset, and a fixed locale `en-US` with timezone `UTC`
- Deterministic test data: fixed clock `2026-09-03T00:00:00Z`, fonts loaded from the repository rather than the network, animations disabled during screenshots, device pixel ratio 1
- Mock/stub contracts: no API mocks are needed; a `fetch` spy asserts zero calls from `apps/web/src/ui/**`
- Parallel isolation: stories render in isolated jsdom or browser contexts per worker; screenshot baselines are keyed by story id, theme, and density
- Targeted command: `cargo xtask test-feature F062`
- Full command: `cargo xtask test-all`
- CI artifact/evidence: `testing/evidence/F062/`

## 6. Acceptance criteria

```gherkin
Feature: One design language and one component library

Scenario: Dark theme has no missing tokens and no flash
  Given a user whose stored theme is dark
  When the app loads
  Then every token name defined in light is defined in dark
  And the first painted frame is already dark

Scenario: A feature cannot invent a second button
  Given a feature module that defines and exports its own Button component
  When pnpm --filter web lint runs
  Then the run fails naming the duplicated primitive

Scenario: Contrast is verified by computation
  Given the token file
  When the contrast test runs over every text-on-surface pair in both themes
  Then every body pair is at least 4.5:1 and every large-text, icon, and focus-ring pair is at least 3:1

Scenario: Nested overlays close one layer at a time
  Given a dialog containing a menu that is open
  When Escape is pressed
  Then the menu closes, the dialog stays open, and focus returns to the menu trigger

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
- External dependencies: Inter variable (self-hosted, vendored), Lucide icons, an accessible headless primitive base for overlay and composite widgets, axe for the accessibility lane, a deterministic screenshot runner for the visual lane
- Risks and mitigations: a token change silently restyling 59 features, mitigated by pinned visual baselines that fail on a 0.1% pixel diff; features drifting by writing local CSS, mitigated by the lint rules in section 4 and the owned-path gate; over-building primitives nobody uses, mitigated by the list in FR-F062-07 being closed — a new primitive requires a ticket amendment; accessibility regressions, mitigated by axe over every story rather than per feature screen
- Open questions: none

## 7.1 Agent handoff

Recorded at implementation: implemented summary, files changed, commands and evidence, known issues, follow-up tickets, migration and rollback status.

## 8. Entry criteria — ready for implementation

- [ ] F001 accepted and archived so the pnpm workspace and `web` CI job exist
- [ ] Requirement IDs above mapped to failing tests in `testing/features/F062/`
- [ ] Owned paths claimed and `tokens.css` released by F001
- [ ] Inter variable and the Lucide subset vendored into `apps/web/src/design/fonts/` and `apps/web/src/ui/icons.ts`

## 9. Exit criteria — accepted and releasable

- [ ] All FR/NFR acceptance tests pass in targeted and full modes
- [ ] React component, E2E, accessibility, visual, and performance gates pass in both themes and both densities
- [ ] Token parity and computed contrast tests pass; no raw color, spacing, radius, or duration literal exists under `apps/web/src/**`
- [ ] Every changed file ≤ 500 lines; `cargo xtask validate-tickets` and `check-contracts` pass
- [ ] Rollback verified: disabling `F062_FEATURE` falls back to the unstyled `/status` baseline without a build error
- [ ] `finished_at` recorded and file moved to `work/archived/`

## 10. Release notes

- Establishes the OpsHub design language: six token scales with fixed values, light and dark themes with system resolution, comfortable and compact density, and a shared primitive, pattern, and shell library that every feature composes instead of reinventing.
- No migration and no API change. The feature is off by default behind `F062_FEATURE`; enabling it switches the app shell and every screen onto the token set.
