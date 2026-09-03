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

Write the token file, the two themes, the typography and density layers, and the pre-paint bootstrap, with the contrast and parity tests that prove them.

## Specification

- Owned paths: `apps/web/src/design/{tokens.css, typography.css, density.css, themes/{light.css, dark.css}, fonts/}` and the bootstrap literal in `apps/web/index.html`.
- Contract/input: the six scales with the exact values in ticket section 2 — spacing `--space-0:0`, `--space-1:4px` … `--space-12:96px`; radius `sm:4px`, `md:6px`, `lg:10px`, `full:9999px`; elevation 0–3 as composed shadows; type `--text-xs:12px/16px` … `--text-3xl:30px/38px` with weights 400/500/600; motion `--duration-fast:100ms`, `-base:150ms`, `-slow:250ms` with `--ease-standard|in|out`; z-index `--z-dropdown:1000` … `--z-tooltip:1600`; density heights 28/32/40 comfortable and 24/28/34 compact with row height 36/28.
- Output/behavior: `tokens.css` declares every scale on `:root`; `themes/light.css` and `themes/dark.css` declare the identical semantic color token set (surfaces, text, borders, focus, and the five intent families each with `-bg`, `-fg`, `-border`, `-emphasis`); `[data-theme="dark"]` selects dark and the unset default resolves `prefers-color-scheme`; `density.css` redefines control and row heights under `[data-density="compact"]`; `typography.css` self-hosts Inter variable with the documented fallback stacks; the inline bootstrap in `index.html` is a static literal that reads `opshub.theme` and `opshub.density` and sets the root attributes before first paint; `prefers-reduced-motion: reduce` collapses every duration to 1 ms.
- Dependencies: F001 Vite and pnpm baseline for the CSS pipeline and font vendoring. No API, no database, no Rust.
- Feature flag: `F062_FEATURE` gates the token import in `main.tsx`; the `/status` page from F001 renders unstyled when the flag is off, which is the rollback path.

## TDD

- Failing test first: `testing/features/F062/accessibility/token_tests.ts::token_scales_match_the_specified_values`, `::light_and_dark_define_identical_token_names`, `::no_component_uses_a_raw_color_or_spacing_literal`, `::computed_contrast_meets_aa_in_both_themes`, `::focus_ring_meets_three_to_one_against_both_neighbours`; `testing/features/F062/accessibility/theme_tests.ts::stored_theme_applies_before_first_paint`, `::system_theme_follows_prefers_color_scheme`, `::density_tokens_change_control_and_row_height`, `::reduced_motion_collapses_transitions`
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
