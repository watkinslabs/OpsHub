---
id: T170
type: task
status: planned
parent_epic: E000
parent_feature: F043
parent_story: S085
depends_on: [T169]
owned_paths: [automation/xtask/src/lanes.rs, .agent-target/**, testing/features/F043/api/**, testing/features/F043/accessibility/**, testing/features/F043/performance/**]
feature_flag: F043_FEATURE
branch: t170-target-dir-allocator
started_at: null
finished_at: null
---

# T170 — Target-dir allocator

## Identity

- Parent story: `S085` Lane claiming
- Owner: platform
- Branch: `t170-target-dir-allocator`
- Decision references: `docs/architecture-decisions.md` sections 1, 9; `docs/capability-contracts.md` row F043

## Objective

Implement `allocate-target` and the shared `env::export_lines` writer so each lane builds into its own `.agent-target/<branch>` with `eval`-safe output, and prove the claim and allocation time budgets.

## Specification

- Owned paths: `automation/xtask/src/lanes.rs` (`TargetEnv`, `allocate_target`, `env::export_lines`, `env::shell_quote`)
- Contract/input: lane id with an existing `.lanes/<ID>.toml`; owner check per FR-F043-13
- Output/behavior: `CARGO_TARGET_DIR=.agent-target/<branch>` (absolute path printed, directory created with mode 0755), `VITE_CACHE_DIR=<target>/vite`, `PLAYWRIGHT_BROWSERS_PATH=$HOME/.cache/ms-playwright`; text mode prints `export KEY='value'` with single-quote escaping so `eval "$(…)"` is safe in sh, bash, and zsh; `--json` prints `{ "id", "target_dir", "vite_cache_dir", "playwright_browsers_path" }`; values stored back into the lane file under the `target_dirs` table; repeated calls produce identical output and no changes; `allocate-target` completes in under 100 ms; `claim-lane` under 5 s with 100 existing lanes
- Dependencies: T169 lane file and owner check
- Feature flag: `F043_FEATURE`
- Note: `support::check_line_limits` already excludes `.agent-target`; T170 adds `.worktrees` and `.lanes` to the exclusion list through the F041 constant

## TDD

- Failing test first: `testing/features/F043/api/target_tests.rs::allocate_target_idempotent_export_lines`, `::allocate_target_json_shape`, `::allocate_target_creates_directory_once`, `::allocate_target_non_owner_refused`, `testing/features/F043/accessibility/output_tests.rs::export_lines_eval_safe_with_spaces_and_quotes`, `::no_color_and_ascii_only`, `testing/features/F043/performance/lane_bench.rs::claim_under_5s_with_100_lanes`, `::allocate_under_100ms`
- Targeted command: `cargo xtask test-feature F043`
- Full command: `cargo xtask test-all`
- Fixtures/mocks: lane file fixtures with a branch name containing a quote and a space; 100 pre-generated lane files

## Exit criteria

- [ ] Tests written before implementation and observed failing
- [ ] `allocate-target` dispatched from `main()`; `eval` round trip verified in sh, bash, and zsh on CI
- [ ] Owned-path check passes
- [ ] File limit and lint gates pass
- [ ] Handoff evidence recorded in S085
- [ ] `finished_at` recorded
