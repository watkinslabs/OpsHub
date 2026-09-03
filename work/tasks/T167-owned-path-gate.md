---
id: T167
type: task
status: planned
parent_epic: E000
parent_feature: F042
parent_story: S084
depends_on: [T166]
owned_paths: [automation/xtask/src/policy.rs, testing/features/F042/api/**, testing/features/F042/database/**]
feature_flag: F042_FEATURE
branch: t167-owned-path-gate
started_at: null
finished_at: null
---

# T167 — Owned-path gate

## Identity

- Parent story: `S084` Ticket/ownership audit
- Owner: platform
- Branch: `t167-owned-path-gate`
- Decision references: `docs/architecture-decisions.md` sections 9–10; `docs/capability-contracts.md` row F042

## Objective

Replace the prefix-based ownership check with `globset` matching over active items, including overlap and ambiguity detection across features, and wire it into both `check-ownership` and `audit-staged`.

## Specification

- Owned paths: `automation/xtask/src/policy.rs` (`ownership::{check_paths, check_overlap, glob_may_overlap}`, `check_ownership`, ownership half of `audit_staged`)
- Contract/input: staged paths from `git diff --cached --name-only -z --diff-filter=ACMR`; active items with compiled `GlobSet` per item; policy-file exemption from `support::policy_file`
- Output/behavior: `ownership.outside <path>: not matched by owned_paths of active items <ids>`; `ownership.overlap <a> and <b>: <glob a> and <glob b> can match the same path` computed by segment-wise comparison where `**` matches any suffix, `*` any single segment, and `*_x_*.sql` literals are compared by pattern intersection; items sharing a `parent_feature` never overlap; `ownership.ambiguous <path>: matched by <feature a> and <feature b>`; empty `work/inprogress/` prints `check-ownership skipped: no active items` and exits 0; `--json` includes `checked: { files, active_items }`
- Dependencies: T166 `OwnershipSet` and `load_active`
- Feature flag: `F042_FEATURE`
- Limits: ≤ 64 active items, ≤ 10,000 staged paths

## TDD

- Failing test first: `testing/features/F042/api/ownership_tests.rs::glob_double_star_matches_nested_not_sibling_prefix`, `::staged_path_outside_active_globs_rejected`, `::policy_file_never_outside`, `::two_features_overlapping_globs_rejected`, `::story_and_its_task_may_overlap`, `::staged_path_matched_by_two_features_is_ambiguous`, `::empty_inprogress_skips_with_exit_zero`, `testing/features/F042/database/index_tests.rs::deleted_staged_path_not_checked`, `::renamed_path_checked_at_destination`
- Targeted command: `cargo xtask test-feature F042`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/features/F042/fixtures/{ownership,overlap}`; scratch repositories with staged adds, renames, and deletes

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] `support::check_ownership` prefix implementation removed; `audit-staged` and `check-ownership` share `ownership::check_paths`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S084
- [ ] `finished_at` recorded
