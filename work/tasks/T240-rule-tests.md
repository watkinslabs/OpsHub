---
id: T240
type: task
status: planned
parent_epic: E008
parent_feature: F060
parent_story: S120
depends_on: [S120]
owned_paths: [testing/features/F060/**]
feature_flag: F060_FEATURE
branch: t240-rule-tests
started_at: null
finished_at: null
---

# T240 — Rule tests

## Identity

- Parent story: `S120` Visual states
- Owner: platform
- Branch: `t240-rule-tests`
- Decision references: `docs/architecture-decisions.md` sections 6, 9; `docs/capability-contracts.md` row F060

## Objective

Build the F060 harness that proves the rules and the visual states: the deterministic fixture sheet and rule sets, the accessibility gates that make colour never the only signal, the performance gates at 500-row pages and 100,000-row materialization, and the requirements traceability from every FR and NFR id to a named test.

## Specification

- Owned paths: `testing/features/F060/{feature.toml, README.md}`, `testing/features/F060/{requirements,api,database,frontend,e2e,accessibility,performance}/`
- Contract/input: `testing/fixtures/formatting.rs` builds tenant A and tenant B, a sheet-editor, a sheet-viewer, and an actor denied the `Budget` column; sheet `Delivery plan` with `Status` (select), `Due date` (date), `Owner` (person), `Budget` (currency), and `Variance` (formula) columns; 50 rows with 6 known exceptions; views `At risk` and `All work`; rule sets `basic_10` (3 row targets, 3 cell targets, 1 view-scoped, 1 disabled, 1 with `stop_if_true`, 1 formula rule) and `stress_100`; generators `rows(5_000)` for the inline-versus-materialized equivalence run and `rows(100_000)` for materialization; a token-contrast table parsed from `apps/web/src/design/tokens.css`; fixed clock `2026-09-03T00:00:00Z`, UTC, fixed UUIDv7 and fractional-position seeds.
- Output/behavior: the seven lane `cases.md` files list every implemented test with its FR or NFR id, and `requirements/cases.md` covers FR-F060-01 through FR-F060-15 and NFR-F060-01 through NFR-F060-04. Accessibility lane runs axe over the panel, editor, legend, popover, and formatted grid, asserts every colour token pair holds at least 4.5:1 for text on fill and 3:1 for icons, asserts formatted rows expose `aria-describedby` naming the applied rules, asserts `Icon only` mode removes fills while keeping icons and badges, and asserts the newly-matched flash disappears under `prefers-reduced-motion`. Performance lane asserts a 100-rule compile under 5 ms, evaluation of 100 rules over 500 rows under 25 ms p95, at most 10% added to the F013 row-page p95 (staying under 550 ms), 100,000-row materialization under 90 s, and no viewport paint frame over 16 ms. Every lane writes evidence under `testing/evidence/F060/<lane>/`. A positive control is included per gate: a rule mutated to colour-only, a token pair mutated below contrast, and a rule set inflated past the page budget each turn their gate red and are then restored to green.
- Dependencies: T237 routes, schema, and events; T239 evaluator, read hook, worker jobs, and web rendering; the F035 fixed-clock evaluator; the F013 view fixtures; the shared schema-per-worker harness in `testing/harness/`.
- Feature flag: `F060_FEATURE` gates every lane; `cargo xtask test-feature F060` runs the suite alone and `cargo xtask test-all` runs it inside the full matrix.

## TDD

- Failing test first: `testing/features/F060/accessibility/formatting.a11y.spec.ts::color_is_never_the_only_signal`, `::token_pairs_meet_contrast_thresholds`, `::formatted_row_describes_applied_rules`; `testing/features/F060/performance/formatting_bench.rs::evaluate_hundred_rules_over_five_hundred_rows_under_25ms`, `::materialize_hundred_thousand_rows_under_90s`, `::view_row_page_p95_within_ten_percent`; `testing/features/F060/requirements/traceability_tests.rs::every_requirement_id_has_a_named_test`, `::every_lane_cites_requirement_ids`
- Targeted command: `cargo xtask test-feature F060`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: the fixture factory above; MSW handlers for the frontend lane; Playwright against the seeded tenant for the e2e and accessibility lanes; criterion for the performance lane; in-memory outbox recorder for event assertions

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Every FR-F060 and NFR-F060 id maps to at least one named test in `testing/features/F060/requirements/cases.md`
- [ ] Positive controls demonstrated red then green for the colour-only, contrast, and budget gates
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S120
- [ ] `finished_at` recorded
