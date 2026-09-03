---
id: S085
type: story
status: planned
parent_epic: E000
parent_feature: F043
depends_on: [F041, F042]
owned_paths: [automation/xtask/src/lanes.rs, .lanes/**, .worktrees/**, .agent-target/**, testing/features/F043/**]
feature_flag: F043_FEATURE
branch: s085-lane-claiming
started_at: null
finished_at: null
---

# S085 — Lane claiming

## Identity

- Parent feature: `F043` Fanout orchestration
- Owner: platform
- Branch: `s085-lane-claiming`
- Decision references: `docs/architecture-decisions.md` sections 7, 9, 10; `docs/capability-contracts.md` row F043

## Vertical slice

As an agent, I want `claim-lane <ID>` to check preconditions, move the item into `work/inprogress/`, create my branch and worktree, allocate a slot and a private build target, and record it all in `.lanes/<ID>.toml`, and `release-lane` to reverse it, so that I can start work in isolation with one command and hand it back cleanly.

## Requirements

- **SR-S085-01:** `claim-lane` refuses with exit 3 `lane.precondition` when the item is not planned or ready, a dependency is not archived, a conflict is active, or owned paths overlap another active feature (covers FR-F043-01).
- **SR-S085-02:** A successful claim moves the file, rewrites only `status` and `started_at` (from `XTASK_NOW` or the clock), creates the branch from `origin/main` or `main`, and adds the worktree at `.worktrees/<branch>` (FR-F043-02, FR-F043-03).
- **SR-S085-03:** The lane file is created atomically with all fields, a second claim fails with `lane.exists`, and the slot is the lowest free integer under `flock` on `.lanes/slots.toml` (FR-F043-04, FR-F043-05).
- **SR-S085-04:** `allocate-target <ID>` prints deterministic `export` lines or JSON for `CARGO_TARGET_DIR`, `VITE_CACHE_DIR`, and `PLAYWRIGHT_BROWSERS_PATH` and is idempotent (FR-F043-06, NFR-F043-03).
- **SR-S085-05:** `release-lane --outcome abandoned` restores the planning file, removes the worktree, frees the slot, and deletes the lane file; `--outcome done` is completed in S086 once evidence exists (FR-F043-12).
- **SR-S085-06:** Only the lane owner may release or allocate; `claim-lane --list` and `--repair` work as specified; every command appends to `.lanes/history.log` (FR-F043-13, FR-F043-14, FR-F043-15, NFR-F043-04).
- **SR-S085-07:** `claim-lane` completes in under 5 s with 100 lanes; allocations under 100 ms (NFR-F043-01).

## Surfaces

- Infrastructure/container: `.gitignore` entries `.lanes/`, `.worktrees/`, `.agent-target/`
- Rust service/API: `automation/xtask/src/lanes.rs` (`Lane`, `Slots`, `LaneEvent`, `claim`, `release` abandoned path, `allocate_target`, `list`, `repair`, `slots::{acquire, release}`, `env::export_lines`, `history::append`)
- Data/migration: none; `.lanes/<ID>.toml`, `.lanes/slots.toml`, `.lanes/history.log`
- React/UI: none (no UI)
- Mocks/fixtures: `testing/features/F043/fixtures/graph` (archived S900, planned T900–T903, conflicting F901 active); scratch repository with `main` and a bare `origin`

## TDD harness

- Test path: `testing/features/F043/api/`, `testing/features/F043/database/`, `testing/features/F043/performance/`
- Feature flag: `F043_FEATURE`
- Targeted command: `cargo xtask test-feature F043`
- Full command: `cargo xtask test-all`
- First failing tests: `claim_refused_when_dependency_not_archived`, `claim_moves_file_and_sets_started_at_from_xtask_now`, `claim_creates_branch_and_worktree_from_origin_main`, `second_claim_fails_with_lane_exists`, `concurrent_claims_get_distinct_slots`, `allocate_target_idempotent_export_lines`, `abandon_restores_planning_file_bytes`, `non_owner_release_refused`

## Exit criteria

- [ ] Requirement tests SR-S085-01 through SR-S085-07 written first and failing
- [ ] Tasks T169 and T170 complete; commands dispatched from `main()`
- [ ] Unit, CLI integration, persistence, and performance tests pass in targeted and full modes
- [ ] Production call path named: `lanes::claim`, `lanes::release`, `lanes::allocate_target` dispatched from `main()` in `automation/xtask/src/main.rs`; agents invoke them from the repository root before entering `.worktrees/<branch>`
- [ ] Handoff evidence recorded in the F043 ticket
