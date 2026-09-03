---
id: S123
type: story
status: planned
parent_epic: E001
parent_feature: F062
depends_on: [F001]
owned_paths: [apps/web/src/design/**, apps/web/src/ui/internal/**, testing/features/F062/accessibility/**, testing/features/F062/performance/**]
feature_flag: F062_FEATURE
branch: s123-design-tokens-and-theming
started_at: null
finished_at: null
---

# S123 — Design tokens and theming

## Identity

- Parent feature: `F062` Design system and UI primitives
- Owner: platform
- Branch: `s123-design-tokens-and-theming`
- Decision references: `docs/architecture-decisions.md` sections 5, 6; `docs/capability-contracts.md` row F062

## Vertical slice

As a product engineer, I want one token file with real values for color, spacing, radius, type, elevation, and motion, resolved into a light and a dark theme and a comfortable and a compact density, applied before first paint and proven to meet contrast, so that every screen I build inherits one visual language and a user can switch theme or density without a flash, a reflow, or an unreadable pair.

## Requirements

- **SR-S123-01:** `apps/web/src/design/tokens.css` defines the six scales with the exact values in the ticket — 4px-based spacing `--space-1` to `--space-12`, radii `sm|md|lg|full`, elevations 0–3 — and a test parses the file and fails on a missing or off-scale step (covers FR-F062-01).
- **SR-S123-02:** The type scale ships Inter variable self-hosted from `apps/web/src/design/fonts/` with the documented fallback stacks and the seven steps and three weights; a size or weight outside the scale fails the scale test (FR-F062-02).
- **SR-S123-03:** Color tokens are semantic only — surfaces, text, borders, focus, and the five intent families each with `-bg`, `-fg`, `-border`, `-emphasis` — and no component may reference a literal palette variable (FR-F062-03).
- **SR-S123-04:** `light.css` and `dark.css` define an identical token name set, `[data-theme="system"]` resolves through `prefers-color-scheme`, the choice persists in `localStorage` key `opshub.theme`, and an inline pre-paint bootstrap applies it so the first painted frame is correct (FR-F062-04).
- **SR-S123-05:** A computed contrast test walks every text-on-surface, icon, border, and focus-ring pair in both themes and asserts 4.5:1 for body, 3:1 for large text, icons, meaningful borders, and `--focus-ring` against both neighbours (FR-F062-05, NFR-F062-03).
- **SR-S123-06:** `density.css` defines `comfortable` and `compact` control heights, padding, and row height on the app root, persisted in `localStorage` key `opshub.density`, with every primitive deriving size from those tokens (FR-F062-06).
- **SR-S123-07:** Motion tokens define three durations and three easings, and `prefers-reduced-motion: reduce` collapses every transition to 1 ms without removing a state signal (FR-F062-12).
- **SR-S123-08:** `internal/{focus.ts, layers.ts, usePersistedState.ts, useMediaQuery.ts}` provide the focus-return, layer-stack, persistence, and breakpoint primitives the component layer builds on, with the z-index tokens from the ticket (FR-F062-08, FR-F062-10).
- **SR-S123-09:** `tokens.css` stays under 12 KB and a theme or density switch repaints a 1,000-row table without a reflow over 16 ms (NFR-F062-01).

## Surfaces

- Infrastructure/container: none; the token file is built by the existing Vite pipeline from F001 and served with the web bundle
- Rust service/API: none — F062 owns no Rust path
- Data/migration: none — theme and density are per-user browser state
- React/UI: `apps/web/src/design/{tokens.css, typography.css, density.css, themes/{light.css, dark.css}, fonts/}`; `apps/web/src/ui/internal/{focus.ts, layers.ts, usePersistedState.ts, useMediaQuery.ts, useControllableState.ts}`; the pre-paint bootstrap literal injected by `apps/web/index.html`
- Mocks/fixtures: `testing/fixtures/design_system.ts` token matrix and the fixed `en-US`/`UTC` locale; fonts loaded from the repository so no network fetch occurs during tests

## TDD harness

- Test path: `testing/features/F062/{accessibility,performance}/`
- Feature flag: `F062_FEATURE`
- Targeted command: `cargo xtask test-feature F062`
- Full command: `cargo xtask test-all`
- First failing tests: `token_scales_match_the_specified_values`, `light_and_dark_define_identical_token_names`, `computed_contrast_meets_aa_in_both_themes`, `stored_theme_applies_before_first_paint`, `density_tokens_change_control_and_row_height`, `reduced_motion_collapses_transitions`, `focus_returns_to_invoker_on_close`, `escape_closes_only_the_top_layer`, `tokens_css_under_12kb`

## Exit criteria

- [ ] Requirement tests SR-S123-01 through SR-S123-09 written first and observed failing
- [ ] Tasks T245 and T246 complete
- [ ] Component, accessibility, and performance lanes pass in targeted and full modes in both themes and both densities
- [ ] Production call path named: `apps/web/src/design/tokens.css` imported by `apps/web/src/main.tsx`; `ThemeProvider` and `DensityProvider` mounted in `apps/web/src/ui/shell/AppShell.tsx`; the pre-paint bootstrap in `apps/web/index.html`
- [ ] Handoff evidence recorded in the F062 ticket
