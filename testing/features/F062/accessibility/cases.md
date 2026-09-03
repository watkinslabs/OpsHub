# F062 accessibility cases

File: `testing/features/F062/accessibility/{token_tests,theme_tests,axe_tests}.ts`. Flag `F062_FEATURE`.

- `token_scales_match_the_specified_values` — FR-F062-01, FR-F062-02: the parsed token file matches the spacing, radius, elevation, type, and motion values in the ticket exactly.
- `light_and_dark_define_identical_token_names` — FR-F062-04: the token name sets are equal; a token present in one theme only fails with its name.
- `no_component_uses_a_raw_color_or_spacing_literal` — FR-F062-01, FR-F062-03: a lint pass over `apps/web/src/**` finds no raw hex, px, ms, or literal palette reference where a token exists.
- `computed_contrast_meets_aa_in_both_themes` — FR-F062-05, NFR-F062-03: every text-on-surface pair computes ≥ 4.5:1, and large text, icons, and meaningful borders ≥ 3:1, in light and dark.
- `focus_ring_meets_three_to_one_against_both_neighbours` — FR-F062-05: `--focus-ring` clears 3:1 against the adjacent surface and the outlined component in both themes.
- `stored_theme_applies_before_first_paint` — FR-F062-04: the bootstrap sets the root attribute before the first style recalculation.
- `reduced_motion_collapses_transitions` — FR-F062-12: under `prefers-reduced-motion: reduce` no computed transition or animation exceeds 1 ms.
- `every_story_passes_axe_in_four_theme_density_combinations` — NFR-F062-03: axe reports zero serious or critical violations across the full story matrix.
- `keyboard_only_walkthrough_reaches_every_control` — NFR-F062-03, FR-F062-11: a keyboard-only pass reaches and operates every interactive element of every pattern and the shell.

Evidence: axe JSON, contrast report, and walkthrough recordings under `testing/evidence/F062/accessibility/`.
