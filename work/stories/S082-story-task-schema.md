---
id: S082
type: story
status: planned
parent_epic: E000
parent_feature: F041
depends_on: [S081]
owned_paths: [automation/xtask/src/backlog.rs, automation/xtask/src/content.rs, automation/xtask/src/support.rs, testing/features/F041/**]
feature_flag: F041_FEATURE
branch: s082-story-task-schema
started_at: null
finished_at: null
---

# S082 — Story/task schema

## Identity

- Parent feature: `F041` Work-item schema
- Owner: platform
- Branch: `s082-story-task-schema`
- Decision references: `docs/architecture-decisions.md` sections 9–10; `docs/capability-contracts.md` row F041

## Vertical slice

As a maintainer, I want every story and task file to be checked for branch and filename agreement, ownership narrower than its feature, required sections, scaffold markers, lifecycle timestamps, harness structure, and the 500-line limit, so that an agent claiming a task inherits a complete, bounded contract.

## Requirements

- **SR-S082-01:** Filename stem equals `{id}-{slug(title)}` and `branch` equals the stem with a lower-case id; mismatches are `file.slug_mismatch` and `branch.invalid` (covers FR-F041-04).
- **SR-S082-02:** `owned_paths` is non-empty, contains no catch-all glob, every story and task glob is equal to or narrower than a parent-feature glob, and features include `testing/features/{id}/**`; overlapping feature globs without `conflicts_with` are `paths.overlap` (FR-F041-08).
- **SR-S082-03:** Required headings per kind and the gherkin block with at least three scenarios are present (`section.missing`), and requirement-count minimums are enforced (`content.too_thin`) (FR-F041-09, FR-F041-10).
- **SR-S082-04:** The forbidden marker list and backticked event names ending in .changed rather than .v1 are `marker.unresolved` (FR-F041-10).
- **SR-S082-05:** Lifecycle status and timestamps agree with the directory (`lifecycle.timestamp`, `lifecycle.status`) (FR-F041-11).
- **SR-S082-06:** Every text file outside excluded directories with more than 500 lines is `line.limit`; binary files are skipped; the scan streams (FR-F041-12, NFR-F041-01).
- **SR-S082-07:** `validate-tickets` additionally checks `testing/features/{id}/` structure, `feature.toml` values, and that `requirements/cases.md` cites every declared FR/NFR (FR-F041-14).
- **SR-S082-08:** `content.rs` scaffold output for a new plan row passes `validate-work` except for `content.too_thin`, proving the templates and schema agree (FR-F041-09).

## Surfaces

- Infrastructure/container: none
- Rust service/API: `automation/xtask/src/backlog.rs` (`check_branch_and_file`, `check_sections`, `check_markers`, `check_owned_paths`, `check_lifecycle`, `check_harness`, `validate_tickets`); `automation/xtask/src/support.rs` (`slug`, `check_line_limits` streaming rewrite, `is_binary`); `automation/xtask/src/content.rs` (template alignment)
- Data/migration: none
- React/UI: none (no UI)
- Mocks/fixtures: `testing/features/F041/fixtures/{catch_all,thin,lifecycle,long_file,harness_missing}`; a 20,000-file generated tree for the performance lane built by `testing/harness/repo.rs::wide_tree(20_000)`

## TDD harness

- Test path: `testing/features/F041/{api,database,performance,e2e}/`
- Feature flag: `F041_FEATURE`
- Targeted command: `cargo xtask test-feature F041`
- Full command: `cargo xtask test-all`
- First failing tests: `story_glob_outside_feature_is_not_subset`, `feature_catch_all_glob_rejected`, `missing_gherkin_block_is_section_missing`, `inprogress_file_without_started_at_rejected`, `file_with_501_lines_reported`, `harness_missing_lane_reported`, `scaffolded_skeleton_only_fails_too_thin`

## Exit criteria

- [ ] Requirement tests SR-S082-01 through SR-S082-08 written first and failing
- [ ] Tasks T163 and T164 complete; `validate-tickets` dispatched from `main()`
- [ ] The live repository tree passes all three commands with exit 0
- [ ] Unit, CLI integration, performance, and hook E2E tests pass in targeted and full modes
- [ ] Production call path named: `backlog::validate_tickets` and `support::check_line_limits` dispatched from `main()` in `automation/xtask/src/main.rs`, invoked by `.githooks/pre-push` and `gates.yml`
- [ ] Handoff evidence recorded in the F041 ticket
