---
id: T072
type: task
status: planned
parent_epic: E004
parent_feature: F018
parent_story: S036
depends_on: [T071]
owned_paths: [testing/features/F018/**]
feature_flag: F018_FEATURE
branch: t072-workflow-fixtures
started_at: null
finished_at: null
---

# T072 — Workflow fixtures

## Identity

- Parent story: `S036` Actions
- Owner: platform
- Branch: `t072-workflow-fixtures`
- Decision references: `docs/architecture-decisions.md` sections 9, 10; `docs/capability-contracts.md` row F018

## Objective

Build the deterministic workflow fixture set, the 5,000-workflow performance generator, and the E2E, accessibility, and performance lanes that prove the builder end to end and hand F019 a reusable definition corpus.

## Specification

- Owned paths: `testing/features/F018/fixtures/{definitions.rs, generator.rs, sample_events.json}`, `testing/features/F018/e2e/workflow.spec.ts`, `testing/features/F018/accessibility/workflow.a11y.spec.ts`, `testing/features/F018/performance/{validate_bench.rs, list_bench.rs}`
- Contract/input: `definitions.rs` exposes `fixture_workflows() -> Vec<WorkflowDefinition>` with one workflow per trigger kind (8) plus 4 invalid definitions (type mismatch, depth 5, 26 actions, inline secret); `generator.rs` builds 5,000 published workflows across 50 sheets with fixed seed `0x0F18`; `sample_events.json` holds one canonical event payload per trigger kind consumed by both this feature's test endpoint and F019 integration tests.
- Output/behavior: Playwright runs against a seeded tenant with the real API: create, test, publish, edit after publish, disable, viewer read-only; axe reports zero serious violations on list and builder; criterion benches assert validation p95 < 200 ms for a 25-action depth-4 definition, `test` p95 < 2 s with a formula leaf, and list p95 < 500 ms with 5,000 workflows.
- Dependencies: T071 UI and publish routes; `testing/harness/` Playwright and axe runners; F035 evaluator for the formula bench.
- Feature flag: `F018_FEATURE` enabled in the seeded tenant.

## TDD

- Failing test first: `testing/features/F018/e2e/workflow.spec.ts::create_test_publish_workflow`, `::edit_after_publish_creates_draft`, `::disable_stops_new_runs_state`, `::viewer_sees_read_only_builder`; `testing/features/F018/accessibility/workflow.a11y.spec.ts::builder_has_no_serious_axe_violations`, `::condition_tree_levels_announced`; `testing/features/F018/performance/validate_bench.rs::validate_25_actions_p95`, `list_bench.rs::workflow_list_5000_p95`
- Targeted command: `cargo xtask test-feature F018`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: seeded tenant from `testing/fixtures/workflows.rs`; F029 vault stub; no run execution (F019 not required)

## Exit criteria

- [ ] Tests written before fixtures and observed failing
- [ ] E2E, accessibility, and performance lanes pass with evidence under `testing/evidence/F018/`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S036
- [ ] `finished_at` recorded
