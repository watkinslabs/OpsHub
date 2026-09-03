---
id: T163
type: task
status: planned
parent_epic: E000
parent_feature: F041
parent_story: S082
depends_on: [T162]
owned_paths: [automation/xtask/src/backlog.rs, automation/xtask/src/content.rs, testing/features/F041/api/**, testing/features/F041/database/**, testing/features/F041/e2e/**]
feature_flag: F041_FEATURE
branch: t163-branch-file-checks
started_at: null
finished_at: null
---

# T163 — Branch/file checks

## Identity

- Parent story: `S082` Story/task schema
- Owner: platform
- Branch: `t163-branch-file-checks`
- Decision references: `docs/architecture-decisions.md` sections 9–10; `docs/capability-contracts.md` row F041

## Objective

Implement filename, branch, owned-path subset, section, marker, lifecycle, and harness-structure checks, wire `validate-tickets`, and bring the live backlog tree to a passing state.

## Specification

- Owned paths: `automation/xtask/src/backlog.rs` (`check_branch_and_file`, `check_owned_paths`, `check_sections`, `check_markers`, `check_lifecycle`, `check_harness`, `validate_tickets`), `automation/xtask/src/content.rs` (templates emit `owned_paths: [testing/features/{id}/**]`, all required headings, and `depends_on` from the plan so skeletons fail only `content.too_thin`)
- Contract/input: `WorkGraph` from T162; slug rule from `support::slug`; catch-all list `services/api/**`, `apps/web/**`, `crates/**`, `testing/features/**`, `services/worker/**`, `services/realtime/**`, `services/mcp/**`, `work/**`, `**`; subset rule: a child glob is a subset when, after splitting on `/`, every parent segment equals the child segment or the parent segment is `**` at the end, or the parent segment `*_x_*.sql` pattern matches the child literal; required heading lists per kind from F041 FR-09; marker list from FR-10; lifecycle rules from FR-11; harness structure from FR-14
- Output/behavior: findings `file.slug_mismatch`, `branch.invalid`, `paths.empty`, `paths.catch_all`, `paths.not_subset` (message shows child and parent globs), `paths.overlap`, `paths.missing_harness_glob`, `section.missing`, `content.too_thin`, `marker.unresolved`, `lifecycle.timestamp`, `lifecycle.status`, `harness.missing`, `harness.uncovered`
- Dependencies: T162 graph loader
- Feature flag: `F041_FEATURE`
- Live-tree gate: the task is not done until `validate-work`, `validate-plan`, and `validate-tickets` exit 0 on the repository

## TDD

- Failing test first: `testing/features/F041/api/paths_tests.rs::story_glob_outside_feature_is_not_subset`, `::feature_catch_all_glob_rejected`, `::migration_glob_narrower_pattern_is_subset`, `testing/features/F041/api/sections_tests.rs::missing_gherkin_block_is_section_missing`, `::changed_event_without_v1_is_marker`, `::inprogress_file_without_started_at_rejected`, `testing/features/F041/api/harness_tests.rs::harness_missing_lane_reported`, `::requirements_cases_must_cite_every_fr`, `testing/features/F041/e2e/hooks.spec.sh::pre_commit_blocks_invalid_ticket`
- Targeted command: `cargo xtask test-feature F041`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/features/F041/fixtures/{catch_all,thin,lifecycle,harness_missing}`; scratch clone with hooks installed for the E2E case

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] Repository tree passes all three commands; `scaffold-plan` output on a fixture plan passes except `content.too_thin`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S082
- [ ] `finished_at` recorded
