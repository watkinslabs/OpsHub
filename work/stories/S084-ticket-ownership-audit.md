---
id: S084
type: story
status: planned
parent_epic: E000
parent_feature: F042
depends_on: [S083]
owned_paths: [automation/xtask/src/policy.rs, .githooks/**, testing/features/F042/**]
feature_flag: F042_FEATURE
branch: s084-ticket-ownership-audit
started_at: null
finished_at: null
---

# S084 — Ticket/ownership audit

## Identity

- Parent feature: `F042` xtask audit/gates
- Owner: platform
- Branch: `s084-ticket-ownership-audit`
- Decision references: `docs/architecture-decisions.md` sections 9–10; `docs/capability-contracts.md` row F042

## Vertical slice

As a maintainer, I want `check-ownership` to match staged paths against the real globs of active items, refuse overlapping or ambiguous ownership across features, refuse active items whose dependencies are not archived or that conflict with another active item, and I want `self-test` to prove all of it with positive controls on every CI run, so that parallel agents cannot collide or start out of order.

## Requirements

- **SR-S084-01:** Active items are loaded from `work/inprogress/` through the F041 `WorkGraph`, and each `owned_paths` entry compiles to a `globset` matcher with `**`/`*` semantics (covers FR-F042-06).
- **SR-S084-02:** Every staged path not matched by an active glob and not a policy file is `ownership.outside` naming the active ids; an empty `work/inprogress/` skips with exit 0 (FR-F042-06).
- **SR-S084-03:** Active items of different features with globs that can match a common path are `ownership.overlap`; a staged path matched by two features is `ownership.ambiguous` (FR-F042-07).
- **SR-S084-04:** An active item whose `depends_on` includes an id not archived with `status: done|archived` is `depends.unmet`; an active item whose `conflicts_with` names another active item is `depends.conflict` (FR-F042-08).
- **SR-S084-05:** `self-test` runs the clean control, every token variant control, the policy-file skip control, the glob controls, `sh -n` on the hooks, and the executable-bit control, exiting 1 on any failure (FR-F042-09).
- **SR-S084-06:** `audit-staged` invokes the ownership gate after the token scan so one command covers both in `pre-commit` (FR-F042-02, FR-F042-11).
- **SR-S084-07:** Findings and JSON follow the shared contract and are byte-identical across runs (FR-F042-12, NFR-F042-04).

## Surfaces

- Infrastructure/container: `.githooks/pre-commit` (ownership runs inside `audit-staged`)
- Rust service/API: `automation/xtask/src/policy.rs` (`ownership::{ActiveItem, OwnershipSet, load_active, check_paths, check_overlap, check_dependencies}`, `check_ownership`, `self_test`)
- Data/migration: none; reads `work/inprogress/**` and `work/archived/**`
- React/UI: none (no UI)
- Mocks/fixtures: `testing/features/F042/fixtures/{ownership,overlap,unmet,conflict}` each with a `work/` tree containing active and archived items

## TDD harness

- Test path: `testing/features/F042/api/`, `testing/features/F042/database/`, `testing/features/F042/accessibility/`
- Feature flag: `F042_FEATURE`
- Targeted command: `cargo xtask test-feature F042`
- Full command: `cargo xtask test-all`
- First failing tests: `glob_double_star_matches_nested_not_sibling_prefix`, `staged_path_outside_active_globs_rejected`, `two_features_overlapping_globs_rejected`, `story_and_its_task_may_overlap`, `active_item_with_unarchived_dependency_rejected`, `conflicting_active_items_rejected`, `self_test_fails_when_control_is_broken`

## Exit criteria

- [ ] Requirement tests SR-S084-01 through SR-S084-07 written first and failing
- [ ] Tasks T167 and T168 complete; `check-ownership` and `self-test` dispatched from `main()`
- [ ] Unit, CLI integration, and E2E tests pass in targeted and full modes; `self-test` green in CI
- [ ] Production call path named: `policy::check_ownership` (called by `policy::audit_staged`) and `policy::self_test` dispatched from `main()` in `automation/xtask/src/main.rs`, invoked by `.githooks/pre-commit` and the `gates.yml` validate step
- [ ] Handoff evidence recorded in the F042 ticket
