---
id: T245
type: task
status: planned
parent_epic: E001
parent_feature: F062
parent_story: S123
depends_on: [S123]
owned_paths: [apps/web/src/design/**, testing/features/F062/accessibility/**]
feature_flag: F062_FEATURE
branch: t245-token-scales-and-themes
started_at: null
finished_at: null
---

# T245 — Token scales and themes

## Identity

- Parent story: `S123` Design tokens and theming
- Owner: platform
- Branch: `t245-token-scales-and-themes`
- Decision references: `docs/architecture-decisions.md` sections 5, 6; `docs/capability-contracts.md` row F062

## Objective

Write the token file with its real values, the two themes, the brand derivation and its contrast gate, the typography and density layers, and the pre-paint bootstrap, with the parity and contrast tests that prove them.

## Specification

- Owned paths: `apps/web/src/design/{tokens.css, typography.css, density.css, themes/{light.css, dark.css}, brand.ts, fonts/}` and the bootstrap literal in `apps/web/index.html`.
- Contract/input: the six scales with the exact values in ticket section 2 — spacing `--space-1:4px` … `--space-12:96px`; radius 4/6/10/9999; the three elevations; type `--text-xs:12px/16px` … `--text-3xl:30px/38px` in Plus Jakarta Sans 400/500/600/700 with JetBrains Mono for numerics; motion 100/150/250 ms with three easings; z-index 1000 … 1600; density 28/32/40 with 36px rows comfortable and 24/28/34 with 28px rows compact; and the light and dark hex values for every surface, text, border and intent token.
- Output/behavior: `tokens.css` declares every scale on `:root`; `themes/light.css` and `themes/dark.css` declare the identical semantic token set with the ticket's hex values; `brand.ts` derives `--accent-bg|-fg|-border|-emphasis`, `--bg-selected` and `--focus-ring` from `--brand` with `color-mix(in oklch, …)` per theme and exposes `validateBrand(hue)` running the contrast floor so tenant settings can refuse a bad hue and name the failing pair; `[data-theme="dark"]` selects dark and the unset default resolves `prefers-color-scheme`; `density.css` redefines control and row heights under `[data-density="compact"]`; `typography.css` self-hosts Plus Jakarta Sans and JetBrains Mono with the documented fallback stacks and tabular numerals; the inline bootstrap in `index.html` is a static literal reading `opshub.theme` and `opshub.density` and setting the root attributes before first paint; `prefers-reduced-motion: reduce` collapses every duration to 1 ms.
- Dependencies: F001 Vite and pnpm baseline for the CSS pipeline and font vendoring. No API, no database, no Rust.
- Feature flag: `F062_FEATURE` gates the token import in `main.tsx`; the `/status` page from F001 renders unstyled when the flag is off, which is the rollback path.

## TDD

- Failing test first: `testing/features/F062/accessibility/token_tests.ts::token_scales_match_the_specified_values`, `::light_and_dark_define_identical_token_names`, `::no_component_uses_a_raw_color_or_spacing_literal`, `::computed_contrast_meets_aa_for_every_brand_preset`, `::brand_hue_failing_contrast_is_refused`, `::focus_ring_meets_three_to_one_against_both_neighbours`; `testing/features/F062/accessibility/theme_tests.ts::stored_theme_applies_before_first_paint`, `::system_theme_follows_prefers_color_scheme`, `::density_tokens_change_control_and_row_height`, `::reduced_motion_collapses_transitions`
- Targeted command: `cargo xtask test-feature F062`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/design_system.ts` token matrix; fonts served from the repository so no network fetch occurs; fixed device pixel ratio 1

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Token parity and computed contrast pass in both themes; `tokens.css` under 12 KB
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S123
- [ ] `finished_at` recorded
