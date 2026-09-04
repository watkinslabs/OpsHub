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

As a product engineer, I want one token file with the real values for color, spacing, radius, type, elevation and motion, resolved into light and dark themes and comfortable and compact density, mapped onto the MUI theme and applied before first paint, so that every screen inherits one visual language and a customer can rebrand the product by changing one hue without any pair falling below contrast.

## Requirements

- **SR-S123-01:** `apps/web/src/design/tokens.css` declares the six scales with the exact values in the ticket — 4px spacing `--space-1` to `--space-12`, radii 4/6/10/9999, the three elevations, the three durations and easings, and the seven z-index layers — and a test parses the file and fails on a missing or off-scale step (covers FR-F062-01).
- **SR-S123-02:** Typography ships Plus Jakarta Sans and JetBrains Mono self-hosted from `apps/web/src/design/fonts/` with the documented fallback stacks, the seven steps, the four weights, `-0.02em` tracking from `--text-xl` up, and tabular numerals on every mono surface (FR-F062-02).
- **SR-S123-03:** `themes/light.css` and `themes/dark.css` declare the identical semantic token set with the hex values in the ticket, including all three intent families in both themes (FR-F062-03).
- **SR-S123-04:** `brand.ts` derives `--accent-*`, `--bg-selected` and `--focus-ring` from `--brand` by `color-mix(in oklch, …)` per theme, so setting the hue rebrands every accent surface and nothing else changes; `validateBrand(hue)` refuses a hue that breaks the contrast floor and names the failing pair (FR-F062-04).
- **SR-S123-05:** `[data-theme="system"]` resolves through `prefers-color-scheme`, the choice persists in `localStorage` key `opshub.theme`, and a static inline bootstrap in `index.html` applies theme and density before first paint so no frame renders in the wrong theme (FR-F062-05).
- **SR-S123-06:** A computed contrast test walks every text-on-surface, icon, border and focus pair in both themes for the default brand and all four presets and asserts 4.5:1 body and 3:1 large text, icons, meaningful borders and focus ring (FR-F062-06, NFR-F062-03).
- **SR-S123-07:** `density.css` defines comfortable 28/32/40 with 36px rows and compact 24/28/34 with 28px rows on the app root, persisted in `localStorage` key `opshub.density`, with every control deriving height from those tokens (FR-F062-07).
- **SR-S123-08:** `theme.ts` maps the tokens onto the MUI v7 theme — palette, typography, `shape.borderRadius` 6, `spacing(1) = 4px`, `zIndex`, `transitions.duration`, and component default sizes — using MUI's CSS-variables mode so a theme or density switch is a CSS change and never a React re-render (FR-F062-08).
- **SR-S123-09:** `tokens.css` stays under 12 KB and a theme or density switch repaints a 1,000-row grid without a reflow over 16 ms (NFR-F062-01).

## Surfaces

- Infrastructure/container: none; the token file and fonts build through the existing Vite pipeline from F001
- Rust service/API: none — F062 owns no Rust path
- Data/migration: none — theme, density and rail width are per-viewer browser state; the tenant brand hue is F002 tenant settings applied here as `--brand`
- React/UI: `apps/web/src/design/{tokens.css, typography.css, density.css, themes/{light.css, dark.css}, theme.ts, brand.ts, fonts/}`; `apps/web/src/ui/{ThemeProvider.tsx, internal/{focus.ts, usePersistedState.ts, useMediaQuery.ts}}`; the pre-paint bootstrap in `apps/web/index.html`
- Mocks/fixtures: `testing/fixtures/design_system.ts` token matrix, the four brand presets and the fixed `en-US`/`UTC` locale; fonts served from the repository so no network fetch occurs

## TDD harness

- Test path: `testing/features/F062/{accessibility,performance}/`
- Feature flag: `F062_FEATURE`
- Targeted command: `cargo xtask test-feature F062`
- Full command: `cargo xtask test-all`
- First failing tests: `token_scales_match_the_specified_values`, `light_and_dark_define_identical_token_names`, `computed_contrast_meets_aa_for_every_brand_preset`, `brand_hue_failing_contrast_is_refused`, `stored_theme_applies_before_first_paint`, `density_tokens_change_control_and_row_height`, `mui_theme_reads_every_token`, `theme_switch_does_not_rerender_tree`, `tokens_css_under_12kb`

## Exit criteria

- [ ] Requirement tests SR-S123-01 through SR-S123-09 written first and observed failing
- [ ] Tasks T245 and T246 complete
- [ ] Component, accessibility and performance lanes pass in targeted and full modes in both themes and both densities
- [ ] Production call path named: `apps/web/src/design/tokens.css` imported by `apps/web/src/main.tsx`; `ThemeProvider` mounted in `apps/web/src/ui/shell/AppShell.tsx`; the pre-paint bootstrap in `apps/web/index.html`
- [ ] Handoff evidence recorded in the F062 ticket
