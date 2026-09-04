---
id: T248
type: task
status: planned
parent_epic: E001
parent_feature: F062
parent_story: S124
depends_on: [T247]
owned_paths: [testing/features/F062/requirements/**, testing/features/F062/performance/**, testing/features/F062/accessibility/**, testing/features/F062/database/**, testing/features/F062/api/**]
feature_flag: F062_FEATURE
branch: t248-visual-and-accessibility-harness
started_at: null
finished_at: null
---

# T248 — Visual and accessibility harness

## Identity

- Parent story: `S124` UI primitives and patterns
- Owner: platform
- Branch: `t248-visual-and-accessibility-harness`
- Decision references: `docs/architecture-decisions.md` sections 5, 6; `docs/capability-contracts.md` row F062

## Objective

Stand up the lanes that keep the design system honest: axe over every story, pinned visual baselines, bundle and size budgets, the requirements traceability matrix, and the negative controls proving this feature owns no server surface.

## Specification

- Owned paths: `testing/features/F062/{requirements,accessibility,performance,api,database}/` — the case files and the runners they describe.
- Contract/input: the story matrix from `testing/fixtures/design_system.ts` — every exported component × its states × 2 themes × 2 densities — plus the token file itself and the built bundle.
- Output/behavior: the accessibility lane runs axe over every story in all four theme-density combinations and fails on a serious or critical violation, runs the keyboard-only walkthrough, and runs the computed contrast pass over the token file for the default brand and every preset; the visual runner captures one deterministic screenshot per story at device pixel ratio 1 with animations disabled and fonts loaded from the repository, and fails on a pixel diff above 0.1% so a token change cannot silently restyle fifty-nine features; the performance lane asserts the 210 KB gzipped themed-bundle budget with Data Grid and Charts in their own chunks, the 12 KB token budget, 60 fps over a 10,000-row `DataGrid` scroll, and a theme switch repainting a 1,000-row table without a reflow over 16 ms; the `api` and `database` lanes hold the negative controls — a `fetch` spy proving no module under `apps/web/src/ui/**` performs a network call, and an assertion that no migration file exists under this feature's owned paths — because F062 owns no route and no table; a dependency check fails the build if `@mui/x-data-grid-pro` or `-premium` enters the tree; the requirements lane maps FR-F062-01 through FR-F062-17 and NFR-F062-01 through NFR-F062-04 to the tests above.
- Dependencies: T245, T246, and T247 for the code under test; F001 for the `web` CI job that runs the lanes and uploads evidence.
- Feature flag: `F062_FEATURE`; the lanes are selected by `cargo xtask test-feature F062` and skipped when the flag is off.

## TDD

- Failing test first: `testing/features/F062/accessibility/axe_tests.ts::every_story_passes_axe_in_four_theme_density_combinations`, `::keyboard_only_walkthrough_reaches_every_control`; `testing/features/F062/performance/budget_tests.ts::primitive_bundle_under_90kb_gzipped`, `::tokens_css_under_12kb`, `::ten_thousand_row_grid_scroll_holds_sixty_fps`, `::theme_switch_repaints_under_sixteen_ms`; `testing/features/F062/performance/visual_tests.ts::story_screenshots_match_pinned_baselines`; `testing/features/F062/api/no_network_tests.ts::ui_modules_perform_no_network_call`; `testing/features/F062/database/no_migration_tests.ts::feature_adds_no_migration_file`
- Targeted command: `cargo xtask test-feature F062`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/fixtures/design_system.ts`; pinned baselines under `testing/evidence/F062/visual/`; fixed clock, fixed device pixel ratio, animations disabled

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Requirements lane covers every FR and NFR of F062
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S124
- [ ] `finished_at` recorded
