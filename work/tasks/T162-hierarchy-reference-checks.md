---
id: T162
type: task
status: planned
parent_epic: E000
parent_feature: F041
parent_story: S081
depends_on: [T161]
owned_paths: [automation/xtask/src/backlog.rs, testing/features/F041/api/**, testing/features/F041/requirements/**]
feature_flag: F041_FEATURE
branch: t162-hierarchy-reference-checks
started_at: null
finished_at: null
---

# T162 — Hierarchy/reference checks

## Identity

- Parent story: `S081` Epic/feature schema
- Owner: platform
- Branch: `t162-hierarchy-reference-checks`
- Decision references: `docs/architecture-decisions.md` sections 9–10; `docs/capability-contracts.md` row F041

## Objective

Implement parent resolution, dependency graph validation with cycle detection, `blocks` mirroring, and plan parity so `validate-work` and `validate-plan` prove the whole backlog is one consistent graph.

## Specification

- Owned paths: `automation/xtask/src/backlog.rs` (`check_hierarchy`, `check_dependencies`, `parse_plan`, `PlanRow`, `check_plan_parity`, `validate_work`, `validate_plan`)
- Contract/input: a loaded `WorkGraph`; `work/plan.md` with `## E### — Title` headings and `| F### Title | S### a; S### b | T### a; T### b; T### c; T### d | deps |` rows where `deps` is a comma-separated id list or an em-dash
- Output/behavior: findings `parent.unresolved`, `parent.inconsistent` (story epic differs from feature epic; task feature differs from story feature), `depends.unresolved`, `depends.self`, `depends.cycle` (Tarjan SCC, cycle printed in ascending id order starting from the smallest id), `depends.blocks_mismatch`, `depends.empty` (skipped for epics and for features with `parent_epic: E000`), `plan.depends_mismatch` (`extra: [..] missing: [..]`), `plan.missing_item`, `plan.orphan_item`, `plan.pairing`, `plan.epic_mismatch`; `validate-work` runs front matter, hierarchy, and dependency checks; `validate-plan` runs plan parity
- Dependencies: T161 types and reporter
- Feature flag: `F041_FEATURE`
- Determinism: graph iteration over `BTreeMap` so output order is stable

## TDD

- Failing test first: `testing/features/F041/api/graph_tests.rs::story_with_foreign_epic_is_parent_inconsistent`, `::dependency_cycle_named_in_id_order`, `::feature_blocks_must_mirror_depends_on`, `::empty_depends_allowed_only_for_e000_features`, `::plan_depends_mismatch_lists_extra_and_missing`, `::plan_row_with_three_stories_is_pairing_error`, `::orphan_task_file_reported`
- Targeted command: `cargo xtask test-feature F041`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/features/F041/fixtures/{cycle,orphan,mispaired,valid}` including a `work/plan.md` per fixture

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] `validate-work` and `validate-plan` dispatched through the new functions; the legacy `plan_ids` and `ids_by_type` helpers removed
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S081
- [ ] `finished_at` recorded
