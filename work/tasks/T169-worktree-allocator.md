---
id: T169
type: task
status: planned
parent_epic: E000
parent_feature: F043
parent_story: S085
depends_on: [S085]
owned_paths: [automation/xtask/src/lanes.rs, .lanes/**, .worktrees/**, testing/features/F043/api/**, testing/features/F043/requirements/**, testing/features/F043/database/**]
feature_flag: F043_FEATURE
branch: t169-worktree-allocator
started_at: null
finished_at: null
---

# T169 — Worktree allocator

## Identity

- Parent story: `S085` Lane claiming
- Owner: platform
- Branch: `t169-worktree-allocator`
- Decision references: `docs/architecture-decisions.md` sections 7, 9, 10; `docs/capability-contracts.md` row F043

## Objective

Implement `claim-lane` and the abandon path of `release-lane`: preconditions, atomic file move and rewrite, branch and worktree creation, slot registry, lane file, owner enforcement, listing, repair, and history log.

## Specification

- Owned paths: `automation/xtask/src/lanes.rs` (`Lane`, `LaneEvent`, `Slots`, `claim`, `release` abandoned path, `list`, `repair`, `slots::{acquire, release}`, `history::append`, `lanefile::{write_atomic, read}`), `.gitignore` entries for `.lanes/`, `.worktrees/`, `.agent-target/`
- Contract/input: item id; `--base REF`; `XTASK_NOW`; `XTASK_OWNER` else `git config user.email`; `WorkGraph` from F041; `ownership::check_overlap` and dependency gate from F042
- Output/behavior: refusals `lane.precondition`, `lane.exists`, `lane.branch_exists`, `lane.slots_exhausted`, `lane.not_owner`, `lane.dirty`, `lane.inconsistent` with exit 3; the move rewrites only the `status:` and `started_at:` lines; `git worktree add .worktrees/<branch> -b <branch> <base>`; `.lanes/<ID>.toml` written via temp file plus rename with `O_EXCL`; `.lanes/slots.toml` updated under `flock`, lowest free slot in `0..=99`; abandon moves the file back to `work/{tickets,stories,tasks}` by kind, resets `status: planned` and `started_at: null`, removes the worktree (`--force` if dirty), frees the slot, deletes the lane file, purges evidence only with `--purge-evidence`; `--list` prints sorted lanes or `no active lanes`; `--repair` reconciles `work/inprogress/`, `.lanes/`, and `git worktree list --porcelain`; every command appends `<timestamp> <actor> <command> <ID> <result>` to `.lanes/history.log`
- Dependencies: F041 loader; F042 ownership module
- Feature flag: `F043_FEATURE`
- Crates: `toml`, `fs2`

## TDD

- Failing test first: `testing/features/F043/api/claim_tests.rs::claim_refused_when_dependency_not_archived`, `::claim_refused_when_paths_overlap_active_feature`, `::claim_moves_file_and_sets_started_at_from_xtask_now`, `::claim_creates_branch_and_worktree_from_origin_main`, `::second_claim_fails_with_lane_exists`, `::abandon_restores_planning_file_bytes`, `::non_owner_release_refused`, `::list_prints_sorted_lanes`, `testing/features/F043/database/lanefile_tests.rs::lane_file_written_atomically`, `::concurrent_claims_get_distinct_slots`, `::repair_reconciles_missing_worktree`
- Targeted command: `cargo xtask test-feature F043`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: `testing/features/F043/fixtures/graph`; scratch repository with `main` and bare `origin`; two-process claim race harness

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] `claim-lane`, `release-lane --outcome abandoned`, `--list`, `--repair` dispatched from `main()`
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S085
- [ ] `finished_at` recorded
